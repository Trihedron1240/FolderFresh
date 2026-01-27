using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using FolderFresh.Models;

namespace FolderFresh.Services;

/// <summary>
/// Service for managing and evaluating file organization rules
/// </summary>
public class RuleService
{
    private const string AppFolderName = "FolderFresh";
    private const string RulesFileName = "rules.json";

    private readonly string _rulesFilePath;
    private readonly CategoryService? _categoryService;
    private List<Rule> _rules = new();

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    // Extension to FileKind mapping
    private static readonly Dictionary<string, FileKind> ExtensionKinds = new(StringComparer.OrdinalIgnoreCase)
    {
        // Images
        { ".jpg", FileKind.Image }, { ".jpeg", FileKind.Image }, { ".png", FileKind.Image },
        { ".gif", FileKind.Image }, { ".bmp", FileKind.Image }, { ".svg", FileKind.Image },
        { ".webp", FileKind.Image }, { ".ico", FileKind.Image }, { ".tiff", FileKind.Image },

        // Documents
        { ".doc", FileKind.Document }, { ".docx", FileKind.Document }, { ".rtf", FileKind.Document },
        { ".odt", FileKind.Document },

        // PDF
        { ".pdf", FileKind.PDF },

        // Video
        { ".mp4", FileKind.Video }, { ".avi", FileKind.Video }, { ".mkv", FileKind.Video },
        { ".mov", FileKind.Video }, { ".wmv", FileKind.Video }, { ".flv", FileKind.Video },
        { ".webm", FileKind.Video },

        // Audio
        { ".mp3", FileKind.Audio }, { ".wav", FileKind.Audio }, { ".flac", FileKind.Audio },
        { ".aac", FileKind.Audio }, { ".ogg", FileKind.Audio }, { ".m4a", FileKind.Audio },
        { ".wma", FileKind.Audio },

        // Archive
        { ".zip", FileKind.Archive }, { ".rar", FileKind.Archive }, { ".7z", FileKind.Archive },
        { ".tar", FileKind.Archive }, { ".gz", FileKind.Archive }, { ".bz2", FileKind.Archive },

        // Executable
        { ".exe", FileKind.Executable }, { ".msi", FileKind.Executable }, { ".bat", FileKind.Executable },
        { ".cmd", FileKind.Executable }, { ".ps1", FileKind.Executable },

        // Code
        { ".cs", FileKind.Code }, { ".js", FileKind.Code }, { ".ts", FileKind.Code },
        { ".py", FileKind.Code }, { ".java", FileKind.Code }, { ".cpp", FileKind.Code },
        { ".c", FileKind.Code }, { ".h", FileKind.Code }, { ".html", FileKind.Code },
        { ".css", FileKind.Code }, { ".json", FileKind.Code }, { ".xml", FileKind.Code },

        // Text
        { ".txt", FileKind.Text }, { ".md", FileKind.Text }, { ".log", FileKind.Text },

        // Spreadsheet
        { ".xls", FileKind.Spreadsheet }, { ".xlsx", FileKind.Spreadsheet }, { ".csv", FileKind.Spreadsheet },
        { ".ods", FileKind.Spreadsheet },

        // Presentation
        { ".ppt", FileKind.Presentation }, { ".pptx", FileKind.Presentation }, { ".odp", FileKind.Presentation },

        // Font
        { ".ttf", FileKind.Font }, { ".otf", FileKind.Font }, { ".woff", FileKind.Font },
        { ".woff2", FileKind.Font }
    };

    public RuleService() : this(null)
    {
    }

    public RuleService(CategoryService? categoryService)
    {
        _categoryService = categoryService;

        var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var appFolderPath = Path.Combine(appDataPath, AppFolderName);

        if (!Directory.Exists(appFolderPath))
        {
            Directory.CreateDirectory(appFolderPath);
        }

        _rulesFilePath = Path.Combine(appFolderPath, RulesFileName);
    }

    #region CRUD Operations

    /// <summary>
    /// Loads rules from JSON file. Creates empty file if doesn't exist.
    /// </summary>
    public async Task<List<Rule>> LoadRulesAsync()
    {
        try
        {
            if (!File.Exists(_rulesFilePath))
            {
                _rules = new List<Rule>();
                await SaveRulesAsync(_rules);
                return _rules;
            }

            var json = await File.ReadAllTextAsync(_rulesFilePath);
            var data = JsonSerializer.Deserialize<RulesFile>(json, JsonOptions);
            _rules = data?.Rules ?? new List<Rule>();

            // Sort by priority
            _rules = _rules.OrderBy(r => r.Priority).ToList();
            return _rules;
        }
        catch (Exception)
        {
            _rules = new List<Rule>();
            return _rules;
        }
    }

    /// <summary>
    /// Saves rules to JSON file.
    /// </summary>
    public async Task SaveRulesAsync(List<Rule> rules)
    {
        try
        {
            _rules = rules;
            var data = new RulesFile { Rules = rules };
            var json = JsonSerializer.Serialize(data, JsonOptions);
            await File.WriteAllTextAsync(_rulesFilePath, json);
        }
        catch (Exception)
        {
            // Log error if needed
        }
    }

    /// <summary>
    /// Gets all loaded rules.
    /// </summary>
    public List<Rule> GetRules()
    {
        return _rules;
    }

    /// <summary>
    /// Adds a new rule and saves to file.
    /// </summary>
    public async Task<Rule> AddRuleAsync(Rule rule)
    {
        if (string.IsNullOrEmpty(rule.Id))
        {
            rule.Id = Guid.NewGuid().ToString("N")[..8];
        }

        rule.CreatedAt = DateTime.Now;
        rule.ModifiedAt = DateTime.Now;

        // Set priority to end of list
        rule.Priority = _rules.Count > 0 ? _rules.Max(r => r.Priority) + 1 : 0;

        _rules.Add(rule);
        await SaveRulesAsync(_rules);
        return rule;
    }

    /// <summary>
    /// Updates an existing rule and saves to file.
    /// </summary>
    public async Task UpdateRuleAsync(Rule rule)
    {
        var index = _rules.FindIndex(r => r.Id == rule.Id);
        if (index >= 0)
        {
            rule.ModifiedAt = DateTime.Now;
            _rules[index] = rule;
            await SaveRulesAsync(_rules);
        }
    }

    /// <summary>
    /// Deletes a rule and saves to file.
    /// </summary>
    public async Task DeleteRuleAsync(string ruleId)
    {
        var rule = _rules.FirstOrDefault(r => r.Id == ruleId);
        if (rule != null)
        {
            _rules.Remove(rule);
            await SaveRulesAsync(_rules);
        }
    }

    /// <summary>
    /// Reorders rules based on the provided ID list.
    /// </summary>
    public async Task ReorderRulesAsync(List<string> ruleIds)
    {
        for (int i = 0; i < ruleIds.Count; i++)
        {
            var rule = _rules.FirstOrDefault(r => r.Id == ruleIds[i]);
            if (rule != null)
            {
                rule.Priority = i;
                rule.ModifiedAt = DateTime.Now;
            }
        }

        _rules = _rules.OrderBy(r => r.Priority).ToList();
        await SaveRulesAsync(_rules);
    }

    #endregion

    #region Rule Evaluation

    /// <summary>
    /// Finds the first matching rule for a file.
    /// </summary>
    public Rule? GetMatchingRule(FileInfo file)
    {
        return _rules
            .Where(r => r.IsEnabled)
            .OrderBy(r => r.Priority)
            .FirstOrDefault(r => EvaluateConditionGroup(r.Conditions, file));
    }

    /// <summary>
    /// Finds the first matching rule for a file from a provided list of rules.
    /// </summary>
    public Rule? GetMatchingRule(FileInfo file, List<Rule> rules)
    {
        return rules
            .Where(r => r.IsEnabled)
            .OrderBy(r => r.Priority)
            .FirstOrDefault(r => EvaluateConditionGroup(r.Conditions, file));
    }

    /// <summary>
    /// Gets all matching rules for a file, respecting the Continue action.
    /// Returns rules in priority order, stopping when a rule without Continue is found.
    /// </summary>
    public List<Rule> GetMatchingRulesWithContinue(FileInfo file, List<Rule> rules)
    {
        var matchingRules = new List<Rule>();
        var orderedRules = rules
            .Where(r => r.IsEnabled)
            .OrderBy(r => r.Priority)
            .ToList();

        foreach (var rule in orderedRules)
        {
            if (EvaluateConditionGroup(rule.Conditions, file))
            {
                matchingRules.Add(rule);

                // Check if this rule has a Continue action
                var hasContinue = rule.Actions.Any(a => a.Type == ActionType.Continue);
                if (!hasContinue)
                {
                    // Stop processing more rules
                    break;
                }
            }
        }

        return matchingRules;
    }

    /// <summary>
    /// Calculates the destination path for a file based on rule actions.
    /// Simulates all actions in sequence and returns the final destination path.
    /// For backward compatibility, returns the primary destination (move/rename location).
    /// </summary>
    public string? CalculateDestinationPath(Rule rule, FileInfo file, string baseFolderPath, CategoryService? categoryService = null)
    {
        var destinations = CalculateAllDestinationPaths(rule, file, baseFolderPath, categoryService);
        // Return the primary destination (first one, which is the move/rename result)
        return destinations.Count > 0 ? destinations[0] : null;
    }

    /// <summary>
    /// Calculates ALL destination paths for a file based on rule actions.
    /// Returns a list of destinations: the primary move/rename destination first,
    /// followed by any copy destinations.
    /// </summary>
    public List<string> CalculateAllDestinationPaths(Rule rule, FileInfo file, string baseFolderPath, CategoryService? categoryService = null)
    {
        var allDestinations = new List<string>();

        // Track current file name and directory as we simulate actions
        var currentFileName = file.Name;
        var currentDirectory = file.DirectoryName ?? baseFolderPath;
        string? primaryDestination = null;

        foreach (var action in rule.Actions)
        {
            switch (action.Type)
            {
                case ActionType.Rename:
                    // Simulate rename - update the current file name
                    currentFileName = ExpandPattern(action.Value, file, categoryService);
                    // If no move action follows, the file stays in current directory with new name
                    primaryDestination = Path.Combine(currentDirectory, currentFileName);
                    break;

                case ActionType.MoveToFolder:
                    var moveDestFolder = action.Value;
                    if (!Path.IsPathRooted(moveDestFolder))
                    {
                        moveDestFolder = Path.Combine(baseFolderPath, moveDestFolder);
                    }
                    currentDirectory = moveDestFolder;
                    primaryDestination = Path.Combine(moveDestFolder, currentFileName);
                    break;

                case ActionType.CopyToFolder:
                    // Copy creates a copy at destination - add to destinations list
                    var copyDestFolder = action.Value;
                    if (!Path.IsPathRooted(copyDestFolder))
                    {
                        copyDestFolder = Path.Combine(baseFolderPath, copyDestFolder);
                    }
                    // Use current filename (may have been renamed)
                    var copyDestPath = Path.Combine(copyDestFolder, currentFileName);
                    allDestinations.Add(copyDestPath);
                    break;

                case ActionType.MoveToCategory:
                    if (categoryService != null && !string.IsNullOrEmpty(action.Value))
                    {
                        var categories = categoryService.GetCategories();
                        var category = categories.FirstOrDefault(c => c.Id == action.Value);
                        if (category != null)
                        {
                            var categoryPath = Path.IsPathRooted(category.Destination)
                                ? category.Destination
                                : Path.Combine(baseFolderPath, category.Destination);
                            currentDirectory = categoryPath;
                            primaryDestination = Path.Combine(categoryPath, currentFileName);
                        }
                    }
                    break;

                case ActionType.SortIntoSubfolder:
                    var subfolderName = ExpandPattern(action.Value, file, categoryService);
                    // Normalize path separators (user might use / in pattern)
                    subfolderName = subfolderName.Replace('/', Path.DirectorySeparatorChar);
                    var subfolderPath = Path.Combine(baseFolderPath, subfolderName);
                    currentDirectory = subfolderPath;
                    primaryDestination = Path.Combine(subfolderPath, currentFileName);
                    break;

                case ActionType.Delete:
                    // Delete is a terminal action
                    return new List<string> { "[RECYCLE BIN]" };

                case ActionType.Ignore:
                    return new List<string>();

                case ActionType.Continue:
                    // Continue doesn't affect destination
                    break;
            }
        }

        // Build final list: primary destination first, then copies
        var result = new List<string>();
        if (primaryDestination != null)
        {
            result.Add(primaryDestination);
        }
        result.AddRange(allDestinations);

        return result;
    }

    /// <summary>
    /// Gets the primary action type for a rule (first move/copy/delete action).
    /// </summary>
    public ActionType? GetPrimaryActionType(Rule rule)
    {
        return rule.Actions.FirstOrDefault()?.Type;
    }

    /// <summary>
    /// Calculates all destination paths for a file based on rule actions.
    /// Returns a list of (destination path, action type) tuples representing
    /// every location where a file or copy will end up.
    /// </summary>
    public List<(string Path, ActionType ActionType)> CalculateAllDestinations(Rule rule, FileInfo file, string baseFolderPath, CategoryService? categoryService = null)
    {
        var destinations = new List<(string Path, ActionType ActionType)>();

        // Track current file name and directory as we simulate actions
        var currentFileName = file.Name;
        var currentDirectory = file.DirectoryName ?? baseFolderPath;
        string? currentFilePath = null; // Where the original file currently is

        foreach (var action in rule.Actions)
        {
            switch (action.Type)
            {
                case ActionType.Rename:
                    // Simulate rename - update the current file name
                    currentFileName = ExpandPattern(action.Value, file, categoryService);
                    currentFilePath = Path.Combine(currentDirectory, currentFileName);
                    break;

                case ActionType.MoveToFolder:
                    var moveDestFolder = action.Value;
                    if (!Path.IsPathRooted(moveDestFolder))
                    {
                        moveDestFolder = Path.Combine(baseFolderPath, moveDestFolder);
                    }
                    currentDirectory = moveDestFolder;
                    currentFilePath = Path.Combine(moveDestFolder, currentFileName);
                    // Don't add yet - we add the final location of the original at the end
                    break;

                case ActionType.CopyToFolder:
                    var copyDestFolder = action.Value;
                    if (!Path.IsPathRooted(copyDestFolder))
                    {
                        copyDestFolder = Path.Combine(baseFolderPath, copyDestFolder);
                    }
                    // Copy creates a new file - add it immediately
                    destinations.Add((Path.Combine(copyDestFolder, currentFileName), ActionType.CopyToFolder));
                    break;

                case ActionType.MoveToCategory:
                    if (categoryService != null && !string.IsNullOrEmpty(action.Value))
                    {
                        var categories = categoryService.GetCategories();
                        var category = categories.FirstOrDefault(c => c.Id == action.Value);
                        if (category != null)
                        {
                            var categoryPath = Path.IsPathRooted(category.Destination)
                                ? category.Destination
                                : Path.Combine(baseFolderPath, category.Destination);
                            currentDirectory = categoryPath;
                            currentFilePath = Path.Combine(categoryPath, currentFileName);
                        }
                    }
                    break;

                case ActionType.SortIntoSubfolder:
                    var subfolderName2 = ExpandPattern(action.Value, file, categoryService);
                    var subfolderPath2 = Path.Combine(baseFolderPath, subfolderName2);
                    currentDirectory = subfolderPath2;
                    currentFilePath = Path.Combine(subfolderPath2, currentFileName);
                    break;

                case ActionType.Delete:
                    // File is deleted - add recycle bin as destination
                    destinations.Add(("[RECYCLE BIN]", ActionType.Delete));
                    return destinations; // No further destinations after delete

                case ActionType.Ignore:
                    // File is ignored - no destinations
                    return destinations;

                case ActionType.Continue:
                    // Continue doesn't affect destination
                    break;
            }
        }

        // Add the final location of the original file (from move/rename operations)
        if (currentFilePath != null)
        {
            // Insert at beginning so the original file's location comes first
            destinations.Insert(0, (currentFilePath, ActionType.MoveToFolder));
        }

        return destinations;
    }

    /// <summary>
    /// Evaluates a condition group against a file.
    /// </summary>
    public bool EvaluateConditionGroup(ConditionGroup group, FileInfo file)
    {
        if (group.Conditions.Count == 0 && group.NestedGroups.Count == 0)
            return true; // Empty group matches everything

        var conditionResults = group.Conditions.Select(c => EvaluateCondition(c, file)).ToList();
        var nestedResults = group.NestedGroups.Select(g => EvaluateConditionGroup(g, file)).ToList();
        var allResults = conditionResults.Concat(nestedResults).ToList();

        return group.MatchType switch
        {
            ConditionMatchType.All => allResults.All(r => r),
            ConditionMatchType.Any => allResults.Any(r => r),
            ConditionMatchType.None => !allResults.Any(r => r),
            _ => false
        };
    }

    /// <summary>
    /// Evaluates a single condition against a file.
    /// </summary>
    public bool EvaluateCondition(Condition condition, FileInfo file)
    {
        // Handle special attribute types with dedicated evaluation methods
        return condition.Attribute switch
        {
            ConditionAttribute.Name => EvaluateStringCondition(
                Path.GetFileNameWithoutExtension(file.Name),
                condition.Operator,
                condition.Value ?? string.Empty),

            ConditionAttribute.Extension => EvaluateStringCondition(
                file.Extension.TrimStart('.').ToLowerInvariant(),
                condition.Operator,
                (condition.Value ?? string.Empty).TrimStart('.').ToLowerInvariant()),

            ConditionAttribute.FullName => EvaluateStringCondition(
                file.Name,
                condition.Operator,
                condition.Value ?? string.Empty),

            ConditionAttribute.Kind => EvaluateKindCondition(file, condition),

            ConditionAttribute.Size => EvaluateSizeCondition(file.Length, condition),

            ConditionAttribute.DateCreated => EvaluateDateCondition(file.CreationTime, condition),

            ConditionAttribute.DateModified => EvaluateDateCondition(file.LastWriteTime, condition),

            ConditionAttribute.DateAccessed => EvaluateDateCondition(file.LastAccessTime, condition),

            ConditionAttribute.Contents => false, // Future: implement content search

            ConditionAttribute.Folder => EvaluateStringCondition(
                file.Directory?.Name ?? string.Empty,
                condition.Operator,
                condition.Value ?? string.Empty),

            ConditionAttribute.FolderPath => EvaluatePathCondition(
                file.DirectoryName ?? string.Empty,
                condition.Operator,
                condition.Value ?? string.Empty),

            _ => false
        };
    }

    /// <summary>
    /// Normalizes a path by trimming quotes and trailing slashes/backslashes.
    /// </summary>
    private static string NormalizePath(string path)
    {
        if (string.IsNullOrEmpty(path))
            return path;
        // Trim surrounding quotes first, then trailing slashes
        return path.Trim('"', '\'').TrimEnd('\\', '/');
    }

    /// <summary>
    /// Evaluates path-based conditions with normalization for trailing slashes.
    /// </summary>
    private static bool EvaluatePathCondition(string actual, ConditionOperator op, string expected)
    {
        // Normalize paths to handle trailing slash differences
        var normalizedActual = NormalizePath(actual);
        var normalizedExpected = NormalizePath(expected);

        return op switch
        {
            ConditionOperator.Is => normalizedActual.Equals(normalizedExpected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.IsNot => !normalizedActual.Equals(normalizedExpected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.Contains => normalizedActual.Contains(normalizedExpected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.DoesNotContain => !normalizedActual.Contains(normalizedExpected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.StartsWith => normalizedActual.StartsWith(normalizedExpected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.EndsWith => normalizedActual.EndsWith(normalizedExpected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.MatchesPattern => MatchesWildcard(normalizedActual, normalizedExpected),
            ConditionOperator.IsBlank => string.IsNullOrWhiteSpace(actual),
            ConditionOperator.IsNotBlank => !string.IsNullOrWhiteSpace(actual),
            _ => false
        };
    }

    /// <summary>
    /// Evaluates string-based conditions (Name, Extension, FullName)
    /// </summary>
    private static bool EvaluateStringCondition(string actual, ConditionOperator op, string expected)
    {
        return op switch
        {
            ConditionOperator.Is => actual.Equals(expected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.IsNot => !actual.Equals(expected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.Contains => actual.Contains(expected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.DoesNotContain => !actual.Contains(expected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.StartsWith => actual.StartsWith(expected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.EndsWith => actual.EndsWith(expected, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.MatchesPattern => MatchesWildcard(actual, expected),
            ConditionOperator.IsBlank => string.IsNullOrWhiteSpace(actual),
            ConditionOperator.IsNotBlank => !string.IsNullOrWhiteSpace(actual),
            _ => false
        };
    }

    /// <summary>
    /// Evaluates file kind conditions (Document, Image, Audio, Video, Archive, etc.)
    /// </summary>
    private bool EvaluateKindCondition(FileInfo file, Condition condition)
    {
        var kind = GetFileKind(file.Extension).ToString();
        var expectedKind = condition.Value ?? string.Empty;

        return condition.Operator switch
        {
            ConditionOperator.Is => kind.Equals(expectedKind, StringComparison.OrdinalIgnoreCase),
            ConditionOperator.IsNot => !kind.Equals(expectedKind, StringComparison.OrdinalIgnoreCase),
            _ => false
        };
    }

    /// <summary>
    /// Evaluates file size conditions with unit support
    /// </summary>
    private static bool EvaluateSizeCondition(long bytes, Condition condition)
    {
        var targetBytes = ParseSizeToBytes(condition.Value ?? "0", condition.SecondaryValue);

        return condition.Operator switch
        {
            ConditionOperator.IsGreaterThan => bytes > targetBytes,
            ConditionOperator.IsLessThan => bytes < targetBytes,
            ConditionOperator.Is => bytes == targetBytes,
            ConditionOperator.IsNot => bytes != targetBytes,
            _ => false
        };
    }

    /// <summary>
    /// Parses a size value with optional unit to bytes
    /// </summary>
    private static long ParseSizeToBytes(string value, string? unit)
    {
        if (!long.TryParse(value, out var number))
        {
            // Try parsing with embedded unit (e.g., "10MB")
            return ParseSizeWithUnits(value);
        }

        return (unit?.ToUpperInvariant()) switch
        {
            "KB" => number * 1024,
            "MB" => number * 1024 * 1024,
            "GB" => number * 1024 * 1024 * 1024,
            "TB" => number * 1024 * 1024 * 1024 * 1024,
            "B" or null or "" => number,
            _ => number
        };
    }

    /// <summary>
    /// Evaluates date-based conditions
    /// </summary>
    private static bool EvaluateDateCondition(DateTime actual, Condition condition)
    {
        return condition.Operator switch
        {
            ConditionOperator.IsBefore => DateTime.TryParse(condition.Value, out var beforeDate) && actual < beforeDate,
            ConditionOperator.IsAfter => DateTime.TryParse(condition.Value, out var afterDate) && actual > afterDate,
            ConditionOperator.IsInTheLast => IsInTheLastInternal(actual, condition.Value ?? "0", condition.SecondaryValue),
            _ => false
        };
    }

    /// <summary>
    /// Checks if a date is within the last N units of time
    /// </summary>
    private static bool IsInTheLastInternal(DateTime date, string value, string? unit)
    {
        if (!int.TryParse(value, out var number))
            return false;

        var cutoff = (unit?.ToLowerInvariant()) switch
        {
            "days" or "day" => DateTime.Now.AddDays(-number),
            "weeks" or "week" => DateTime.Now.AddDays(-number * 7),
            "months" or "month" => DateTime.Now.AddMonths(-number),
            "years" or "year" => DateTime.Now.AddYears(-number),
            "hours" or "hour" => DateTime.Now.AddHours(-number),
            "minutes" or "minute" => DateTime.Now.AddMinutes(-number),
            _ => DateTime.Now.AddDays(-number) // Default to days
        };

        return date >= cutoff;
    }

    /// <summary>
    /// Matches a string against a wildcard pattern (* and ?)
    /// </summary>
    private static bool MatchesWildcard(string value, string pattern)
    {
        try
        {
            if (string.IsNullOrEmpty(pattern))
                return string.IsNullOrEmpty(value);

            // Convert glob/wildcard to regex
            var regexPattern = "^" + Regex.Escape(pattern)
                .Replace("\\*", ".*")
                .Replace("\\?", ".") + "$";

            return Regex.IsMatch(value, regexPattern, RegexOptions.IgnoreCase);
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Gets the file kind based on extension using the ExtensionKinds dictionary
    /// </summary>
    private static FileKind GetFileKind(string extension)
    {
        if (string.IsNullOrEmpty(extension))
            return FileKind.Other;

        return ExtensionKinds.TryGetValue(extension, out var kind) ? kind : FileKind.Other;
    }

    /// <summary>
    /// Parses size strings with embedded units (e.g., "10MB", "1.5GB")
    /// </summary>
    private static long ParseSizeWithUnits(string sizeString)
    {
        sizeString = sizeString.Trim().ToUpperInvariant();

        var match = Regex.Match(sizeString, @"^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)?$");
        if (!match.Success)
            return 0;

        var value = double.Parse(match.Groups[1].Value);
        var unit = match.Groups[2].Value;

        return unit switch
        {
            "KB" => (long)(value * 1024),
            "MB" => (long)(value * 1024 * 1024),
            "GB" => (long)(value * 1024 * 1024 * 1024),
            "TB" => (long)(value * 1024 * 1024 * 1024 * 1024),
            _ => (long)value
        };
    }

    #endregion

    #region Action Execution

    /// <summary>
    /// Executes the actions for a rule on a file.
    /// Returns true if the file was handled (no fallback to categories needed).
    /// </summary>
    public async Task<RuleExecutionResult> ExecuteActionsAsync(Rule rule, FileInfo file, string baseOutputPath)
    {
        var result = new RuleExecutionResult { RuleId = rule.Id, RuleName = rule.Name };
        var shouldContinue = false;

        // Track current file path - actions may rename/move the file
        var currentFile = file;

        foreach (var action in rule.Actions)
        {
            try
            {
                switch (action.Type)
                {
                    case ActionType.MoveToFolder:
                        var moveDestFolder = Path.IsPathRooted(action.Value)
                            ? action.Value
                            : Path.Combine(baseOutputPath, action.Value);
                        currentFile = await MoveFileAsync(currentFile, moveDestFolder, action.Options);
                        result.ActionsTaken.Add($"Moved to {action.Value}");
                        break;

                    case ActionType.CopyToFolder:
                        if (!string.IsNullOrEmpty(action.Value))
                        {
                            var copyDestFolder = Path.IsPathRooted(action.Value)
                                ? action.Value
                                : Path.Combine(baseOutputPath, action.Value);
                            await CopyFileAsync(currentFile, copyDestFolder, action.Options);
                            result.ActionsTaken.Add($"Copied to {action.Value}");
                        }
                        else
                        {
                            result.Errors.Add("CopyToFolder: No destination folder specified");
                        }
                        break;

                    case ActionType.SortIntoSubfolder:
                        var subfolderName3 = ExpandPattern(action.Value, currentFile, _categoryService);
                        var subfolderPath3 = Path.Combine(baseOutputPath, subfolderName3);
                        currentFile = await MoveFileAsync(currentFile, subfolderPath3, action.Options);
                        result.ActionsTaken.Add($"Sorted into {subfolderName3}");
                        break;

                    case ActionType.Rename:
                        var newName = ExpandPattern(action.Value, currentFile, _categoryService);
                        currentFile = await RenameFileAsync(currentFile, newName);
                        result.ActionsTaken.Add($"Renamed to {newName}");
                        break;

                    case ActionType.Delete:
                        DeleteFileToRecycleBin(currentFile);
                        result.ActionsTaken.Add("Moved to Recycle Bin");
                        result.ShouldDelete = true;
                        break;

                    case ActionType.Ignore:
                        result.ActionsTaken.Add("Ignored");
                        result.WasIgnored = true;
                        break;

                    case ActionType.Continue:
                        shouldContinue = true;
                        result.ActionsTaken.Add("Continue to next rule");
                        break;

                    case ActionType.MoveToCategory:
                        if (_categoryService != null && !string.IsNullOrEmpty(action.Value))
                        {
                            currentFile = await MoveToCategoryAsync(currentFile, action.Value, baseOutputPath, action.Options);
                            result.ActionsTaken.Add($"Moved to category: {action.Value}");
                        }
                        else
                        {
                            result.UseCategory = true;
                            result.ActionsTaken.Add("Use category destination");
                        }
                        break;
                }
            }
            catch (Exception ex)
            {
                result.Errors.Add($"Action {action.Type} failed: {ex.Message}");
            }
        }

        result.ShouldContinue = shouldContinue;
        result.Success = result.Errors.Count == 0;
        return result;
    }

    private async Task<FileInfo> MoveFileAsync(FileInfo file, string destinationFolder, Dictionary<string, string> options)
    {
        if (!Directory.Exists(destinationFolder))
        {
            Directory.CreateDirectory(destinationFolder);
        }

        var destPath = Path.Combine(destinationFolder, file.Name);

        if (File.Exists(destPath))
        {
            var resolution = options.GetValueOrDefault(ActionOptionKeys.ConflictResolution, "rename");
            destPath = resolution switch
            {
                "skip" => throw new InvalidOperationException("File exists, skipping"),
                "overwrite" => destPath,
                _ => GetUniqueFileName(destPath)
            };

            if (resolution == "overwrite")
            {
                File.Delete(destPath);
            }
        }

        await Task.Run(() => file.MoveTo(destPath));
        return new FileInfo(destPath);
    }

    private async Task CopyFileAsync(FileInfo file, string destinationFolder, Dictionary<string, string> options)
    {
        if (!Directory.Exists(destinationFolder))
        {
            Directory.CreateDirectory(destinationFolder);
        }

        // Refresh file info to ensure we have current state after previous actions
        file.Refresh();

        if (!file.Exists)
        {
            throw new FileNotFoundException($"Source file not found: {file.FullName}");
        }

        var destPath = Path.Combine(destinationFolder, file.Name);

        if (File.Exists(destPath))
        {
            var resolution = options.GetValueOrDefault(ActionOptionKeys.ConflictResolution, "rename");
            destPath = resolution switch
            {
                "skip" => throw new InvalidOperationException("File exists, skipping"),
                "overwrite" => destPath,
                _ => GetUniqueFileName(destPath)
            };
        }

        await Task.Run(() => file.CopyTo(destPath, overwrite: true));
    }

    private async Task<FileInfo> RenameFileAsync(FileInfo file, string newName)
    {
        var newPath = Path.Combine(file.DirectoryName ?? "", newName);

        // Check if this is a case-only rename (same name, different case)
        var isCaseOnlyRename = file.FullName.Equals(newPath, StringComparison.OrdinalIgnoreCase) &&
                               !file.FullName.Equals(newPath, StringComparison.Ordinal);

        if (isCaseOnlyRename)
        {
            // Windows requires two-step rename for case changes
            var tempPath = file.FullName + ".tmp_rename";
            await Task.Run(() =>
            {
                file.MoveTo(tempPath);
                File.Move(tempPath, newPath);
            });
            return new FileInfo(newPath);
        }

        if (File.Exists(newPath))
        {
            newPath = GetUniqueFileName(newPath);
        }

        await Task.Run(() => file.MoveTo(newPath));
        return new FileInfo(newPath);
    }

    private static string GetUniqueFileName(string path)
    {
        var directory = Path.GetDirectoryName(path) ?? "";
        var name = Path.GetFileNameWithoutExtension(path);
        var extension = Path.GetExtension(path);
        var counter = 1;

        while (File.Exists(path))
        {
            path = Path.Combine(directory, $"{name} ({counter}){extension}");
            counter++;
        }

        return path;
    }

    /// <summary>
    /// Moves a file to a category destination folder.
    /// </summary>
    private async Task<FileInfo> MoveToCategoryAsync(FileInfo file, string categoryId, string baseOutputPath, Dictionary<string, string>? options)
    {
        if (_categoryService == null)
            throw new InvalidOperationException("CategoryService not available");

        var categories = _categoryService.GetCategories();
        var category = categories.FirstOrDefault(c => c.Id == categoryId);

        if (category == null)
            throw new InvalidOperationException($"Category not found: {categoryId}");

        var categoryPath = Path.IsPathRooted(category.Destination)
            ? category.Destination
            : Path.Combine(baseOutputPath, category.Destination);

        return await MoveFileAsync(file, categoryPath, options ?? new Dictionary<string, string>());
    }

    /// <summary>
    /// Deletes a file by moving it to the Windows Recycle Bin.
    /// </summary>
    private static void DeleteFileToRecycleBin(FileInfo file)
    {
#if WINDOWS
        Microsoft.VisualBasic.FileIO.FileSystem.DeleteFile(
            file.FullName,
            Microsoft.VisualBasic.FileIO.UIOption.OnlyErrorDialogs,
            Microsoft.VisualBasic.FileIO.RecycleOption.SendToRecycleBin);
#else
        // Fallback for non-Windows: permanent delete
        file.Delete();
#endif
    }

    /// <summary>
    /// Expands pattern tokens in a string using file properties.
    /// Supported tokens: {Name}, {Extension}, {Category}, {Year}, {Month}, {Day}, {Date}, {Today}, {Kind},
    /// {CreatedYear}, {CreatedMonth}, {CreatedDay}, {date:format}, {created:format}, {today:format}
    /// </summary>
    public static string ExpandPattern(string pattern, FileInfo file)
    {
        return ExpandPattern(pattern, file, null);
    }

    /// <summary>
    /// Expands pattern tokens in a string using file properties.
    /// Supported tokens: {Name}, {Extension}, {Category}, {Year}, {Month}, {Day}, {Date}, {Today}, {Kind},
    /// {CreatedYear}, {CreatedMonth}, {CreatedDay}, {date:format}, {created:format}, {today:format}
    /// </summary>
    public static string ExpandPattern(string pattern, FileInfo file, CategoryService? categoryService)
    {
        var result = pattern;
        var now = DateTime.Now;

        // {Name} / {name} - filename without extension
        result = result.Replace("{Name}", Path.GetFileNameWithoutExtension(file.Name));
        result = result.Replace("{name}", Path.GetFileNameWithoutExtension(file.Name));

        // {Extension} / {extension} / {ext} - extension without dot
        result = result.Replace("{Extension}", file.Extension.TrimStart('.'));
        result = result.Replace("{extension}", file.Extension.TrimStart('.'));
        result = result.Replace("{ext}", file.Extension.TrimStart('.'));

        // {date:format} - modified date with custom format
        var datePattern = new Regex(@"\{date:([^}]+)\}", RegexOptions.IgnoreCase);
        result = datePattern.Replace(result, m =>
        {
            var format = m.Groups[1].Value;
            return file.LastWriteTime.ToString(format);
        });

        // {created:format} - created date with custom format
        var createdPattern = new Regex(@"\{created:([^}]+)\}", RegexOptions.IgnoreCase);
        result = createdPattern.Replace(result, m =>
        {
            var format = m.Groups[1].Value;
            return file.CreationTime.ToString(format);
        });

        // {today:format} - current date with custom format
        var todayPattern = new Regex(@"\{today:([^}]+)\}", RegexOptions.IgnoreCase);
        result = todayPattern.Replace(result, m =>
        {
            var format = m.Groups[1].Value;
            return now.ToString(format);
        });

        // {Date} / {date} - modified date in default format
        result = result.Replace("{Date}", file.LastWriteTime.ToString("yyyy-MM-dd"));
        result = result.Replace("{date}", file.LastWriteTime.ToString("yyyy-MM-dd"));

        // {Today} / {today} - current date in default format
        result = result.Replace("{Today}", now.ToString("yyyy-MM-dd"));
        result = result.Replace("{today}", now.ToString("yyyy-MM-dd"));

        // {Year}, {Month}, {Day} - modified date components
        result = result.Replace("{Year}", file.LastWriteTime.Year.ToString());
        result = result.Replace("{year}", file.LastWriteTime.Year.ToString());
        result = result.Replace("{Month}", file.LastWriteTime.Month.ToString("D2"));
        result = result.Replace("{month}", file.LastWriteTime.Month.ToString("D2"));
        result = result.Replace("{Day}", file.LastWriteTime.Day.ToString("D2"));
        result = result.Replace("{day}", file.LastWriteTime.Day.ToString("D2"));

        // {CreatedYear}, {CreatedMonth}, {CreatedDay} - created date components
        result = result.Replace("{CreatedYear}", file.CreationTime.Year.ToString());
        result = result.Replace("{CreatedMonth}", file.CreationTime.Month.ToString("D2"));
        result = result.Replace("{CreatedDay}", file.CreationTime.Day.ToString("D2"));

        // {Kind} / {kind} - file kind based on extension
        result = result.Replace("{Kind}", GetFileKind(file.Extension).ToString());
        result = result.Replace("{kind}", GetFileKind(file.Extension).ToString());

        // {Category} / {category} - user-defined category name based on extension
        if (categoryService != null && (result.Contains("{Category}") || result.Contains("{category}")))
        {
            var category = categoryService.GetCategoryForFile(file.Extension);
            result = result.Replace("{Category}", category.Name);
            result = result.Replace("{category}", category.Name);
        }

        return result;
    }

    #endregion

    #region Helper Classes

    private class RulesFile
    {
        [JsonPropertyName("rules")]
        public List<Rule> Rules { get; set; } = new();

        [JsonPropertyName("version")]
        public int Version { get; set; } = 1;
    }

    #endregion
}

/// <summary>
/// Result of executing rule actions on a file
/// </summary>
public class RuleExecutionResult
{
    public string RuleId { get; set; } = string.Empty;
    public string RuleName { get; set; } = string.Empty;
    public bool Success { get; set; }
    public bool ShouldContinue { get; set; }
    public bool ShouldDelete { get; set; }
    public bool WasIgnored { get; set; }
    public bool UseCategory { get; set; }
    public List<string> ActionsTaken { get; set; } = new();
    public List<string> Errors { get; set; } = new();
}
