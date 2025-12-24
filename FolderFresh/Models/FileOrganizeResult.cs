using System.Collections.Generic;
using System.Linq;

namespace FolderFresh.Models;

/// <summary>
/// Represents the organize result for a single file
/// </summary>
public class FileOrganizeResult
{
    /// <summary>
    /// Original file path
    /// </summary>
    public string SourcePath { get; set; } = string.Empty;

    /// <summary>
    /// Primary destination path after organizing (null if no match).
    /// For backward compatibility - returns first destination from AllDestinations.
    /// </summary>
    public string? DestinationPath
    {
        get => AllDestinations.FirstOrDefault().Path;
        set
        {
            // For backward compatibility - set as the only destination
            if (value != null)
            {
                AllDestinations = new List<(string Path, ActionType ActionType)> { (value, ActionType.MoveToFolder) };
            }
            else
            {
                AllDestinations.Clear();
            }
        }
    }

    /// <summary>
    /// All destinations for this file (includes copies).
    /// Each tuple contains the destination path and the action type (Move, Copy, etc.)
    /// </summary>
    public List<(string Path, ActionType ActionType)> AllDestinations { get; set; } = new();

    /// <summary>
    /// How this file was matched
    /// </summary>
    public OrganizeMatchType MatchedBy { get; set; } = OrganizeMatchType.None;

    /// <summary>
    /// Name of the matched rule (if MatchedBy == Rule)
    /// </summary>
    public string? MatchedRuleName { get; set; }

    /// <summary>
    /// ID of the matched rule (if MatchedBy == Rule)
    /// </summary>
    public string? MatchedRuleId { get; set; }

    /// <summary>
    /// All matched rules when using Continue action (in priority order)
    /// </summary>
    public List<Rule> MatchedRules { get; set; } = new();

    /// <summary>
    /// Name of the matched category (if MatchedBy == Category)
    /// </summary>
    public string? MatchedCategoryName { get; set; }

    /// <summary>
    /// Icon of the matched category (if MatchedBy == Category)
    /// </summary>
    public string? MatchedCategoryIcon { get; set; }

    /// <summary>
    /// Actions to execute (if MatchedBy == Rule)
    /// </summary>
    public List<RuleAction> Actions { get; set; } = new();

    /// <summary>
    /// File name for display
    /// </summary>
    public string FileName => System.IO.Path.GetFileName(SourcePath);

    /// <summary>
    /// File extension
    /// </summary>
    public string Extension => System.IO.Path.GetExtension(SourcePath);

    /// <summary>
    /// File size in bytes
    /// </summary>
    public long FileSize { get; set; }

    /// <summary>
    /// Whether this file will be organized
    /// </summary>
    public bool WillBeOrganized => MatchedBy != OrganizeMatchType.None && AllDestinations.Count > 0;
}
