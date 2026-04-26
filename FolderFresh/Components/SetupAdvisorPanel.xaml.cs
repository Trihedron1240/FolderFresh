using System.Collections.Specialized;
using System.ComponentModel;
using FolderFresh.Models;
using FolderFresh.Services;
using FolderFresh.ViewModels;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.Storage.Pickers;
using Windows.UI;

namespace FolderFresh.Components;

public sealed partial class SetupAdvisorPanel : UserControl
{
    private readonly SmartSetupViewModel _viewModel = new();
    private bool _isInitialized;
    private bool _isRefreshing;

    public event EventHandler? CloseRequested;
    public event EventHandler? SuggestionsApplied;

    public SetupAdvisorPanel()
    {
        this.InitializeComponent();
        ApplyLocalization();
        LocalizationService.Instance.LanguageChanged += (_, _) => DispatcherQueue.TryEnqueue(ApplyLocalization);
    }

    public void Initialize(CategoryService categoryService, RuleService ruleService, SettingsService settingsService)
    {
        if (_isInitialized)
        {
            return;
        }

        _viewModel.Initialize(categoryService, ruleService, settingsService);
        _viewModel.PropertyChanged += ViewModel_PropertyChanged;
        _viewModel.CategorySuggestions.CollectionChanged += Suggestions_CollectionChanged;
        _viewModel.RuleSuggestions.CollectionChanged += Suggestions_CollectionChanged;
        _viewModel.SuggestionsApplied += ViewModel_SuggestionsApplied;
        _isInitialized = true;

        RefreshView();
    }

    public void SetSelectedFolder(string? folderPath)
    {
        _viewModel.SetSelectedFolder(folderPath);
        RefreshView();
    }

    private void ApplyLocalization()
    {
        HeaderTitle.Text = Loc.Get("SmartSetup_Title");
        HeaderSubtitle.Text = Loc.Get("SmartSetup_Subtitle");
        FolderLabel.Text = Loc.Get("SmartSetup_Folder");
        BrowseButtonText.Text = Loc.Get("SmartSetup_Browse");
        IncludeSubfoldersToggle.Header = Loc.Get("SmartSetup_IncludeSubfolders");
        MaxFilesLabel.Text = Loc.Get("SmartSetup_MaxFiles");
        AnalyzeButtonText.Text = Loc.Get("SmartSetup_Analyze");
        StatusLabel.Text = Loc.Get("SmartSetup_Status");
        CategoriesLabel.Text = Loc.Get("SmartSetup_Categories");
        RulesLabel.Text = Loc.Get("SmartSetup_Rules");
        NoCategoriesText.Text = Loc.Get("SmartSetup_NoCategories");
        NoRulesText.Text = Loc.Get("SmartSetup_NoRules");
        CloseButtonText.Text = Loc.Get("Close");
        ApplyButtonText.Text = Loc.Get("SmartSetup_Apply");
        RefreshCards();
    }

    private async void BrowseButton_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FolderPicker
        {
            SuggestedStartLocation = PickerLocationId.Desktop,
            ViewMode = PickerViewMode.List
        };
        picker.FileTypeFilter.Add("*");

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var folder = await picker.PickSingleFolderAsync();
        if (folder != null)
        {
            _viewModel.SetSelectedFolder(folder.Path);
            RefreshView();
        }
    }

    private void IncludeSubfoldersToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isRefreshing)
        {
            return;
        }

        _viewModel.IncludeSubfolders = IncludeSubfoldersToggle.IsOn;
        RefreshView();
    }

    private void MaxFilesTextBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        if (_isRefreshing)
        {
            return;
        }

        if (int.TryParse(MaxFilesTextBox.Text, out var value))
        {
            _viewModel.MaxFiles = value;
            RefreshView();
        }
    }

    private async void AnalyzeButton_Click(object sender, RoutedEventArgs e)
    {
        await _viewModel.AnalyzeAsync();
        RefreshView();
    }

    private async void ApplyButton_Click(object sender, RoutedEventArgs e)
    {
        await _viewModel.ApplyAsync();
        RefreshView();
    }

    private void CloseButton_Click(object sender, RoutedEventArgs e)
    {
        CloseRequested?.Invoke(this, EventArgs.Empty);
    }

    private void ViewModel_PropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        RefreshView();
    }

    private void ViewModel_SuggestionsApplied(object? sender, EventArgs e)
    {
        SuggestionsApplied?.Invoke(this, EventArgs.Empty);
    }

    private void Suggestions_CollectionChanged(object? sender, NotifyCollectionChangedEventArgs e)
    {
        if (e.OldItems != null)
        {
            foreach (var item in e.OldItems.OfType<INotifyPropertyChanged>())
            {
                item.PropertyChanged -= SuggestionItem_PropertyChanged;
            }
        }

        if (e.NewItems != null)
        {
            foreach (var item in e.NewItems.OfType<INotifyPropertyChanged>())
            {
                item.PropertyChanged += SuggestionItem_PropertyChanged;
            }
        }

        RefreshView();
    }

    private void SuggestionItem_PropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        RefreshView();
    }

    private void RefreshView()
    {
        _isRefreshing = true;

        FolderPathText.Text = string.IsNullOrWhiteSpace(_viewModel.SelectedFolderPath)
            ? Loc.Get("SelectFolder")
            : _viewModel.SelectedFolderPath;
        FolderPathText.Foreground = string.IsNullOrWhiteSpace(_viewModel.SelectedFolderPath)
            ? new SolidColorBrush(Color.FromArgb(255, 153, 153, 153))
            : new SolidColorBrush(Color.FromArgb(255, 255, 255, 255));

        IncludeSubfoldersToggle.IsOn = _viewModel.IncludeSubfolders;
        MaxFilesTextBox.Text = _viewModel.MaxFiles.ToString();
        StatusText.Text = _viewModel.StatusMessage;

        AnalyzeButton.IsEnabled = _viewModel.CanAnalyze;
        ApplyButton.IsEnabled = _viewModel.CanApply;
        BrowseButton.IsEnabled = !_viewModel.IsBusy;
        NoCategoriesText.Visibility = _viewModel.CategorySuggestions.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
        NoRulesText.Visibility = _viewModel.RuleSuggestions.Count == 0 ? Visibility.Visible : Visibility.Collapsed;

        AnalyzeButtonText.Text = _viewModel.IsBusy ? $"{Loc.Get("SmartSetup_Analyze")}..." : Loc.Get("SmartSetup_Analyze");
        ApplyButtonText.Text = _viewModel.IsBusy ? $"{Loc.Get("SmartSetup_Apply")}..." : Loc.Get("SmartSetup_Apply");

        RefreshCards();
        _isRefreshing = false;
    }

    private void RefreshCards()
    {
        CategoriesPanel.Children.Clear();
        foreach (var category in _viewModel.CategorySuggestions)
        {
            CategoriesPanel.Children.Add(BuildCategoryCard(category));
        }

        RulesPanel.Children.Clear();
        foreach (var rule in _viewModel.RuleSuggestions)
        {
            RulesPanel.Children.Add(BuildRuleCard(rule));
        }
    }

    private FrameworkElement BuildCategoryCard(SmartSetupCategoryItem category)
    {
        var container = new Border
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 45, 45, 45)),
            BorderBrush = new SolidColorBrush(Color.FromArgb(255, 58, 58, 58)),
            BorderThickness = new Thickness(1),
            CornerRadius = new CornerRadius(10),
            Padding = new Thickness(16)
        };

        var content = new StackPanel { Spacing = 12 };
        content.Children.Add(BuildToggleHeader(category.IsSelected, value => category.IsSelected = value, category.Reason, out var nameBox));
        nameBox.Text = category.Name;
        nameBox.TextChanged += (_, _) => category.Name = nameBox.Text;

        content.Children.Add(CreateLabelValueRow(Loc.Get("SmartSetup_Destination"), category.Destination));
        content.Children.Add(CreateLabelValueRow(Loc.Get("SmartSetup_Extensions"), category.ExtensionsDisplay));
        content.Children.Add(CreateLabelValueRow(Loc.Get("SmartSetup_SampleFiles"), string.Join(", ", category.SampleFiles)));

        container.Child = content;
        return container;
    }

    private FrameworkElement BuildRuleCard(SmartSetupRuleItem rule)
    {
        var container = new Border
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 45, 45, 45)),
            BorderBrush = new SolidColorBrush(Color.FromArgb(255, 58, 58, 58)),
            BorderThickness = new Thickness(1),
            CornerRadius = new CornerRadius(10),
            Padding = new Thickness(16)
        };

        var content = new StackPanel { Spacing = 12 };
        content.Children.Add(BuildToggleHeader(rule.IsSelected, value => rule.IsSelected = value, rule.Reason, out var nameBox));
        nameBox.Text = rule.Name;
        nameBox.TextChanged += (_, _) => rule.Name = nameBox.Text;

        var tokenBox = new TextBox
        {
            Text = rule.MatchToken,
            Background = new SolidColorBrush(Color.FromArgb(255, 37, 37, 37)),
            BorderBrush = new SolidColorBrush(Color.FromArgb(255, 64, 64, 64)),
            CornerRadius = new CornerRadius(8)
        };
        tokenBox.TextChanged += (_, _) => rule.MatchToken = tokenBox.Text;

        content.Children.Add(CreateLabelHostRow(Loc.Get("SmartSetup_MatchToken"), tokenBox));
        content.Children.Add(CreateLabelValueRow(Loc.Get("SmartSetup_TargetCategory"), rule.TargetCategoryName));
        content.Children.Add(CreateLabelValueRow(Loc.Get("SmartSetup_SampleFiles"), string.Join(", ", rule.SampleFiles)));

        container.Child = content;
        return container;
    }

    private static FrameworkElement BuildToggleHeader(bool isOn, Action<bool> setValue, string description, out TextBox nameBox)
    {
        var grid = new Grid();
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

        var toggle = new ToggleSwitch
        {
            IsOn = isOn,
            OnContent = string.Empty,
            OffContent = string.Empty,
            MinWidth = 40,
            VerticalAlignment = VerticalAlignment.Top
        };
        toggle.Toggled += (_, _) => setValue(toggle.IsOn);
        grid.Children.Add(toggle);

        var panel = new StackPanel { Spacing = 8 };
        Grid.SetColumn(panel, 1);
        panel.Children.Add(new TextBlock
        {
            Text = description,
            FontSize = 13,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 181, 186, 193)),
            TextWrapping = TextWrapping.Wrap
        });

        nameBox = new TextBox
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 37, 37, 37)),
            BorderBrush = new SolidColorBrush(Color.FromArgb(255, 64, 64, 64)),
            CornerRadius = new CornerRadius(8)
        };
        panel.Children.Add(nameBox);

        grid.Children.Add(panel);
        return grid;
    }

    private static FrameworkElement CreateLabelValueRow(string label, string value)
    {
        return CreateLabelHostRow(label, new TextBlock
        {
            Text = string.IsNullOrWhiteSpace(value) ? "-" : value,
            FontSize = 13,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 255, 255, 255)),
            TextWrapping = TextWrapping.Wrap
        });
    }

    private static FrameworkElement CreateLabelHostRow(string label, FrameworkElement content)
    {
        var panel = new StackPanel { Spacing = 4 };
        panel.Children.Add(new TextBlock
        {
            Text = label,
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 153, 153, 153))
        });
        panel.Children.Add(content);
        return panel;
    }
}
