using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using FolderFresh.Models;

namespace FolderFresh.Components;

public sealed partial class RuleCard : UserControl
{
    private Rule? _rule;
    private int _matchCount;

    public event EventHandler<Rule>? EditRequested;
    public event EventHandler<Rule>? DeleteRequested;
    public event EventHandler<Rule>? EnabledChanged;
    public event EventHandler<(Rule Rule, string RuleId)>? DragStarted;

    public RuleCard()
    {
        this.InitializeComponent();
    }

    public Rule? Rule
    {
        get => _rule;
        set
        {
            _rule = value;
            UpdateDisplay();
        }
    }

    public int MatchCount
    {
        get => _matchCount;
        set
        {
            _matchCount = value;
            UpdateMatchCount();
        }
    }

    private void UpdateDisplay()
    {
        if (_rule == null) return;

        RuleNameText.Text = _rule.Name;
        EnabledToggle.IsOn = _rule.IsEnabled;
        ConditionSummaryText.Text = GetConditionSummary(_rule.Conditions);
        ActionSummaryText.Text = GetActionSummary(_rule.Actions);
        UpdateMatchCount();

        // Update visual state based on enabled
        UpdateEnabledState();
    }

    private void UpdateMatchCount()
    {
        if (_matchCount == 0)
        {
            MatchCountText.Text = "No matches";
            MatchCountText.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 102, 102, 102));
        }
        else
        {
            MatchCountText.Text = _matchCount == 1 ? "1 file" : $"{_matchCount} files";
            MatchCountText.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 96, 205, 255));
        }
    }

    private void UpdateEnabledState()
    {
        var opacity = _rule?.IsEnabled == true ? 1.0 : 0.5;
        RuleNameText.Opacity = opacity;
        ConditionSummaryText.Opacity = opacity;
        ActionSummaryText.Opacity = opacity;
    }

    private static string GetConditionSummary(ConditionGroup? group)
    {
        if (group == null || group.Conditions.Count == 0)
            return "No conditions (matches all files)";

        var parts = new List<string>();
        foreach (var condition in group.Conditions.Take(3))
        {
            parts.Add(GetConditionText(condition));
        }

        var connector = group.MatchType switch
        {
            ConditionMatchType.All => " AND ",
            ConditionMatchType.Any => " OR ",
            ConditionMatchType.None => " NOR ",
            _ => " AND "
        };

        var summary = string.Join(connector, parts);

        if (group.Conditions.Count > 3)
        {
            summary += $" (+{group.Conditions.Count - 3} more)";
        }

        return summary;
    }

    private static string GetConditionText(Condition condition)
    {
        var attr = condition.Attribute switch
        {
            ConditionAttribute.Name => "Name",
            ConditionAttribute.Extension => "Extension",
            ConditionAttribute.FullName => "Full name",
            ConditionAttribute.Kind => "Kind",
            ConditionAttribute.Size => "Size",
            ConditionAttribute.DateCreated => "Created",
            ConditionAttribute.DateModified => "Modified",
            ConditionAttribute.DateAccessed => "Accessed",
            _ => condition.Attribute.ToString()
        };

        var op = condition.Operator switch
        {
            ConditionOperator.Is => "is",
            ConditionOperator.IsNot => "is not",
            ConditionOperator.Contains => "contains",
            ConditionOperator.DoesNotContain => "doesn't contain",
            ConditionOperator.StartsWith => "starts with",
            ConditionOperator.EndsWith => "ends with",
            ConditionOperator.MatchesPattern => "matches",
            ConditionOperator.IsGreaterThan => ">",
            ConditionOperator.IsLessThan => "<",
            ConditionOperator.IsInTheLast => "in last",
            ConditionOperator.IsBefore => "before",
            ConditionOperator.IsAfter => "after",
            ConditionOperator.IsBlank => "is blank",
            ConditionOperator.IsNotBlank => "is not blank",
            _ => condition.Operator.ToString()
        };

        if (condition.Operator == ConditionOperator.IsBlank ||
            condition.Operator == ConditionOperator.IsNotBlank)
        {
            return $"{attr} {op}";
        }

        var value = condition.Value;
        if (condition.Operator == ConditionOperator.IsInTheLast && !string.IsNullOrEmpty(condition.SecondaryValue))
        {
            value = $"{condition.Value} {condition.SecondaryValue}";
        }

        return $"{attr} {op} \"{value}\"";
    }

    private static string GetActionSummary(List<RuleAction>? actions)
    {
        if (actions == null || actions.Count == 0)
            return "No actions";

        var summaries = new List<string>();
        foreach (var action in actions.Take(2))
        {
            summaries.Add(GetActionText(action));
        }

        var summary = string.Join(", then ", summaries);

        if (actions.Count > 2)
        {
            summary += $" (+{actions.Count - 2} more)";
        }

        return summary;
    }

    private static string GetActionText(RuleAction action)
    {
        return action.Type switch
        {
            ActionType.MoveToFolder => $"Move to {GetFolderName(action.Value)}",
            ActionType.CopyToFolder => $"Copy to {GetFolderName(action.Value)}",
            ActionType.MoveToCategory => "Move to category folder",
            ActionType.SortIntoSubfolder => $"Sort into {action.Value}",
            ActionType.Rename => $"Rename to {action.Value}",
            ActionType.Delete => "Move to trash",
            ActionType.Ignore => "Ignore",
            ActionType.Continue => "Continue matching",
            _ => action.Type.ToString()
        };
    }

    private static string GetFolderName(string path)
    {
        if (string.IsNullOrEmpty(path)) return "folder";
        try
        {
            return Path.GetFileName(path) ?? path;
        }
        catch
        {
            return path;
        }
    }

    private void CardBorder_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        CardBorder.BorderBrush = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(102, 96, 205, 255)); // 40% opacity
    }

    private void CardBorder_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        CardBorder.BorderBrush = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 51, 51, 51));
    }

    private void ActionButton_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        EditIcon.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 153, 153, 153));
    }

    private void ActionButton_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        EditIcon.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 102, 102, 102));
    }

    private void DeleteButton_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        DeleteIcon.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 239, 68, 68));
    }

    private void DeleteButton_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        DeleteIcon.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 102, 102, 102));
    }

    private void EnabledToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_rule == null) return;

        _rule.IsEnabled = EnabledToggle.IsOn;
        UpdateEnabledState();
        EnabledChanged?.Invoke(this, _rule);
    }

    private void EditButton_Click(object sender, RoutedEventArgs e)
    {
        if (_rule != null)
        {
            EditRequested?.Invoke(this, _rule);
        }
    }

    private void DeleteButton_Click(object sender, RoutedEventArgs e)
    {
        if (_rule != null)
        {
            DeleteRequested?.Invoke(this, _rule);
        }
    }

    private void DragHandle_DragStarting(UIElement sender, DragStartingEventArgs args)
    {
        if (_rule != null)
        {
            args.Data.SetText(_rule.Id);
            args.Data.RequestedOperation = Windows.ApplicationModel.DataTransfer.DataPackageOperation.Move;
            DragStarted?.Invoke(this, (_rule, _rule.Id));
        }
    }
}
