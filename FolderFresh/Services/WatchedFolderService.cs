using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using FolderFresh.Models;

namespace FolderFresh.Services;

/// <summary>
/// Service for managing watched folders configuration.
/// </summary>
public class WatchedFolderService
{
    private const string AppFolderName = "FolderFresh";
    private const string WatchedFoldersFileName = "watchedFolders.json";

    private readonly string _watchedFoldersFilePath;
    private List<WatchedFolder> _watchedFolders = new();

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) }
    };

    public WatchedFolderService()
    {
        var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var appFolderPath = Path.Combine(appDataPath, AppFolderName);

        if (!Directory.Exists(appFolderPath))
        {
            Directory.CreateDirectory(appFolderPath);
        }

        _watchedFoldersFilePath = Path.Combine(appFolderPath, WatchedFoldersFileName);
    }

    /// <summary>
    /// Loads watched folders from JSON file. Creates empty file if doesn't exist.
    /// Validates folder accessibility and marks inaccessible folders as Error status.
    /// </summary>
    public async Task<List<WatchedFolder>> LoadWatchedFoldersAsync()
    {
        try
        {
            if (!File.Exists(_watchedFoldersFilePath))
            {
                _watchedFolders = new List<WatchedFolder>();
                await SaveWatchedFoldersAsync();
                return _watchedFolders;
            }

            var json = await File.ReadAllTextAsync(_watchedFoldersFilePath);
            var data = JsonSerializer.Deserialize<WatchedFoldersFile>(json, JsonOptions);
            _watchedFolders = data?.WatchedFolders ?? new List<WatchedFolder>();

            // Validate each folder on load
            foreach (var folder in _watchedFolders)
            {
                // Reset Organizing status on load (organization can't persist across app restarts)
                if (folder.Status == WatchStatus.Organizing)
                {
                    folder.Status = WatchStatus.Idle;
                }

                var (isValid, error) = ValidateFolderPath(folder.FolderPath);
                if (!isValid)
                {
                    folder.Status = WatchStatus.Error;
                    folder.LastError = error;
                }
                else if (folder.Status == WatchStatus.Error)
                {
                    // Folder was previously in error but is now accessible
                    folder.Status = WatchStatus.Idle;
                    folder.LastError = null;
                }
            }

            return _watchedFolders;
        }
        catch (Exception)
        {
            _watchedFolders = new List<WatchedFolder>();
            return _watchedFolders;
        }
    }

    /// <summary>
    /// Saves watched folders to JSON file.
    /// </summary>
    public async Task SaveWatchedFoldersAsync()
    {
        try
        {
            var data = new WatchedFoldersFile { WatchedFolders = _watchedFolders };
            var json = JsonSerializer.Serialize(data, JsonOptions);
            await File.WriteAllTextAsync(_watchedFoldersFilePath, json);
        }
        catch (Exception)
        {
            // Log error if needed
        }
    }

    /// <summary>
    /// Gets all loaded watched folders (synchronous, from cache).
    /// </summary>
    public List<WatchedFolder> GetWatchedFolders()
    {
        return _watchedFolders;
    }

    /// <summary>
    /// Gets a watched folder by ID.
    /// </summary>
    public WatchedFolder? GetWatchedFolder(string id)
    {
        return _watchedFolders.FirstOrDefault(f => f.Id == id);
    }

    /// <summary>
    /// Gets a watched folder by path (case-insensitive on Windows).
    /// </summary>
    public WatchedFolder? GetWatchedFolderByPath(string path)
    {
        var normalizedPath = NormalizePath(path);
        return _watchedFolders.FirstOrDefault(f =>
            NormalizePath(f.FolderPath).Equals(normalizedPath, StringComparison.OrdinalIgnoreCase));
    }

    /// <summary>
    /// Adds a new watched folder and saves to file.
    /// </summary>
    public async Task<WatchedFolder> AddWatchedFolderAsync(WatchedFolder folder)
    {
        if (string.IsNullOrEmpty(folder.Id))
        {
            folder.Id = Guid.NewGuid().ToString("N")[..8];
        }

        folder.CreatedAt = DateTime.Now;
        _watchedFolders.Add(folder);
        await SaveWatchedFoldersAsync();
        return folder;
    }

    /// <summary>
    /// Updates an existing watched folder and saves to file.
    /// </summary>
    public async Task UpdateWatchedFolderAsync(WatchedFolder folder)
    {
        var index = _watchedFolders.FindIndex(f => f.Id == folder.Id);
        if (index >= 0)
        {
            _watchedFolders[index] = folder;
            await SaveWatchedFoldersAsync();
        }
    }

    /// <summary>
    /// Deletes a watched folder by ID and saves to file.
    /// </summary>
    /// <returns>True if the folder was found and deleted, false otherwise.</returns>
    public async Task<bool> DeleteWatchedFolderAsync(string id)
    {
        var folder = _watchedFolders.FirstOrDefault(f => f.Id == id);
        if (folder != null)
        {
            _watchedFolders.Remove(folder);
            await SaveWatchedFoldersAsync();
            return true;
        }
        return false;
    }

    /// <summary>
    /// Checks if a folder path already exists in the watched folders list.
    /// Uses case-insensitive comparison on Windows.
    /// </summary>
    public bool FolderPathExists(string path)
    {
        return GetWatchedFolderByPath(path) != null;
    }

    /// <summary>
    /// Validates that a folder path exists and is accessible.
    /// </summary>
    /// <returns>A tuple of (isValid, errorMessage). errorMessage is null if valid.</returns>
    public (bool isValid, string? error) ValidateFolderPath(string path)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            return (false, "Folder path cannot be empty.");
        }

        try
        {
            // Normalize the path first
            path = NormalizePath(path);

            // Check if path is valid
            if (!Path.IsPathRooted(path))
            {
                return (false, "Folder path must be an absolute path.");
            }

            // Check if directory exists
            if (!Directory.Exists(path))
            {
                return (false, "Folder does not exist or is not accessible.");
            }

            // Try to access the directory to verify permissions
            _ = Directory.GetFiles(path, "*", SearchOption.TopDirectoryOnly);

            return (true, null);
        }
        catch (UnauthorizedAccessException)
        {
            return (false, "Access denied. You do not have permission to access this folder.");
        }
        catch (PathTooLongException)
        {
            return (false, "The folder path is too long.");
        }
        catch (DirectoryNotFoundException)
        {
            return (false, "Folder does not exist or is not accessible.");
        }
        catch (IOException ex)
        {
            // Network paths may throw IOException when unavailable
            return (false, $"Unable to access folder: {ex.Message}");
        }
        catch (Exception ex)
        {
            return (false, $"Invalid folder path: {ex.Message}");
        }
    }

    /// <summary>
    /// Checks if a path is a network path (UNC or mapped drive pointing to network).
    /// </summary>
    public bool IsNetworkPath(string path)
    {
        if (string.IsNullOrEmpty(path))
            return false;

        // UNC path (\\server\share)
        if (path.StartsWith(@"\\"))
            return true;

        // Check if it's a mapped drive pointing to a network location
        try
        {
            var root = Path.GetPathRoot(path);
            if (!string.IsNullOrEmpty(root) && root.Length == 3 && root[1] == ':')
            {
                var driveInfo = new DriveInfo(root);
                return driveInfo.DriveType == DriveType.Network;
            }
        }
        catch
        {
            // Ignore errors checking drive type
        }

        return false;
    }

    /// <summary>
    /// Checks if a path appears to be a cloud-synced folder (OneDrive, Dropbox, etc.).
    /// </summary>
    public bool IsCloudSyncedPath(string path)
    {
        if (string.IsNullOrEmpty(path))
            return false;

        var lowerPath = path.ToLowerInvariant();

        // Common cloud sync folder indicators
        var cloudIndicators = new[]
        {
            "onedrive",
            "dropbox",
            "google drive",
            "googledrive",
            "icloud",
            "box sync",
            "mega",
            "pcloud"
        };

        return cloudIndicators.Any(indicator => lowerPath.Contains(indicator));
    }

    /// <summary>
    /// Gets warnings for special folder types (network, cloud, etc.).
    /// </summary>
    public List<string> GetPathWarnings(string path)
    {
        var warnings = new List<string>();

        if (IsNetworkPath(path))
        {
            warnings.Add("This is a network folder. Watching may be less reliable if the network connection is unstable.");
        }

        if (IsCloudSyncedPath(path))
        {
            warnings.Add("This appears to be a cloud-synced folder. File organization may conflict with sync operations. Consider disabling auto-organize and using manual organization instead.");
        }

        return warnings;
    }

    /// <summary>
    /// Checks if a file path is within any watched folder.
    /// </summary>
    public WatchedFolder? GetWatchedFolderContainingPath(string filePath)
    {
        if (string.IsNullOrEmpty(filePath))
            return null;

        var normalizedFilePath = NormalizePath(filePath);

        foreach (var folder in _watchedFolders)
        {
            var normalizedFolderPath = NormalizePath(folder.FolderPath);

            if (normalizedFilePath.StartsWith(normalizedFolderPath + Path.DirectorySeparatorChar,
                    StringComparison.OrdinalIgnoreCase) ||
                normalizedFilePath.Equals(normalizedFolderPath, StringComparison.OrdinalIgnoreCase))
            {
                return folder;
            }
        }

        return null;
    }

    /// <summary>
    /// Checks if a destination path would create a potential loop (destination is inside a watched folder).
    /// </summary>
    public bool IsDestinationInWatchedFolder(string destinationPath, string? excludeFolderId = null)
    {
        var watchedFolder = GetWatchedFolderContainingPath(destinationPath);
        if (watchedFolder == null)
            return false;

        // Exclude the source folder itself
        if (excludeFolderId != null && watchedFolder.Id == excludeFolderId)
            return false;

        return watchedFolder.AutoOrganize;
    }

    /// <summary>
    /// Checks if the given path is a subfolder of any existing watched folder.
    /// </summary>
    /// <returns>The parent watched folder if found, null otherwise.</returns>
    public WatchedFolder? GetParentWatchedFolder(string path)
    {
        var normalizedPath = NormalizePath(path);

        foreach (var folder in _watchedFolders)
        {
            var normalizedWatchedPath = NormalizePath(folder.FolderPath);

            // Check if path is under the watched folder
            if (normalizedPath.StartsWith(normalizedWatchedPath + Path.DirectorySeparatorChar,
                    StringComparison.OrdinalIgnoreCase))
            {
                return folder;
            }
        }

        return null;
    }

    /// <summary>
    /// Checks if the given path is a parent folder of any existing watched folder.
    /// </summary>
    /// <returns>List of child watched folders that would be under this path.</returns>
    public List<WatchedFolder> GetChildWatchedFolders(string path)
    {
        var normalizedPath = NormalizePath(path);
        var children = new List<WatchedFolder>();

        foreach (var folder in _watchedFolders)
        {
            var normalizedWatchedPath = NormalizePath(folder.FolderPath);

            // Check if the watched folder is under the given path
            if (normalizedWatchedPath.StartsWith(normalizedPath + Path.DirectorySeparatorChar,
                    StringComparison.OrdinalIgnoreCase))
            {
                children.Add(folder);
            }
        }

        return children;
    }

    /// <summary>
    /// Checks for potential conflicts with an existing watched folder.
    /// Returns warnings for subfolder/parent relationships but allows the operation.
    /// </summary>
    /// <returns>A list of warning messages (empty if no conflicts).</returns>
    public List<string> CheckFolderConflicts(string path)
    {
        var warnings = new List<string>();

        // Check for exact duplicate
        if (FolderPathExists(path))
        {
            warnings.Add("This folder is already being watched.");
            return warnings;
        }

        // Check if this is a subfolder of an existing watched folder
        var parent = GetParentWatchedFolder(path);
        if (parent != null)
        {
            warnings.Add($"This folder is a subfolder of already-watched folder: {parent.DisplayName}");
        }

        // Check if this would be a parent of existing watched folders
        var children = GetChildWatchedFolders(path);
        if (children.Count > 0)
        {
            var childNames = string.Join(", ", children.Select(c => c.DisplayName));
            warnings.Add($"This folder contains already-watched folders: {childNames}");
        }

        return warnings;
    }

    /// <summary>
    /// Normalizes a path for consistent comparison.
    /// Removes trailing separators and ensures consistent separator usage.
    /// </summary>
    private static string NormalizePath(string path)
    {
        if (string.IsNullOrEmpty(path))
            return string.Empty;

        // Get full path to resolve any relative components
        try
        {
            path = Path.GetFullPath(path);
        }
        catch
        {
            // If GetFullPath fails, just work with what we have
        }

        // Remove trailing separators
        return path.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    }

    /// <summary>
    /// Wrapper class for JSON serialization.
    /// </summary>
    private class WatchedFoldersFile
    {
        [JsonPropertyName("watchedFolders")]
        public List<WatchedFolder> WatchedFolders { get; set; } = new();

        [JsonPropertyName("version")]
        public int Version { get; set; } = 1;
    }
}
