using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using FolderFresh.Models;
using FolderFresh.Services;
using Microsoft.UI;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.Storage.Pickers;

namespace FolderFresh.Components;

public sealed partial class ProfilesContent : UserControl
{
    private ProfileService? _profileService;
    private string? _currentProfileId;

    public ObservableCollection<Profile> Profiles { get; } = new();

    /// <summary>
    /// Event fired when a profile is switched, so MainPage can update its state
    /// </summary>
    public event EventHandler<string>? ProfileSwitched;

    /// <summary>
    /// Event fired when profiles list changes (add/delete), so MainPage can update
    /// </summary>
    public event EventHandler? ProfilesChanged;

    public ProfilesContent()
    {
        this.InitializeComponent();
    }

    /// <summary>
    /// Initialize with the ProfileService from MainPage
    /// </summary>
    public void Initialize(ProfileService profileService)
    {
        _profileService = profileService;
        LoadProfiles();
    }

    private void UserControl_Loaded(object sender, RoutedEventArgs e)
    {
        // Profiles are loaded via Initialize() from MainPage
    }

    public void LoadProfiles()
    {
        if (_profileService == null) return;

        _currentProfileId = _profileService.GetCurrentProfileId();
        var profiles = _profileService.GetProfiles();

        Profiles.Clear();
        ProfilesListPanel.Children.Clear();

        foreach (var profile in profiles)
        {
            Profiles.Add(profile);
            ProfilesListPanel.Children.Add(BuildProfileCard(profile));
        }
    }

    private Border BuildProfileCard(Profile profile)
    {
        bool isActive = profile.Id == _currentProfileId;

        // Main card border
        var card = new Border
        {
            Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 45, 45, 45)),
            CornerRadius = new CornerRadius(8),
            Padding = new Thickness(16)
        };

        // Card content grid
        var grid = new Grid();
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        // Left side - Profile info
        var infoPanel = new StackPanel { Orientation = Orientation.Vertical, Spacing = 4 };

        var namePanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
        namePanel.Children.Add(new TextBlock
        {
            Text = profile.Name,
            FontSize = 15,
            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 255, 255))
        });

        if (isActive)
        {
            var activeBadge = new Border
            {
                Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 88, 101, 242)),
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(6, 2, 6, 2),
                VerticalAlignment = VerticalAlignment.Center
            };
            activeBadge.Child = new TextBlock
            {
                Text = "Active",
                FontSize = 11,
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 255, 255))
            };
            namePanel.Children.Add(activeBadge);
        }

        infoPanel.Children.Add(namePanel);

        // Date info
        var dateText = new TextBlock
        {
            Text = $"Created {profile.CreatedAt:MMM d, yyyy}",
            FontSize = 12,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 102, 102, 102))
        };
        infoPanel.Children.Add(dateText);

        Grid.SetColumn(infoPanel, 0);
        grid.Children.Add(infoPanel);

        // Right side - Action buttons
        var actionPanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, VerticalAlignment = VerticalAlignment.Center };

        // Switch/Active button
        if (isActive)
        {
            var activeButton = new Button
            {
                Content = "Active",
                Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 35, 36, 40)),
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 102, 102, 102)),
                Padding = new Thickness(16, 8, 16, 8),
                CornerRadius = new CornerRadius(6),
                IsEnabled = false
            };
            actionPanel.Children.Add(activeButton);
        }
        else
        {
            var switchButton = new Button
            {
                Content = "Switch",
                Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 88, 101, 242)),
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 255, 255)),
                Padding = new Thickness(16, 8, 16, 8),
                CornerRadius = new CornerRadius(6),
                Tag = profile.Id
            };
            switchButton.Click += SwitchProfileButton_Click;
            actionPanel.Children.Add(switchButton);
        }

        // More options button with menu
        var moreButton = new Button
        {
            Background = new SolidColorBrush(Colors.Transparent),
            BorderThickness = new Thickness(0),
            Padding = new Thickness(8),
            CornerRadius = new CornerRadius(6)
        };
        moreButton.Content = new FontIcon
        {
            Glyph = "\uE712",
            FontSize = 16,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 153, 153, 153))
        };

        // Create flyout menu
        var menuFlyout = new MenuFlyout();

        var renameItem = new MenuFlyoutItem { Text = "Rename", Tag = profile.Id };
        renameItem.Click += RenameMenuItem_Click;
        menuFlyout.Items.Add(renameItem);

        var duplicateItem = new MenuFlyoutItem { Text = "Duplicate", Tag = profile.Id };
        duplicateItem.Click += DuplicateMenuItem_Click;
        menuFlyout.Items.Add(duplicateItem);

        var exportItem = new MenuFlyoutItem { Text = "Export", Tag = profile.Id };
        exportItem.Click += ExportMenuItem_Click;
        menuFlyout.Items.Add(exportItem);

        menuFlyout.Items.Add(new MenuFlyoutSeparator());

        var deleteItem = new MenuFlyoutItem
        {
            Text = "Delete",
            Tag = profile.Id,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 237, 66, 69))
        };
        deleteItem.Click += DeleteMenuItem_Click;
        menuFlyout.Items.Add(deleteItem);

        moreButton.Flyout = menuFlyout;
        actionPanel.Children.Add(moreButton);

        Grid.SetColumn(actionPanel, 1);
        grid.Children.Add(actionPanel);

        card.Child = grid;
        return card;
    }

    private async void NewProfileButton_Click(object sender, RoutedEventArgs e)
    {
        if (_profileService == null) return;

        var result = await ShowProfileNameDialogAsync("New Profile", "Create", "New Profile", null);
        if (result != null)
        {
            await _profileService.CreateProfileAsync(result);
            LoadProfiles();
            ProfilesChanged?.Invoke(this, EventArgs.Empty);
        }
    }

    /// <summary>
    /// Shows a dialog for entering a profile name with duplicate validation.
    /// </summary>
    /// <param name="title">Dialog title</param>
    /// <param name="primaryButtonText">Text for the primary button</param>
    /// <param name="initialName">Initial text in the textbox</param>
    /// <param name="excludeProfileId">Profile ID to exclude from duplicate check (for rename)</param>
    /// <returns>The validated name, or null if cancelled</returns>
    private async Task<string?> ShowProfileNameDialogAsync(string title, string primaryButtonText, string initialName, string? excludeProfileId)
    {
        var dialog = new ContentDialog
        {
            Title = title,
            PrimaryButtonText = primaryButtonText,
            CloseButtonText = "Cancel",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = this.XamlRoot
        };

        var panel = new StackPanel { Spacing = 8 };

        var textBox = new TextBox
        {
            PlaceholderText = "Profile name",
            Text = initialName
        };

        var errorText = new TextBlock
        {
            Text = "",
            FontSize = 12,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 237, 66, 69)),
            Visibility = Visibility.Collapsed,
            TextWrapping = TextWrapping.Wrap
        };

        panel.Children.Add(textBox);
        panel.Children.Add(errorText);
        dialog.Content = panel;

        // Validate on text change
        textBox.TextChanged += (s, args) =>
        {
            var name = textBox.Text.Trim();
            var validationError = ValidateProfileName(name, excludeProfileId);

            if (validationError != null)
            {
                errorText.Text = validationError;
                errorText.Visibility = Visibility.Visible;
                dialog.IsPrimaryButtonEnabled = false;
            }
            else
            {
                errorText.Visibility = Visibility.Collapsed;
                dialog.IsPrimaryButtonEnabled = true;
            }
        };

        // Initial validation
        var initialError = ValidateProfileName(initialName.Trim(), excludeProfileId);
        if (initialError != null)
        {
            errorText.Text = initialError;
            errorText.Visibility = Visibility.Visible;
            dialog.IsPrimaryButtonEnabled = false;
        }

        textBox.SelectAll();

        var result = await dialog.ShowAsync();
        if (result == ContentDialogResult.Primary)
        {
            return textBox.Text.Trim();
        }

        return null;
    }

    /// <summary>
    /// Validates a profile name and returns an error message if invalid, or null if valid.
    /// </summary>
    private string? ValidateProfileName(string name, string? excludeProfileId)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            return "Profile name cannot be empty.";
        }

        if (_profileService == null) return null;

        // Check for duplicate names (excluding the current profile if renaming)
        var profiles = _profileService.GetProfiles();
        var duplicate = profiles.FirstOrDefault(p =>
            p.Name.Equals(name, StringComparison.OrdinalIgnoreCase) &&
            p.Id != excludeProfileId);

        if (duplicate != null)
        {
            return "A profile with this name already exists.";
        }

        return null;
    }

    private async void ImportButton_Click(object sender, RoutedEventArgs e)
    {
        if (_profileService == null) return;

        var picker = new FileOpenPicker
        {
            SuggestedStartLocation = PickerLocationId.DocumentsLibrary
        };
        picker.FileTypeFilter.Add(".folderfresh");

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var file = await picker.PickSingleFileAsync();
        if (file != null)
        {
            try
            {
                // Read the file to get the profile name
                var json = await Windows.Storage.FileIO.ReadTextAsync(file);
                var tempProfile = System.Text.Json.JsonSerializer.Deserialize<ImportedProfileInfo>(json);
                var suggestedName = tempProfile?.Name ?? "Imported Profile";

                // Get a unique suggested name if there's a conflict
                var initialName = _profileService.ProfileNameExists(suggestedName)
                    ? _profileService.GetUniqueProfileName(suggestedName)
                    : suggestedName;

                // Show dialog with validation
                var finalName = await ShowProfileNameDialogAsync("Import Profile", "Import", initialName, null);
                if (finalName == null) return;

                await _profileService.ImportProfileAsync(file.Path, finalName);
                LoadProfiles();
                ProfilesChanged?.Invoke(this, EventArgs.Empty);
            }
            catch (Exception ex)
            {
                var errorDialog = new ContentDialog
                {
                    Title = "Import Failed",
                    Content = $"Failed to import profile: {ex.Message}",
                    CloseButtonText = "OK",
                    XamlRoot = this.XamlRoot
                };
                await errorDialog.ShowAsync();
            }
        }
    }

    private async void SwitchProfileButton_Click(object sender, RoutedEventArgs e)
    {
        if (_profileService == null) return;
        if (sender is not Button button || button.Tag is not string profileId) return;

        // Don't switch if already active
        if (profileId == _currentProfileId) return;

        await _profileService.SwitchToProfileAsync(profileId);
        _currentProfileId = profileId;
        LoadProfiles();
        ProfileSwitched?.Invoke(this, profileId);
    }

    private async void RenameMenuItem_Click(object sender, RoutedEventArgs e)
    {
        if (_profileService == null) return;
        if (sender is not MenuFlyoutItem menuItem || menuItem.Tag is not string profileId) return;

        var profile = _profileService.GetProfile(profileId);
        if (profile == null) return;

        // Pass profileId as excludeProfileId so renaming to the same name is allowed
        var result = await ShowProfileNameDialogAsync("Rename Profile", "Rename", profile.Name, profileId);
        if (result != null)
        {
            await _profileService.RenameProfileAsync(profileId, result);
            LoadProfiles();
            ProfilesChanged?.Invoke(this, EventArgs.Empty);
        }
    }

    private async void DuplicateMenuItem_Click(object sender, RoutedEventArgs e)
    {
        if (_profileService == null) return;
        if (sender is not MenuFlyoutItem menuItem || menuItem.Tag is not string profileId) return;

        var profile = _profileService.GetProfile(profileId);
        if (profile == null) return;

        // Generate a unique suggested name for the duplicate
        var suggestedName = $"{profile.Name} (Copy)";
        var initialName = _profileService.ProfileNameExists(suggestedName)
            ? _profileService.GetUniqueProfileName(suggestedName)
            : suggestedName;

        var result = await ShowProfileNameDialogAsync("Duplicate Profile", "Duplicate", initialName, null);
        if (result != null)
        {
            await _profileService.DuplicateProfileAsync(profileId, result);
            LoadProfiles();
            ProfilesChanged?.Invoke(this, EventArgs.Empty);
        }
    }

    private async void ExportMenuItem_Click(object sender, RoutedEventArgs e)
    {
        if (_profileService == null) return;
        if (sender is not MenuFlyoutItem menuItem || menuItem.Tag is not string profileId) return;

        var profile = _profileService.GetProfile(profileId);
        if (profile == null) return;

        var picker = new FileSavePicker
        {
            SuggestedStartLocation = PickerLocationId.DocumentsLibrary,
            SuggestedFileName = profile.Name
        };
        picker.FileTypeChoices.Add("FolderFresh Profile", new List<string> { ".folderfresh" });

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var file = await picker.PickSaveFileAsync();
        if (file != null)
        {
            try
            {
                await _profileService.ExportProfileAsync(profileId, file.Path);

                var successDialog = new ContentDialog
                {
                    Title = "Exported",
                    Content = $"Profile \"{profile.Name}\" exported successfully.",
                    CloseButtonText = "OK",
                    XamlRoot = this.XamlRoot
                };
                await successDialog.ShowAsync();
            }
            catch (Exception ex)
            {
                var errorDialog = new ContentDialog
                {
                    Title = "Export Failed",
                    Content = $"Failed to export profile: {ex.Message}",
                    CloseButtonText = "OK",
                    XamlRoot = this.XamlRoot
                };
                await errorDialog.ShowAsync();
            }
        }
    }

    private async void DeleteMenuItem_Click(object sender, RoutedEventArgs e)
    {
        if (_profileService == null) return;
        if (sender is not MenuFlyoutItem menuItem || menuItem.Tag is not string profileId) return;

        var profile = _profileService.GetProfile(profileId);
        if (profile == null) return;

        var profiles = _profileService.GetProfiles();
        if (profiles.Count <= 1)
        {
            var errorDialog = new ContentDialog
            {
                Title = "Cannot Delete",
                Content = "You cannot delete the last remaining profile.",
                CloseButtonText = "OK",
                XamlRoot = this.XamlRoot
            };
            await errorDialog.ShowAsync();
            return;
        }

        var dialog = new ContentDialog
        {
            Title = "Delete Profile",
            Content = $"Are you sure you want to delete \"{profile.Name}\"?\n\nThis will permanently delete all rules, categories, and settings in this profile.",
            PrimaryButtonText = "Delete",
            CloseButtonText = "Cancel",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = this.XamlRoot
        };

        var result = await dialog.ShowAsync();
        if (result == ContentDialogResult.Primary)
        {
            // If deleting the active profile, switch to another first
            if (profileId == _currentProfileId)
            {
                var targetProfile = profiles.FirstOrDefault(p => p.Id == ProfileService.DefaultProfileId && p.Id != profileId)
                                    ?? profiles.FirstOrDefault(p => p.Id != profileId);

                if (targetProfile != null)
                {
                    await _profileService.SwitchToProfileAsync(targetProfile.Id);
                    _currentProfileId = targetProfile.Id;
                    ProfileSwitched?.Invoke(this, targetProfile.Id);
                }
            }

            await _profileService.DeleteProfileAsync(profileId);
            LoadProfiles();
            ProfilesChanged?.Invoke(this, EventArgs.Empty);
        }
    }

    private void DismissBannerButton_Click(object sender, RoutedEventArgs e)
    {
        InfoBanner.Visibility = Visibility.Collapsed;
    }

    // Helper class for reading imported profile name
    private class ImportedProfileInfo
    {
        [System.Text.Json.Serialization.JsonPropertyName("name")]
        public string? Name { get; set; }
    }
}
