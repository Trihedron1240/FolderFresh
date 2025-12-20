using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using System;
using System.Collections.Generic;
using System.Linq;
using Windows.Storage.Pickers;
using FolderFreshLite.Models;
using FolderFreshLite.Services;

namespace FolderFreshLite.Components;

public sealed partial class ActionRow : UserControl
{
    private RuleAction? _action;
    private bool _isUpdating;
    private int _orderNumber = 1;
    private List<Category>? _categories;

    public event EventHandler<RuleAction>? ActionChanged;
    public event EventHandler<RuleAction>? DeleteRequested;

    public ActionRow()
    {
        this.InitializeComponent();
        ActionTypeComboBox.SelectedIndex = 0;
    }

    public RuleAction? Action
    {
        get => _action;
        set
        {
            _action = value;
            LoadAction();
        }
    }

    public int OrderNumber
    {
        get => _orderNumber;
        set
        {
            _orderNumber = value;
            NumberBadge.Text = value.ToString();
        }
    }

    /// <summary>
    /// Sets the available categories for "Move to category" action
    /// </summary>
    public void SetCategories(List<Category> categories)
    {
        _categories = categories;
        PopulateCategoryDropdown();

        // If action is already set, re-apply the category selection
        if (_action?.Type == ActionType.MoveToCategory && !string.IsNullOrEmpty(_action.Value))
        {
            SelectCategoryInDropdown(_action.Value);
        }
    }

    private void SelectCategoryInDropdown(string categoryId)
    {
        for (int i = 0; i < CategoryComboBox.Items.Count; i++)
        {
            if (CategoryComboBox.Items[i] is ComboBoxItem item &&
                item.Tag?.ToString() == categoryId)
            {
                CategoryComboBox.SelectedIndex = i;
                UpdateCategoryDestinationHelper();
                break;
            }
        }
    }

    private void PopulateCategoryDropdown()
    {
        CategoryComboBox.Items.Clear();

        if (_categories == null) return;

        foreach (var category in _categories.Where(c => c.IsEnabled))
        {
            CategoryComboBox.Items.Add(new ComboBoxItem
            {
                Content = $"{category.Icon} {category.Name}",
                Tag = category.Id
            });
        }
    }

    private void LoadAction()
    {
        if (_action == null) return;

        _isUpdating = true;
        try
        {
            // Set action type
            for (int i = 0; i < ActionTypeComboBox.Items.Count; i++)
            {
                if (ActionTypeComboBox.Items[i] is ComboBoxItem item &&
                    item.Tag?.ToString() == _action.Type.ToString())
                {
                    ActionTypeComboBox.SelectedIndex = i;
                    break;
                }
            }

            UpdateConfigVisibility();
            SetValueFromAction();
        }
        finally
        {
            _isUpdating = false;
        }
    }

    private void SetValueFromAction()
    {
        if (_action == null) return;

        switch (_action.Type)
        {
            case ActionType.MoveToFolder:
            case ActionType.CopyToFolder:
                FolderPathInput.Text = _action.Value;
                break;

            case ActionType.MoveToCategory:
                SelectCategoryInDropdown(_action.Value);
                break;

            case ActionType.SortIntoSubfolder:
            case ActionType.Rename:
                PatternInput.Text = _action.Value;
                break;
        }
    }

    private void ActionTypeComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ActionTypeComboBox.SelectedItem is ComboBoxItem item && item.Tag is string tagStr)
        {
            if (Enum.TryParse<ActionType>(tagStr, out var actionType))
            {
                if (_action != null && !_isUpdating)
                {
                    _action.Type = actionType;
                    _action.Value = "";
                }

                UpdateConfigVisibility();

                if (!_isUpdating)
                {
                    NotifyActionChanged();
                }
            }
        }
    }

    private void UpdateConfigVisibility()
    {
        // Hide all config elements first
        FolderPathGrid.Visibility = Visibility.Collapsed;
        CategoryComboBox.Visibility = Visibility.Collapsed;
        PatternInput.Visibility = Visibility.Collapsed;
        DeleteWarning.Visibility = Visibility.Collapsed;
        IgnoreInfo.Visibility = Visibility.Collapsed;
        ContinueInfo.Visibility = Visibility.Collapsed;
        HelperPanel.Visibility = Visibility.Collapsed;
        CategoryDestinationHelper.Visibility = Visibility.Collapsed;
        PatternTokensHelper.Visibility = Visibility.Collapsed;

        if (ActionTypeComboBox.SelectedItem is not ComboBoxItem item || item.Tag is not string tagStr)
            return;

        if (!Enum.TryParse<ActionType>(tagStr, out var actionType))
            return;

        switch (actionType)
        {
            case ActionType.MoveToFolder:
            case ActionType.CopyToFolder:
                FolderPathGrid.Visibility = Visibility.Visible;
                break;

            case ActionType.MoveToCategory:
                CategoryComboBox.Visibility = Visibility.Visible;
                HelperPanel.Visibility = Visibility.Visible;
                CategoryDestinationHelper.Visibility = Visibility.Visible;
                UpdateCategoryDestinationHelper();
                break;

            case ActionType.SortIntoSubfolder:
                PatternInput.Visibility = Visibility.Visible;
                PatternInput.PlaceholderText = "Invoices/{Year}/{Month}";
                HelperPanel.Visibility = Visibility.Visible;
                PatternTokensHelper.Visibility = Visibility.Visible;
                break;

            case ActionType.Rename:
                PatternInput.Visibility = Visibility.Visible;
                PatternInput.PlaceholderText = "{Name}_{Date}.{Extension}";
                HelperPanel.Visibility = Visibility.Visible;
                PatternTokensHelper.Visibility = Visibility.Visible;
                break;

            case ActionType.Delete:
                DeleteWarning.Visibility = Visibility.Visible;
                break;

            case ActionType.Ignore:
                IgnoreInfo.Visibility = Visibility.Visible;
                break;

            case ActionType.Continue:
                ContinueInfo.Visibility = Visibility.Visible;
                break;
        }
    }

    private void UpdateCategoryDestinationHelper()
    {
        if (CategoryComboBox.SelectedItem is ComboBoxItem item && item.Tag is string categoryId)
        {
            var category = _categories?.FirstOrDefault(c => c.Id == categoryId);
            if (category != null)
            {
                CategoryDestinationHelper.Text = $"Files will go to: {category.Destination}/";
            }
            else
            {
                CategoryDestinationHelper.Text = "";
            }
        }
        else
        {
            CategoryDestinationHelper.Text = "";
        }
    }

    private void FolderPathInput_TextChanged(object sender, TextChangedEventArgs e)
    {
        if (_action != null && !_isUpdating)
        {
            _action.Value = FolderPathInput.Text;
            NotifyActionChanged();
        }
    }

    private async void BrowseFolderButton_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FolderPicker
        {
            SuggestedStartLocation = PickerLocationId.DocumentsLibrary,
            ViewMode = PickerViewMode.List
        };
        picker.FileTypeFilter.Add("*");

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var folder = await picker.PickSingleFolderAsync();

        if (folder != null)
        {
            FolderPathInput.Text = folder.Path;
        }
    }

    private void CategoryComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_action != null && !_isUpdating &&
            CategoryComboBox.SelectedItem is ComboBoxItem item)
        {
            _action.Value = item.Tag?.ToString() ?? "";
            UpdateCategoryDestinationHelper();
            NotifyActionChanged();
        }
    }

    private void PatternInput_TextChanged(object sender, TextChangedEventArgs e)
    {
        if (_action != null && !_isUpdating)
        {
            _action.Value = PatternInput.Text;
            NotifyActionChanged();
        }
    }

    private void NotifyActionChanged()
    {
        if (_action != null)
        {
            ActionChanged?.Invoke(this, _action);
        }
    }

    private void DeleteButton_Click(object sender, RoutedEventArgs e)
    {
        if (_action != null)
        {
            DeleteRequested?.Invoke(this, _action);
        }
    }

    private void UserControl_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        DeleteButton.Opacity = 1;
    }

    private void UserControl_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        DeleteButton.Opacity = 0;
    }

    private void DeleteButton_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        DeleteIcon.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 239, 68, 68));
    }

    private void DeleteButton_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        DeleteIcon.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 102, 102, 102));
    }

    /// <summary>
    /// Creates a new default action
    /// </summary>
    public static RuleAction CreateDefaultAction()
    {
        return new RuleAction
        {
            Type = ActionType.MoveToCategory,
            Value = ""
        };
    }
}
