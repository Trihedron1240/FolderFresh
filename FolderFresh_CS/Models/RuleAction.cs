using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace FolderFreshLite.Models;

/// <summary>
/// An action to perform when a rule matches
/// </summary>
public class RuleAction
{
    /// <summary>
    /// The type of action to perform
    /// </summary>
    [JsonPropertyName("type")]
    public ActionType Type { get; set; }

    /// <summary>
    /// Primary value for the action (path, pattern, category ID, etc.)
    /// </summary>
    [JsonPropertyName("value")]
    public string Value { get; set; } = string.Empty;

    /// <summary>
    /// Additional options for the action
    /// </summary>
    [JsonPropertyName("options")]
    public Dictionary<string, string> Options { get; set; } = new();

    /// <summary>
    /// Display string describing this action
    /// </summary>
    [JsonIgnore]
    public string DisplayText => Type switch
    {
        ActionType.MoveToFolder => $"Move to \"{Value}\"",
        ActionType.CopyToFolder => $"Copy to \"{Value}\"",
        ActionType.MoveToCategory => $"Move to category folder",
        ActionType.SortIntoSubfolder => $"Sort into subfolder \"{Value}\"",
        ActionType.Rename => $"Rename with pattern \"{Value}\"",
        ActionType.Delete => "Move to trash",
        ActionType.Ignore => "Ignore (skip this file)",
        ActionType.Continue => "Continue matching rules",
        _ => Type.ToString()
    };

    /// <summary>
    /// Icon for this action type
    /// </summary>
    [JsonIgnore]
    public string Icon => Type switch
    {
        ActionType.MoveToFolder => "\uE8DE",      // MoveToFolder
        ActionType.CopyToFolder => "\uE8C8",      // Copy
        ActionType.MoveToCategory => "\uE8B7",    // FolderOpen
        ActionType.SortIntoSubfolder => "\uE8D5", // NewFolder
        ActionType.Rename => "\uE8AC",            // Rename
        ActionType.Delete => "\uE74D",            // Delete
        ActionType.Ignore => "\uE711",            // Cancel
        ActionType.Continue => "\uE72A",          // Forward
        _ => "\uE713"                             // Settings
    };
}

/// <summary>
/// Types of actions that can be performed
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum ActionType
{
    /// <summary>
    /// Move the file to a specific folder
    /// </summary>
    MoveToFolder,

    /// <summary>
    /// Copy the file to a specific folder
    /// </summary>
    CopyToFolder,

    /// <summary>
    /// Move to the category's destination folder (FolderFresh integration)
    /// </summary>
    MoveToCategory,

    /// <summary>
    /// Sort into a dynamically-named subfolder based on patterns
    /// Patterns: {date:yyyy-MM}, {extension}, {name}, etc.
    /// </summary>
    SortIntoSubfolder,

    /// <summary>
    /// Rename the file using a pattern
    /// Patterns: {date:yyyy-MM-dd}, {counter}, {name}, {extension}
    /// </summary>
    Rename,

    /// <summary>
    /// Move the file to the recycle bin
    /// </summary>
    Delete,

    /// <summary>
    /// Skip this file - don't apply any category or further rules
    /// </summary>
    Ignore,

    /// <summary>
    /// After performing actions, continue checking more rules
    /// (Default behavior is to stop after first matching rule)
    /// </summary>
    Continue
}

/// <summary>
/// Common option keys for RuleAction.Options
/// </summary>
public static class ActionOptionKeys
{
    /// <summary>
    /// What to do when destination file exists: "skip", "overwrite", "rename"
    /// </summary>
    public const string ConflictResolution = "conflictResolution";

    /// <summary>
    /// Pattern format for dates in rename/subfolder patterns
    /// </summary>
    public const string DateFormat = "dateFormat";

    /// <summary>
    /// Starting number for counter patterns
    /// </summary>
    public const string CounterStart = "counterStart";

    /// <summary>
    /// Number of digits for counter (zero-padded)
    /// </summary>
    public const string CounterDigits = "counterDigits";

    /// <summary>
    /// Whether to create parent folders if they don't exist
    /// </summary>
    public const string CreateFolders = "createFolders";
}
