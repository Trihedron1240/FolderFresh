using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using FolderFresh.Models;
using FolderFresh.Services;
using Microsoft.UI;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.Storage.Pickers;
using Windows.UI;

namespace FolderFresh.Components;

public sealed partial class WatchedFoldersContent : UserControl
{
    private WatchedFolderService? _watchedFolderService;
    private FolderWatcherManager? _folderWatcherManager;
    private ProfileService? _profileService;
    private OrganizationExecutor? _organizationExecutor;
    private bool _isLoading;
    private bool _isInitialized;

    public ObservableCollection<WatchedFolder> WatchedFolders { get; } = new();

    /// <summary>
    /// Event fired when a folder is added.
    /// </summary>
    public event EventHandler<WatchedFolder>? FolderAdded;

    /// <summary>
    /// Event fired when a folder is removed.
    /// </summary>
    public event EventHandler<string>? FolderRemoved;

    /// <summary>
    /// Event fired when organization is requested.
    /// </summary>
    public event EventHandler<(string folderId, bool previewOnly)>? OrganizationRequested;

    public WatchedFoldersContent()
    {
        this.InitializeComponent();
        ApplyLocalization();
        LocalizationService.Instance.LanguageChanged += (s, e) => DispatcherQueue.TryEnqueue(ApplyLocalization);
    }

    private void ApplyLocalization()
    {
        TitleText.Text = Loc.Get("Folders_Title");
        SubtitleText.Text = Loc.Get("Folders_Subtitle");
        AddFolderButtonText.Text = Loc.Get("Folders_AddFolder");
        StopAllButtonText.Text = Loc.Get("Folders_StopAll");
        StartAllButtonText.Text = Loc.Get("Folders_StartAll");
        InfoBannerText.Text = Loc.Get("Folders_InfoBanner");
        EmptyTitleText.Text = Loc.Get("Folders_EmptyTitle");
        EmptyDescText.Text = Loc.Get("Folders_EmptyDesc");
        EmptyAddButtonText.Text = Loc.Get("Folders_AddFolder");
    }

    /// <summary>
    /// Initialize with required services.
    /// </summary>
    public async void Initialize(
        WatchedFolderService watchedFolderService,
        FolderWatcherManager folderWatcherManager,
        ProfileService profileService,
        OrganizationExecutor? organizationExecutor = null)
    {
        _watchedFolderService = watchedFolderService;
        _folderWatcherManager = folderWatcherManager;
        _profileService = profileService;
        _organizationExecutor = organizationExecutor;
        _isInitialized = true;

        // Subscribe to watcher events
        if (_folderWatcherManager != null)
        {
            _folderWatcherManager.StatusChanged += OnWatcherStatusChanged;
            _folderWatcherManager.OrganizationCompleted += OnOrganizationCompleted;
        }

        // Load from file on initial load
        await ReloadWatchedFoldersAsync();
    }

    private void UserControl_Loaded(object sender, RoutedEventArgs e)
    {
        // Load is done via Initialize() from parent
    }

    /// <summary>
    /// Refreshes the UI from the cached watched folders list.
    /// Call ReloadWatchedFoldersAsync to reload from file.
    /// </summary>
    public void LoadWatchedFolders()
    {
        if (_watchedFolderService == null || !_isInitialized) return;

        _isLoading = true;

        try
        {
            var folders = _watchedFolderService.GetWatchedFolders();

            // Update profile names
            if (_profileService != null)
            {
                foreach (var folder in folders)
                {
                    var profile = _profileService.GetProfile(folder.ProfileId);
                    folder.ProfileName = profile?.Name ?? "Unknown Profile";
                }
            }

            WatchedFolders.Clear();
            FoldersListPanel.Children.Clear();

            foreach (var folder in folders)
            {
                WatchedFolders.Add(folder);
                FoldersListPanel.Children.Add(BuildFolderCard(folder));
            }

            UpdateEmptyState();
            UpdateActionButtons();
        }
        finally
        {
            _isLoading = false;
        }
    }

    /// <summary>
    /// Reloads watched folders from file and refreshes the UI.
    /// Use this when first initializing or when external changes may have occurred.
    /// </summary>
    public async Task ReloadWatchedFoldersAsync()
    {
        if (_watchedFolderService == null || !_isInitialized) return;

        ShowLoading(true);
        try
        {
            await _watchedFolderService.LoadWatchedFoldersAsync();
            LoadWatchedFolders();
        }
        finally
        {
            ShowLoading(false);
        }
    }

    /// <summary>
    /// Refreshes folder statuses (file counts, accessibility).
    /// </summary>
    public async void RefreshFolderStatuses()
    {
        if (_watchedFolderService == null) return;

        foreach (var folder in WatchedFolders)
        {
            // Check accessibility
            var (isValid, error) = _watchedFolderService.ValidateFolderPath(folder.FolderPath);
            if (!isValid && folder.Status != WatchStatus.Error)
            {
                folder.Status = WatchStatus.Error;
                folder.LastError = error;
            }
            else if (isValid && folder.Status == WatchStatus.Error)
            {
                folder.Status = WatchStatus.Idle;
                folder.LastError = null;
            }

            // Update file count using profile's includeSubfolders setting
            if (isValid && _profileService != null)
            {
                try
                {
                    var profile = _profileService.GetProfile(folder.ProfileId);
                    var includeSubfolders = true; // Default
                    if (profile != null && !string.IsNullOrEmpty(profile.SettingsJson))
                    {
                        try
                        {
                            var settings = System.Text.Json.JsonSerializer.Deserialize<AppSettings>(profile.SettingsJson);
                            if (settings != null)
                            {
                                includeSubfolders = settings.IncludeSubfolders;
                            }
                        }
                        catch { /* Use default */ }
                    }

                    var files = Directory.GetFiles(folder.FolderPath, "*",
                        includeSubfolders ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly);
                    folder.FileCount = files.Length;
                }
                catch
                {
                    // Ignore errors counting files
                }
            }

            await _watchedFolderService.UpdateWatchedFolderAsync(folder);
        }

        // Rebuild UI
        FoldersListPanel.Children.Clear();
        foreach (var folder in WatchedFolders)
        {
            FoldersListPanel.Children.Add(BuildFolderCard(folder));
        }
    }

    private Border BuildFolderCard(WatchedFolder folder)
    {
        var card = new Border
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 45, 45, 45)),
            CornerRadius = new CornerRadius(8),
            Padding = new Thickness(16)
        };

        var grid = new Grid();
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        // Left side - Folder info
        var infoPanel = new StackPanel { Orientation = Orientation.Vertical, Spacing = 6 };

        // Row 1: Icon + Display name + Status badge
        var headerPanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10 };

        var folderIcon = new FontIcon
        {
            Glyph = "\uE8B7",
            FontSize = 20,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 96, 205, 255)),
            VerticalAlignment = VerticalAlignment.Center
        };
        headerPanel.Children.Add(folderIcon);

        var nameText = new TextBlock
        {
            Text = folder.DisplayName,
            FontSize = 15,
            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
            Foreground = new SolidColorBrush(Colors.White),
            VerticalAlignment = VerticalAlignment.Center
        };
        headerPanel.Children.Add(nameText);

        headerPanel.Children.Add(BuildStatusBadge(folder));

        infoPanel.Children.Add(headerPanel);

        // Row 2: Folder path
        var pathText = new TextBlock
        {
            Text = folder.DisplayPath,
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102)),
            TextTrimming = TextTrimming.CharacterEllipsis,
            MaxWidth = 400
        };
        infoPanel.Children.Add(pathText);

        // Row 3: Profile + Last organized + File count
        var metaPanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 16 };

        // Profile
        var profilePanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 4 };
        profilePanel.Children.Add(new FontIcon
        {
            Glyph = "\uE77B",
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 136, 136, 136))
        });
        profilePanel.Children.Add(new TextBlock
        {
            Text = $"Using: {folder.ProfileName ?? "Unknown"}",
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 136, 136, 136))
        });
        metaPanel.Children.Add(profilePanel);

        // Last organized
        var lastOrganizedText = folder.LastOrganizedAt.HasValue
            ? FormatTimeAgo(folder.LastOrganizedAt.Value)
            : "Never organized";

        var lastOrganizedPanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 4 };
        lastOrganizedPanel.Children.Add(new FontIcon
        {
            Glyph = "\uE823",
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 136, 136, 136))
        });
        lastOrganizedPanel.Children.Add(new TextBlock
        {
            Text = lastOrganizedText,
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 136, 136, 136))
        });
        metaPanel.Children.Add(lastOrganizedPanel);

        // File count badge
        var fileCountBadge = new Border
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 55, 55, 55)),
            CornerRadius = new CornerRadius(4),
            Padding = new Thickness(6, 2, 6, 2)
        };
        fileCountBadge.Child = new TextBlock
        {
            Text = $"{folder.FileCount} files",
            FontSize = 11,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 153, 153, 153))
        };
        metaPanel.Children.Add(fileCountBadge);

        infoPanel.Children.Add(metaPanel);

        // Error message if applicable
        if (folder.Status == WatchStatus.Error && !string.IsNullOrEmpty(folder.LastError))
        {
            var errorPanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 6, Margin = new Thickness(0, 4, 0, 0) };
            errorPanel.Children.Add(new FontIcon
            {
                Glyph = "\uE7BA",
                FontSize = 12,
                Foreground = new SolidColorBrush(Color.FromArgb(255, 239, 68, 68))
            });
            errorPanel.Children.Add(new TextBlock
            {
                Text = folder.LastError,
                FontSize = 12,
                Foreground = new SolidColorBrush(Color.FromArgb(255, 239, 68, 68)),
                TextTrimming = TextTrimming.CharacterEllipsis,
                MaxWidth = 350
            });
            infoPanel.Children.Add(errorPanel);
        }

        Grid.SetColumn(infoPanel, 0);
        grid.Children.Add(infoPanel);

        // Right side - Action buttons
        var actionPanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, VerticalAlignment = VerticalAlignment.Center };

        // Enable/Disable toggle
        var enableToggle = new ToggleSwitch
        {
            IsOn = folder.IsEnabled,
            OnContent = "",
            OffContent = "",
            Tag = folder.Id,
            VerticalAlignment = VerticalAlignment.Center
        };
        ToolTipService.SetToolTip(enableToggle, folder.IsEnabled ? "Disable watching" : "Enable watching");
        enableToggle.Toggled += EnableToggle_Toggled;
        actionPanel.Children.Add(enableToggle);

        // Retry button (for error state)
        if (folder.Status == WatchStatus.Error)
        {
            var retryButton = new Button
            {
                Content = "Retry",
                Background = new SolidColorBrush(Color.FromArgb(255, 239, 68, 68)),
                Foreground = new SolidColorBrush(Colors.White),
                Padding = new Thickness(12, 6, 12, 6),
                CornerRadius = new CornerRadius(6),
                Tag = folder.Id
            };
            retryButton.Click += RetryButton_Click;
            actionPanel.Children.Add(retryButton);
        }

        // Organize Now button
        var organizeButton = new Button
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 88, 101, 242)),
            Foreground = new SolidColorBrush(Colors.White),
            Padding = new Thickness(12, 6, 12, 6),
            CornerRadius = new CornerRadius(6),
            Tag = folder.Id,
            IsEnabled = folder.Status != WatchStatus.Error && folder.Status != WatchStatus.Organizing
        };
        organizeButton.Content = new TextBlock { Text = Loc.Get("Folders_Organize"), FontSize = 12 };
        ToolTipService.SetToolTip(organizeButton, "Organize files now using the assigned profile");
        organizeButton.Click += OrganizeButton_Click;
        actionPanel.Children.Add(organizeButton);

        // Preview button
        var previewButton = new Button
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 45, 45, 45)),
            Foreground = new SolidColorBrush(Color.FromArgb(255, 181, 186, 193)),
            Padding = new Thickness(12, 6, 12, 6),
            CornerRadius = new CornerRadius(6),
            BorderBrush = new SolidColorBrush(Color.FromArgb(255, 70, 70, 70)),
            BorderThickness = new Thickness(1),
            Tag = folder.Id,
            IsEnabled = folder.Status != WatchStatus.Error
        };
        previewButton.Content = new TextBlock { Text = Loc.Get("Folders_Preview"), FontSize = 12 };
        ToolTipService.SetToolTip(previewButton, "Preview what files will be organized");
        previewButton.Click += PreviewButton_Click;
        actionPanel.Children.Add(previewButton);

        // More options menu
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
            Foreground = new SolidColorBrush(Color.FromArgb(255, 153, 153, 153))
        };
        ToolTipService.SetToolTip(moreButton, Loc.Get("Folders_MoreOptions"));

        var menuFlyout = new MenuFlyout();

        var configureItem = new MenuFlyoutItem { Text = Loc.Get("Folders_Configure"), Tag = folder.Id };
        configureItem.Click += ConfigureMenuItem_Click;
        menuFlyout.Items.Add(configureItem);

        var openFolderItem = new MenuFlyoutItem { Text = Loc.Get("Folders_OpenFolder"), Tag = folder.Id };
        openFolderItem.Click += OpenFolderMenuItem_Click;
        menuFlyout.Items.Add(openFolderItem);

        // Undo option (only if undo state available)
        if (_organizationExecutor?.HasUndoState(folder.Id) == true)
        {
            var undoItem = new MenuFlyoutItem
            {
                Text = Loc.Get("Folders_UndoLastOrganize"),
                Tag = folder.Id,
                Icon = new FontIcon { Glyph = "\uE7A7" }
            };
            undoItem.Click += UndoMenuItem_Click;
            menuFlyout.Items.Add(undoItem);
        }

        menuFlyout.Items.Add(new MenuFlyoutSeparator());

        var removeItem = new MenuFlyoutItem
        {
            Text = Loc.Get("Folders_Remove"),
            Tag = folder.Id,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 239, 68, 68))
        };
        removeItem.Click += RemoveMenuItem_Click;
        menuFlyout.Items.Add(removeItem);

        moreButton.Flyout = menuFlyout;
        actionPanel.Children.Add(moreButton);

        Grid.SetColumn(actionPanel, 1);
        grid.Children.Add(actionPanel);

        card.Child = grid;
        return card;
    }

    private Border BuildStatusBadge(WatchedFolder folder)
    {
        Color bgColor;
        Color fgColor;
        string text;
        string? glyph = null;
        string tooltip;

        switch (folder.Status)
        {
            case WatchStatus.Watching:
                bgColor = Color.FromArgb(255, 16, 185, 129);
                fgColor = Colors.White;
                text = "Watching";
                glyph = "\uEA3A"; // Dot
                tooltip = "Actively monitoring for file changes";
                break;
            case WatchStatus.Organizing:
                bgColor = Color.FromArgb(255, 59, 130, 246);
                fgColor = Colors.White;
                text = "Organizing...";
                tooltip = "Currently organizing files";
                break;
            case WatchStatus.Error:
                bgColor = Color.FromArgb(255, 239, 68, 68);
                fgColor = Colors.White;
                text = "Error";
                glyph = "\uE7BA"; // Warning
                tooltip = folder.LastError ?? "An error occurred";
                break;
            case WatchStatus.Idle:
            default:
                bgColor = Color.FromArgb(255, 107, 114, 128);
                fgColor = Colors.White;
                text = "Idle";
                tooltip = "Not currently watching for changes";
                break;
        }

        var badge = new Border
        {
            Background = new SolidColorBrush(bgColor),
            CornerRadius = new CornerRadius(4),
            Padding = new Thickness(6, 2, 6, 2),
            VerticalAlignment = VerticalAlignment.Center
        };

        ToolTipService.SetToolTip(badge, tooltip);

        var content = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 4 };

        if (glyph != null)
        {
            content.Children.Add(new FontIcon
            {
                Glyph = glyph,
                FontSize = 8,
                Foreground = new SolidColorBrush(fgColor)
            });
        }

        if (folder.Status == WatchStatus.Organizing)
        {
            content.Children.Add(new ProgressRing
            {
                IsActive = true,
                Width = 10,
                Height = 10,
                Foreground = new SolidColorBrush(fgColor)
            });
        }

        content.Children.Add(new TextBlock
        {
            Text = text,
            FontSize = 11,
            Foreground = new SolidColorBrush(fgColor)
        });

        badge.Child = content;
        return badge;
    }

    private static string FormatTimeAgo(DateTime dateTime)
    {
        var span = DateTime.Now - dateTime;

        if (span.TotalMinutes < 1)
            return "Just now";
        if (span.TotalMinutes < 60)
            return $"{(int)span.TotalMinutes} min ago";
        if (span.TotalHours < 24)
            return $"{(int)span.TotalHours} hours ago";
        if (span.TotalDays < 7)
            return $"{(int)span.TotalDays} days ago";

        return dateTime.ToString("MMM d, yyyy");
    }

    private void ShowLoading(bool show)
    {
        LoadingIndicator.IsActive = show;
        LoadingIndicator.Visibility = show ? Visibility.Visible : Visibility.Collapsed;
        FoldersScrollViewer.Visibility = show ? Visibility.Collapsed : Visibility.Visible;
    }

    private void UpdateEmptyState()
    {
        var hasItems = WatchedFolders.Count > 0;
        EmptyState.Visibility = hasItems ? Visibility.Collapsed : Visibility.Visible;
        FoldersScrollViewer.Visibility = hasItems ? Visibility.Visible : Visibility.Collapsed;
    }

    private void UpdateActionButtons()
    {
        var hasItems = WatchedFolders.Count > 0;
        StartAllButton.Visibility = hasItems ? Visibility.Visible : Visibility.Collapsed;
        StopAllButton.Visibility = hasItems ? Visibility.Visible : Visibility.Collapsed;
    }

    private async void AddFolderButton_Click(object sender, RoutedEventArgs e)
    {
        if (_watchedFolderService == null || _profileService == null) return;

        // Show folder picker
        var picker = new FolderPicker
        {
            SuggestedStartLocation = PickerLocationId.Desktop,
            ViewMode = PickerViewMode.List
        };
        picker.FileTypeFilter.Add("*");

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var selectedFolder = await picker.PickSingleFolderAsync();
        if (selectedFolder == null) return;

        // Check for duplicates
        if (_watchedFolderService.FolderPathExists(selectedFolder.Path))
        {
            await ShowErrorDialogAsync("Duplicate Folder", "This folder is already being watched.");
            return;
        }

        // Check for conflicts
        var warnings = _watchedFolderService.CheckFolderConflicts(selectedFolder.Path);

        // Add network/cloud path warnings
        var pathWarnings = _watchedFolderService.GetPathWarnings(selectedFolder.Path);
        warnings.AddRange(pathWarnings);

        if (warnings.Count > 0)
        {
            var warningText = string.Join("\n\n", warnings);
            var continueResult = await ShowConfirmDialogAsync(
                "Folder Warning",
                $"{warningText}\n\nDo you want to add this folder anyway?",
                "Add Anyway",
                "Cancel");

            if (!continueResult) return;
        }

        // Show configuration dialog
        var folder = WatchedFolder.Create(selectedFolder.Path);
        var configResult = await ShowConfigurationDialogAsync(folder, isNew: true);

        if (configResult != null)
        {
            await _watchedFolderService.AddWatchedFolderAsync(configResult);

            // Start watching if enabled
            if (configResult.IsEnabled && _folderWatcherManager != null)
            {
                await _folderWatcherManager.StartWatchingAsync(configResult);
            }

            LoadWatchedFolders();
            FolderAdded?.Invoke(this, configResult);
        }
    }

    private async Task<WatchedFolder?> ShowConfigurationDialogAsync(WatchedFolder folder, bool isNew)
    {
        if (_profileService == null) return null;

        var dialog = new ContentDialog
        {
            Title = isNew ? Loc.Get("ConfigDialog_AddTitle") : Loc.Get("ConfigDialog_EditTitle"),
            PrimaryButtonText = isNew ? Loc.Get("Add") : Loc.Get("Save"),
            CloseButtonText = Loc.Get("Cancel"),
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = this.XamlRoot
        };

        var panel = new StackPanel { Spacing = 16 };

        // Folder path (read-only)
        var pathPanel = new StackPanel { Spacing = 4 };
        pathPanel.Children.Add(new TextBlock
        {
            Text = Loc.Get("ConfigDialog_FolderPath"),
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 153, 153, 153))
        });
        pathPanel.Children.Add(new TextBlock
        {
            Text = folder.FolderPath,
            FontSize = 13,
            Foreground = new SolidColorBrush(Colors.White),
            TextTrimming = TextTrimming.CharacterEllipsis
        });
        panel.Children.Add(pathPanel);

        // Display name
        var namePanel = new StackPanel { Spacing = 4 };
        namePanel.Children.Add(new TextBlock
        {
            Text = Loc.Get("ConfigDialog_DisplayName"),
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 153, 153, 153))
        });
        var nameTextBox = new TextBox
        {
            Text = folder.DisplayName,
            PlaceholderText = Loc.Get("ConfigDialog_DisplayNamePlaceholder")
        };
        namePanel.Children.Add(nameTextBox);
        panel.Children.Add(namePanel);

        // Profile dropdown
        var profilePanel = new StackPanel { Spacing = 4 };
        profilePanel.Children.Add(new TextBlock
        {
            Text = Loc.Get("ConfigDialog_ProfileToUse"),
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 153, 153, 153))
        });

        var profileComboBox = new ComboBox
        {
            HorizontalAlignment = HorizontalAlignment.Stretch,
            PlaceholderText = Loc.Get("ConfigDialog_SelectProfile")
        };

        var profiles = _profileService.GetProfiles();
        var currentProfileId = _profileService.GetCurrentProfileId();

        foreach (var profile in profiles)
        {
            var item = new ComboBoxItem
            {
                Content = profile.Name,
                Tag = profile.Id
            };
            profileComboBox.Items.Add(item);

            // Select current profile or folder's profile
            if ((!string.IsNullOrEmpty(folder.ProfileId) && profile.Id == folder.ProfileId) ||
                (string.IsNullOrEmpty(folder.ProfileId) && profile.Id == currentProfileId))
            {
                profileComboBox.SelectedItem = item;
            }
        }

        profilePanel.Children.Add(profileComboBox);
        panel.Children.Add(profilePanel);

        // Auto-organize toggle
        var autoOrganizePanel = new StackPanel { Spacing = 4 };
        var autoOrganizeToggle = new ToggleSwitch
        {
            Header = Loc.Get("ConfigDialog_AutoOrganize"),
            IsOn = folder.AutoOrganize,
            OnContent = "On",
            OffContent = "Off"
        };
        autoOrganizePanel.Children.Add(autoOrganizeToggle);
        autoOrganizePanel.Children.Add(new TextBlock
        {
            Text = Loc.Get("ConfigDialog_AutoOrganizeDesc"),
            FontSize = 11,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102)),
            TextWrapping = TextWrapping.Wrap
        });
        panel.Children.Add(autoOrganizePanel);

        dialog.Content = panel;

        // Validate profile selection
        profileComboBox.SelectionChanged += (s, args) =>
        {
            dialog.IsPrimaryButtonEnabled = profileComboBox.SelectedItem != null;
        };
        dialog.IsPrimaryButtonEnabled = profileComboBox.SelectedItem != null;

        var result = await dialog.ShowAsync();
        if (result == ContentDialogResult.Primary)
        {
            folder.DisplayName = string.IsNullOrWhiteSpace(nameTextBox.Text)
                ? Path.GetFileName(folder.FolderPath)
                : nameTextBox.Text.Trim();

            if (profileComboBox.SelectedItem is ComboBoxItem selectedProfile)
            {
                folder.ProfileId = selectedProfile.Tag as string ?? "";
                folder.ProfileName = selectedProfile.Content as string;
            }

            folder.AutoOrganize = autoOrganizeToggle.IsOn;

            return folder;
        }

        return null;
    }

    private async void EnableToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (_watchedFolderService == null || _folderWatcherManager == null || _isLoading) return;
        if (sender is not ToggleSwitch toggle || toggle.Tag is not string folderId) return;

        var folder = _watchedFolderService.GetWatchedFolder(folderId);
        if (folder == null) return;

        folder.IsEnabled = toggle.IsOn;
        await _watchedFolderService.UpdateWatchedFolderAsync(folder);

        if (toggle.IsOn)
        {
            await _folderWatcherManager.StartWatchingAsync(folder);
        }
        else
        {
            _folderWatcherManager.StopWatching(folderId);
        }

        // Refresh the card to show updated status
        LoadWatchedFolders();
    }

    private async void OrganizeButton_Click(object sender, RoutedEventArgs e)
    {
        if (_folderWatcherManager == null || _watchedFolderService == null) return;
        if (sender is not Button button || button.Tag is not string folderId) return;

        var folder = _watchedFolderService.GetWatchedFolder(folderId);
        if (folder == null) return;

        // Update button to show loading state
        var originalContent = button.Content;
        button.IsEnabled = false;
        button.Content = new StackPanel
        {
            Orientation = Orientation.Horizontal,
            Spacing = 6,
            Children =
            {
                new ProgressRing { IsActive = true, Width = 12, Height = 12, Foreground = new SolidColorBrush(Colors.White) },
                new TextBlock { Text = "Organizing...", FontSize = 12, VerticalAlignment = VerticalAlignment.Center }
            }
        };

        OrganizationRequested?.Invoke(this, (folderId, false));

        try
        {
            var result = await _folderWatcherManager.OrganizeFolderAsync(folderId, previewOnly: false);

            if (result.Errors.Count > 0)
            {
                await ShowErrorDialogAsync("Organization Errors", string.Join("\n", result.Errors.Take(5)));
            }
            else if (result.FilesMoved > 0)
            {
                await ShowInfoDialogAsync("Organization Complete",
                    $"Successfully organized {result.FilesMoved} files.\n\n{result.FilesSkipped} files were already in their correct locations.");
            }
            else
            {
                await ShowInfoDialogAsync("Nothing to Organize",
                    "All files are already organized or don't match any rules/categories.");
            }
        }
        finally
        {
            button.Content = originalContent;
            LoadWatchedFolders();
        }
    }

    private async void PreviewButton_Click(object sender, RoutedEventArgs e)
    {
        if (_folderWatcherManager == null || _watchedFolderService == null) return;
        if (sender is not Button button || button.Tag is not string folderId) return;

        var folder = _watchedFolderService.GetWatchedFolder(folderId);
        if (folder == null) return;

        // Update button to show loading state
        var originalContent = button.Content;
        button.IsEnabled = false;
        button.Content = new StackPanel
        {
            Orientation = Orientation.Horizontal,
            Spacing = 6,
            Children =
            {
                new ProgressRing { IsActive = true, Width = 12, Height = 12, Foreground = new SolidColorBrush(Color.FromArgb(255, 181, 186, 193)) },
                new TextBlock { Text = "Scanning...", FontSize = 12, VerticalAlignment = VerticalAlignment.Center }
            }
        };

        OrganizationRequested?.Invoke(this, (folderId, true));

        try
        {
            var result = await _folderWatcherManager.OrganizeFolderAsync(folderId, previewOnly: true);

            // Show the new preview dialog
            var previewDialog = new WatchedFolderPreviewDialog(
                folder,
                result,
                _folderWatcherManager,
                _watchedFolderService)
            {
                XamlRoot = this.XamlRoot
            };

            await previewDialog.ShowAsync();

            // Refresh if organization was performed
            if (previewDialog.WasOrganized)
            {
                LoadWatchedFolders();

                // Show result summary
                var orgResult = previewDialog.OrganizationResult;
                if (orgResult != null)
                {
                    if (orgResult.Errors.Count > 0)
                    {
                        await ShowErrorDialogAsync("Organization Completed with Errors",
                            $"Organized {orgResult.FilesMoved} files.\n\nErrors:\n{string.Join("\n", orgResult.Errors.Take(5))}");
                    }
                }
            }
        }
        finally
        {
            button.Content = originalContent;
            button.IsEnabled = true;
        }
    }

    private async Task ShowPreviewDialogAsync(WatchedFolder folder, OrganizationResult result)
    {
        var dialog = new ContentDialog
        {
            Title = $"Preview: {folder.DisplayName}",
            CloseButtonText = "Close",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = this.XamlRoot
        };

        var panel = new StackPanel { Spacing = 12, MaxWidth = 500 };

        // Summary
        var summaryPanel = new StackPanel { Spacing = 4 };
        summaryPanel.Children.Add(new TextBlock
        {
            Text = $"Files that would be organized: {result.FilesWouldMove}",
            FontSize = 14,
            Foreground = new SolidColorBrush(Colors.White)
        });
        summaryPanel.Children.Add(new TextBlock
        {
            Text = $"Files that would be skipped: {result.FilesSkipped}",
            FontSize = 14,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 153, 153, 153))
        });
        panel.Children.Add(summaryPanel);

        // Preview list
        if (result.PreviewResults.Count > 0)
        {
            var scrollViewer = new ScrollViewer
            {
                MaxHeight = 300,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto
            };

            var listPanel = new StackPanel { Spacing = 8 };

            var displayResults = result.PreviewResults
                .Where(r => r.WillBeOrganized)
                .Take(50)
                .ToList();

            foreach (var preview in displayResults)
            {
                var itemPanel = new StackPanel { Spacing = 2 };

                itemPanel.Children.Add(new TextBlock
                {
                    Text = preview.FileName,
                    FontSize = 12,
                    Foreground = new SolidColorBrush(Colors.White)
                });

                var destinationText = preview.DestinationPath != null
                    ? $"→ {Path.GetFileName(Path.GetDirectoryName(preview.DestinationPath))}"
                    : "→ (no change)";

                itemPanel.Children.Add(new TextBlock
                {
                    Text = $"  {destinationText} ({preview.MatchedBy})",
                    FontSize = 11,
                    Foreground = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102))
                });

                listPanel.Children.Add(itemPanel);
            }

            if (result.PreviewResults.Count > 50)
            {
                listPanel.Children.Add(new TextBlock
                {
                    Text = $"... and {result.PreviewResults.Count - 50} more files",
                    FontSize = 11,
                    Foreground = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102)),
                    FontStyle = Windows.UI.Text.FontStyle.Italic
                });
            }

            scrollViewer.Content = listPanel;
            panel.Children.Add(scrollViewer);
        }

        // Organize Now button
        if (result.FilesWouldMove > 0)
        {
            dialog.PrimaryButtonText = "Organize Now";
            dialog.PrimaryButtonClick += async (s, args) =>
            {
                args.Cancel = true; // Prevent dialog from closing immediately
                dialog.Hide();

                if (_folderWatcherManager != null)
                {
                    var organizeResult = await _folderWatcherManager.OrganizeFolderAsync(folder.Id, previewOnly: false);
                    LoadWatchedFolders();

                    if (organizeResult.Errors.Count > 0)
                    {
                        await ShowErrorDialogAsync("Organization Errors", string.Join("\n", organizeResult.Errors.Take(5)));
                    }
                }
            };
        }

        dialog.Content = panel;
        await dialog.ShowAsync();
    }

    private async void RetryButton_Click(object sender, RoutedEventArgs e)
    {
        if (_folderWatcherManager == null || _watchedFolderService == null) return;
        if (sender is not Button button || button.Tag is not string folderId) return;

        var folder = _watchedFolderService.GetWatchedFolder(folderId);
        if (folder == null) return;

        // Validate folder still exists
        var (isValid, error) = _watchedFolderService.ValidateFolderPath(folder.FolderPath);

        if (!isValid)
        {
            var removeResult = await ShowConfirmDialogAsync(
                "Folder Not Accessible",
                $"{error}\n\nWould you like to remove this folder from the watch list?",
                "Remove",
                "Cancel");

            if (removeResult)
            {
                await RemoveFolderAsync(folderId);
            }
            return;
        }

        // Clear error and restart watcher
        folder.Status = WatchStatus.Idle;
        folder.LastError = null;
        await _watchedFolderService.UpdateWatchedFolderAsync(folder);

        if (folder.IsEnabled)
        {
            await _folderWatcherManager.StartWatchingAsync(folder);
        }

        LoadWatchedFolders();
    }

    private async void ConfigureMenuItem_Click(object sender, RoutedEventArgs e)
    {
        if (_watchedFolderService == null) return;
        if (sender is not MenuFlyoutItem menuItem || menuItem.Tag is not string folderId) return;

        var folder = _watchedFolderService.GetWatchedFolder(folderId);
        if (folder == null) return;

        var configResult = await ShowConfigurationDialogAsync(folder, isNew: false);
        if (configResult != null)
        {
            await _watchedFolderService.UpdateWatchedFolderAsync(configResult);

            // Restart watcher if enabled (config may have changed)
            if (_folderWatcherManager != null)
            {
                await _folderWatcherManager.RestartWatching(folderId);
            }

            LoadWatchedFolders();
        }
    }

    private async void OpenFolderMenuItem_Click(object sender, RoutedEventArgs e)
    {
        if (_watchedFolderService == null) return;
        if (sender is not MenuFlyoutItem menuItem || menuItem.Tag is not string folderId) return;

        var folder = _watchedFolderService.GetWatchedFolder(folderId);
        if (folder == null) return;

        try
        {
            await Windows.System.Launcher.LaunchFolderPathAsync(folder.FolderPath);
        }
        catch
        {
            await ShowErrorDialogAsync("Error", "Could not open folder.");
        }
    }

    private async void UndoMenuItem_Click(object sender, RoutedEventArgs e)
    {
        if (_organizationExecutor == null) return;
        if (sender is not MenuFlyoutItem menuItem || menuItem.Tag is not string folderId) return;

        var folder = _watchedFolderService?.GetWatchedFolder(folderId);
        if (folder == null) return;

        // Confirm undo
        var undoState = _organizationExecutor.GetUndoState(folderId);
        var fileCount = undoState?.Operations.Count ?? 0;

        var confirmed = await ShowConfirmDialogAsync(
            "Undo Organization",
            $"This will undo the last organization of \"{folder.DisplayName}\".\n\n" +
            $"{fileCount} file operations will be reverted.\n\n" +
            "Note: Deleted files cannot be restored automatically.",
            "Undo",
            "Cancel");

        if (!confirmed) return;

        try
        {
            var result = await _organizationExecutor.UndoLastOrganizationAsync(folderId);

            if (result.Success)
            {
                await ShowInfoDialogAsync("Undo Complete",
                    $"Restored {result.FilesRestored} files, deleted {result.CopiesDeleted} copies.");
            }
            else
            {
                var errorMessage = result.Error ?? string.Join("\n", result.Errors.Take(5));
                await ShowErrorDialogAsync("Undo Failed", errorMessage);
            }

            // Show warnings if any
            if (result.Warnings.Count > 0)
            {
                await ShowErrorDialogAsync("Undo Warnings", string.Join("\n", result.Warnings));
            }

            LoadWatchedFolders();
        }
        catch (Exception ex)
        {
            await ShowErrorDialogAsync("Undo Error", ex.Message);
        }
    }

    private async void RemoveMenuItem_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not MenuFlyoutItem menuItem || menuItem.Tag is not string folderId) return;

        var folder = _watchedFolderService?.GetWatchedFolder(folderId);
        if (folder == null) return;

        var result = await ShowConfirmDialogAsync(
            Loc.Get("Folders_RemoveDialog"),
            Loc.Get("Folders_RemoveConfirm", folder.DisplayName),
            Loc.Get("Folders_Remove"),
            Loc.Get("Cancel"));

        if (result)
        {
            await RemoveFolderAsync(folderId);
        }
    }

    private async Task RemoveFolderAsync(string folderId)
    {
        if (_watchedFolderService == null) return;

        // Stop watcher first
        _folderWatcherManager?.StopWatching(folderId);

        // Remove from service
        await _watchedFolderService.DeleteWatchedFolderAsync(folderId);

        LoadWatchedFolders();
        FolderRemoved?.Invoke(this, folderId);
    }

    private async void StartAllButton_Click(object sender, RoutedEventArgs e)
    {
        await StartAllWatchersAsync();
    }

    /// <summary>
    /// Starts all watchers and enables them. Can be called externally (e.g., from tray resume).
    /// </summary>
    public async Task StartAllWatchersAsync()
    {
        if (_folderWatcherManager == null || _watchedFolderService == null) return;

        // Take a snapshot of folders to process (collection may be modified by status change events)
        var foldersToStart = WatchedFolders.Where(f => f.Status != WatchStatus.Error).ToList();

        // Enable and start all folders that aren't in error state
        foreach (var folder in foldersToStart)
        {
            if (!folder.IsEnabled)
            {
                folder.IsEnabled = true;
                await _watchedFolderService.UpdateWatchedFolderAsync(folder);
            }

            if (folder.Status != WatchStatus.Watching)
            {
                await _folderWatcherManager.StartWatchingAsync(folder);
            }
        }

        LoadWatchedFolders();
    }

    private async void StopAllButton_Click(object sender, RoutedEventArgs e)
    {
        await StopAllWatchersAsync();
    }

    /// <summary>
    /// Stops all watchers and disables them. Can be called externally (e.g., from tray pause).
    /// </summary>
    public async Task StopAllWatchersAsync()
    {
        if (_folderWatcherManager == null || _watchedFolderService == null) return;

        // Take a snapshot of folders to process (collection may be modified by status change events)
        var foldersToStop = WatchedFolders.Where(f => f.IsEnabled).ToList();

        // Stop all watchers and disable them
        foreach (var folder in foldersToStop)
        {
            _folderWatcherManager.StopWatching(folder.Id);
            folder.IsEnabled = false;
            await _watchedFolderService.UpdateWatchedFolderAsync(folder);
        }

        LoadWatchedFolders();
    }

    private void DismissBannerButton_Click(object sender, RoutedEventArgs e)
    {
        InfoBanner.Visibility = Visibility.Collapsed;
    }

    private void OnWatcherStatusChanged(object? sender, WatcherStatusChangedEventArgs e)
    {
        // Update UI on dispatcher thread - already dispatched by FolderWatcherManager
        try
        {
            if (!_isInitialized) return;

            var folder = WatchedFolders.FirstOrDefault(f => f.Id == e.WatchedFolderId);
            if (folder != null)
            {
                folder.Status = e.NewStatus;
                folder.LastError = e.ErrorMessage;
                LoadWatchedFolders();
            }
        }
        catch
        {
            // Ignore errors if control is being unloaded
        }
    }

    private void OnOrganizationCompleted(object? sender, OrganizationCompletedEventArgs e)
    {
        // Update UI - already dispatched by FolderWatcherManager
        try
        {
            if (!_isInitialized) return;
            LoadWatchedFolders();
        }
        catch
        {
            // Ignore errors if control is being unloaded
        }
    }

    private async Task ShowErrorDialogAsync(string title, string message)
    {
        var dialog = new ContentDialog
        {
            Title = title,
            Content = message,
            CloseButtonText = "OK",
            XamlRoot = this.XamlRoot
        };
        await dialog.ShowAsync();
    }

    private async Task ShowInfoDialogAsync(string title, string message)
    {
        var dialog = new ContentDialog
        {
            Title = title,
            Content = message,
            CloseButtonText = "OK",
            XamlRoot = this.XamlRoot
        };
        await dialog.ShowAsync();
    }

    private async Task<bool> ShowConfirmDialogAsync(string title, string message, string confirmText, string cancelText)
    {
        var dialog = new ContentDialog
        {
            Title = title,
            Content = message,
            PrimaryButtonText = confirmText,
            CloseButtonText = cancelText,
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = this.XamlRoot
        };

        var result = await dialog.ShowAsync();
        return result == ContentDialogResult.Primary;
    }
}
