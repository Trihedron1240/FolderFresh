using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;

namespace FolderFresh.Models;

/// <summary>
/// Represents a saved snapshot of a folder's state.
/// Contains metadata about the snapshot and references to the stored files.
/// </summary>
public class FolderSnapshot : INotifyPropertyChanged
{
    private string _id = string.Empty;
    private string _name = string.Empty;
    private string _folderPath = string.Empty;
    private DateTime _createdAt = DateTime.Now;
    private int _fileCount;
    private long _totalSizeBytes;
    private string _description = string.Empty;

    /// <summary>
    /// Unique identifier for the snapshot (8-character alphanumeric)
    /// </summary>
    [JsonPropertyName("id")]
    public string Id
    {
        get => _id;
        set => SetProperty(ref _id, value);
    }

    /// <summary>
    /// User-provided name for the snapshot
    /// </summary>
    [JsonPropertyName("name")]
    public string Name
    {
        get => _name;
        set => SetProperty(ref _name, value);
    }

    /// <summary>
    /// The folder path that was snapshotted
    /// </summary>
    [JsonPropertyName("folderPath")]
    public string FolderPath
    {
        get => _folderPath;
        set => SetProperty(ref _folderPath, value);
    }

    /// <summary>
    /// When the snapshot was created
    /// </summary>
    [JsonPropertyName("createdAt")]
    public DateTime CreatedAt
    {
        get => _createdAt;
        set => SetProperty(ref _createdAt, value);
    }

    /// <summary>
    /// Number of files in the snapshot
    /// </summary>
    [JsonPropertyName("fileCount")]
    public int FileCount
    {
        get => _fileCount;
        set => SetProperty(ref _fileCount, value);
    }

    /// <summary>
    /// Total size of all files in the snapshot (bytes)
    /// </summary>
    [JsonPropertyName("totalSizeBytes")]
    public long TotalSizeBytes
    {
        get => _totalSizeBytes;
        set => SetProperty(ref _totalSizeBytes, value);
    }

    /// <summary>
    /// Optional description for the snapshot
    /// </summary>
    [JsonPropertyName("description")]
    public string Description
    {
        get => _description;
        set => SetProperty(ref _description, value);
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? propertyName = null)
    {
        if (Equals(field, value)) return false;
        field = value;
        OnPropertyChanged(propertyName);
        return true;
    }

    /// <summary>
    /// Creates a new snapshot with a generated ID
    /// </summary>
    public static FolderSnapshot Create(string name, string folderPath)
    {
        return new FolderSnapshot
        {
            Id = Guid.NewGuid().ToString("N")[..8],
            Name = name,
            FolderPath = folderPath,
            CreatedAt = DateTime.Now
        };
    }

    /// <summary>
    /// Formats the total size as a human-readable string
    /// </summary>
    [JsonIgnore]
    public string FormattedSize
    {
        get
        {
            if (TotalSizeBytes < 1024)
                return $"{TotalSizeBytes} B";
            if (TotalSizeBytes < 1024 * 1024)
                return $"{TotalSizeBytes / 1024.0:F1} KB";
            if (TotalSizeBytes < 1024 * 1024 * 1024)
                return $"{TotalSizeBytes / (1024.0 * 1024.0):F1} MB";
            return $"{TotalSizeBytes / (1024.0 * 1024.0 * 1024.0):F2} GB";
        }
    }
}

/// <summary>
/// Represents a single file entry within a snapshot.
/// Stores the original relative path and file metadata.
/// </summary>
public class SnapshotFileEntry
{
    /// <summary>
    /// Path relative to the snapshot's folder root
    /// </summary>
    [JsonPropertyName("relativePath")]
    public string RelativePath { get; set; } = string.Empty;

    /// <summary>
    /// Original file name
    /// </summary>
    [JsonPropertyName("fileName")]
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes
    /// </summary>
    [JsonPropertyName("fileSize")]
    public long FileSize { get; set; }

    /// <summary>
    /// Last modified time of the original file
    /// </summary>
    [JsonPropertyName("lastModified")]
    public DateTime LastModified { get; set; }

    /// <summary>
    /// Path to the backed up file within the snapshot storage folder
    /// </summary>
    [JsonPropertyName("storedFileName")]
    public string StoredFileName { get; set; } = string.Empty;
}

/// <summary>
/// Result of comparing a snapshot to the current folder state
/// </summary>
public class SnapshotCompareResult
{
    /// <summary>
    /// Files that exist in the snapshot but are now in different locations
    /// </summary>
    public List<SnapshotFileDiff> MovedFiles { get; set; } = new();

    /// <summary>
    /// Files that exist in the snapshot but were deleted from disk
    /// </summary>
    public List<SnapshotFileEntry> DeletedFiles { get; set; } = new();

    /// <summary>
    /// Files that exist in the snapshot but have been modified since
    /// </summary>
    public List<SnapshotFileDiff> ModifiedFiles { get; set; } = new();

    /// <summary>
    /// Files that are unchanged and in the correct location
    /// </summary>
    public List<SnapshotFileEntry> UnchangedFiles { get; set; } = new();

    /// <summary>
    /// Total number of files that would be restored
    /// </summary>
    public int TotalFilesToRestore => MovedFiles.Count + DeletedFiles.Count + ModifiedFiles.Count;

    /// <summary>
    /// Whether any changes are needed
    /// </summary>
    public bool HasChanges => TotalFilesToRestore > 0;
}

/// <summary>
/// Represents a difference between snapshot and current state for a file
/// </summary>
public class SnapshotFileDiff
{
    /// <summary>
    /// The original snapshot entry
    /// </summary>
    public SnapshotFileEntry SnapshotEntry { get; set; } = new();

    /// <summary>
    /// Current path of the file (if found)
    /// </summary>
    public string? CurrentPath { get; set; }

    /// <summary>
    /// Description of the change
    /// </summary>
    public string ChangeDescription { get; set; } = string.Empty;
}
