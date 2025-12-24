using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Windows.ApplicationModel.DataTransfer;
using Windows.Storage;
using FolderFresh.Models;
using FolderFresh.Services;

namespace FolderFresh.Components;

public sealed partial class RulesContent : UserControl
{
    private readonly RuleService _ruleService;
    private readonly SettingsService _settingsService;
    private List<Rule> _rules = new();
    private string? _draggedRuleId;
    private int _dropIndex = -1;
    private string? _selectedFolderPath;
    private Dictionary<string, int> _ruleMatchCounts = new();

    private const string InfoBannerDismissedKey = "RulesInfoBannerDismissed";

    public event EventHandler<Rule>? NewRuleRequested;
    public event EventHandler<Rule>? EditRuleRequested;

    public RulesContent()
    {
        this.InitializeComponent();
        _ruleService = new RuleService();
        _settingsService = new SettingsService();
    }

    /// <summary>
    /// Sets the selected folder path for calculating rule match counts
    /// </summary>
    public void SetSelectedFolder(string? folderPath)
    {
        _selectedFolderPath = folderPath;
        _ = CalculateMatchCountsAsync();
    }

    private async Task CalculateMatchCountsAsync()
    {
        _ruleMatchCounts.Clear();

        if (string.IsNullOrEmpty(_selectedFolderPath) || !Directory.Exists(_selectedFolderPath))
        {
            RefreshRulesList();
            return;
        }

        var settings = await _settingsService.LoadSettingsAsync();

        try
        {
            // Get all files in the folder (and subfolders if enabled)
            var files = new List<FileInfo>();

            // Root files
            foreach (var filePath in Directory.GetFiles(_selectedFolderPath))
            {
                var fileInfo = new FileInfo(filePath);
                if (!ShouldSkipFile(fileInfo, settings))
                {
                    files.Add(fileInfo);
                }
            }

            // Subfolder files (if enabled)
            if (settings.IncludeSubfolders)
            {
                foreach (var subDir in Directory.GetDirectories(_selectedFolderPath))
                {
                    var dirInfo = new DirectoryInfo(subDir);
                    if (settings.IgnoreHiddenFiles && (dirInfo.Attributes & System.IO.FileAttributes.Hidden) != 0) continue;
                    if (settings.IgnoreSystemFiles && (dirInfo.Attributes & System.IO.FileAttributes.System) != 0) continue;

                    foreach (var filePath in Directory.GetFiles(subDir))
                    {
                        var fileInfo = new FileInfo(filePath);
                        if (!ShouldSkipFile(fileInfo, settings))
                        {
                            files.Add(fileInfo);
                        }
                    }
                }
            }

            // Calculate matches for each rule
            foreach (var rule in _rules)
            {
                var matchCount = 0;
                if (rule.IsEnabled)
                {
                    foreach (var file in files)
                    {
                        if (_ruleService.EvaluateConditionGroup(rule.Conditions, file))
                        {
                            matchCount++;
                        }
                    }
                }
                _ruleMatchCounts[rule.Id] = matchCount;
            }
        }
        catch
        {
            // Ignore errors calculating matches
        }

        RefreshRulesList();
    }

    private static bool ShouldSkipFile(FileInfo fileInfo, AppSettings settings)
    {
        if (settings.IgnoreHiddenFiles && (fileInfo.Attributes & System.IO.FileAttributes.Hidden) != 0)
            return true;
        if (settings.IgnoreSystemFiles && (fileInfo.Attributes & System.IO.FileAttributes.System) != 0)
            return true;
        return false;
    }

    private async void UserControl_Loaded(object sender, RoutedEventArgs e)
    {
        await LoadRulesAsync();
        await LoadSettingsAsync();
        LoadBannerPreference();
    }

    private async Task LoadSettingsAsync()
    {
        await _settingsService.LoadSettingsAsync();
    }

    private async Task LoadRulesAsync()
    {
        _rules = await _ruleService.LoadRulesAsync();
        RefreshRulesList();
    }

    private void RefreshRulesList()
    {
        RulesListPanel.Children.Clear();

        if (_rules.Count == 0)
        {
            EmptyState.Visibility = Visibility.Visible;
            RulesScrollViewer.Visibility = Visibility.Collapsed;
            return;
        }

        EmptyState.Visibility = Visibility.Collapsed;
        RulesScrollViewer.Visibility = Visibility.Visible;

        foreach (var rule in _rules.OrderBy(r => r.Priority))
        {
            // Get match count from calculated values, default to 0 if not calculated
            var matchCount = _ruleMatchCounts.TryGetValue(rule.Id, out var count) ? count : 0;

            var card = new RuleCard
            {
                Rule = rule,
                MatchCount = matchCount
            };

            card.EditRequested += RuleCard_EditRequested;
            card.DeleteRequested += RuleCard_DeleteRequested;
            card.EnabledChanged += RuleCard_EnabledChanged;
            card.DragStarted += RuleCard_DragStarted;

            RulesListPanel.Children.Add(card);
        }
    }

    private void LoadBannerPreference()
    {
        try
        {
            var localSettings = ApplicationData.Current.LocalSettings;
            if (localSettings.Values.TryGetValue(InfoBannerDismissedKey, out var value) && value is bool dismissed && dismissed)
            {
                InfoBanner.Visibility = Visibility.Collapsed;
            }
        }
        catch
        {
            // Settings not available, show banner
        }
    }

    private void SaveBannerPreference(bool dismissed)
    {
        try
        {
            var localSettings = ApplicationData.Current.LocalSettings;
            localSettings.Values[InfoBannerDismissedKey] = dismissed;
        }
        catch
        {
            // Ignore settings errors
        }
    }

    private void DismissBannerButton_Click(object sender, RoutedEventArgs e)
    {
        InfoBanner.Visibility = Visibility.Collapsed;
        SaveBannerPreference(true);
    }

    private void NewRuleButton_Click(object sender, RoutedEventArgs e)
    {
        var newRule = Rule.Create("New Rule");
        NewRuleRequested?.Invoke(this, newRule);
    }

    private void RuleCard_EditRequested(object? sender, Rule rule)
    {
        EditRuleRequested?.Invoke(this, rule);
    }

    private async void RuleCard_DeleteRequested(object? sender, Rule rule)
    {
        var dialog = new ContentDialog
        {
            Title = "Delete Rule",
            Content = $"Are you sure you want to delete \"{rule.Name}\"?",
            PrimaryButtonText = "Delete",
            CloseButtonText = "Cancel",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = this.XamlRoot
        };

        var result = await dialog.ShowAsync();

        if (result == ContentDialogResult.Primary)
        {
            await _ruleService.DeleteRuleAsync(rule.Id);
            _rules.Remove(rule);
            RefreshRulesList();
        }
    }

    private async void RuleCard_EnabledChanged(object? sender, Rule rule)
    {
        await _ruleService.UpdateRuleAsync(rule);
    }

    private void RuleCard_DragStarted(object? sender, (Rule Rule, string RuleId) args)
    {
        _draggedRuleId = args.RuleId;
    }

    private void RulesListPanel_DragOver(object sender, DragEventArgs e)
    {
        e.AcceptedOperation = DataPackageOperation.Move;

        // Calculate drop position
        var position = e.GetPosition(RulesListPanel);
        var newDropIndex = GetDropIndex(position.Y);

        if (newDropIndex != _dropIndex)
        {
            _dropIndex = newDropIndex;
            UpdateDropIndicator(position.Y);
        }
    }

    private int GetDropIndex(double y)
    {
        double cumulativeHeight = 0;
        for (int i = 0; i < RulesListPanel.Children.Count; i++)
        {
            if (RulesListPanel.Children[i] is FrameworkElement element)
            {
                cumulativeHeight += element.ActualHeight + 8; // 8 is spacing
                if (y < cumulativeHeight - (element.ActualHeight / 2))
                {
                    return i;
                }
            }
        }
        return RulesListPanel.Children.Count;
    }

    private void UpdateDropIndicator(double y)
    {
        if (_dropIndex < 0 || _dropIndex > RulesListPanel.Children.Count)
        {
            DropIndicator.Visibility = Visibility.Collapsed;
            return;
        }

        DropIndicator.Visibility = Visibility.Visible;

        // Calculate Y position for the indicator
        double indicatorY = 0;
        for (int i = 0; i < _dropIndex && i < RulesListPanel.Children.Count; i++)
        {
            if (RulesListPanel.Children[i] is FrameworkElement element)
            {
                indicatorY += element.ActualHeight + 8;
            }
        }

        // Position the indicator (this is approximate - proper positioning would need transforms)
        DropIndicator.Margin = new Thickness(24, indicatorY, 24, 0);
        DropIndicator.VerticalAlignment = VerticalAlignment.Top;
    }

    private async void RulesListPanel_Drop(object sender, DragEventArgs e)
    {
        DropIndicator.Visibility = Visibility.Collapsed;

        if (string.IsNullOrEmpty(_draggedRuleId) || _dropIndex < 0)
            return;

        // Find the dragged rule
        var draggedRule = _rules.FirstOrDefault(r => r.Id == _draggedRuleId);
        if (draggedRule == null) return;

        var currentIndex = _rules.IndexOf(draggedRule);
        if (currentIndex == _dropIndex || currentIndex == _dropIndex - 1)
        {
            // No change needed
            _draggedRuleId = null;
            _dropIndex = -1;
            return;
        }

        // Reorder the list
        _rules.Remove(draggedRule);
        var insertIndex = _dropIndex > currentIndex ? _dropIndex - 1 : _dropIndex;
        _rules.Insert(Math.Max(0, Math.Min(insertIndex, _rules.Count)), draggedRule);

        // Update priorities
        var ruleIds = _rules.Select(r => r.Id).ToList();
        await _ruleService.ReorderRulesAsync(ruleIds);

        // Reload to get updated priorities
        _rules = await _ruleService.LoadRulesAsync();
        RefreshRulesList();

        _draggedRuleId = null;
        _dropIndex = -1;
    }

    /// <summary>
    /// Public method to add a new rule (called from parent after rule editor saves)
    /// </summary>
    public async Task AddRuleAsync(Rule rule)
    {
        await _ruleService.AddRuleAsync(rule);
        _rules = await _ruleService.LoadRulesAsync();
        RefreshRulesList();
    }

    /// <summary>
    /// Public method to update a rule (called from parent after rule editor saves)
    /// </summary>
    public async Task UpdateRuleAsync(Rule rule)
    {
        await _ruleService.UpdateRuleAsync(rule);
        _rules = await _ruleService.LoadRulesAsync();
        RefreshRulesList();
    }

    /// <summary>
    /// Refresh the rules list from storage
    /// </summary>
    public async Task RefreshAsync()
    {
        await LoadRulesAsync();
    }
}
