using System;
using System.Diagnostics;
using System.Threading.Tasks;
using FolderFresh.Models;
using FolderFresh.Services;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.Storage.Pickers;

namespace FolderFresh.Components;

public sealed partial class SnapshotsContent : UserControl
{
    private readonly SnapshotService _snapshotService;
    private bool _bannerDismissed;

    public SnapshotsContent()
    {
        this.InitializeComponent();
        _snapshotService = App.GetService<SnapshotService>();
        ApplyLocalization();
        LocalizationService.Instance.LanguageChanged += (s, e) => DispatcherQueue.TryEnqueue(ApplyLocalization);
    }

    private void ApplyLocalization()
    {
        TitleText.Text = Loc.Get("Snapshots_Title");
        SubtitleText.Text = Loc.Get("Snapshots_Subtitle");
        NewSnapshotButtonText.Text = Loc.Get("Snapshots_NewSnapshot");
        InfoBannerText.Text = Loc.Get("Snapshots_InfoBanner");
        StorageUsedLabel.Text = Loc.Get("Snapshots_StorageUsed");
        OpenFolderButtonText.Text = Loc.Get("Snapshots_OpenFolder");
        EmptyTitleText.Text = Loc.Get("Snapshots_EmptyTitle");
        EmptyDescText.Text = Loc.Get("Snapshots_EmptyDesc");
        CreateSnapshotButtonText.Text = Loc.Get("Snapshots_CreateSnapshot");
    }

    private async void UserControl_Loaded(object sender, RoutedEventArgs e)
    {
        await LoadSnapshotsAsync();
    }

    private async Task LoadSnapshotsAsync()
    {
        await _snapshotService.LoadSnapshotsAsync();
        RefreshSnapshotsList();
        UpdateStorageInfo();
    }

    private void RefreshSnapshotsList()
    {
        SnapshotsListPanel.Children.Clear();

        var snapshots = _snapshotService.GetSnapshots();

        if (snapshots.Count == 0)
        {
            EmptyState.Visibility = Visibility.Visible;
            SnapshotsScrollViewer.Visibility = Visibility.Collapsed;
            return;
        }

        EmptyState.Visibility = Visibility.Collapsed;
        SnapshotsScrollViewer.Visibility = Visibility.Visible;

        foreach (var snapshot in snapshots)
        {
            var card = CreateSnapshotCard(snapshot);
            SnapshotsListPanel.Children.Add(card);
        }
    }

    private void UpdateStorageInfo()
    {
        var snapshots = _snapshotService.GetSnapshots();
        StorageUsedText.Text = _snapshotService.GetFormattedTotalStorage();
        SnapshotCountText.Text = Loc.Get("Snapshots_AcrossSnapshots", snapshots.Count);
    }

    private Border CreateSnapshotCard(FolderSnapshot snapshot)
    {
        var card = new Border
        {
            Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 30, 31, 34)),
            CornerRadius = new CornerRadius(12),
            Padding = new Thickness(16),
            BorderBrush = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 43, 45, 49)),
            BorderThickness = new Thickness(1),
            Tag = snapshot.Id
        };

        var mainGrid = new Grid();
        mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        // Left content
        var leftPanel = new StackPanel { Spacing = 4 };

        // Snapshot name
        var nameText = new TextBlock
        {
            Text = snapshot.Name,
            FontSize = 15,
            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 255, 255))
        };
        leftPanel.Children.Add(nameText);

        // Folder path
        var pathText = new TextBlock
        {
            Text = snapshot.FolderPath,
            FontSize = 12,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 148, 155, 164)),
            TextTrimming = TextTrimming.CharacterEllipsis,
            MaxWidth = 400
        };
        leftPanel.Children.Add(pathText);

        // Meta info (date, file count, size)
        var metaPanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 16, Margin = new Thickness(0, 8, 0, 0) };

        var dateText = new TextBlock
        {
            Text = snapshot.CreatedAt.ToString("MMM d, yyyy 'at' h:mm tt"),
            FontSize = 12,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 102, 102, 102))
        };
        metaPanel.Children.Add(dateText);

        var separator1 = new TextBlock
        {
            Text = "\u2022",
            FontSize = 12,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 68, 68, 68))
        };
        metaPanel.Children.Add(separator1);

        var fileCountText = new TextBlock
        {
            Text = snapshot.FileCount == 1 ? Loc.Get("Snapshots_OneFile") : Loc.Get("Snapshots_Files", snapshot.FileCount.ToString("N0")),
            FontSize = 12,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 102, 102, 102))
        };
        metaPanel.Children.Add(fileCountText);

        var separator2 = new TextBlock
        {
            Text = "\u2022",
            FontSize = 12,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 68, 68, 68))
        };
        metaPanel.Children.Add(separator2);

        var sizeText = new TextBlock
        {
            Text = snapshot.FormattedSize,
            FontSize = 12,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 102, 102, 102))
        };
        metaPanel.Children.Add(sizeText);

        leftPanel.Children.Add(metaPanel);

        Grid.SetColumn(leftPanel, 0);
        mainGrid.Children.Add(leftPanel);

        // Right content - action buttons
        var buttonsPanel = new StackPanel
        {
            Orientation = Orientation.Horizontal,
            Spacing = 8,
            VerticalAlignment = VerticalAlignment.Center
        };

        // Restore button
        var restoreButton = new Button
        {
            Content = Loc.Get("Snapshots_Restore"),
            Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 88, 101, 242)),
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 255, 255)),
            Padding = new Thickness(12, 6, 12, 6),
            CornerRadius = new CornerRadius(6),
            Tag = snapshot.Id
        };
        restoreButton.Click += RestoreButton_Click;
        buttonsPanel.Children.Add(restoreButton);

        // Rename button
        var renameButton = new Button
        {
            Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 45, 45, 45)),
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 181, 186, 193)),
            Padding = new Thickness(8, 6, 8, 6),
            CornerRadius = new CornerRadius(6),
            Tag = snapshot.Id,
            Content = new FontIcon
            {
                Glyph = "\uE8AC",
                FontSize = 14
            }
        };
        ToolTipService.SetToolTip(renameButton, Loc.Get("Profiles_Rename"));
        renameButton.Click += RenameButton_Click;
        buttonsPanel.Children.Add(renameButton);

        // Delete button
        var deleteButton = new Button
        {
            Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 45, 45, 45)),
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 181, 186, 193)),
            Padding = new Thickness(8, 6, 8, 6),
            CornerRadius = new CornerRadius(6),
            Tag = snapshot.Id,
            Content = new FontIcon
            {
                Glyph = "\uE74D",
                FontSize = 14
            }
        };
        ToolTipService.SetToolTip(deleteButton, Loc.Get("Delete"));
        deleteButton.Click += DeleteButton_Click;
        buttonsPanel.Children.Add(deleteButton);

        Grid.SetColumn(buttonsPanel, 1);
        mainGrid.Children.Add(buttonsPanel);

        card.Child = mainGrid;
        return card;
    }

    private async void NewSnapshotButton_Click(object sender, RoutedEventArgs e)
    {
        // Show folder picker
        var picker = new FolderPicker();
        picker.SuggestedStartLocation = PickerLocationId.DocumentsLibrary;
        picker.FileTypeFilter.Add("*");

        // Get the window handle
        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var folder = await picker.PickSingleFolderAsync();
        if (folder == null)
        {
            return;
        }

        // Show name input dialog
        var dialog = new ContentDialog
        {
            Title = Loc.Get("Snapshots_CreateSnapshot"),
            PrimaryButtonText = Loc.Get("Snapshots_Create"),
            CloseButtonText = Loc.Get("Cancel"),
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = this.XamlRoot
        };

        var dialogContent = new StackPanel { Spacing = 16 };

        var folderInfo = new StackPanel { Spacing = 4 };
        folderInfo.Children.Add(new TextBlock
        {
            Text = Loc.Get("Snapshots_FolderToSnapshot"),
            FontSize = 13,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 148, 155, 164))
        });
        folderInfo.Children.Add(new TextBlock
        {
            Text = folder.Path,
            FontSize = 13,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 255, 255)),
            TextWrapping = TextWrapping.Wrap
        });
        dialogContent.Children.Add(folderInfo);

        var nameBox = new TextBox
        {
            Header = Loc.Get("Snapshots_SnapshotName"),
            PlaceholderText = Loc.Get("Snapshots_SnapshotNamePlaceholder"),
            Text = $"{folder.Name} - {DateTime.Now:MMM d, yyyy}"
        };
        dialogContent.Children.Add(nameBox);

        var warningBanner = new Border
        {
            Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 50, 45, 35)),
            CornerRadius = new CornerRadius(6),
            Padding = new Thickness(12),
            Margin = new Thickness(0, 8, 0, 0)
        };
        var warningContent = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10 };
        warningContent.Children.Add(new FontIcon
        {
            Glyph = "\uE7BA",
            FontSize = 14,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 240, 160, 32))
        });
        warningContent.Children.Add(new TextBlock
        {
            Text = Loc.Get("Snapshots_Warning"),
            FontSize = 12,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 180, 160, 120)),
            TextWrapping = TextWrapping.Wrap,
            MaxWidth = 300
        });
        warningBanner.Child = warningContent;
        dialogContent.Children.Add(warningBanner);

        dialog.Content = dialogContent;

        var result = await dialog.ShowAsync();

        if (result == ContentDialogResult.Primary && !string.IsNullOrWhiteSpace(nameBox.Text))
        {
            await CreateSnapshotWithProgressAsync(nameBox.Text.Trim(), folder.Path);
        }
    }

    private async Task CreateSnapshotWithProgressAsync(string name, string folderPath)
    {
        // Show progress dialog
        var progressDialog = new ContentDialog
        {
            Title = Loc.Get("Snapshots_Creating"),
            XamlRoot = this.XamlRoot
        };

        var progressContent = new StackPanel { Spacing = 12 };
        var progressBar = new ProgressBar
        {
            IsIndeterminate = false,
            Value = 0,
            Maximum = 100,
            Width = 300
        };
        progressContent.Children.Add(new TextBlock
        {
            Text = Loc.Get("Snapshots_CopyingFiles"),
            FontSize = 13,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 148, 155, 164))
        });
        progressContent.Children.Add(progressBar);
        progressDialog.Content = progressContent;

        // Start showing dialog (don't await it)
        var dialogTask = progressDialog.ShowAsync();

        try
        {
            var progress = new Progress<int>(value =>
            {
                progressBar.Value = value;
            });

            await _snapshotService.CreateSnapshotAsync(name, folderPath, includeSubfolders: true, progress);

            progressDialog.Hide();
            RefreshSnapshotsList();
            UpdateStorageInfo();

            // Show success notification
            await ShowMessageAsync(Loc.Get("Snapshots_Created"), Loc.Get("Snapshots_CreatedMsg", name));
        }
        catch (Exception ex)
        {
            progressDialog.Hide();
            await ShowMessageAsync(Loc.Get("Snapshots_Error"), Loc.Get("Snapshots_FailedToCreate", ex.Message));
        }
    }

    private async void RestoreButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.Tag is string snapshotId)
        {
            var snapshot = _snapshotService.GetSnapshot(snapshotId);
            if (snapshot == null) return;

            // Show warning dialog
            var dialog = new ContentDialog
            {
                Title = Loc.Get("Snapshots_RestoreDialog"),
                PrimaryButtonText = Loc.Get("Snapshots_Restore"),
                CloseButtonText = Loc.Get("Cancel"),
                DefaultButton = ContentDialogButton.Close,
                XamlRoot = this.XamlRoot
            };

            var content = new StackPanel { Spacing = 12 };

            var warningBanner = new Border
            {
                Background = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 60, 40, 40)),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(12)
            };
            var warningPanel = new StackPanel { Spacing = 8 };
            var warningHeader = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
            warningHeader.Children.Add(new FontIcon
            {
                Glyph = "\uE7BA",
                FontSize = 16,
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 240, 100, 100))
            });
            warningHeader.Children.Add(new TextBlock
            {
                Text = Loc.Get("Snapshots_RestoreWarning"),
                FontSize = 14,
                FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 240, 100, 100))
            });
            warningPanel.Children.Add(warningHeader);
            warningPanel.Children.Add(new TextBlock
            {
                Text = Loc.Get("Snapshots_RestoreWarningMsg"),
                FontSize = 13,
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 200, 150, 150)),
                TextWrapping = TextWrapping.Wrap,
                MaxWidth = 350
            });
            warningBanner.Child = warningPanel;
            content.Children.Add(warningBanner);

            content.Children.Add(new TextBlock
            {
                Text = Loc.Get("Snapshots_RestoreTo", snapshot.Name),
                FontSize = 13,
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 181, 186, 193))
            });
            content.Children.Add(new TextBlock
            {
                Text = snapshot.FolderPath,
                FontSize = 13,
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 255, 255, 255)),
                TextWrapping = TextWrapping.Wrap
            });

            var infoPanel = new StackPanel { Spacing = 4, Margin = new Thickness(0, 8, 0, 0) };
            infoPanel.Children.Add(new TextBlock
            {
                Text = Loc.Get("Snapshots_FilesToRestore", snapshot.FileCount.ToString("N0")),
                FontSize = 12,
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 102, 102, 102))
            });
            infoPanel.Children.Add(new TextBlock
            {
                Text = Loc.Get("Snapshots_SnapshotCreatedAt", snapshot.CreatedAt.ToString("MMM d, yyyy 'at' h:mm tt")),
                FontSize = 12,
                Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 102, 102, 102))
            });
            content.Children.Add(infoPanel);

            dialog.Content = content;

            var result = await dialog.ShowAsync();

            if (result == ContentDialogResult.Primary)
            {
                await RestoreSnapshotWithProgressAsync(snapshotId);
            }
        }
    }

    private async Task RestoreSnapshotWithProgressAsync(string snapshotId)
    {
        var snapshot = _snapshotService.GetSnapshot(snapshotId);
        if (snapshot == null) return;

        // Show progress dialog
        var progressDialog = new ContentDialog
        {
            Title = Loc.Get("Snapshots_Restoring"),
            XamlRoot = this.XamlRoot
        };

        var progressContent = new StackPanel { Spacing = 12 };
        var progressBar = new ProgressBar
        {
            IsIndeterminate = false,
            Value = 0,
            Maximum = 100,
            Width = 300
        };
        progressContent.Children.Add(new TextBlock
        {
            Text = Loc.Get("Snapshots_RestoringFiles"),
            FontSize = 13,
            Foreground = new SolidColorBrush(Windows.UI.Color.FromArgb(255, 148, 155, 164))
        });
        progressContent.Children.Add(progressBar);
        progressDialog.Content = progressContent;

        var dialogTask = progressDialog.ShowAsync();

        try
        {
            var progress = new Progress<int>(value =>
            {
                progressBar.Value = value;
            });

            var restoredCount = await _snapshotService.RestoreSnapshotAsync(snapshotId, progress);

            progressDialog.Hide();

            await ShowMessageAsync(Loc.Get("Snapshots_RestoreComplete"), Loc.Get("Snapshots_RestoreCompleteMsg", restoredCount.ToString("N0")));
        }
        catch (Exception ex)
        {
            progressDialog.Hide();
            await ShowMessageAsync(Loc.Get("Snapshots_Error"), Loc.Get("Snapshots_FailedToRestore", ex.Message));
        }
    }

    private async void RenameButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.Tag is string snapshotId)
        {
            var snapshot = _snapshotService.GetSnapshot(snapshotId);
            if (snapshot == null) return;

            var dialog = new ContentDialog
            {
                Title = Loc.Get("Snapshots_RenameDialog"),
                PrimaryButtonText = Loc.Get("Profiles_Rename"),
                CloseButtonText = Loc.Get("Cancel"),
                DefaultButton = ContentDialogButton.Primary,
                XamlRoot = this.XamlRoot
            };

            var nameBox = new TextBox
            {
                Text = snapshot.Name,
                PlaceholderText = Loc.Get("Snapshots_RenameNamePlaceholder")
            };
            nameBox.SelectAll();

            dialog.Content = nameBox;

            var result = await dialog.ShowAsync();

            if (result == ContentDialogResult.Primary && !string.IsNullOrWhiteSpace(nameBox.Text))
            {
                await _snapshotService.RenameSnapshotAsync(snapshotId, nameBox.Text.Trim());
                RefreshSnapshotsList();
            }
        }
    }

    private async void DeleteButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.Tag is string snapshotId)
        {
            var snapshot = _snapshotService.GetSnapshot(snapshotId);
            if (snapshot == null) return;

            var dialog = new ContentDialog
            {
                Title = Loc.Get("Snapshots_DeleteDialog"),
                Content = Loc.Get("Snapshots_DeleteConfirm", snapshot.Name, snapshot.FormattedSize),
                PrimaryButtonText = Loc.Get("Delete"),
                CloseButtonText = Loc.Get("Cancel"),
                DefaultButton = ContentDialogButton.Close,
                XamlRoot = this.XamlRoot
            };

            var result = await dialog.ShowAsync();

            if (result == ContentDialogResult.Primary)
            {
                await _snapshotService.DeleteSnapshotAsync(snapshotId);
                RefreshSnapshotsList();
                UpdateStorageInfo();
            }
        }
    }

    private void DismissBannerButton_Click(object sender, RoutedEventArgs e)
    {
        InfoBanner.Visibility = Visibility.Collapsed;
        _bannerDismissed = true;
    }

    private void OpenFolderButton_Click(object sender, RoutedEventArgs e)
    {
        var path = _snapshotService.GetSnapshotsBasePath();
        if (System.IO.Directory.Exists(path))
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = path,
                UseShellExecute = true
            });
        }
    }

    private async Task ShowMessageAsync(string title, string message)
    {
        var dialog = new ContentDialog
        {
            Title = title,
            Content = message,
            CloseButtonText = Loc.Get("OK"),
            XamlRoot = this.XamlRoot
        };
        await dialog.ShowAsync();
    }
}
