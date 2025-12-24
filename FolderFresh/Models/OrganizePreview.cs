using System.Collections.Generic;

namespace FolderFresh.Models;

/// <summary>
/// Represents a preview of the organize operation before execution
/// </summary>
public class OrganizePreview
{
    public List<FileOrganizeResult> Results { get; set; } = new();

    /// <summary>
    /// Total files that will be organized
    /// </summary>
    public int TotalFiles => Results.Count;

    /// <summary>
    /// Files matched by rules
    /// </summary>
    public int RuleMatchCount => Results.FindAll(r => r.MatchedBy == OrganizeMatchType.Rule).Count;

    /// <summary>
    /// Files matched by categories
    /// </summary>
    public int CategoryMatchCount => Results.FindAll(r => r.MatchedBy == OrganizeMatchType.Category).Count;

    /// <summary>
    /// Files with no match
    /// </summary>
    public int NoMatchCount => Results.FindAll(r => r.MatchedBy == OrganizeMatchType.None).Count;
}

/// <summary>
/// How a file was matched for organization
/// </summary>
public enum OrganizeMatchType
{
    None,
    Rule,
    Category
}
