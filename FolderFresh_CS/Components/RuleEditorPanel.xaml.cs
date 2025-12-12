using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using FolderFreshLite.Models;
using FolderFreshLite.Services;

namespace FolderFreshLite.Components;

public sealed partial class RuleEditorPanel : UserControl
{
    private Rule? _rule;
    private bool _isNewRule;
    private bool _isUpdating;
    private readonly CategoryService _categoryService;
    private List<Category> _categories = new();

    public event EventHandler<Rule>? SaveRequested;
    public event EventHandler? CloseRequested;

    public RuleEditorPanel()
    {
        this.InitializeComponent();
        _categoryService = new CategoryService();
    }

    /// <summary>
    /// Sets the rule to edit, or null for a new rule
    /// </summary>
    public async void SetRule(Rule? rule)
    {
        _isUpdating = true;

        // Load categories for action dropdowns
        await LoadCategoriesAsync();

        if (rule == null)
        {
            _rule = Rule.Create("New Rule");
            _isNewRule = true;
            HeaderTitle.Text = "New Rule";
        }
        else
        {
            _rule = rule;
            _isNewRule = false;
            HeaderTitle.Text = "Edit Rule";
        }

        LoadRuleData();
        UpdateSaveButtonState();
        _isUpdating = false;
    }

    private async Task LoadCategoriesAsync()
    {
        _categories = await _categoryService.LoadCategoriesAsync();
    }

    private void LoadRuleData()
    {
        if (_rule == null) return;

        // Load basics
        RuleNameTextBox.Text = _rule.Name;
        EnabledToggle.IsOn = _rule.IsEnabled;

        // Load match type
        switch (_rule.Conditions.MatchType)
        {
            case ConditionMatchType.All:
                MatchAllRadio.IsChecked = true;
                UpdatePillStyles(MatchAllRadio);
                break;
            case ConditionMatchType.Any:
                MatchAnyRadio.IsChecked = true;
                UpdatePillStyles(MatchAnyRadio);
                break;
            case ConditionMatchType.None:
                MatchNoneRadio.IsChecked = true;
                UpdatePillStyles(MatchNoneRadio);
                break;
        }

        // Load conditions
        LoadConditions();

        // Load actions
        LoadActions();
    }

    private void LoadConditions()
    {
        ConditionsPanel.Children.Clear();

        if (_rule?.Conditions?.Conditions != null)
        {
            foreach (var condition in _rule.Conditions.Conditions)
            {
                AddConditionRow(condition);
            }
        }

        // Add a default condition if empty
        if (ConditionsPanel.Children.Count == 0)
        {
            AddConditionButton_Click(null, null!);
        }
    }

    private void AddConditionRow(Condition condition)
    {
        var row = new ConditionRow
        {
            Condition = condition
        };

        row.ConditionChanged += ConditionRow_ConditionChanged;
        row.DeleteRequested += ConditionRow_DeleteRequested;

        ConditionsPanel.Children.Add(row);
    }

    private void ConditionRow_ConditionChanged(object? sender, Condition condition)
    {
        UpdateSaveButtonState();
    }

    private void ConditionRow_DeleteRequested(object? sender, Condition condition)
    {
        if (_rule?.Conditions?.Conditions == null) return;

        _rule.Conditions.Conditions.Remove(condition);

        // Remove the row from UI
        if (sender is ConditionRow row)
        {
            ConditionsPanel.Children.Remove(row);
        }

        // Ensure at least one condition row exists
        if (ConditionsPanel.Children.Count == 0)
        {
            AddConditionButton_Click(null, null!);
        }

        UpdateSaveButtonState();
    }

    private void LoadActions()
    {
        ActionsPanel.Children.Clear();

        if (_rule?.Actions != null && _rule.Actions.Count > 0)
        {
            for (int i = 0; i < _rule.Actions.Count; i++)
            {
                AddActionRow(_rule.Actions[i], i + 1);
            }
        }
        else
        {
            // Add a default action if empty
            AddActionButton_Click(null!, null!);
        }
    }

    private void AddActionRow(RuleAction action, int orderNumber)
    {
        var row = new ActionRow
        {
            Action = action,
            OrderNumber = orderNumber
        };

        row.SetCategories(_categories);
        row.ActionChanged += ActionRow_ActionChanged;
        row.DeleteRequested += ActionRow_DeleteRequested;

        ActionsPanel.Children.Add(row);
    }

    private void ActionRow_ActionChanged(object? sender, RuleAction action)
    {
        UpdateSaveButtonState();
    }

    private void ActionRow_DeleteRequested(object? sender, RuleAction action)
    {
        if (_rule?.Actions == null) return;

        _rule.Actions.Remove(action);

        // Remove the row from UI
        if (sender is ActionRow row)
        {
            ActionsPanel.Children.Remove(row);
        }

        // Update order numbers
        UpdateActionOrderNumbers();

        // Ensure at least one action row exists
        if (ActionsPanel.Children.Count == 0)
        {
            AddActionButton_Click(null!, null!);
        }

        UpdateSaveButtonState();
    }

    private void UpdateActionOrderNumbers()
    {
        int order = 1;
        foreach (var child in ActionsPanel.Children)
        {
            if (child is ActionRow row)
            {
                row.OrderNumber = order++;
            }
        }
    }

    private void RuleNameTextBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        if (_rule != null && !_isUpdating)
        {
            _rule.Name = RuleNameTextBox.Text;
            UpdateSaveButtonState();
        }
    }

    private void EnabledToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_rule != null && !_isUpdating)
        {
            _rule.IsEnabled = EnabledToggle.IsOn;
        }
    }

    private void MatchTypeRadio_Checked(object sender, RoutedEventArgs e)
    {
        if (_rule == null || _isUpdating) return;

        if (MatchAllRadio.IsChecked == true)
        {
            _rule.Conditions.MatchType = ConditionMatchType.All;
            UpdatePillStyles(MatchAllRadio);
        }
        else if (MatchAnyRadio.IsChecked == true)
        {
            _rule.Conditions.MatchType = ConditionMatchType.Any;
            UpdatePillStyles(MatchAnyRadio);
        }
        else if (MatchNoneRadio.IsChecked == true)
        {
            _rule.Conditions.MatchType = ConditionMatchType.None;
            UpdatePillStyles(MatchNoneRadio);
        }
    }

    private void UpdatePillStyles(RadioButton selectedPill)
    {
        // Reset all pills
        var pills = new[] { MatchAllRadio, MatchAnyRadio, MatchNoneRadio };
        foreach (var pill in pills)
        {
            if (pill == selectedPill)
            {
                pill.Background = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 96, 205, 255));
                pill.Foreground = new SolidColorBrush(Microsoft.UI.Colors.White);
            }
            else
            {
                pill.Background = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 51, 51, 51));
                pill.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 153, 153, 153));
            }
        }
    }

    private void AddConditionButton_Click(object? sender, RoutedEventArgs e)
    {
        if (_rule == null) return;

        var newCondition = ConditionRow.CreateDefaultCondition();
        _rule.Conditions.Conditions.Add(newCondition);
        AddConditionRow(newCondition);
        UpdateSaveButtonState();
    }

    private void AddActionButton_Click(object sender, RoutedEventArgs e)
    {
        if (_rule == null) return;

        var newAction = ActionRow.CreateDefaultAction();
        _rule.Actions.Add(newAction);
        AddActionRow(newAction, _rule.Actions.Count);
        UpdateSaveButtonState();
    }

    private void UpdateSaveButtonState()
    {
        // Enable save if: name is not empty AND at least 1 condition AND at least 1 action
        var hasName = !string.IsNullOrWhiteSpace(RuleNameTextBox.Text);
        var hasConditions = _rule?.Conditions?.Conditions?.Count > 0;
        var hasActions = _rule?.Actions?.Count > 0;

        SaveButton.IsEnabled = hasName && hasConditions == true && hasActions == true;

        // Update button opacity for visual feedback
        SaveButton.Opacity = SaveButton.IsEnabled ? 1.0 : 0.5;
    }

    private void CloseButton_Click(object sender, RoutedEventArgs e)
    {
        CloseRequested?.Invoke(this, EventArgs.Empty);
    }

    private void CancelButton_Click(object sender, RoutedEventArgs e)
    {
        CloseRequested?.Invoke(this, EventArgs.Empty);
    }

    private void SaveButton_Click(object sender, RoutedEventArgs e)
    {
        if (_rule == null) return;

        // Validate
        if (string.IsNullOrWhiteSpace(_rule.Name))
        {
            _rule.Name = "Untitled Rule";
        }

        // Update modified timestamp
        _rule.ModifiedAt = DateTime.Now;

        SaveRequested?.Invoke(this, _rule);
    }

    /// <summary>
    /// Gets whether this is a new rule or editing existing
    /// </summary>
    public bool IsNewRule => _isNewRule;

    /// <summary>
    /// Gets the current rule being edited
    /// </summary>
    public Rule? CurrentRule => _rule;
}
