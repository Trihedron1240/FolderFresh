namespace FolderFresh.Models;

/// <summary>
/// Represents the current status of a watched folder.
/// </summary>
public enum WatchStatus
{
    /// <summary>
    /// Not currently watching (watcher is stopped).
    /// </summary>
    Idle,

    /// <summary>
    /// Actively monitoring for file changes.
    /// </summary>
    Watching,

    /// <summary>
    /// Currently processing/organizing files.
    /// </summary>
    Organizing,

    /// <summary>
    /// Watcher failed (e.g., folder deleted or inaccessible).
    /// </summary>
    Error
}
