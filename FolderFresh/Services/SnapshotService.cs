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
/// Service for managing folder snapshots. Snapshots store actual file copies
/// that can be restored to return a folder to a previous state.
/// </summary>
public class SnapshotService
{
    private const string AppFolderName = "FolderFresh";
    private const string SnapshotsFolderName = "snapshots";
    private const string IndexFileName = "index.json";

    private readonly string _snapshotsBasePath;
    private readonly string _indexFilePath;
    private List<FolderSnapshot> _snapshots = new();

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public SnapshotService()
    {
        var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var appFolderPath = Path.Combine(appDataPath, AppFolderName);
        _snapshotsBasePath = Path.Combine(appFolderPath, SnapshotsFolderName);
        _indexFilePath = Path.Combine(_snapshotsBasePath, IndexFileName);

        if (!Directory.Exists(_snapshotsBasePath))
        {
            Directory.CreateDirectory(_snapshotsBasePath);
        }
    }

    #region CRUD Operations

    /// <summary>
    /// Loads the snapshot index from disk.
    /// </summary>
    public async Task<List<FolderSnapshot>> LoadSnapshotsAsync()
    {
        try
        {
            if (!File.Exists(_indexFilePath))
            {
                _snapshots = new List<FolderSnapshot>();
                return _snapshots;
            }

            var json = await File.ReadAllTextAsync(_indexFilePath);
            var data = JsonSerializer.Deserialize<SnapshotsIndex>(json, JsonOptions);
            _snapshots = data?.Snapshots ?? new List<FolderSnapshot>();

            // Verify each snapshot's storage folder exists
            _snapshots = _snapshots.Where(s => Directory.Exists(GetSnapshotStoragePath(s.Id))).ToList();

            return _snapshots;
        }
        catch (Exception)
        {
            _snapshots = new List<FolderSnapshot>();
            return _snapshots;
        }
    }

    /// <summary>
    /// Saves the snapshot index to disk.
    /// </summary>
    private async Task SaveIndexAsync()
    {
        try
        {
            var data = new SnapshotsIndex { Snapshots = _snapshots };
            var json = JsonSerializer.Serialize(data, JsonOptions);
            await File.WriteAllTextAsync(_indexFilePath, json);
        }
        catch (Exception)
        {
            // Log error if needed
        }
    }

    /// <summary>
    /// Gets all loaded snapshots.
    /// </summary>
    public List<FolderSnapshot> GetSnapshots()
    {
        return _snapshots.OrderByDescending(s => s.CreatedAt).ToList();
    }

    /// <summary>
    /// Gets a snapshot by ID.
    /// </summary>
    public FolderSnapshot? GetSnapshot(string snapshotId)
    {
        return _snapshots.FirstOrDefault(s => s.Id == snapshotId);
    }

    /// <summary>
    /// Gets all snapshots for a specific folder path.
    /// </summary>
    public List<FolderSnapshot> GetSnapshotsForFolder(string folderPath)
    {
        return _snapshots
            .Where(s => s.FolderPath.Equals(folderPath, StringComparison.OrdinalIgnoreCase))
            .OrderByDescending(s => s.CreatedAt)
            .ToList();
    }

    /// <summary>
    /// Creates a new snapshot of a folder by copying all files.
    /// </summary>
    /// <param name="name">User-provided name for the snapshot</param>
    /// <param name="folderPath">Path to the folder to snapshot</param>
    /// <param name="includeSubfolders">Whether to include subfolders</param>
    /// <param name="progress">Optional progress callback (0-100)</param>
    /// <returns>The created snapshot</returns>
    public async Task<FolderSnapshot> CreateSnapshotAsync(
        string name,
        string folderPath,
        bool includeSubfolders = true,
        IProgress<int>? progress = null)
    {
        if (!Directory.Exists(folderPath))
        {
            throw new DirectoryNotFoundException($"Folder not found: {folderPath}");
        }

        var snapshot = FolderSnapshot.Create(name, folderPath);
        var storagePath = GetSnapshotStoragePath(snapshot.Id);
        Directory.CreateDirectory(storagePath);

        try
        {
            // Get all files to copy
            var searchOption = includeSubfolders ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;
            var files = Directory.GetFiles(folderPath, "*", searchOption);
            var entries = new List<SnapshotFileEntry>();
            long totalSize = 0;

            for (int i = 0; i < files.Length; i++)
            {
                var filePath = files[i];
                var fileInfo = new FileInfo(filePath);

                // Skip hidden and system files
                if ((fileInfo.Attributes & System.IO.FileAttributes.Hidden) != 0 ||
                    (fileInfo.Attributes & System.IO.FileAttributes.System) != 0)
                {
                    continue;
                }

                // Create relative path
                var relativePath = Path.GetRelativePath(folderPath, filePath);

                // Generate unique stored filename to avoid conflicts
                var storedFileName = $"{Guid.NewGuid():N}{fileInfo.Extension}";
                var storedFilePath = Path.Combine(storagePath, storedFileName);

                // Copy the file
                await Task.Run(() => File.Copy(filePath, storedFilePath, overwrite: true));

                entries.Add(new SnapshotFileEntry
                {
                    RelativePath = relativePath,
                    FileName = fileInfo.Name,
                    FileSize = fileInfo.Length,
                    LastModified = fileInfo.LastWriteTime,
                    StoredFileName = storedFileName
                });

                totalSize += fileInfo.Length;

                // Report progress
                progress?.Report((i + 1) * 100 / files.Length);
            }

            // Save the file entries
            var entriesPath = Path.Combine(storagePath, "files.json");
            var entriesJson = JsonSerializer.Serialize(entries, JsonOptions);
            await File.WriteAllTextAsync(entriesPath, entriesJson);

            // Update snapshot metadata
            snapshot.FileCount = entries.Count;
            snapshot.TotalSizeBytes = totalSize;

            // Add to index and save
            _snapshots.Add(snapshot);
            await SaveIndexAsync();

            return snapshot;
        }
        catch (Exception)
        {
            // Clean up on failure
            if (Directory.Exists(storagePath))
            {
                try { Directory.Delete(storagePath, recursive: true); } catch { }
            }
            throw;
        }
    }

    /// <summary>
    /// Deletes a snapshot and its stored files.
    /// </summary>
    public async Task<bool> DeleteSnapshotAsync(string snapshotId)
    {
        var snapshot = _snapshots.FirstOrDefault(s => s.Id == snapshotId);
        if (snapshot == null)
        {
            return false;
        }

        // Delete storage folder
        var storagePath = GetSnapshotStoragePath(snapshotId);
        if (Directory.Exists(storagePath))
        {
            try
            {
                Directory.Delete(storagePath, recursive: true);
            }
            catch (Exception)
            {
                // Continue with index removal even if folder deletion fails
            }
        }

        // Remove from index
        _snapshots.Remove(snapshot);
        await SaveIndexAsync();

        return true;
    }

    /// <summary>
    /// Renames a snapshot.
    /// </summary>
    public async Task RenameSnapshotAsync(string snapshotId, string newName)
    {
        var snapshot = _snapshots.FirstOrDefault(s => s.Id == snapshotId);
        if (snapshot != null)
        {
            snapshot.Name = newName;
            await SaveIndexAsync();
        }
    }

    #endregion

    #region Restore Operations

    /// <summary>
    /// Compares a snapshot to the current folder state.
    /// </summary>
    public async Task<SnapshotCompareResult> CompareSnapshotAsync(string snapshotId)
    {
        var snapshot = _snapshots.FirstOrDefault(s => s.Id == snapshotId);
        if (snapshot == null)
        {
            throw new InvalidOperationException($"Snapshot not found: {snapshotId}");
        }

        var entries = await LoadSnapshotEntriesAsync(snapshotId);
        var result = new SnapshotCompareResult();

        foreach (var entry in entries)
        {
            var expectedPath = Path.Combine(snapshot.FolderPath, entry.RelativePath);

            if (File.Exists(expectedPath))
            {
                var currentInfo = new FileInfo(expectedPath);

                // Check if file was modified
                if (Math.Abs((currentInfo.LastWriteTime - entry.LastModified).TotalSeconds) > 1 ||
                    currentInfo.Length != entry.FileSize)
                {
                    result.ModifiedFiles.Add(new SnapshotFileDiff
                    {
                        SnapshotEntry = entry,
                        CurrentPath = expectedPath,
                        ChangeDescription = "File has been modified since snapshot"
                    });
                }
                else
                {
                    result.UnchangedFiles.Add(entry);
                }
            }
            else
            {
                // File not at expected location - check if it was moved or deleted
                // For now, mark as deleted (would need full disk search to find moved files)
                result.DeletedFiles.Add(entry);
            }
        }

        return result;
    }

    /// <summary>
    /// Restores a snapshot by copying files back to their original locations.
    /// </summary>
    /// <param name="snapshotId">ID of the snapshot to restore</param>
    /// <param name="progress">Optional progress callback (0-100)</param>
    /// <returns>Number of files restored</returns>
    public async Task<int> RestoreSnapshotAsync(string snapshotId, IProgress<int>? progress = null)
    {
        var snapshot = _snapshots.FirstOrDefault(s => s.Id == snapshotId);
        if (snapshot == null)
        {
            throw new InvalidOperationException($"Snapshot not found: {snapshotId}");
        }

        var entries = await LoadSnapshotEntriesAsync(snapshotId);
        var storagePath = GetSnapshotStoragePath(snapshotId);
        int restoredCount = 0;

        for (int i = 0; i < entries.Count; i++)
        {
            var entry = entries[i];
            var storedFilePath = Path.Combine(storagePath, entry.StoredFileName);
            var targetPath = Path.Combine(snapshot.FolderPath, entry.RelativePath);

            if (!File.Exists(storedFilePath))
            {
                continue; // Skip if stored file is missing
            }

            try
            {
                // Ensure target directory exists
                var targetDir = Path.GetDirectoryName(targetPath);
                if (!string.IsNullOrEmpty(targetDir) && !Directory.Exists(targetDir))
                {
                    Directory.CreateDirectory(targetDir);
                }

                // Copy file back (overwrite if exists)
                await Task.Run(() => File.Copy(storedFilePath, targetPath, overwrite: true));

                // Restore last modified time
                File.SetLastWriteTime(targetPath, entry.LastModified);

                restoredCount++;
            }
            catch (Exception)
            {
                // Continue with other files on error
            }

            progress?.Report((i + 1) * 100 / entries.Count);
        }

        return restoredCount;
    }

    /// <summary>
    /// Loads the file entries for a snapshot.
    /// </summary>
    private async Task<List<SnapshotFileEntry>> LoadSnapshotEntriesAsync(string snapshotId)
    {
        var entriesPath = Path.Combine(GetSnapshotStoragePath(snapshotId), "files.json");

        if (!File.Exists(entriesPath))
        {
            return new List<SnapshotFileEntry>();
        }

        var json = await File.ReadAllTextAsync(entriesPath);
        return JsonSerializer.Deserialize<List<SnapshotFileEntry>>(json, JsonOptions) ?? new List<SnapshotFileEntry>();
    }

    #endregion

    #region Storage Management

    /// <summary>
    /// Gets the total storage used by all snapshots.
    /// </summary>
    public long GetTotalStorageUsed()
    {
        return _snapshots.Sum(s => s.TotalSizeBytes);
    }

    /// <summary>
    /// Formats total storage as a human-readable string.
    /// </summary>
    public string GetFormattedTotalStorage()
    {
        var bytes = GetTotalStorageUsed();

        if (bytes < 1024)
            return $"{bytes} B";
        if (bytes < 1024 * 1024)
            return $"{bytes / 1024.0:F1} KB";
        if (bytes < 1024 * 1024 * 1024)
            return $"{bytes / (1024.0 * 1024.0):F1} MB";
        return $"{bytes / (1024.0 * 1024.0 * 1024.0):F2} GB";
    }

    /// <summary>
    /// Gets the storage path for a snapshot's files.
    /// </summary>
    private string GetSnapshotStoragePath(string snapshotId)
    {
        return Path.Combine(_snapshotsBasePath, snapshotId);
    }

    /// <summary>
    /// Gets the base path where all snapshots are stored.
    /// </summary>
    public string GetSnapshotsBasePath()
    {
        return _snapshotsBasePath;
    }

    #endregion

    #region Helper Classes

    private class SnapshotsIndex
    {
        [JsonPropertyName("snapshots")]
        public List<FolderSnapshot> Snapshots { get; set; } = new();

        [JsonPropertyName("version")]
        public int Version { get; set; } = 1;
    }

    #endregion
}
