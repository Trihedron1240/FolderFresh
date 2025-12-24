using System;
using System.ComponentModel;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;

namespace FolderFresh.Models;

/// <summary>
/// Represents a folder being monitored for file changes.
/// </summary>
public class WatchedFolder : INotifyPropertyChanged
{
    private string _id = string.Empty;
    private string _folderPath = string.Empty;
    private string _displayName = string.Empty;
    private string _profileId = string.Empty;
    private bool _isEnabled = true;
    private bool _autoOrganize = true;
    private bool _includeSubfolders;
    private DateTime _createdAt = DateTime.Now;
    private DateTime? _lastOrganizedAt;
    private int _fileCount;
    private WatchStatus _status = WatchStatus.Idle;
    private string? _lastError;
    private string? _profileName;

    private const int MaxDisplayPathLength = 50;

    /// <summary>
    /// Unique identifier for the watched folder (8-character alphanumeric).
    /// </summary>
    [JsonPropertyName("id")]
    public string Id
    {
        get => _id;
        set => SetProperty(ref _id, value);
    }

    /// <summary>
    /// Absolute path to the watched folder.
    /// </summary>
    [JsonPropertyName("folderPath")]
    public string FolderPath
    {
        get => _folderPath;
        set
        {
            if (SetProperty(ref _folderPath, value))
            {
                OnPropertyChanged(nameof(DisplayPath));
            }
        }
    }

    /// <summary>
    /// User-friendly display name for the folder.
    /// </summary>
    [JsonPropertyName("displayName")]
    public string DisplayName
    {
        get => _displayName;
        set => SetProperty(ref _displayName, value);
    }

    /// <summary>
    /// ID of the profile to use for organizing this folder.
    /// </summary>
    [JsonPropertyName("profileId")]
    public string ProfileId
    {
        get => _profileId;
        set => SetProperty(ref _profileId, value);
    }

    /// <summary>
    /// Whether watching is active for this folder.
    /// </summary>
    [JsonPropertyName("isEnabled")]
    public bool IsEnabled
    {
        get => _isEnabled;
        set => SetProperty(ref _isEnabled, value);
    }

    /// <summary>
    /// If true, automatically organize on file changes; if false, just notify.
    /// </summary>
    [JsonPropertyName("autoOrganize")]
    public bool AutoOrganize
    {
        get => _autoOrganize;
        set => SetProperty(ref _autoOrganize, value);
    }

    /// <summary>
    /// Whether to include subfolders when watching this folder.
    /// </summary>
    [JsonPropertyName("includeSubfolders")]
    public bool IncludeSubfolders
    {
        get => _includeSubfolders;
        set => SetProperty(ref _includeSubfolders, value);
    }

    /// <summary>
    /// When the watched folder was created.
    /// </summary>
    [JsonPropertyName("createdAt")]
    public DateTime CreatedAt
    {
        get => _createdAt;
        set => SetProperty(ref _createdAt, value);
    }

    /// <summary>
    /// When the folder was last successfully organized (null if never).
    /// </summary>
    [JsonPropertyName("lastOrganizedAt")]
    public DateTime? LastOrganizedAt
    {
        get => _lastOrganizedAt;
        set => SetProperty(ref _lastOrganizedAt, value);
    }

    /// <summary>
    /// Cached file count for display purposes (updated on scan).
    /// </summary>
    [JsonPropertyName("fileCount")]
    public int FileCount
    {
        get => _fileCount;
        set => SetProperty(ref _fileCount, value);
    }

    /// <summary>
    /// Current status of the watcher.
    /// </summary>
    [JsonPropertyName("status")]
    public WatchStatus Status
    {
        get => _status;
        set => SetProperty(ref _status, value);
    }

    /// <summary>
    /// Last error message if Status is Error (null otherwise).
    /// </summary>
    [JsonPropertyName("lastError")]
    public string? LastError
    {
        get => _lastError;
        set => SetProperty(ref _lastError, value);
    }

    /// <summary>
    /// Display name of the associated profile (not persisted, set externally).
    /// </summary>
    [JsonIgnore]
    public string? ProfileName
    {
        get => _profileName;
        set => SetProperty(ref _profileName, value);
    }

    /// <summary>
    /// Truncated path for display purposes. Long paths are prefixed with "...".
    /// </summary>
    [JsonIgnore]
    public string DisplayPath
    {
        get
        {
            if (string.IsNullOrEmpty(_folderPath))
                return string.Empty;

            if (_folderPath.Length <= MaxDisplayPathLength)
                return _folderPath;

            // Truncate from the beginning, keeping the end visible
            return "..." + _folderPath[^(MaxDisplayPathLength - 3)..];
        }
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
    /// Creates a new watched folder with a generated ID.
    /// </summary>
    /// <param name="folderPath">The absolute path to the folder to watch.</param>
    /// <returns>A new WatchedFolder instance.</returns>
    public static WatchedFolder Create(string folderPath)
    {
        var folderName = Path.GetFileName(folderPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar));

        // If folder name is empty (e.g., root drive), use the path itself
        if (string.IsNullOrEmpty(folderName))
        {
            folderName = folderPath;
        }

        return new WatchedFolder
        {
            Id = Guid.NewGuid().ToString("N")[..8],
            FolderPath = folderPath,
            DisplayName = folderName,
            CreatedAt = DateTime.Now,
            IsEnabled = true,
            AutoOrganize = true,
            Status = WatchStatus.Idle
        };
    }
}
