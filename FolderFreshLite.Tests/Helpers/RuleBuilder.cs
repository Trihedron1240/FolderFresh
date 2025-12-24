using FolderFreshLite.Models;

namespace FolderFreshLite.Tests.Helpers;

/// <summary>
/// Fluent builder for creating test rules
/// </summary>
public class RuleBuilder
{
    private readonly Rule _rule;

    public RuleBuilder(string name = "Test Rule")
    {
        _rule = Rule.Create(name);
    }

    public static RuleBuilder Create(string name = "Test Rule") => new(name);

    public RuleBuilder WithCondition(
        ConditionAttribute attribute,
        ConditionOperator op,
        string value,
        string? secondaryValue = null)
    {
        _rule.Conditions.Conditions.Add(new Condition
        {
            Attribute = attribute,
            Operator = op,
            Value = value,
            SecondaryValue = secondaryValue
        });
        return this;
    }

    public RuleBuilder WithMatchType(ConditionMatchType matchType)
    {
        _rule.Conditions.MatchType = matchType;
        return this;
    }

    public RuleBuilder WithAction(ActionType type, string value = "", Dictionary<string, string>? options = null)
    {
        _rule.Actions.Add(new RuleAction
        {
            Type = type,
            Value = value,
            Options = options ?? new Dictionary<string, string>()
        });
        return this;
    }

    public RuleBuilder WithMoveToFolder(string folder)
        => WithAction(ActionType.MoveToFolder, folder);

    public RuleBuilder WithCopyToFolder(string folder)
        => WithAction(ActionType.CopyToFolder, folder);

    public RuleBuilder WithSortIntoSubfolder(string pattern)
        => WithAction(ActionType.SortIntoSubfolder, pattern);

    public RuleBuilder WithRename(string pattern)
        => WithAction(ActionType.Rename, pattern);

    public RuleBuilder WithDelete()
        => WithAction(ActionType.Delete);

    public RuleBuilder WithIgnore()
        => WithAction(ActionType.Ignore);

    public RuleBuilder WithContinue()
        => WithAction(ActionType.Continue);

    public RuleBuilder Enabled(bool enabled = true)
    {
        _rule.IsEnabled = enabled;
        return this;
    }

    public RuleBuilder WithPriority(int priority)
    {
        _rule.Priority = priority;
        return this;
    }

    public Rule Build() => _rule;
}
