using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using System;
using System.Threading.Tasks;
using FolderFresh.Models;
using FolderFresh.Services;

namespace FolderFresh.Components;

public sealed partial class SettingsContent : UserControl
{
    private readonly SettingsService _settingsService;
    private AppSettings? _settings;
    private bool _isLoading;
    private string? _initialLanguage;

    public SettingsContent()
    {
        this.InitializeComponent();
        _settingsService = new SettingsService();
        ApplyLocalization();
        _ = LoadSettingsAsync();

        // Subscribe to language changes for immediate UI updates
        LocalizationService.Instance.LanguageChanged += (s, e) => DispatcherQueue.TryEnqueue(ApplyLocalization);
    }

    private void ApplyLocalization()
    {
        // Header
        SettingsTitle.Text = Loc.Get("Settings_Title");

        // Language section
        LanguageLabel.Text = Loc.Get("Settings_Language");
        LanguageDesc.Text = Loc.Get("Settings_LanguageDesc");
        RestartHint.Text = Loc.Get("Settings_LanguageRestart");

        // Organization Mode section
        OrganizationModeLabel.Text = Loc.Get("Settings_OrganizationMode");
        OrganizationModeDesc.Text = Loc.Get("Settings_OrganizationModeDesc");
        RulesFirstText.Text = Loc.Get("Settings_RulesFirst");
        RulesFirstDesc.Text = Loc.Get("Settings_RulesFirstDesc");
        CategoriesOnlyText.Text = Loc.Get("Settings_CategoriesOnly");
        CategoriesOnlyDesc.Text = Loc.Get("Settings_CategoriesOnlyDesc");
        RulesOnlyText.Text = Loc.Get("Settings_RulesOnly");
        RulesOnlyDesc.Text = Loc.Get("Settings_RulesOnlyDesc");

        // Notifications section
        NotificationsLabel.Text = Loc.Get("Settings_Notifications");
        ShowNotificationsText.Text = Loc.Get("Settings_ShowNotifications");
        ShowNotificationsDesc.Text = Loc.Get("Settings_ShowNotificationsDesc");

        // File Scanning section
        FileScanningLabel.Text = Loc.Get("Settings_FileScanning");
        IncludeSubfoldersText.Text = Loc.Get("Settings_IncludeSubfolders");
        IncludeSubfoldersDesc.Text = Loc.Get("Settings_IncludeSubfoldersDesc");
        IgnoreHiddenText.Text = Loc.Get("Settings_IgnoreHidden");
        IgnoreHiddenDesc.Text = Loc.Get("Settings_IgnoreHiddenDesc");
        IgnoreSystemText.Text = Loc.Get("Settings_IgnoreSystem");
        IgnoreSystemDesc.Text = Loc.Get("Settings_IgnoreSystemDesc");

        // System Tray section
        SystemTrayLabel.Text = Loc.Get("Settings_SystemTray");
        MinimizeToTrayText.Text = Loc.Get("Settings_MinimizeToTray");
        MinimizeToTrayDesc.Text = Loc.Get("Settings_MinimizeToTrayDesc");
        CloseToTrayText.Text = Loc.Get("Settings_CloseToTray");
        CloseToTrayDesc.Text = Loc.Get("Settings_CloseToTrayDesc");
        StartMinimizedText.Text = Loc.Get("Settings_StartMinimized");
        StartMinimizedDesc.Text = Loc.Get("Settings_StartMinimizedDesc");
        RunOnStartupText.Text = Loc.Get("Settings_RunOnStartup");
        RunOnStartupDesc.Text = Loc.Get("Settings_RunOnStartupDesc");

        // Safety section
        SafetyLabel.Text = Loc.Get("Settings_Safety");
        RecycleBinText.Text = Loc.Get("Settings_RecycleBin");
        RecycleBinDesc.Text = Loc.Get("Settings_RecycleBinDesc");
        ConfirmText.Text = Loc.Get("Settings_Confirm");
        ConfirmDesc.Text = Loc.Get("Settings_ConfirmDesc");

        // About section
        AboutLabel.Text = Loc.Get("Settings_About");
        VersionText.Text = Loc.Get("Settings_Version");
        DescriptionText.Text = Loc.Get("Settings_Description");
    }

    private async Task LoadSettingsAsync()
    {
        _isLoading = true;

        try
        {
            // Guard against null service (shouldn't happen, but defensive)
            if (_settingsService == null)
            {
                System.Diagnostics.Debug.WriteLine("[SettingsContent] LoadSettingsAsync: _settingsService is null");
                return;
            }

            _settings = await _settingsService.LoadSettingsAsync();

            // Set organization mode
            if (!_settings.UseRulesFirst)
            {
                CategoriesOnlyRadio.IsChecked = true;
            }
            else if (!_settings.FallbackToCategories)
            {
                RulesOnlyRadio.IsChecked = true;
            }
            else
            {
                RulesFirstRadio.IsChecked = true;
            }

            // Set toggles
            NotificationsToggle.IsOn = _settings.ShowNotifications;
            RecycleBinToggle.IsOn = _settings.MoveToTrashInsteadOfDelete;
            ConfirmToggle.IsOn = _settings.ConfirmBeforeOrganize;
            IncludeSubfoldersToggle.IsOn = _settings.IncludeSubfolders;
            IgnoreHiddenToggle.IsOn = _settings.IgnoreHiddenFiles;
            IgnoreSystemToggle.IsOn = _settings.IgnoreSystemFiles;

            // Set tray toggles
            MinimizeToTrayToggle.IsOn = _settings.MinimizeToTray;
            CloseToTrayToggle.IsOn = _settings.CloseToTray;
            StartMinimizedToggle.IsOn = _settings.StartMinimized;

            // Sync RunOnStartup with actual registry state (in case they got out of sync)
            var actualRegistryState = StartupManager.IsRunOnStartupEnabled();
            if (_settings.RunOnStartup != actualRegistryState)
            {
                // Registry state takes precedence - update settings to match
                _settings.RunOnStartup = actualRegistryState;
                _ = SaveSettingsAsync();
            }
            RunOnStartupToggle.IsOn = _settings.RunOnStartup;

            // Set language combo box
            _initialLanguage = _settings.Language;
            SetLanguageComboBox(_settings.Language);
        }
        finally
        {
            _isLoading = false;
        }
    }

    private void SetLanguageComboBox(string languageCode)
    {
        foreach (ComboBoxItem item in LanguageComboBox.Items)
        {
            if (item.Tag?.ToString() == languageCode)
            {
                LanguageComboBox.SelectedItem = item;
                break;
            }
        }
    }

    private async void OrganizeMode_Changed(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        if (RulesFirstRadio.IsChecked == true)
        {
            _settings.UseRulesFirst = true;
            _settings.FallbackToCategories = true;
        }
        else if (CategoriesOnlyRadio.IsChecked == true)
        {
            _settings.UseRulesFirst = false;
            _settings.FallbackToCategories = true;
        }
        else if (RulesOnlyRadio.IsChecked == true)
        {
            _settings.UseRulesFirst = true;
            _settings.FallbackToCategories = false;
        }

        await SaveSettingsAsync();
    }

    private async void NotificationsToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.ShowNotifications = NotificationsToggle.IsOn;
        await SaveSettingsAsync();
    }

    private async void RecycleBinToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.MoveToTrashInsteadOfDelete = RecycleBinToggle.IsOn;
        await SaveSettingsAsync();
    }

    private async void ConfirmToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.ConfirmBeforeOrganize = ConfirmToggle.IsOn;
        await SaveSettingsAsync();
    }

    private async void IncludeSubfoldersToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.IncludeSubfolders = IncludeSubfoldersToggle.IsOn;
        await SaveSettingsAsync();
    }

    private async void IgnoreHiddenToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.IgnoreHiddenFiles = IgnoreHiddenToggle.IsOn;
        await SaveSettingsAsync();
    }

    private async void IgnoreSystemToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.IgnoreSystemFiles = IgnoreSystemToggle.IsOn;
        await SaveSettingsAsync();
    }

    private async void MinimizeToTrayToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.MinimizeToTray = MinimizeToTrayToggle.IsOn;
        await SaveSettingsAsync();
    }

    private async void CloseToTrayToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.CloseToTray = CloseToTrayToggle.IsOn;
        await SaveSettingsAsync();
    }

    private async void StartMinimizedToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.StartMinimized = StartMinimizedToggle.IsOn;
        await SaveSettingsAsync();
    }

    private async void RunOnStartupToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        _settings.RunOnStartup = RunOnStartupToggle.IsOn;
        await SaveSettingsAsync();

        // Apply the startup setting immediately
        StartupManager.SetRunOnStartup(_settings.RunOnStartup);
    }

    private async void LanguageComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_isLoading || _settings == null) return;

        if (LanguageComboBox.SelectedItem is ComboBoxItem selectedItem &&
            selectedItem.Tag is string languageCode)
        {
            _settings.Language = languageCode;
            await SaveSettingsAsync();

            // Apply the language change - UI will update immediately via LanguageChanged event
            LocalizationService.Instance.SetLanguage(languageCode);

            // Hide restart hint - language now updates immediately
            RestartHint.Visibility = Visibility.Collapsed;
        }
    }

    private async Task SaveSettingsAsync()
    {
        if (_settings != null && _settingsService != null)
        {
            await _settingsService.SaveSettingsAsync(_settings);
        }
    }
}
