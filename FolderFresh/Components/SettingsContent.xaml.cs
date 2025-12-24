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

    public SettingsContent()
    {
        this.InitializeComponent();
        _settingsService = new SettingsService();
        _ = LoadSettingsAsync();
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
            RunOnStartupToggle.IsOn = _settings.RunOnStartup;
        }
        finally
        {
            _isLoading = false;
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

    private async Task SaveSettingsAsync()
    {
        if (_settings != null && _settingsService != null)
        {
            await _settingsService.SaveSettingsAsync(_settings);
        }
    }
}
