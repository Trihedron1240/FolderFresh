using System;
using System.Collections.Generic;
using FolderFresh.Models;

namespace FolderFresh.Services;

/// <summary>
/// Type of file system change detected.
/// </summary>
public enum FileChangeType
{
    Created,
    Modified,
    Deleted,
    Renamed
}

/// <summary>
/// Event args for folder change events.
/// </summary>
public class FolderChangedEventArgs : EventArgs
{
    /// <summary>
    /// ID of the watched folder that changed.
    /// </summary>
    public string WatchedFolderId { get; }

    /// <summary>
    /// Path to the watched folder.
    /// </summary>
    public string FolderPath { get; }

    /// <summary>
    /// Type of change that occurred.
    /// </summary>
    public FileChangeType ChangeType { get; }

    /// <summary>
    /// List of affected file paths.
    /// </summary>
    public IReadOnlyList<string> AffectedFiles { get; }

    public FolderChangedEventArgs(string watchedFolderId, string folderPath, FileChangeType changeType, IReadOnlyList<string> affectedFiles)
    {
        WatchedFolderId = watchedFolderId;
        FolderPath = folderPath;
        ChangeType = changeType;
        AffectedFiles = affectedFiles;
    }
}

/// <summary>
/// Event args when automatic organization is requested.
/// </summary>
public class OrganizationRequestedEventArgs : EventArgs
{
    /// <summary>
    /// ID of the watched folder to organize.
    /// </summary>
    public string WatchedFolderId { get; }

    /// <summary>
    /// Path to the watched folder.
    /// </summary>
    public string FolderPath { get; }

    /// <summary>
    /// ID of the profile to use for organization.
    /// </summary>
    public string ProfileId { get; }

    /// <summary>
    /// List of file paths to process.
    /// </summary>
    public IReadOnlyList<string> FilesToProcess { get; }

    public OrganizationRequestedEventArgs(string watchedFolderId, string folderPath, string profileId, IReadOnlyList<string> filesToProcess)
    {
        WatchedFolderId = watchedFolderId;
        FolderPath = folderPath;
        ProfileId = profileId;
        FilesToProcess = filesToProcess;
    }
}

/// <summary>
/// Event args for watcher status changes.
/// </summary>
public class WatcherStatusChangedEventArgs : EventArgs
{
    /// <summary>
    /// ID of the watched folder.
    /// </summary>
    public string WatchedFolderId { get; }

    /// <summary>
    /// Previous status.
    /// </summary>
    public WatchStatus OldStatus { get; }

    /// <summary>
    /// New status.
    /// </summary>
    public WatchStatus NewStatus { get; }

    /// <summary>
    /// Error message if NewStatus is Error.
    /// </summary>
    public string? ErrorMessage { get; }

    public WatcherStatusChangedEventArgs(string watchedFolderId, WatchStatus oldStatus, WatchStatus newStatus, string? errorMessage = null)
    {
        WatchedFolderId = watchedFolderId;
        OldStatus = oldStatus;
        NewStatus = newStatus;
        ErrorMessage = errorMessage;
    }
}

/// <summary>
/// Event args for organization completion.
/// </summary>
public class OrganizationCompletedEventArgs : EventArgs
{
    /// <summary>
    /// ID of the watched folder that was organized.
    /// </summary>
    public string WatchedFolderId { get; }

    /// <summary>
    /// Number of files successfully moved/organized.
    /// </summary>
    public int FilesMoved { get; }

    /// <summary>
    /// Number of files skipped (already organized or no match).
    /// </summary>
    public int FilesSkipped { get; }

    /// <summary>
    /// List of errors that occurred during organization.
    /// </summary>
    public IReadOnlyList<string> Errors { get; }

    public OrganizationCompletedEventArgs(string watchedFolderId, int filesMoved, int filesSkipped, IReadOnlyList<string> errors)
    {
        WatchedFolderId = watchedFolderId;
        FilesMoved = filesMoved;
        FilesSkipped = filesSkipped;
        Errors = errors;
    }
}

/// <summary>
/// Result of an organization operation.
/// </summary>
public class OrganizationResult
{
    /// <summary>
    /// Whether the operation completed successfully.
    /// </summary>
    public bool Success { get; set; }

    /// <summary>
    /// Number of files moved/organized.
    /// </summary>
    public int FilesMoved { get; set; }

    /// <summary>
    /// Number of files skipped.
    /// </summary>
    public int FilesSkipped { get; set; }

    /// <summary>
    /// Number of files that would be moved (preview mode only).
    /// </summary>
    public int FilesWouldMove { get; set; }

    /// <summary>
    /// List of errors that occurred.
    /// </summary>
    public List<string> Errors { get; set; } = new();

    /// <summary>
    /// Preview results (only populated when previewOnly is true).
    /// </summary>
    public List<FileOrganizeResult> PreviewResults { get; set; } = new();

    /// <summary>
    /// Total files scanned.
    /// </summary>
    public int TotalFilesScanned { get; set; }
}
