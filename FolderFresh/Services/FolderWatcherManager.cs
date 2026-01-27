using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using FolderFresh.Models;
using Microsoft.UI.Dispatching;

namespace FolderFresh.Services;

/// <summary>
/// Manages multiple FileSystemWatcher instances for watched folders.
/// Handles debouncing, event aggregation, and organization triggering.
/// </summary>
public class FolderWatcherManager : IDisposable
{
    private readonly WatchedFolderService _watchedFolderService;
    private readonly ProfileService _profileService;
    private readonly RuleService _ruleService;
    private readonly CategoryService _categoryService;
    private readonly SettingsService _settingsService;
    private readonly DispatcherQueue? _dispatcherQueue;

    private readonly ConcurrentDictionary<string, FileSystemWatcher> _watchers = new();
    private readonly ConcurrentDictionary<string, long> _debounceCounters = new();
    private readonly ConcurrentDictionary<string, List<FileChangeInfo>> _pendingChanges = new();
    private readonly ConcurrentDictionary<string, DateTime> _recentlyOrganizedFiles = new();
    private readonly ConcurrentDictionary<string, PendingRenameInfo> _pendingRenames = new();
    private readonly object _lockObject = new();

    private const int DebounceDelayMs = 1000;
    private const int PendingRenameTimeoutMs = 5000; // Wait up to 5 seconds for user to finish renaming
    private const int RecentlyOrganizedExpirySeconds = 5;
    private const int MaxFileAccessRetries = 3;
    private const int FileAccessRetryDelayMs = 500;
    private bool _disposed;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    /// <summary>
    /// Raised when files in a watched folder change.
    /// </summary>
    public event EventHandler<FolderChangedEventArgs>? FolderChanged;

    /// <summary>
    /// Raised when automatic organization is requested (for AutoOrganize folders).
    /// </summary>
    public event EventHandler<OrganizationRequestedEventArgs>? OrganizationRequested;

    /// <summary>
    /// Raised when a watcher's status changes.
    /// </summary>
    public event EventHandler<WatcherStatusChangedEventArgs>? StatusChanged;

    /// <summary>
    /// Raised when organization completes.
    /// </summary>
    public event EventHandler<OrganizationCompletedEventArgs>? OrganizationCompleted;

    public FolderWatcherManager(
        WatchedFolderService watchedFolderService,
        ProfileService profileService,
        RuleService ruleService,
        CategoryService categoryService,
        SettingsService settingsService,
        DispatcherQueue? dispatcherQueue = null)
    {
        _watchedFolderService = watchedFolderService;
        _profileService = profileService;
        _ruleService = ruleService;
        _categoryService = categoryService;
        _settingsService = settingsService;
        _dispatcherQueue = dispatcherQueue;
    }

    /// <summary>
    /// Starts watching a folder for file changes.
    /// </summary>
    /// <param name="folder">The watched folder configuration.</param>
    /// <returns>True if watcher started successfully, false if folder is inaccessible.</returns>
    public async Task<bool> StartWatchingAsync(WatchedFolder folder)
    {
        if (_disposed) return false;

        // Validate folder is accessible
        var (isValid, error) = _watchedFolderService.ValidateFolderPath(folder.FolderPath);
        if (!isValid)
        {
            await UpdateFolderStatusAsync(folder, WatchStatus.Error, error);
            return false;
        }

        // Stop existing watcher if any
        StopWatching(folder.Id);

        try
        {
            // Get profile settings for IncludeSubfolders
            var includeSubfolders = true; // Default
            var profile = _profileService.GetProfile(folder.ProfileId);
            if (profile != null && !string.IsNullOrEmpty(profile.SettingsJson))
            {
                try
                {
                    var settings = JsonSerializer.Deserialize<AppSettings>(profile.SettingsJson, JsonOptions);
                    if (settings != null)
                    {
                        includeSubfolders = settings.IncludeSubfolders;
                    }
                }
                catch { /* Use default */ }
            }

            var watcher = new FileSystemWatcher(folder.FolderPath)
            {
                NotifyFilter = NotifyFilters.FileName | NotifyFilters.DirectoryName | NotifyFilters.LastWrite | NotifyFilters.CreationTime,
                IncludeSubdirectories = includeSubfolders,
                EnableRaisingEvents = true
            };

            // Set up event handlers
            watcher.Created += (s, e) => OnFileCreated(folder.Id, e);
            watcher.Changed += (s, e) => OnFileSystemEvent(folder.Id, e, FileChangeType.Modified);
            watcher.Deleted += (s, e) => OnFileSystemEvent(folder.Id, e, FileChangeType.Deleted);
            watcher.Renamed += (s, e) => OnFileRenamed(folder.Id, e);
            watcher.Error += (s, e) => OnWatcherError(folder.Id, e);

            _watchers[folder.Id] = watcher;
            _pendingChanges[folder.Id] = new List<FileChangeInfo>();

            await UpdateFolderStatusAsync(folder, WatchStatus.Watching, null);
            return true;
        }
        catch (Exception ex)
        {
            await UpdateFolderStatusAsync(folder, WatchStatus.Error, $"Failed to start watcher: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// Stops watching a folder.
    /// </summary>
    /// <param name="watchedFolderId">ID of the watched folder.</param>
    public void StopWatching(string watchedFolderId)
    {
        // Increment debounce counter to invalidate any pending debounce operations
        _debounceCounters.AddOrUpdate(watchedFolderId, 1, (_, count) => count + 1);

        // Remove and dispose watcher
        if (_watchers.TryRemove(watchedFolderId, out var watcher))
        {
            watcher.EnableRaisingEvents = false;
            watcher.Dispose();
        }

        // Clear pending changes
        _pendingChanges.TryRemove(watchedFolderId, out _);

        // Update status
        var folder = _watchedFolderService.GetWatchedFolder(watchedFolderId);
        if (folder != null && folder.Status != WatchStatus.Error)
        {
            var oldStatus = folder.Status;
            folder.Status = WatchStatus.Idle;
            folder.LastError = null;

            RaiseStatusChanged(watchedFolderId, oldStatus, WatchStatus.Idle, null);

            // Save asynchronously
            _ = _watchedFolderService.UpdateWatchedFolderAsync(folder);
        }
    }

    /// <summary>
    /// Stops all active watchers. Used on app shutdown.
    /// </summary>
    public void StopAllWatching()
    {
        var folderIds = _watchers.Keys.ToList();
        foreach (var folderId in folderIds)
        {
            StopWatching(folderId);
        }
    }

    /// <summary>
    /// Checks if a folder is currently being watched.
    /// </summary>
    public bool IsWatching(string watchedFolderId)
    {
        return _watchers.ContainsKey(watchedFolderId);
    }

    /// <summary>
    /// Restarts watching a folder (for configuration changes).
    /// </summary>
    public async Task<bool> RestartWatching(string watchedFolderId)
    {
        var folder = _watchedFolderService.GetWatchedFolder(watchedFolderId);
        if (folder == null) return false;

        StopWatching(watchedFolderId);

        if (folder.IsEnabled)
        {
            return await StartWatchingAsync(folder);
        }

        return true;
    }

    /// <summary>
    /// Restarts all watchers that are using a specific profile.
    /// Call this when profile settings change to apply new settings.
    /// </summary>
    /// <param name="profileId">The profile ID whose watchers should be restarted.</param>
    public async Task RestartWatchersByProfileAsync(string profileId)
    {
        var folders = _watchedFolderService.GetWatchedFolders()
            .Where(f => f.ProfileId == profileId && f.IsEnabled && IsWatching(f.Id))
            .ToList();

        foreach (var folder in folders)
        {
            await RestartWatching(folder.Id);
        }
    }

    /// <summary>
    /// Restarts all active watchers.
    /// Call this when global settings change that affect all watchers.
    /// </summary>
    public async Task RestartAllWatchersAsync()
    {
        var folderIds = _watchers.Keys.ToList();

        foreach (var folderId in folderIds)
        {
            await RestartWatching(folderId);
        }
    }

    /// <summary>
    /// Gets the count of active watchers.
    /// </summary>
    public int GetActiveWatcherCount()
    {
        return _watchers.Count;
    }

    /// <summary>
    /// Manually triggers organization for a watched folder.
    /// </summary>
    /// <param name="watchedFolderId">ID of the watched folder.</param>
    /// <param name="previewOnly">If true, returns what would happen without moving files.</param>
    /// <returns>Organization result with counts and any errors.</returns>
    public async Task<OrganizationResult> OrganizeFolderAsync(string watchedFolderId, bool previewOnly = false)
    {
        var result = new OrganizationResult();

        var folder = _watchedFolderService.GetWatchedFolder(watchedFolderId);
        if (folder == null)
        {
            result.Errors.Add("Watched folder not found.");
            return result;
        }

        // Validate folder is accessible
        var (isValid, error) = _watchedFolderService.ValidateFolderPath(folder.FolderPath);
        if (!isValid)
        {
            await UpdateFolderStatusAsync(folder, WatchStatus.Error, error);
            result.Errors.Add(error ?? "Folder is not accessible.");
            return result;
        }

        // Get the profile for this folder
        var profile = _profileService.GetProfile(folder.ProfileId);
        if (profile == null)
        {
            result.Errors.Add($"Profile not found: {folder.ProfileId}");
            return result;
        }

        // Set status to Organizing
        var previousStatus = folder.Status;
        await UpdateFolderStatusAsync(folder, WatchStatus.Organizing, null);

        try
        {
            // Load profile's rules and categories temporarily
            var (rules, categories, settings) = await LoadProfileDataAsync(profile);

            // Scan and organize files
            result = await ScanAndOrganizeAsync(folder, rules, categories, settings, previewOnly);

            // Update last organized timestamp if not preview
            if (!previewOnly && result.FilesMoved > 0)
            {
                folder.LastOrganizedAt = DateTime.Now;
            }

            // Update file count
            folder.FileCount = result.TotalFilesScanned;

            result.Success = result.Errors.Count == 0;
        }
        catch (Exception ex)
        {
            result.Errors.Add($"Organization failed: {ex.Message}");
            await UpdateFolderStatusAsync(folder, WatchStatus.Error, ex.Message);
        }
        finally
        {
            // Restore previous status (or Watching if was Idle and enabled)
            if (folder.Status == WatchStatus.Organizing)
            {
                var newStatus = folder.IsEnabled && IsWatching(watchedFolderId) ? WatchStatus.Watching : WatchStatus.Idle;
                await UpdateFolderStatusAsync(folder, newStatus, null);
            }

            // Raise completion event
            OrganizationCompleted?.Invoke(this, new OrganizationCompletedEventArgs(
                watchedFolderId,
                result.FilesMoved,
                result.FilesSkipped,
                result.Errors));
        }

        return result;
    }

    private void OnFileCreated(string watchedFolderId, FileSystemEventArgs e)
    {
        if (_disposed) return;

        // Skip directory changes
        if (Directory.Exists(e.FullPath))
            return;

        // Skip recently organized files to prevent loops
        if (IsRecentlyOrganizedFile(e.FullPath))
            return;

        // Skip files that look like incomplete downloads
        if (IsIncompleteDownload(e.FullPath))
            return;

        // Check if this is a file with a default Windows name (user might be renaming it)
        if (IsLikelyBeingRenamed(e.FullPath))
        {
            // Track this file as pending rename - wait for Renamed event or timeout
            var pendingInfo = new PendingRenameInfo
            {
                OriginalPath = e.FullPath,
                WatchedFolderId = watchedFolderId,
                CreatedAt = DateTime.Now
            };
            _pendingRenames[e.FullPath.ToLowerInvariant()] = pendingInfo;

            // Start a delayed task that will process the file if no rename happens
            _ = ProcessPendingRenameAfterTimeoutAsync(e.FullPath, watchedFolderId);
            return;
        }

        // Regular file creation - add to pending changes
        AddPendingChange(watchedFolderId, e.FullPath, FileChangeType.Created);
        StartDebounceTimer(watchedFolderId);
    }

    private void OnFileRenamed(string watchedFolderId, RenamedEventArgs e)
    {
        if (_disposed) return;

        // Skip directory changes
        if (Directory.Exists(e.FullPath))
            return;

        // Check if this was a file we were tracking as pending rename
        var oldPathKey = e.OldFullPath.ToLowerInvariant();
        if (_pendingRenames.TryRemove(oldPathKey, out var pendingInfo))
        {
            // User finished renaming - use the new path
            // Skip if the new file was recently organized
            if (!IsRecentlyOrganizedFile(e.FullPath) && !IsIncompleteDownload(e.FullPath))
            {
                AddPendingChange(watchedFolderId, e.FullPath, FileChangeType.Created);
                StartDebounceTimer(watchedFolderId);
            }
            return;
        }

        // Regular rename event - treat as a created file with new name
        if (!IsRecentlyOrganizedFile(e.FullPath) && !IsIncompleteDownload(e.FullPath))
        {
            AddPendingChange(watchedFolderId, e.FullPath, FileChangeType.Renamed);
            StartDebounceTimer(watchedFolderId);
        }
    }

    private void OnFileSystemEvent(string watchedFolderId, FileSystemEventArgs e, FileChangeType changeType)
    {
        if (_disposed) return;

        // Skip directory changes for organization (we only organize files)
        if (Directory.Exists(e.FullPath) && changeType != FileChangeType.Deleted)
            return;

        // Skip recently organized files to prevent loops
        if (IsRecentlyOrganizedFile(e.FullPath))
            return;

        // Skip files that look like incomplete downloads
        if (IsIncompleteDownload(e.FullPath))
            return;

        // Add to pending changes
        AddPendingChange(watchedFolderId, e.FullPath, changeType);

        // Start/reset debounce timer
        StartDebounceTimer(watchedFolderId);
    }

    private void AddPendingChange(string watchedFolderId, string filePath, FileChangeType changeType)
    {
        lock (_lockObject)
        {
            if (_pendingChanges.TryGetValue(watchedFolderId, out var changes))
            {
                changes.Add(new FileChangeInfo
                {
                    FilePath = filePath,
                    ChangeType = changeType,
                    Timestamp = DateTime.Now
                });
            }
        }
    }

    private async Task ProcessPendingRenameAfterTimeoutAsync(string originalPath, string watchedFolderId)
    {
        try
        {
            await Task.Delay(PendingRenameTimeoutMs);

            // Check if still pending (wasn't renamed in the meantime)
            var pathKey = originalPath.ToLowerInvariant();
            if (_pendingRenames.TryRemove(pathKey, out _))
            {
                // User didn't rename the file - process it with original name if it still exists
                if (File.Exists(originalPath) && !IsRecentlyOrganizedFile(originalPath))
                {
                    AddPendingChange(watchedFolderId, originalPath, FileChangeType.Created);
                    StartDebounceTimer(watchedFolderId);
                }
            }
        }
        catch
        {
            // Ignore errors in timeout processing
        }
    }

    /// <summary>
    /// Checks if a file was recently organized (to prevent loops).
    /// </summary>
    private bool IsRecentlyOrganizedFile(string filePath)
    {
        CleanupExpiredRecentlyOrganizedFiles();

        var normalizedPath = filePath.ToLowerInvariant();
        if (_recentlyOrganizedFiles.TryGetValue(normalizedPath, out var timestamp))
        {
            return (DateTime.Now - timestamp).TotalSeconds < RecentlyOrganizedExpirySeconds;
        }
        return false;
    }

    /// <summary>
    /// Marks a file as recently organized.
    /// </summary>
    private void MarkAsRecentlyOrganized(string filePath)
    {
        var normalizedPath = filePath.ToLowerInvariant();
        _recentlyOrganizedFiles[normalizedPath] = DateTime.Now;
    }

    /// <summary>
    /// Removes expired entries from the recently organized files cache.
    /// </summary>
    private void CleanupExpiredRecentlyOrganizedFiles()
    {
        var expiredKeys = _recentlyOrganizedFiles
            .Where(kvp => (DateTime.Now - kvp.Value).TotalSeconds > RecentlyOrganizedExpirySeconds * 2)
            .Select(kvp => kvp.Key)
            .ToList();

        foreach (var key in expiredKeys)
        {
            _recentlyOrganizedFiles.TryRemove(key, out _);
        }
    }

    /// <summary>
    /// Checks if a file appears to be an incomplete download.
    /// </summary>
    private static bool IsIncompleteDownload(string filePath)
    {
        var extension = Path.GetExtension(filePath).ToLowerInvariant();
        var incompleteExtensions = new[]
        {
            ".part",        // Firefox, others
            ".crdownload",  // Chrome
            ".partial",     // IE/Edge
            ".download",    // Safari
            ".tmp",         // Various
            ".temp",        // Various
            ".!ut",         // uTorrent
            ".bc!",         // BitComet
            ".aria2"        // aria2
        };

        return incompleteExtensions.Contains(extension);
    }

    /// <summary>
    /// Checks if a file is accessible (not locked by another process).
    /// </summary>
    private static bool IsFileAccessible(string filePath)
    {
        if (!File.Exists(filePath))
            return false;

        try
        {
            using var stream = File.Open(filePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            return true;
        }
        catch (IOException)
        {
            return false;
        }
        catch (UnauthorizedAccessException)
        {
            return false;
        }
    }

    /// <summary>
    /// Checks if a file appears to be a newly created file that the user might be
    /// in the process of renaming. Uses both language-independent heuristics (file age/size)
    /// and localized name patterns for common European languages.
    /// </summary>
    private static bool IsLikelyBeingRenamed(string filePath)
    {
        try
        {
            var fileInfo = new FileInfo(filePath);
            if (!fileInfo.Exists)
                return false;

            var ageSeconds = (DateTime.Now - fileInfo.CreationTime).TotalSeconds;

            // Very recently created file (< 2 sec) - always wait for potential rename
            if (ageSeconds < 2)
                return true;

            // Empty file created in last 10 seconds - likely a new file being renamed
            if (fileInfo.Length == 0 && ageSeconds < 10)
                return true;

            // Small file (< 1KB) created in last 5 seconds - may be a template file being renamed
            if (fileInfo.Length < 1024 && ageSeconds < 5)
                return true;

            // Check for localized default file name patterns (improves UX by extending wait time)
            if (HasDefaultFileName(filePath))
                return true;
        }
        catch
        {
            // If we can't check the file, assume it's not being renamed
            return false;
        }

        return false;
    }

    /// <summary>
    /// Checks if a file has a default Windows name pattern in any of the supported languages.
    /// Covers the 15 most common European languages.
    /// </summary>
    private static bool HasDefaultFileName(string filePath)
    {
        var fileName = Path.GetFileNameWithoutExtension(filePath);
        if (string.IsNullOrEmpty(fileName))
            return false;

        // Default file name patterns for 15 European languages
        // Format: "New Text Document" equivalents and common variations
        var defaultNamePatterns = new[]
        {
            // English
            "New Text Document", "New Bitmap image", "New Microsoft Word Document",
            "New Microsoft Excel Worksheet", "New Microsoft PowerPoint Presentation",
            "New Rich Text Document", "New Shortcut", "New Folder",
            "New WinRAR archive", "New 7-Zip archive", "New Compressed (zipped) Folder",

            // German (Deutsch)
            "Neues Textdokument", "Neues Bitmap", "Neues Microsoft Word-Dokument",
            "Neues Microsoft Excel-Arbeitsblatt", "Neues Microsoft PowerPoint-Präsentation",
            "Neues RTF-Dokument", "Neue Verknüpfung", "Neuer Ordner",
            "Neues WinRAR-Archiv", "Neues 7-Zip-Archiv", "Neuer komprimierter (gezippter) Ordner",

            // French (Français)
            "Nouveau document texte", "Nouvelle image Bitmap", "Nouveau Document Microsoft Word",
            "Nouvelle Feuille de calcul Microsoft Excel", "Nouvelle Présentation Microsoft PowerPoint",
            "Nouveau document RTF", "Nouveau raccourci", "Nouveau dossier",
            "Nouvelle archive WinRAR", "Nouvelle archive 7-Zip", "Dossier compressé",

            // Spanish (Español)
            "Nuevo documento de texto", "Nueva imagen de mapa de bits", "Nuevo Documento de Microsoft Word",
            "Nueva Hoja de cálculo de Microsoft Excel", "Nueva Presentación de Microsoft PowerPoint",
            "Nuevo documento de texto enriquecido", "Nuevo acceso directo", "Nueva carpeta",
            "Nuevo archivo WinRAR", "Nuevo archivo 7-Zip", "Carpeta comprimida",

            // Italian (Italiano)
            "Nuovo documento di testo", "Nuova immagine bitmap", "Nuovo Documento di Microsoft Word",
            "Nuovo Foglio di lavoro di Microsoft Excel", "Nuova Presentazione di Microsoft PowerPoint",
            "Nuovo documento RTF", "Nuovo collegamento", "Nuova cartella",
            "Nuovo archivio WinRAR", "Nuovo archivio 7-Zip", "Cartella compressa",

            // Portuguese (Português)
            "Novo Documento de Texto", "Nova Imagem de Bitmap", "Novo Documento do Microsoft Word",
            "Nova Planilha do Microsoft Excel", "Nova Apresentação do Microsoft PowerPoint",
            "Novo Documento de Texto Formatado", "Novo Atalho", "Nova pasta",
            "Novo arquivo WinRAR", "Novo arquivo 7-Zip", "Pasta compactada",

            // Dutch (Nederlands)
            "Nieuw tekstdocument", "Nieuwe Bitmap-afbeelding", "Nieuw Microsoft Word-document",
            "Nieuw Microsoft Excel-werkblad", "Nieuwe Microsoft PowerPoint-presentatie",
            "Nieuw RTF-document", "Nieuwe snelkoppeling", "Nieuwe map",
            "Nieuw WinRAR-archief", "Nieuw 7-Zip-archief", "Gecomprimeerde map",

            // Polish (Polski)
            "Nowy dokument tekstowy", "Nowa mapa bitowa", "Nowy Dokument programu Microsoft Word",
            "Nowy Arkusz programu Microsoft Excel", "Nowa Prezentacja programu Microsoft PowerPoint",
            "Nowy dokument RTF", "Nowy skrót", "Nowy folder",
            "Nowe archiwum WinRAR", "Nowe archiwum 7-Zip", "Skompresowany folder",

            // Swedish (Svenska)
            "Nytt textdokument", "Ny bitmappsbild", "Nytt Microsoft Word-dokument",
            "Nytt Microsoft Excel-kalkylblad", "Ny Microsoft PowerPoint-presentation",
            "Nytt RTF-dokument", "Ny genväg", "Ny mapp",
            "Nytt WinRAR-arkiv", "Nytt 7-Zip-arkiv", "Komprimerad mapp",

            // Danish (Dansk)
            "Nyt tekstdokument", "Nyt bitmapbillede", "Nyt Microsoft Word-dokument",
            "Nyt Microsoft Excel-regneark", "Ny Microsoft PowerPoint-præsentation",
            "Nyt RTF-dokument", "Ny genvej", "Ny mappe",
            "Nyt WinRAR-arkiv", "Nyt 7-Zip-arkiv", "Komprimeret mappe",

            // Norwegian (Norsk)
            "Nytt tekstdokument", "Nytt punktgrafikkbilde", "Nytt Microsoft Word-dokument",
            "Nytt Microsoft Excel-regneark", "Ny Microsoft PowerPoint-presentasjon",
            "Nytt RTF-dokument", "Ny snarvei", "Ny mappe",
            "Nytt WinRAR-arkiv", "Nytt 7-Zip-arkiv", "Komprimert mappe",

            // Finnish (Suomi)
            "Uusi tekstiasiakirja", "Uusi bittikarttakuva", "Uusi Microsoft Word -asiakirja",
            "Uusi Microsoft Excel -laskentataulukko", "Uusi Microsoft PowerPoint -esitys",
            "Uusi RTF-asiakirja", "Uusi pikakuvake", "Uusi kansio",
            "Uusi WinRAR-arkisto", "Uusi 7-Zip-arkisto", "Pakattu kansio",

            // Czech (Čeština)
            "Nový textový dokument", "Nový rastrový obrázek", "Nový dokument aplikace Microsoft Word",
            "Nový list aplikace Microsoft Excel", "Nová prezentace aplikace Microsoft PowerPoint",
            "Nový dokument RTF", "Nový zástupce", "Nová složka",
            "Nový archiv WinRAR", "Nový archiv 7-Zip", "Komprimovaná složka",

            // Hungarian (Magyar)
            "Új szöveges dokumentum", "Új bitképes kép", "Új Microsoft Word-dokumentum",
            "Új Microsoft Excel-munkalap", "Új Microsoft PowerPoint-bemutató",
            "Új RTF-dokumentum", "Új parancsikon", "Új mappa",
            "Új WinRAR-archívum", "Új 7-Zip archívum", "Tömörített mappa",

            // Greek (Ελληνικά)
            "Νέο έγγραφο κειμένου", "Νέα εικόνα Bitmap", "Νέο Έγγραφο του Microsoft Word",
            "Νέο Φύλλο εργασίας του Microsoft Excel", "Νέα Παρουσίαση του Microsoft PowerPoint",
            "Νέο έγγραφο RTF", "Νέα συντόμευση", "Νέος φάκελος",
            "Νέο αρχείο WinRAR", "Νέο αρχείο 7-Zip", "Συμπιεσμένος φάκελος",

            // Romanian (Română)
            "Document text nou", "Imagine bitmap nouă", "Document Microsoft Word nou",
            "Foaie de calcul Microsoft Excel nouă", "Prezentare Microsoft PowerPoint nouă",
            "Document RTF nou", "Comandă rapidă nouă", "Folder nou",
            "Arhivă WinRAR nouă", "Arhivă 7-Zip nouă", "Folder comprimat"
        };

        foreach (var pattern in defaultNamePatterns)
        {
            if (fileName.Equals(pattern, StringComparison.OrdinalIgnoreCase))
                return true;

            // Check for numbered variants like "New Text Document (2)" or "Neues Textdokument (2)"
            if (fileName.StartsWith(pattern, StringComparison.OrdinalIgnoreCase) &&
                fileName.Length > pattern.Length)
            {
                var suffix = fileName.Substring(pattern.Length).Trim();
                if (suffix.StartsWith("(") && suffix.EndsWith(")"))
                    return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Waits for a file to become accessible with retries.
    /// </summary>
    private static async Task<bool> WaitForFileAccessAsync(string filePath, int maxRetries = MaxFileAccessRetries)
    {
        for (int i = 0; i < maxRetries; i++)
        {
            if (IsFileAccessible(filePath))
                return true;

            await Task.Delay(FileAccessRetryDelayMs);
        }
        return IsFileAccessible(filePath);
    }

    private void OnWatcherError(string watchedFolderId, ErrorEventArgs e)
    {
        var folder = _watchedFolderService.GetWatchedFolder(watchedFolderId);
        if (folder == null) return;

        var errorMessage = e.GetException()?.Message ?? "Unknown watcher error";

        // Check if folder still exists
        if (!Directory.Exists(folder.FolderPath))
        {
            errorMessage = "Folder no longer exists or is inaccessible.";
            StopWatching(watchedFolderId);
        }

        _ = UpdateFolderStatusAsync(folder, WatchStatus.Error, errorMessage);
    }

    private void StartDebounceTimer(string watchedFolderId)
    {
        // Use atomic counter pattern to avoid race conditions with cancellation tokens
        // Each call increments the counter; the task only processes if counter hasn't changed
        var currentCount = _debounceCounters.AddOrUpdate(watchedFolderId, 1, (_, count) => count + 1);

        Task.Run(async () =>
        {
            try
            {
                await Task.Delay(DebounceDelayMs);

                // Only process if no new events came in during the delay
                // (counter would have been incremented again if new events arrived)
                if (_debounceCounters.TryGetValue(watchedFolderId, out var latestCount) && latestCount == currentCount)
                {
                    await ProcessPendingChangesAsync(watchedFolderId);
                }
            }
            catch (Exception)
            {
                // Swallow exceptions from background processing to prevent app crash
                // Errors during organization are already captured in OrganizationResult.Errors
            }
        });
    }

    private async Task ProcessPendingChangesAsync(string watchedFolderId)
    {
        List<FileChangeInfo> changes;

        lock (_lockObject)
        {
            if (!_pendingChanges.TryGetValue(watchedFolderId, out var pendingList) || pendingList.Count == 0)
                return;

            changes = new List<FileChangeInfo>(pendingList);
            pendingList.Clear();
        }

        var folder = _watchedFolderService.GetWatchedFolder(watchedFolderId);
        if (folder == null) return;

        // Group changes by type and get unique files
        var groupedChanges = changes
            .GroupBy(c => c.ChangeType)
            .ToDictionary(g => g.Key, g => g.Select(c => c.FilePath).Distinct().ToList());

        // Raise FolderChanged event for each change type
        foreach (var (changeType, files) in groupedChanges)
        {
            RaiseFolderChanged(watchedFolderId, folder.FolderPath, changeType, files);
        }

        // If AutoOrganize is enabled, trigger organization
        if (folder.AutoOrganize && folder.IsEnabled)
        {
            // Get files that need processing (new or modified files that exist)
            var filesToProcess = changes
                .Where(c => c.ChangeType == FileChangeType.Created || c.ChangeType == FileChangeType.Modified)
                .Select(c => c.FilePath)
                .Where(File.Exists)
                .Distinct()
                .ToList();

            if (filesToProcess.Count > 0)
            {
                RaiseOrganizationRequested(watchedFolderId, folder.FolderPath, folder.ProfileId, filesToProcess);

                // Actually organize the folder
                await OrganizeFolderAsync(watchedFolderId, previewOnly: false);
            }
        }
    }

    private async Task UpdateFolderStatusAsync(WatchedFolder folder, WatchStatus newStatus, string? errorMessage)
    {
        var oldStatus = folder.Status;

        if (oldStatus == newStatus && folder.LastError == errorMessage)
            return;

        folder.Status = newStatus;
        folder.LastError = errorMessage;

        await _watchedFolderService.UpdateWatchedFolderAsync(folder);

        RaiseStatusChanged(folder.Id, oldStatus, newStatus, errorMessage);
    }

    private async Task<(List<Rule> rules, List<Category> categories, AppSettings settings)> LoadProfileDataAsync(Profile profile)
    {
        // Clear caches and reload from disk to get the latest data
        // This is necessary because UI components have their own service instances
        // that save directly to JSON files, so our in-memory caches may be stale
        _settingsService.ClearCache();
        await _ruleService.LoadRulesAsync();
        await _categoryService.LoadCategoriesAsync();

        var currentProfileId = _settingsService.GetSettings().CurrentProfileId;
        var isCurrentProfile = profile.Id == currentProfileId;

        // For the current active profile, use live data from services (freshly loaded)
        // For other profiles, use the stored JSON snapshots
        List<Rule> rules;
        List<Category> categories;
        AppSettings settings;

        if (isCurrentProfile)
        {
            // This is the active profile - use live data from services
            rules = _ruleService.GetRules();
            categories = _categoryService.GetCategories();
            settings = _settingsService.GetSettings();
        }
        else
        {
            // Different profile - use the profile's stored snapshots
            // Parse rules
            try
            {
                if (!string.IsNullOrEmpty(profile.RulesJson))
                {
                    var rulesWrapper = JsonSerializer.Deserialize<RulesWrapper>(profile.RulesJson, JsonOptions);
                    rules = rulesWrapper?.Rules ?? new List<Rule>();
                }
                else
                {
                    rules = new List<Rule>();
                }
            }
            catch
            {
                rules = new List<Rule>();
            }

            // Parse categories
            try
            {
                if (!string.IsNullOrEmpty(profile.CategoriesJson))
                {
                    var categoriesWrapper = JsonSerializer.Deserialize<CategoriesWrapper>(profile.CategoriesJson, JsonOptions);
                    categories = categoriesWrapper?.Categories ?? Category.GetDefaultCategories();
                }
                else
                {
                    categories = Category.GetDefaultCategories();
                }
            }
            catch
            {
                categories = Category.GetDefaultCategories();
            }

            // Parse settings
            try
            {
                if (!string.IsNullOrEmpty(profile.SettingsJson))
                {
                    settings = JsonSerializer.Deserialize<AppSettings>(profile.SettingsJson, JsonOptions) ?? AppSettings.GetDefaults();
                }
                else
                {
                    settings = AppSettings.GetDefaults();
                }
            }
            catch
            {
                settings = AppSettings.GetDefaults();
            }
        }

        return (rules, categories, settings);
    }

    private async Task<OrganizationResult> ScanAndOrganizeAsync(
        WatchedFolder folder,
        List<Rule> rules,
        List<Category> categories,
        AppSettings settings,
        bool previewOnly)
    {
        var result = new OrganizationResult();
        var basePath = folder.FolderPath;

        // Use profile's IncludeSubfolders setting
        var includeSubfolders = settings.IncludeSubfolders;

        await Task.Run(() =>
        {
            // Scan root folder
            ScanDirectory(basePath, basePath, rules, categories, settings, includeSubfolders, previewOnly, result);
        });

        return result;
    }

    private void ScanDirectory(
        string currentPath,
        string basePath,
        List<Rule> rules,
        List<Category> categories,
        AppSettings settings,
        bool includeSubfolders,
        bool previewOnly,
        OrganizationResult result)
    {
        try
        {
            var files = Directory.GetFiles(currentPath);

            foreach (var filePath in files)
            {
                result.TotalFilesScanned++;

                try
                {
                    // Skip if file no longer exists (may have been renamed/deleted)
                    if (!File.Exists(filePath))
                    {
                        result.FilesSkipped++;
                        continue;
                    }

                    // Skip if file is locked/in-use
                    if (!IsFileAccessible(filePath))
                    {
                        result.FilesSkipped++;
                        continue;
                    }

                    var fileInfo = new FileInfo(filePath);

                    // Skip hidden/system files based on settings
                    if (ShouldSkipFile(fileInfo, settings))
                    {
                        result.FilesSkipped++;
                        continue;
                    }

                    var organizeResult = GetFileOrganizeResult(fileInfo, basePath, rules, categories, settings);

                    if (organizeResult != null && organizeResult.WillBeOrganized)
                    {
                        if (previewOnly)
                        {
                            result.PreviewResults.Add(organizeResult);
                            result.FilesWouldMove++;
                        }
                        else
                        {
                            try
                            {
                                ExecuteOrganization(organizeResult, fileInfo, basePath);
                                result.FilesMoved++;
                            }
                            catch (IOException ex) when (ex.Message.Contains("being used by another process"))
                            {
                                // File became locked after our check, skip it silently
                                result.FilesSkipped++;
                            }
                            catch (Exception ex)
                            {
                                result.Errors.Add($"Failed to organize {fileInfo.Name}: {ex.Message}");
                            }
                        }
                    }
                    else
                    {
                        result.FilesSkipped++;
                        if (previewOnly && organizeResult != null)
                        {
                            result.PreviewResults.Add(organizeResult);
                        }
                    }
                }
                catch (Exception ex)
                {
                    result.Errors.Add($"Error processing file: {ex.Message}");
                }
            }

            // Process subfolders if enabled
            if (includeSubfolders)
            {
                var subdirs = Directory.GetDirectories(currentPath);
                foreach (var subdir in subdirs)
                {
                    try
                    {
                        var dirInfo = new DirectoryInfo(subdir);

                        // Skip hidden/system folders
                        if (settings.IgnoreHiddenFiles && (dirInfo.Attributes & System.IO.FileAttributes.Hidden) != 0)
                            continue;
                        if (settings.IgnoreSystemFiles && (dirInfo.Attributes & System.IO.FileAttributes.System) != 0)
                            continue;

                        ScanDirectory(subdir, basePath, rules, categories, settings, includeSubfolders, previewOnly, result);
                    }
                    catch
                    {
                        // Skip inaccessible directories
                    }
                }
            }
        }
        catch (Exception ex)
        {
            result.Errors.Add($"Error scanning directory {currentPath}: {ex.Message}");
        }
    }

    private static bool ShouldSkipFile(FileInfo fileInfo, AppSettings settings)
    {
        try
        {
            if (settings.IgnoreHiddenFiles && (fileInfo.Attributes & System.IO.FileAttributes.Hidden) != 0)
                return true;
            if (settings.IgnoreSystemFiles && (fileInfo.Attributes & System.IO.FileAttributes.System) != 0)
                return true;
            return false;
        }
        catch
        {
            return true;
        }
    }

    private FileOrganizeResult? GetFileOrganizeResult(
        FileInfo fileInfo,
        string basePath,
        List<Rule> rules,
        List<Category> categories,
        AppSettings settings)
    {
        var result = new FileOrganizeResult
        {
            SourcePath = fileInfo.FullName,
            FileSize = fileInfo.Length
        };

        // Step 1: Try rules first (if enabled)
        if (settings.UseRulesFirst && rules.Any(r => r.IsEnabled))
        {
            var matchingRules = _ruleService.GetMatchingRulesWithContinue(fileInfo, rules);
            if (matchingRules.Count > 0)
            {
                var allActions = matchingRules.SelectMany(r => r.Actions).ToList();

                // Check for Ignore action - return result with Ignore so it shows in preview
                if (allActions.Any(a => a.Type == ActionType.Ignore))
                {
                    result.MatchedBy = OrganizeMatchType.Rule;
                    result.MatchedRuleName = string.Join(" → ", matchingRules.Select(r => r.Name));
                    result.MatchedRuleId = matchingRules.First().Id;
                    result.MatchedRules = matchingRules;
                    result.Actions = allActions;
                    // No destination - file stays in place
                    return result;
                }

                // Calculate destinations
                var allDestinations = new List<string>();
                foreach (var rule in matchingRules)
                {
                    var destinations = _ruleService.CalculateAllDestinationPaths(rule, fileInfo, basePath, _categoryService);
                    allDestinations.AddRange(destinations);
                }

                result.MatchedBy = OrganizeMatchType.Rule;
                result.MatchedRuleName = string.Join(" → ", matchingRules.Select(r => r.Name));
                result.MatchedRuleId = matchingRules.First().Id;
                result.MatchedRules = matchingRules;
                result.Actions = allActions;
                result.DestinationPath = allDestinations.Count > 0 ? allDestinations[0] : null;

                var lastRuleHasContinue = matchingRules.Last().Actions.Any(a => a.Type == ActionType.Continue);
                if (!lastRuleHasContinue || allDestinations.Count > 0)
                {
                    return result;
                }
            }
        }

        // Step 2: Fall back to categories (if enabled)
        if (settings.FallbackToCategories)
        {
            var category = GetCategoryForFile(fileInfo.Extension, categories);
            if (category != null && category.IsEnabled)
            {
                var expectedFolder = Path.Combine(basePath, category.Destination);
                var currentFolder = fileInfo.DirectoryName ?? "";

                if (currentFolder.Equals(expectedFolder, StringComparison.OrdinalIgnoreCase))
                {
                    // Already in correct location - return result so it shows in preview
                    result.MatchedBy = OrganizeMatchType.Category;
                    result.MatchedCategoryName = category.Name;
                    result.MatchedCategoryIcon = category.Icon;
                    // No destination - file stays in place (already organized)
                    return result;
                }

                result.MatchedBy = OrganizeMatchType.Category;
                result.MatchedCategoryName = category.Name;
                result.MatchedCategoryIcon = category.Icon;
                result.DestinationPath = Path.Combine(basePath, category.Destination, fileInfo.Name);
                return result;
            }
        }

        return null;
    }

    private static Category? GetCategoryForFile(string extension, List<Category> categories)
    {
        if (string.IsNullOrEmpty(extension))
            return categories.FirstOrDefault(c => c.IsFallback);

        extension = extension.ToLowerInvariant();
        if (!extension.StartsWith('.'))
            extension = "." + extension;

        // Check non-default categories first
        var customCategory = categories
            .Where(c => !c.IsDefault && c.IsEnabled)
            .FirstOrDefault(c => c.Extensions.Contains(extension, StringComparer.OrdinalIgnoreCase));

        if (customCategory != null)
            return customCategory;

        // Check default categories (excluding fallback)
        var defaultCategory = categories
            .Where(c => c.IsDefault && !c.IsFallback && c.IsEnabled)
            .FirstOrDefault(c => c.Extensions.Contains(extension, StringComparer.OrdinalIgnoreCase));

        if (defaultCategory != null)
            return defaultCategory;

        // Return fallback
        return categories.FirstOrDefault(c => c.IsFallback);
    }

    private void ExecuteOrganization(FileOrganizeResult organizeResult, FileInfo fileInfo, string basePath)
    {
        if (organizeResult.MatchedBy == OrganizeMatchType.Rule)
        {
            ExecuteRuleActions(organizeResult, fileInfo, basePath);
        }
        else if (organizeResult.MatchedBy == OrganizeMatchType.Category && organizeResult.DestinationPath != null)
        {
            var destDir = Path.GetDirectoryName(organizeResult.DestinationPath)!;
            Directory.CreateDirectory(destDir);

            var finalPath = GetUniqueFilePath(organizeResult.DestinationPath, organizeResult.SourcePath);
            File.Move(organizeResult.SourcePath, finalPath);

            // Mark as recently organized to prevent loops
            MarkAsRecentlyOrganized(finalPath);
        }
    }

    private void ExecuteRuleActions(FileOrganizeResult result, FileInfo fileInfo, string basePath)
    {
        var currentFilePath = fileInfo.FullName;
        var currentFileName = fileInfo.Name;
        var currentDirectory = fileInfo.DirectoryName!;

        foreach (var action in result.Actions)
        {
            switch (action.Type)
            {
                case ActionType.MoveToFolder:
                    {
                        var destFolder = action.Value;
                        if (!Path.IsPathRooted(destFolder))
                            destFolder = Path.Combine(basePath, destFolder);

                        var targetPath = Path.Combine(destFolder, currentFileName);
                        if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                        File.Move(currentFilePath, destPath);
                        MarkAsRecentlyOrganized(destPath);

                        currentFilePath = destPath;
                        currentFileName = Path.GetFileName(destPath);
                        currentDirectory = destFolder;
                    }
                    break;

                case ActionType.CopyToFolder:
                    {
                        var destFolder = action.Value;
                        if (!Path.IsPathRooted(destFolder))
                            destFolder = Path.Combine(basePath, destFolder);

                        var targetPath = Path.Combine(destFolder, currentFileName);
                        if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                        File.Copy(currentFilePath, destPath);
                        MarkAsRecentlyOrganized(destPath);
                    }
                    break;

                case ActionType.MoveToCategory:
                    {
                        var categoryId = action.Value;
                        var categories = _categoryService.GetCategories();
                        var category = categories.FirstOrDefault(c => c.Id == categoryId);

                        if (category != null)
                        {
                            var destFolder = Path.IsPathRooted(category.Destination)
                                ? category.Destination
                                : Path.Combine(basePath, category.Destination);

                            var targetPath = Path.Combine(destFolder, currentFileName);
                            if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                                break;

                            Directory.CreateDirectory(destFolder);
                            var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                            File.Move(currentFilePath, destPath);
                            MarkAsRecentlyOrganized(destPath);

                            currentFilePath = destPath;
                            currentFileName = Path.GetFileName(destPath);
                            currentDirectory = destFolder;
                        }
                    }
                    break;

                case ActionType.SortIntoSubfolder:
                    {
                        var subfolderName = RuleService.ExpandPattern(action.Value, fileInfo, _categoryService);
                        subfolderName = subfolderName.Replace('/', Path.DirectorySeparatorChar);
                        var destFolder = Path.Combine(basePath, subfolderName);

                        var targetPath = Path.Combine(destFolder, currentFileName);
                        if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                        File.Move(currentFilePath, destPath);
                        MarkAsRecentlyOrganized(destPath);

                        currentFilePath = destPath;
                        currentFileName = Path.GetFileName(destPath);
                        currentDirectory = destFolder;
                    }
                    break;

                case ActionType.Rename:
                    {
                        var newName = RuleService.ExpandPattern(action.Value, fileInfo, _categoryService);
                        var targetPath = Path.Combine(currentDirectory, newName);

                        if (currentFilePath.Equals(targetPath, StringComparison.Ordinal))
                            break;

                        var isCaseOnlyRename = currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase);

                        if (isCaseOnlyRename)
                        {
                            var tempPath = currentFilePath + ".tmp_rename";
                            File.Move(currentFilePath, tempPath);
                            File.Move(tempPath, targetPath);
                        }
                        else
                        {
                            var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                            File.Move(currentFilePath, destPath);
                            targetPath = destPath;
                        }

                        MarkAsRecentlyOrganized(targetPath);
                        currentFilePath = targetPath;
                        currentFileName = Path.GetFileName(targetPath);
                    }
                    break;

                case ActionType.Delete:
                    {
                        MoveToRecycleBin(currentFilePath);
                        return; // File no longer exists, stop processing
                    }

                case ActionType.Ignore:
                case ActionType.Continue:
                    break;
            }
        }
    }

    private static string GetUniqueFilePath(string path, string? sourcePathToExclude = null)
    {
        if (!File.Exists(path)) return path;
        if (sourcePathToExclude != null && path.Equals(sourcePathToExclude, StringComparison.OrdinalIgnoreCase))
            return path;

        var directory = Path.GetDirectoryName(path) ?? "";
        var name = Path.GetFileNameWithoutExtension(path);
        var extension = Path.GetExtension(path);

        var counter = 1;
        string newPath;

        do
        {
            newPath = Path.Combine(directory, $"{name} ({counter}){extension}");
            counter++;
        }
        while (File.Exists(newPath) && (sourcePathToExclude == null || !newPath.Equals(sourcePathToExclude, StringComparison.OrdinalIgnoreCase)));

        return newPath;
    }

    private static void MoveToRecycleBin(string filePath)
    {
        Microsoft.VisualBasic.FileIO.FileSystem.DeleteFile(
            filePath,
            Microsoft.VisualBasic.FileIO.UIOption.OnlyErrorDialogs,
            Microsoft.VisualBasic.FileIO.RecycleOption.SendToRecycleBin);
    }

    private void RaiseFolderChanged(string watchedFolderId, string folderPath, FileChangeType changeType, IReadOnlyList<string> affectedFiles)
    {
        var args = new FolderChangedEventArgs(watchedFolderId, folderPath, changeType, affectedFiles);

        if (_dispatcherQueue != null)
        {
            _dispatcherQueue.TryEnqueue(() => FolderChanged?.Invoke(this, args));
        }
        else
        {
            FolderChanged?.Invoke(this, args);
        }
    }

    private void RaiseOrganizationRequested(string watchedFolderId, string folderPath, string profileId, IReadOnlyList<string> filesToProcess)
    {
        var args = new OrganizationRequestedEventArgs(watchedFolderId, folderPath, profileId, filesToProcess);

        if (_dispatcherQueue != null)
        {
            _dispatcherQueue.TryEnqueue(() => OrganizationRequested?.Invoke(this, args));
        }
        else
        {
            OrganizationRequested?.Invoke(this, args);
        }
    }

    private void RaiseStatusChanged(string watchedFolderId, WatchStatus oldStatus, WatchStatus newStatus, string? errorMessage)
    {
        var args = new WatcherStatusChangedEventArgs(watchedFolderId, oldStatus, newStatus, errorMessage);

        if (_dispatcherQueue != null)
        {
            _dispatcherQueue.TryEnqueue(() => StatusChanged?.Invoke(this, args));
        }
        else
        {
            StatusChanged?.Invoke(this, args);
        }
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;

        StopAllWatching();

        // Clear debounce counters and pending renames
        _debounceCounters.Clear();
        _pendingRenames.Clear();
    }

    /// <summary>
    /// Helper class for tracking pending file changes.
    /// </summary>
    private class FileChangeInfo
    {
        public string FilePath { get; set; } = "";
        public FileChangeType ChangeType { get; set; }
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Wrapper for deserializing rules from profile JSON.
    /// </summary>
    private class RulesWrapper
    {
        [System.Text.Json.Serialization.JsonPropertyName("rules")]
        public List<Rule> Rules { get; set; } = new();
    }

    /// <summary>
    /// Wrapper for deserializing categories from profile JSON.
    /// </summary>
    private class CategoriesWrapper
    {
        [System.Text.Json.Serialization.JsonPropertyName("categories")]
        public List<Category> Categories { get; set; } = new();
    }

    /// <summary>
    /// Tracks files with default Windows names that may be pending rename by user.
    /// </summary>
    private class PendingRenameInfo
    {
        public string OriginalPath { get; set; } = "";
        public string WatchedFolderId { get; set; } = "";
        public DateTime CreatedAt { get; set; }
    }
}
