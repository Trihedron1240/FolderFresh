using System.Text.Json.Serialization;

namespace FolderFresh.Models;

/// <summary>
/// A single condition that evaluates a file attribute against a value
/// </summary>
public class Condition
{
    /// <summary>
    /// The file attribute to evaluate
    /// </summary>
    [JsonPropertyName("attribute")]
    public ConditionAttribute Attribute { get; set; }

    /// <summary>
    /// The comparison operator
    /// </summary>
    [JsonPropertyName("operator")]
    public ConditionOperator Operator { get; set; }

    /// <summary>
    /// The value to compare against
    /// </summary>
    [JsonPropertyName("value")]
    public string Value { get; set; } = string.Empty;

    /// <summary>
    /// Secondary value for operators like "between" or "is in the last X days"
    /// </summary>
    [JsonPropertyName("secondaryValue")]
    public string? SecondaryValue { get; set; }

    /// <summary>
    /// Display string describing this condition
    /// </summary>
    [JsonIgnore]
    public string DisplayText => $"{GetAttributeDisplay()} {GetOperatorDisplay()} {GetValueDisplay()}";

    private string GetAttributeDisplay() => Attribute switch
    {
        ConditionAttribute.Name => "Name",
        ConditionAttribute.Extension => "Extension",
        ConditionAttribute.FullName => "Full name",
        ConditionAttribute.Kind => "Kind",
        ConditionAttribute.Size => "Size",
        ConditionAttribute.DateCreated => "Date created",
        ConditionAttribute.DateModified => "Date modified",
        ConditionAttribute.DateAccessed => "Date accessed",
        ConditionAttribute.Contents => "Contents",
        _ => Attribute.ToString()
    };

    private string GetOperatorDisplay() => Operator switch
    {
        ConditionOperator.Is => "is",
        ConditionOperator.IsNot => "is not",
        ConditionOperator.Contains => "contains",
        ConditionOperator.DoesNotContain => "does not contain",
        ConditionOperator.StartsWith => "starts with",
        ConditionOperator.EndsWith => "ends with",
        ConditionOperator.MatchesPattern => "matches pattern",
        ConditionOperator.IsGreaterThan => "is greater than",
        ConditionOperator.IsLessThan => "is less than",
        ConditionOperator.IsInTheLast => "is in the last",
        ConditionOperator.IsBefore => "is before",
        ConditionOperator.IsAfter => "is after",
        ConditionOperator.IsBlank => "is blank",
        ConditionOperator.IsNotBlank => "is not blank",
        _ => Operator.ToString()
    };

    private string GetValueDisplay()
    {
        if (Operator == ConditionOperator.IsBlank || Operator == ConditionOperator.IsNotBlank)
            return string.Empty;

        if (Operator == ConditionOperator.IsInTheLast && !string.IsNullOrEmpty(SecondaryValue))
            return $"{Value} {SecondaryValue}";

        return $"\"{Value}\"";
    }
}

/// <summary>
/// File attributes that can be evaluated in conditions
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum ConditionAttribute
{
    /// <summary>
    /// File name without extension
    /// </summary>
    Name,

    /// <summary>
    /// File extension (e.g., ".pdf", ".jpg")
    /// </summary>
    Extension,

    /// <summary>
    /// Full file name including extension
    /// </summary>
    FullName,

    /// <summary>
    /// File type/kind (Image, PDF, Document, Video, Audio, Archive, etc.)
    /// </summary>
    Kind,

    /// <summary>
    /// File size in bytes
    /// </summary>
    Size,

    /// <summary>
    /// Date the file was created
    /// </summary>
    DateCreated,

    /// <summary>
    /// Date the file was last modified
    /// </summary>
    DateModified,

    /// <summary>
    /// Date the file was last accessed
    /// </summary>
    DateAccessed,

    /// <summary>
    /// File contents (for text files, future feature)
    /// </summary>
    Contents
}

/// <summary>
/// Comparison operators for conditions
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum ConditionOperator
{
    /// <summary>
    /// Exact match
    /// </summary>
    Is,

    /// <summary>
    /// Not an exact match
    /// </summary>
    IsNot,

    /// <summary>
    /// Contains the value as a substring
    /// </summary>
    Contains,

    /// <summary>
    /// Does not contain the value
    /// </summary>
    DoesNotContain,

    /// <summary>
    /// Starts with the value
    /// </summary>
    StartsWith,

    /// <summary>
    /// Ends with the value
    /// </summary>
    EndsWith,

    /// <summary>
    /// Matches a regex or glob pattern
    /// </summary>
    MatchesPattern,

    /// <summary>
    /// Greater than (for sizes and dates)
    /// </summary>
    IsGreaterThan,

    /// <summary>
    /// Less than (for sizes and dates)
    /// </summary>
    IsLessThan,

    /// <summary>
    /// Within the last X days/weeks/months (SecondaryValue = unit)
    /// </summary>
    IsInTheLast,

    /// <summary>
    /// Before a specific date
    /// </summary>
    IsBefore,

    /// <summary>
    /// After a specific date
    /// </summary>
    IsAfter,

    /// <summary>
    /// Value is empty or null
    /// </summary>
    IsBlank,

    /// <summary>
    /// Value is not empty
    /// </summary>
    IsNotBlank
}

/// <summary>
/// File kinds for the Kind attribute
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum FileKind
{
    Image,
    Document,
    PDF,
    Video,
    Audio,
    Archive,
    Executable,
    Code,
    Text,
    Spreadsheet,
    Presentation,
    Font,
    Other
}
