using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace FolderFreshLite.Models;

/// <summary>
/// A group of conditions with a match type (All/Any/None).
/// Supports nested groups for complex AND/OR logic.
/// </summary>
public class ConditionGroup
{
    /// <summary>
    /// How conditions in this group are evaluated
    /// </summary>
    [JsonPropertyName("matchType")]
    public ConditionMatchType MatchType { get; set; } = ConditionMatchType.All;

    /// <summary>
    /// The conditions in this group
    /// </summary>
    [JsonPropertyName("conditions")]
    public List<Condition> Conditions { get; set; } = new();

    /// <summary>
    /// Nested condition groups for complex logic (e.g., (A AND B) OR (C AND D))
    /// </summary>
    [JsonPropertyName("nestedGroups")]
    public List<ConditionGroup> NestedGroups { get; set; } = new();

    /// <summary>
    /// Display string describing the match type
    /// </summary>
    [JsonIgnore]
    public string MatchTypeDisplay => MatchType switch
    {
        ConditionMatchType.All => "Match ALL of the following",
        ConditionMatchType.Any => "Match ANY of the following",
        ConditionMatchType.None => "Match NONE of the following",
        _ => "Match conditions"
    };
}

/// <summary>
/// Defines how conditions in a group are combined
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum ConditionMatchType
{
    /// <summary>
    /// All conditions must be true (AND)
    /// </summary>
    All,

    /// <summary>
    /// At least one condition must be true (OR)
    /// </summary>
    Any,

    /// <summary>
    /// No conditions can be true (NOT ANY)
    /// </summary>
    None
}
