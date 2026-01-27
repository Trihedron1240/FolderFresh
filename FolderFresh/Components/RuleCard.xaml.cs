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
using FolderFresh.Services;

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
        LocalizationService.Instance.LanguageChanged += (s, e) => DispatcherQueue.TryEnqueue(UpdateDisplay);
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
            MatchCountText.Text = Loc.Get("RuleCard_NoMatches");
            MatchCountText.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 102, 102, 102));
        }
        else
        {
            MatchCountText.Text = _matchCount == 1 ? Loc.Get("RuleCard_OneFile") : Loc.Get("RuleCard_Files", _matchCount);
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
            return Loc.Get("RuleCard_NoConditions");

        var parts = new List<string>();
        foreach (var condition in group.Conditions.Take(3))
        {
            parts.Add(GetConditionText(condition));
        }

        var connector = group.MatchType switch
        {
            ConditionMatchType.All => $" {Loc.Get("RuleCard_And")} ",
            ConditionMatchType.Any => $" {Loc.Get("RuleCard_Or")} ",
            ConditionMatchType.None => $" {Loc.Get("RuleCard_Nor")} ",
            _ => $" {Loc.Get("RuleCard_And")} "
        };

        var summary = string.Join(connector, parts);

        if (group.Conditions.Count > 3)
        {
            summary += " " + Loc.Get("RuleCard_MoreConditions", group.Conditions.Count - 3);
        }

        return summary;
    }

    private static string GetConditionText(Condition condition)
    {
        var attr = condition.Attribute switch
        {
            ConditionAttribute.Name => Loc.Get("RuleCard_Attr_Name"),
            ConditionAttribute.Extension => Loc.Get("RuleCard_Attr_Extension"),
            ConditionAttribute.FullName => Loc.Get("RuleCard_Attr_FullName"),
            ConditionAttribute.Kind => Loc.Get("RuleCard_Attr_Kind"),
            ConditionAttribute.Size => Loc.Get("RuleCard_Attr_Size"),
            ConditionAttribute.DateCreated => Loc.Get("RuleCard_Attr_Created"),
            ConditionAttribute.DateModified => Loc.Get("RuleCard_Attr_Modified"),
            ConditionAttribute.DateAccessed => Loc.Get("RuleCard_Attr_Accessed"),
            ConditionAttribute.Folder => Loc.Get("RuleCard_Attr_Folder"),
            ConditionAttribute.FolderPath => Loc.Get("RuleCard_Attr_FolderPath"),
            _ => condition.Attribute.ToString()
        };

        var op = condition.Operator switch
        {
            ConditionOperator.Is => Loc.Get("RuleCard_Op_Is"),
            ConditionOperator.IsNot => Loc.Get("RuleCard_Op_IsNot"),
            ConditionOperator.Contains => Loc.Get("RuleCard_Op_Contains"),
            ConditionOperator.DoesNotContain => Loc.Get("RuleCard_Op_DoesNotContain"),
            ConditionOperator.StartsWith => Loc.Get("RuleCard_Op_StartsWith"),
            ConditionOperator.EndsWith => Loc.Get("RuleCard_Op_EndsWith"),
            ConditionOperator.MatchesPattern => Loc.Get("RuleCard_Op_Matches"),
            ConditionOperator.IsGreaterThan => Loc.Get("RuleCard_Op_GreaterThan"),
            ConditionOperator.IsLessThan => Loc.Get("RuleCard_Op_LessThan"),
            ConditionOperator.IsInTheLast => Loc.Get("RuleCard_Op_InLast"),
            ConditionOperator.IsBefore => Loc.Get("RuleCard_Op_Before"),
            ConditionOperator.IsAfter => Loc.Get("RuleCard_Op_After"),
            ConditionOperator.IsBlank => Loc.Get("RuleCard_Op_IsBlank"),
            ConditionOperator.IsNotBlank => Loc.Get("RuleCard_Op_IsNotBlank"),
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
            return Loc.Get("RuleCard_NoActions");

        var summaries = new List<string>();
        foreach (var action in actions.Take(2))
        {
            summaries.Add(GetActionText(action));
        }

        var summary = string.Join(Loc.Get("RuleCard_ThenConnector"), summaries);

        if (actions.Count > 2)
        {
            summary += " " + Loc.Get("RuleCard_MoreActions", actions.Count - 2);
        }

        return summary;
    }

    private static string GetActionText(RuleAction action)
    {
        return action.Type switch
        {
            ActionType.MoveToFolder => Loc.Get("RuleCard_Action_MoveTo", GetFolderName(action.Value)),
            ActionType.CopyToFolder => Loc.Get("RuleCard_Action_CopyTo", GetFolderName(action.Value)),
            ActionType.MoveToCategory => Loc.Get("RuleCard_Action_MoveToCategory"),
            ActionType.SortIntoSubfolder => Loc.Get("RuleCard_Action_SortInto", action.Value),
            ActionType.Rename => Loc.Get("RuleCard_Action_RenameTo", action.Value),
            ActionType.Delete => Loc.Get("RuleCard_Action_Trash"),
            ActionType.Ignore => Loc.Get("RuleCard_Action_Ignore"),
            ActionType.Continue => Loc.Get("RuleCard_Action_Continue"),
            _ => action.Type.ToString()
        };
    }

    private static string GetFolderName(string path)
    {
        if (string.IsNullOrEmpty(path)) return Loc.Get("RuleCard_Action_Folder");
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
