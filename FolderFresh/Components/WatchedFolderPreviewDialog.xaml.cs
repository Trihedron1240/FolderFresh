using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using FolderFresh.Models;
using FolderFresh.Services;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.UI;

namespace FolderFresh.Components;

/// <summary>
/// Dialog for previewing and executing organization for a watched folder.
/// </summary>
public sealed partial class WatchedFolderPreviewDialog : ContentDialog
{
    private readonly WatchedFolder _folder;
    private readonly OrganizationResult _previewResult;
    private readonly FolderWatcherManager _folderWatcherManager;
    private readonly WatchedFolderService _watchedFolderService;
    private bool _isOrganizing;
    private OrganizationResult? _organizationResult;

    /// <summary>
    /// Gets the result of the organization operation (null if cancelled or preview only).
    /// </summary>
    public OrganizationResult? OrganizationResult => _organizationResult;

    /// <summary>
    /// Gets whether organization was executed.
    /// </summary>
    public bool WasOrganized { get; private set; }

    public WatchedFolderPreviewDialog(
        WatchedFolder folder,
        OrganizationResult previewResult,
        FolderWatcherManager folderWatcherManager,
        WatchedFolderService watchedFolderService)
    {
        this.InitializeComponent();

        _folder = folder;
        _previewResult = previewResult;
        _folderWatcherManager = folderWatcherManager;
        _watchedFolderService = watchedFolderService;

        ApplyLocalization();
        PopulateDialog();
    }

    private void ApplyLocalization()
    {
        Title = Loc.Get("Preview_Title");
        PrimaryButtonText = Loc.Get("Preview_OrganizeNow");
        CloseButtonText = Loc.Get("Cancel");
        ScannedLabel.Text = Loc.Get("Preview_Scanned");
        ToOrganizeLabel.Text = Loc.Get("Preview_ToOrganize");
        AlreadyDoneLabel.Text = Loc.Get("Preview_AlreadyDone");
        IgnoredLabel.Text = Loc.Get("Preview_Ignored");
        ProgressText.Text = Loc.Get("Preview_OrganizingFiles");
    }

    private void PopulateDialog()
    {
        // Header info
        FolderNameText.Text = _folder.DisplayName;
        FolderPathText.Text = _folder.FolderPath;
        ProfileText.Text = string.Format(Loc.Get("Preview_UsingProfile"), _folder.ProfileName ?? "Unknown");

        // Summary stats
        TotalScannedText.Text = _previewResult.TotalFilesScanned.ToString();
        ToOrganizeText.Text = _previewResult.FilesWouldMove.ToString();

        // Already Done = files that matched but are already in correct location (excluding ignored by rule)
        var alreadyDone = _previewResult.PreviewResults.Count(r =>
            !r.WillBeOrganized &&
            r.MatchedBy != OrganizeMatchType.None &&
            !r.IsIgnoredByRule);
        AlreadyDoneText.Text = alreadyDone.ToString();

        // Ignored = files with no match OR explicitly ignored by a rule
        var ignored = _previewResult.PreviewResults.Count(r => r.MatchedBy == OrganizeMatchType.None || r.IsIgnoredByRule);
        IgnoredText.Text = ignored.ToString();

        // Warnings
        if (_previewResult.Errors.Count > 0)
        {
            WarningsPanel.Visibility = Visibility.Visible;
            WarningsText.Text = string.Join("; ", _previewResult.Errors.Take(3));
            if (_previewResult.Errors.Count > 3)
            {
                WarningsText.Text += $" (+{_previewResult.Errors.Count - 3} more)";
            }
        }

        // Disable organize button if nothing to organize
        IsPrimaryButtonEnabled = _previewResult.FilesWouldMove > 0;

        // Build destination groups
        BuildDestinationGroups();
    }

    private void BuildDestinationGroups()
    {
        DestinationGroupsPanel.Children.Clear();

        var filesToOrganize = _previewResult.PreviewResults
            .Where(r => r.WillBeOrganized)
            .ToList();

        if (filesToOrganize.Count == 0)
        {
            var emptyMessage = new TextBlock
            {
                Text = Loc.Get("Preview_NoFilesToOrganize"),
                FontSize = 13,
                Foreground = new SolidColorBrush(Color.FromArgb(255, 136, 136, 136)),
                TextWrapping = TextWrapping.Wrap,
                HorizontalAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 24, 0, 24)
            };
            DestinationGroupsPanel.Children.Add(emptyMessage);
            return;
        }

        // Group by destination folder
        var groups = filesToOrganize
            .GroupBy(r => GetDestinationFolder(r))
            .OrderByDescending(g => g.Count())
            .ToList();

        foreach (var group in groups)
        {
            var groupPanel = BuildGroupExpander(group.Key, group.ToList());
            DestinationGroupsPanel.Children.Add(groupPanel);
        }

        // Show ignored files section if any (both unmatched and explicitly ignored by rule)
        var ignoredFiles = _previewResult.PreviewResults
            .Where(r => r.MatchedBy == OrganizeMatchType.None || r.IsIgnoredByRule)
            .ToList();

        if (ignoredFiles.Count > 0)
        {
            var label = ignoredFiles.Any(r => r.IsIgnoredByRule)
                ? Loc.Get("Preview_IgnoredStaysInPlace")
                : Loc.Get("Preview_NoMatchStaysInPlace");
            var ignoredGroup = BuildGroupExpander(label, ignoredFiles, isIgnored: true);
            DestinationGroupsPanel.Children.Add(ignoredGroup);
        }
    }

    private static string GetDestinationFolder(FileOrganizeResult result)
    {
        if (result.DestinationPath == null)
            return "[Unknown]";

        var folder = Path.GetDirectoryName(result.DestinationPath);
        if (string.IsNullOrEmpty(folder))
            return "[Root]";

        // Get just the folder name, not full path
        return Path.GetFileName(folder) ?? folder;
    }

    private Border BuildGroupExpander(string folderName, List<FileOrganizeResult> files, bool isIgnored = false)
    {
        var border = new Border
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 45, 45, 45)),
            CornerRadius = new CornerRadius(6),
            Padding = new Thickness(12)
        };

        var mainPanel = new StackPanel { Spacing = 8 };

        // Header with folder name and count
        var headerPanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };

        var folderIcon = new FontIcon
        {
            Glyph = isIgnored ? "\uE8D7" : "\uE8B7",
            FontSize = 16,
            Foreground = new SolidColorBrush(isIgnored
                ? Color.FromArgb(255, 245, 158, 11)
                : Color.FromArgb(255, 96, 205, 255))
        };
        headerPanel.Children.Add(folderIcon);

        var folderNameText = new TextBlock
        {
            Text = folderName,
            FontSize = 13,
            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 255, 255, 255)),
            VerticalAlignment = VerticalAlignment.Center
        };
        headerPanel.Children.Add(folderNameText);

        var countBadge = new Border
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 55, 55, 55)),
            CornerRadius = new CornerRadius(4),
            Padding = new Thickness(6, 2, 6, 2),
            VerticalAlignment = VerticalAlignment.Center
        };
        countBadge.Child = new TextBlock
        {
            Text = string.Format(Loc.Get("Preview_Files"), files.Count),
            FontSize = 11,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 153, 153, 153))
        };
        headerPanel.Children.Add(countBadge);

        mainPanel.Children.Add(headerPanel);

        // File list (show first 5)
        var fileListPanel = new StackPanel { Spacing = 4, Margin = new Thickness(24, 4, 0, 0) };

        var displayFiles = files.Take(5).ToList();
        foreach (var file in displayFiles)
        {
            var filePanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 6 };

            var fileIcon = new FontIcon
            {
                Glyph = "\uE8A5",
                FontSize = 10,
                Foreground = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102))
            };
            filePanel.Children.Add(fileIcon);

            var fileName = new TextBlock
            {
                Text = file.FileName,
                FontSize = 12,
                Foreground = new SolidColorBrush(Color.FromArgb(255, 180, 180, 180)),
                TextTrimming = TextTrimming.CharacterEllipsis,
                MaxWidth = 350
            };
            filePanel.Children.Add(fileName);

            // Show match type
            if (!isIgnored)
            {
                var matchType = file.MatchedBy == OrganizeMatchType.Rule
                    ? file.MatchedRuleName ?? "Rule"
                    : file.MatchedCategoryName ?? "Category";

                var matchBadge = new TextBlock
                {
                    Text = $"({matchType})",
                    FontSize = 10,
                    Foreground = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102))
                };
                filePanel.Children.Add(matchBadge);
            }

            fileListPanel.Children.Add(filePanel);
        }

        // "More" indicator
        if (files.Count > 5)
        {
            var moreText = new TextBlock
            {
                Text = string.Format(Loc.Get("Preview_MoreFiles"), files.Count - 5),
                FontSize = 11,
                Foreground = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102)),
                FontStyle = Windows.UI.Text.FontStyle.Italic,
                Margin = new Thickness(0, 4, 0, 0)
            };
            fileListPanel.Children.Add(moreText);
        }

        mainPanel.Children.Add(fileListPanel);
        border.Child = mainPanel;
        return border;
    }

    private async void OrganizeButton_Click(ContentDialog sender, ContentDialogButtonClickEventArgs args)
    {
        // Prevent dialog from closing
        args.Cancel = true;

        if (_isOrganizing) return;
        _isOrganizing = true;

        // Show progress overlay
        ProgressOverlay.Visibility = Visibility.Visible;
        IsPrimaryButtonEnabled = false;
        IsSecondaryButtonEnabled = false;

        try
        {
            // Create progress reporter
            var progress = new Progress<OrganizationProgress>(p =>
            {
                DispatcherQueue.TryEnqueue(() =>
                {
                    ProgressDetailText.Text = string.Format(Loc.Get("Preview_FilesProgress"), p.CurrentFile, p.TotalFiles);
                    if (!string.IsNullOrEmpty(p.CurrentFileName))
                    {
                        ProgressText.Text = string.Format(Loc.Get("Preview_Organizing"), p.CurrentFileName);
                    }
                });
            });

            // Execute organization
            _organizationResult = await _folderWatcherManager.OrganizeFolderAsync(_folder.Id, previewOnly: false);
            WasOrganized = true;

            // Hide dialog
            Hide();
        }
        catch (Exception ex)
        {
            // Show error
            ProgressOverlay.Visibility = Visibility.Collapsed;
            WarningsPanel.Visibility = Visibility.Visible;
            WarningsText.Text = string.Format(Loc.Get("Preview_OrganizationFailed"), ex.Message);
            IsPrimaryButtonEnabled = false;
            IsSecondaryButtonEnabled = true;
            _isOrganizing = false;
        }
    }
}

/// <summary>
/// Progress information for organization operation.
/// </summary>
public class OrganizationProgress
{
    public int CurrentFile { get; set; }
    public int TotalFiles { get; set; }
    public string? CurrentFileName { get; set; }
    public string? CurrentAction { get; set; }
}
