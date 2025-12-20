using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Windows.Storage;
using Windows.Storage.Pickers;
using Windows.UI;
using FolderFreshLite.Models;
using FolderFreshLite.Helpers;
using FolderFreshLite.Components;
using FolderFreshLite.Services;

namespace FolderFreshLite;

public sealed partial class MainPage : Page
{
    private StorageFolder? _selectedFolder;
    private StorageFolder? _rootFolder; // The originally selected folder (for ".." navigation)
    private OrganizePreview? _organizePreview;
    private Dictionary<string, OrganizedFolder>? _organizedPreview; // Legacy, kept for compatibility
    private string? _lastOrganizedPath;
    private Stack<StorageFolder> _navigationHistory = new();
    private readonly CategoryService _categoryService;
    private readonly RuleService _ruleService;
    private readonly SettingsService _settingsService;

    // After panel navigation state
    private string? _afterCurrentPath; // null = root (show folders), otherwise show files in that group

    // Undo tracking - stores the last organize operation's file moves
    private List<MoveOperation>? _lastMoveOperations;

    // File system watcher for real-time folder monitoring
    private FileSystemWatcher? _folderWatcher;
    private CancellationTokenSource? _debounceTokenSource;
    private const int DebounceDelayMs = 300;

    // Prevent concurrent organize/undo operations
    private bool _isOperationInProgress;

    public ObservableCollection<FileItem> CurrentFiles { get; } = new();
    public ObservableCollection<FileItem> AfterFiles { get; } = new();
    public ObservableCollection<FileItem> SelectedFiles { get; } = new();

    public MainPage()
    {
        this.InitializeComponent();
        _categoryService = new CategoryService();
        _ruleService = new RuleService();
        _settingsService = new SettingsService();
        CurrentFilesPanel.ItemsSource = CurrentFiles;
        AfterFilesPanel.ItemsSource = AfterFiles;

        // Load services on startup
        _ = InitializeServicesAsync();
    }

    private async Task InitializeServicesAsync()
    {
        await _categoryService.LoadCategoriesAsync();
        await _ruleService.LoadRulesAsync();
        await _settingsService.LoadSettingsAsync();
    }

    private void NavView_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        if (args.SelectedItemContainer is NavigationViewItem item)
        {
            var tag = item.Tag?.ToString();

            switch (tag)
            {
                case "home":
                    HomeContent.Visibility = Visibility.Visible;
                    ContentFrame.Visibility = Visibility.Collapsed;
                    // Refresh panels when returning to home
                    _ = RefreshPanelsAsync();
                    break;
                case "folders":
                    ShowPlaceholder("Folders", "Manage watched folders");
                    break;
                case "rules":
                    ShowRulesContent();
                    break;
                case "categories":
                    ShowCategoriesContent();
                    break;
                case "profiles":
                    ShowPlaceholder("Profiles", "Save and load organization profiles");
                    break;
                case "settings":
                    ShowSettingsContent();
                    break;
            }
        }
    }

    private void ShowPlaceholder(string title, string description)
    {
        HomeContent.Visibility = Visibility.Collapsed;
        ContentFrame.Visibility = Visibility.Visible;

        ContentFrame.Content = new Grid
        {
            Children =
            {
                new StackPanel
                {
                    VerticalAlignment = VerticalAlignment.Center,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Spacing = 8,
                    Children =
                    {
                        new TextBlock
                        {
                            Text = title,
                            FontSize = 24,
                            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
                            Foreground = new SolidColorBrush(Microsoft.UI.Colors.White),
                            HorizontalAlignment = HorizontalAlignment.Center
                        },
                        new TextBlock
                        {
                            Text = description,
                            FontSize = 14,
                            Foreground = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102)),
                            HorizontalAlignment = HorizontalAlignment.Center
                        },
                        new TextBlock
                        {
                            Text = "Coming soon",
                            FontSize = 12,
                            Foreground = new SolidColorBrush(Color.FromArgb(255, 77, 77, 77)),
                            HorizontalAlignment = HorizontalAlignment.Center,
                            Margin = new Thickness(0, 16, 0, 0)
                        }
                    }
                }
            }
        };
    }

    private CategoriesContent? _categoriesContent;
    private RulesContent? _rulesContent;
    private SettingsContent? _settingsContent;

    private void ShowRulesContent()
    {
        HomeContent.Visibility = Visibility.Collapsed;
        ContentFrame.Visibility = Visibility.Visible;

        if (_rulesContent == null)
        {
            _rulesContent = new RulesContent();
            _rulesContent.NewRuleRequested += RulesContent_NewRuleRequested;
            _rulesContent.EditRuleRequested += RulesContent_EditRuleRequested;
        }

        // Update match counts based on selected folder
        _rulesContent.SetSelectedFolder(_selectedFolder?.Path);

        ContentFrame.Content = _rulesContent;
    }

    private RuleEditorPanel? _ruleEditorPanel;

    private void RulesContent_NewRuleRequested(object? sender, Models.Rule rule)
    {
        ShowRuleEditor(null);
    }

    private void RulesContent_EditRuleRequested(object? sender, Models.Rule rule)
    {
        ShowRuleEditor(rule);
    }

    private void ShowRuleEditor(Models.Rule? rule)
    {
        if (_ruleEditorPanel == null)
        {
            _ruleEditorPanel = new RuleEditorPanel();
            _ruleEditorPanel.SaveRequested += RuleEditorPanel_SaveRequested;
            _ruleEditorPanel.CloseRequested += RuleEditorPanel_CloseRequested;
        }

        _ruleEditorPanel.SetRule(rule);
        ContentFrame.Content = _ruleEditorPanel;
    }

    private async void RuleEditorPanel_SaveRequested(object? sender, Models.Rule rule)
    {
        if (_rulesContent != null)
        {
            if (_ruleEditorPanel?.IsNewRule == true)
            {
                await _rulesContent.AddRuleAsync(rule);
            }
            else
            {
                await _rulesContent.UpdateRuleAsync(rule);
            }
        }

        // Go back to rules list
        ShowRulesContent();
    }

    private void RuleEditorPanel_CloseRequested(object? sender, EventArgs e)
    {
        // Go back to rules list
        ShowRulesContent();
    }

    private void ShowCategoriesContent()
    {
        HomeContent.Visibility = Visibility.Collapsed;
        ContentFrame.Visibility = Visibility.Visible;

        if (_categoriesContent == null)
        {
            _categoriesContent = new CategoriesContent();
            _categoriesContent.NewCategoryRequested += CategoriesContent_NewCategoryRequested;
            _categoriesContent.CategoryEditRequested += CategoriesContent_CategoryEditRequested;
            _categoriesContent.CategoryDeleteRequested += CategoriesContent_CategoryDeleteRequested;
        }

        ContentFrame.Content = _categoriesContent;
    }

    private void CategoriesContent_NewCategoryRequested(object? sender, EventArgs e)
    {
        // Form panel handles this internally now
    }

    private void CategoriesContent_CategoryEditRequested(object? sender, Category category)
    {
        // Form panel handles this internally now
    }

    private void CategoriesContent_CategoryDeleteRequested(object? sender, Category category)
    {
        // Deletion handled internally now
    }

    private void ShowSettingsContent()
    {
        HomeContent.Visibility = Visibility.Collapsed;
        ContentFrame.Visibility = Visibility.Visible;

        if (_settingsContent == null)
        {
            _settingsContent = new SettingsContent();
        }

        ContentFrame.Content = _settingsContent;
    }

    private async void FolderSelector_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FolderPicker
        {
            SuggestedStartLocation = PickerLocationId.Desktop,
            ViewMode = PickerViewMode.List
        };
        picker.FileTypeFilter.Add("*");

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        _selectedFolder = await picker.PickSingleFolderAsync();

        if (_selectedFolder != null)
        {
            _rootFolder = _selectedFolder; // Store as root folder
            FolderPathText.Text = TruncatePath(_selectedFolder.Path, 30);
            _navigationHistory.Clear();

            // Setup real-time folder monitoring
            SetupFolderWatcher(_selectedFolder.Path);

            await LoadFolderContentsAsync(_selectedFolder);
            await GeneratePreviewAsync();
        }
    }

    private async Task RefreshPanelsAsync()
    {
        if (_selectedFolder != null)
        {
            // Clear settings cache to pick up any changes made in Settings page
            _settingsService.ClearCache();
            await _settingsService.LoadSettingsAsync();

            await LoadFolderContentsAsync(_selectedFolder);
            await GeneratePreviewAsync();
        }
    }

    private async Task LoadFolderContentsAsync(StorageFolder folder)
    {
        CurrentFiles.Clear();

        try
        {
            // Add ".." entry if we're not at the root folder
            if (_rootFolder != null && folder.Path != _rootFolder.Path)
            {
                CurrentFiles.Add(new FileItem
                {
                    Name = "..",
                    Path = "__PARENT__",
                    IsFolder = true,
                    DateModified = DateTime.Now
                });
            }

            var subFolders = await folder.GetFoldersAsync();
            foreach (var subFolder in subFolders.OrderBy(f => f.Name))
            {
                // Use System.IO for fast property access instead of slow GetBasicPropertiesAsync
                var dirInfo = new DirectoryInfo(subFolder.Path);
                CurrentFiles.Add(new FileItem
                {
                    Name = subFolder.Name,
                    Path = subFolder.Path,
                    IsFolder = true,
                    DateModified = dirInfo.LastWriteTime
                });
            }

            var files = await folder.GetFilesAsync();
            foreach (var file in files.OrderBy(f => f.Name))
            {
                // Use System.IO for fast property access instead of slow GetBasicPropertiesAsync
                var fileInfo = new FileInfo(file.Path);
                CurrentFiles.Add(new FileItem
                {
                    Name = file.Name,
                    Path = file.Path,
                    Extension = file.FileType,
                    IsFolder = false,
                    Size = (ulong)fileInfo.Length,
                    DateModified = fileInfo.LastWriteTime
                });
            }

            CurrentEmptyState.Visibility = CurrentFiles.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
            CurrentFilesPanel.Visibility = CurrentFiles.Count > 0 ? Visibility.Visible : Visibility.Collapsed;
        }
        catch (UnauthorizedAccessException)
        {
            CurrentEmptyState.Visibility = Visibility.Visible;
            CurrentFilesPanel.Visibility = Visibility.Collapsed;
        }
    }

    private async void CurrentFilesPanel_FolderOpened(object? sender, FileItem folder)
    {
        // Handle ".." navigation
        if (folder.Path == "__PARENT__")
        {
            if (_navigationHistory.Count > 0)
            {
                _selectedFolder = _navigationHistory.Pop();
                FolderPathText.Text = TruncatePath(_selectedFolder.Path, 30);

                // Update watcher for parent folder
                SetupFolderWatcher(_selectedFolder.Path);

                await LoadFolderContentsAsync(_selectedFolder);
            }
            return;
        }

        if (_selectedFolder != null)
        {
            _navigationHistory.Push(_selectedFolder);
        }

        try
        {
            var subFolder = await StorageFolder.GetFolderFromPathAsync(folder.Path);
            _selectedFolder = subFolder;
            FolderPathText.Text = TruncatePath(subFolder.Path, 30);

            // Update watcher for new folder
            SetupFolderWatcher(subFolder.Path);

            await LoadFolderContentsAsync(subFolder);
        }
        catch (Exception)
        {
            // Handle error
        }
    }

    private async void CurrentFilesPanel_FileOpened(object? sender, FileItem file)
    {
        try
        {
            var storageFile = await StorageFile.GetFileFromPathAsync(file.Path);
            await Windows.System.Launcher.LaunchFileAsync(storageFile);
        }
        catch (Exception)
        {
            // Handle error
        }
    }

    private void CurrentFilesPanel_SelectionChanged(object? sender, IList<FileItem> selectedItems)
    {
        SelectedFiles.Clear();
        foreach (var item in selectedItems)
        {
            SelectedFiles.Add(item);
        }
    }

    private async Task GeneratePreviewAsync()
    {
        if (_selectedFolder == null) return;

        // Reload services to get latest data
        await _categoryService.LoadCategoriesAsync();
        await _ruleService.LoadRulesAsync();
        var settings = _settingsService.GetSettings();
        var allCategories = _categoryService.GetCategories();
        var rules = _ruleService.GetRules();
        var folderPath = _selectedFolder.Path;

        // Create the new organize preview
        _organizePreview = new OrganizePreview();

        // Legacy organized preview for UI compatibility
        _organizedPreview = new Dictionary<string, OrganizedFolder>();

        // Get files in the root folder
        var rootFiles = Directory.GetFiles(folderPath);
        foreach (var filePath in rootFiles)
        {
            var fileInfo = new FileInfo(filePath);

            // Skip hidden/system files based on settings
            if (ShouldSkipFile(fileInfo, settings)) continue;

            ProcessFileForPreview(fileInfo, folderPath, settings, rules, allCategories, isInRoot: true, sourceSubfolder: null);
        }

        // Also process files in subfolders (if enabled)
        if (settings.IncludeSubfolders)
        {
            await ScanSubfoldersForPreviewAsync(folderPath, settings, rules, allCategories);
        }

        // Reset to root view and update UI
        _afterCurrentPath = null;
        UpdateAfterPanelUI();
    }

    private void ProcessFileForPreview(FileInfo fileInfo, string baseFolderPath, AppSettings settings, List<Rule> rules, List<Category> allCategories, bool isInRoot, string? sourceSubfolder)
    {
        var result = new FileOrganizeResult
        {
            SourcePath = fileInfo.FullName,
            FileSize = fileInfo.Length
        };

        // Step 1: Try rules first (if enabled)
        if (settings.UseRulesFirst && rules.Any(r => r.IsEnabled))
        {
            var matchingRules = _ruleService.GetMatchingRulesWithContinue(fileInfo, rules);
            if (matchingRules.Count > 0)
            {
                // Collect all actions from all matching rules
                var allActions = new List<RuleAction>();
                foreach (var rule in matchingRules)
                {
                    allActions.AddRange(rule.Actions);
                }

                // Check if any rule has an Ignore action - if so, file stays in place
                var hasIgnore = allActions.Any(a => a.Type == ActionType.Ignore);
                if (hasIgnore)
                {
                    // File is ignored by rule - show it staying in its current location
                    result.MatchedBy = OrganizeMatchType.Rule;
                    result.MatchedRuleName = string.Join(" → ", matchingRules.Select(r => r.Name));
                    result.MatchedRuleId = matchingRules.First().Id;
                    result.MatchedRules = matchingRules;
                    result.DestinationPath = null;
                    result.Actions = allActions;
                    _organizePreview!.Results.Add(result);
                    AddUnmatchedToLegacyPreview(fileInfo, sourceSubfolder);
                    return;
                }

                // Calculate all destinations from all matching rules
                var allDestinations = new List<string>();
                foreach (var rule in matchingRules)
                {
                    var ruleDestinations = _ruleService.CalculateAllDestinationPaths(rule, fileInfo, baseFolderPath, _categoryService);
                    allDestinations.AddRange(ruleDestinations);
                }

                result.MatchedBy = OrganizeMatchType.Rule;
                result.MatchedRuleName = string.Join(" → ", matchingRules.Select(r => r.Name));
                result.MatchedRuleId = matchingRules.First().Id;
                result.MatchedRules = matchingRules;
                result.Actions = allActions;
                result.DestinationPath = allDestinations.Count > 0 ? allDestinations[0] : null;

                // Check if the last rule has a Continue action - if so, still check categories as fallback
                var lastRuleHasContinue = matchingRules.Last().Actions.Any(a => a.Type == ActionType.Continue);
                if (!lastRuleHasContinue || allDestinations.Count > 0)
                {
                    _organizePreview!.Results.Add(result);

                    // Add preview entry for primary destination
                    if (allDestinations.Count > 0)
                    {
                        AddToLegacyPreview(result, fileInfo);

                        // Add preview entries for any additional destinations (copies)
                        for (int i = 1; i < allDestinations.Count; i++)
                        {
                            var copyResult = new FileOrganizeResult
                            {
                                SourcePath = fileInfo.FullName,
                                FileSize = fileInfo.Length,
                                MatchedBy = OrganizeMatchType.Rule,
                                MatchedRuleName = result.MatchedRuleName + " (copy)",
                                MatchedRuleId = result.MatchedRuleId,
                                DestinationPath = allDestinations[i],
                                Actions = allActions
                            };
                            AddToLegacyPreview(copyResult, fileInfo);
                        }
                    }
                    else
                    {
                        AddUnmatchedToLegacyPreview(fileInfo, sourceSubfolder);
                    }
                    return;
                }
            }
        }

        // Step 2: Fall back to categories (if enabled)
        if (settings.FallbackToCategories)
        {
            var category = _categoryService.GetCategoryForFile(fileInfo.Extension);
            if (category != null && category.IsEnabled)
            {
                // Check if file is already in the correct category folder
                var expectedFolder = Path.Combine(baseFolderPath, category.Destination);
                var currentFolder = fileInfo.DirectoryName ?? "";

                if (currentFolder.Equals(expectedFolder, StringComparison.OrdinalIgnoreCase))
                {
                    // File is already in correct location - show as unchanged
                    result.MatchedBy = OrganizeMatchType.None;
                    result.DestinationPath = null;
                    _organizePreview!.Results.Add(result);
                    AddUnmatchedToLegacyPreview(fileInfo, sourceSubfolder);
                    return;
                }

                result.MatchedBy = OrganizeMatchType.Category;
                result.MatchedCategoryName = category.Name;
                result.MatchedCategoryIcon = category.Icon;
                result.DestinationPath = Path.Combine(baseFolderPath, category.Destination, fileInfo.Name);
                _organizePreview!.Results.Add(result);
                AddToLegacyPreview(result, fileInfo);
                return;
            }
        }

        // Step 3: No match - file stays in place
        result.MatchedBy = OrganizeMatchType.None;
        result.DestinationPath = null;
        _organizePreview!.Results.Add(result);
        AddUnmatchedToLegacyPreview(fileInfo, sourceSubfolder);
    }

    private async Task ScanSubfoldersForPreviewAsync(string baseFolderPath, AppSettings settings, List<Rule> rules, List<Category> allCategories)
    {
        var subFolders = await _selectedFolder!.GetFoldersAsync();
        foreach (var subFolder in subFolders)
        {
            // Skip hidden/system folders entirely
            var dirInfo = new DirectoryInfo(subFolder.Path);
            if (settings.IgnoreHiddenFiles && (dirInfo.Attributes & System.IO.FileAttributes.Hidden) != 0) continue;
            if (settings.IgnoreSystemFiles && (dirInfo.Attributes & System.IO.FileAttributes.System) != 0) continue;

            var filesInSubfolder = Directory.GetFiles(subFolder.Path);
            var hasIgnoredFiles = false;

            foreach (var filePath in filesInSubfolder)
            {
                var fileInfo = new FileInfo(filePath);

                // Check if file should be skipped (hidden/system)
                if (ShouldSkipFile(fileInfo, settings))
                {
                    // Track that this folder has ignored files - it will remain after organizing
                    hasIgnoredFiles = true;
                    // Add ignored file to preview so folder shows up
                    AddIgnoredFileToPreview(fileInfo, subFolder.Name);
                    continue;
                }

                ProcessFileForPreview(fileInfo, baseFolderPath, settings, rules, allCategories, isInRoot: false, sourceSubfolder: subFolder.Name);
            }

            // If folder only has ignored files (no processable files were added),
            // ensure the folder still shows in preview
            if (hasIgnoredFiles && !filesInSubfolder.Any(f => !ShouldSkipFile(new FileInfo(f), settings)))
            {
                // Folder will remain because it only contains ignored files
                EnsureFolderInPreview(subFolder.Name);
            }
        }
    }

    private void AddIgnoredFileToPreview(FileInfo fileInfo, string subfolderName)
    {
        // Add ignored files to their current folder in preview
        // This ensures folders with ignored files show up in the "After" panel
        var groupKey = $"folder_{subfolderName}";

        // Check if subfolder matches a category
        var allCategories = _categoryService.GetCategories();
        var matchingCategory = allCategories.FirstOrDefault(c =>
            c.IsEnabled && c.Destination.Equals(subfolderName, StringComparison.OrdinalIgnoreCase));

        string groupName, groupIcon, groupColor;
        if (matchingCategory != null)
        {
            groupKey = matchingCategory.Id;
            groupName = matchingCategory.Name;
            groupIcon = matchingCategory.Icon;
            groupColor = matchingCategory.Color;
        }
        else
        {
            groupName = subfolderName;
            groupIcon = "\U0001F4C2"; // 📂
            groupColor = "#6B7280"; // Gray
        }

        if (!_organizedPreview!.TryGetValue(groupKey, out var group))
        {
            group = new OrganizedFolder
            {
                CategoryId = groupKey,
                Name = groupName,
                Icon = groupIcon,
                Color = groupColor,
                Destination = subfolderName,
                FileCount = 0,
                Files = new List<PreviewFile>(),
                IsRuleGroup = false
            };
            _organizedPreview[groupKey] = group;
        }

        group.Files.Add(new PreviewFile
        {
            Name = fileInfo.Name,
            OriginalPath = fileInfo.FullName,
            Extension = fileInfo.Extension,
            Size = (ulong)fileInfo.Length,
            DateModified = fileInfo.LastWriteTime,
            IsAlreadyOrganized = true, // File stays in place (ignored)
            MatchedByRule = false,
            RuleName = null
        });
        group.FileCount++;
    }

    private void EnsureFolderInPreview(string subfolderName)
    {
        // Ensure folder shows up in preview even if empty of processable files
        var groupKey = $"folder_{subfolderName}";

        var allCategories = _categoryService.GetCategories();
        var matchingCategory = allCategories.FirstOrDefault(c =>
            c.IsEnabled && c.Destination.Equals(subfolderName, StringComparison.OrdinalIgnoreCase));

        if (matchingCategory != null)
        {
            groupKey = matchingCategory.Id;
        }

        // If group already exists, nothing to do
        if (_organizedPreview!.ContainsKey(groupKey))
            return;

        string groupName, groupIcon, groupColor;
        if (matchingCategory != null)
        {
            groupName = matchingCategory.Name;
            groupIcon = matchingCategory.Icon;
            groupColor = matchingCategory.Color;
        }
        else
        {
            groupName = subfolderName;
            groupIcon = "\U0001F4C2"; // 📂
            groupColor = "#6B7280"; // Gray
        }

        _organizedPreview[groupKey] = new OrganizedFolder
        {
            CategoryId = groupKey,
            Name = groupName,
            Icon = groupIcon,
            Color = groupColor,
            Destination = subfolderName,
            FileCount = 0,
            Files = new List<PreviewFile>(),
            IsRuleGroup = false
        };
    }

    private static bool ShouldSkipFile(FileInfo fileInfo, AppSettings settings)
    {
        // Skip hidden files if setting is enabled
        if (settings.IgnoreHiddenFiles && (fileInfo.Attributes & System.IO.FileAttributes.Hidden) != 0)
            return true;

        // Skip system files if setting is enabled
        if (settings.IgnoreSystemFiles && (fileInfo.Attributes & System.IO.FileAttributes.System) != 0)
            return true;

        return false;
    }

    private void AddToLegacyPreview(FileOrganizeResult result, FileInfo fileInfo)
    {
        // Group by actual destination folder, not by rule name
        // This shows the preview in the state files will be after organizing

        if (result.DestinationPath == null)
            return;

        // Get the destination folder relative to the selected folder
        var destDir = Path.GetDirectoryName(result.DestinationPath) ?? "";
        var basePath = _selectedFolder?.Path ?? "";
        var relativeDest = destDir.StartsWith(basePath, StringComparison.OrdinalIgnoreCase)
            ? destDir.Substring(basePath.Length).TrimStart(Path.DirectorySeparatorChar)
            : destDir;

        // Handle special cases
        string groupKey;
        string groupName;
        string groupIcon;
        string groupColor;
        bool isRootLevel = string.IsNullOrEmpty(relativeDest);

        // Check if destination matches a category
        var allCategories = _categoryService.GetCategories();
        var matchingCategory = allCategories.FirstOrDefault(c =>
            c.IsEnabled && c.Destination.Equals(relativeDest, StringComparison.OrdinalIgnoreCase));

        if (result.DestinationPath == "[RECYCLE BIN]")
        {
            // File will be deleted
            groupKey = "_delete_";
            groupName = "Recycle Bin";
            groupIcon = "\U0001F5D1"; // 🗑️
            groupColor = "#EF4444"; // Red
            AddFileToGroup(groupKey, groupName, groupIcon, groupColor, "", result, fileInfo);
        }
        else if (isRootLevel)
        {
            // File stays in root (e.g., rename only)
            groupKey = "_root_";
            groupName = "Root";
            groupIcon = "\U0001F4C1"; // 📁
            groupColor = "#6B7280"; // Gray
            AddFileToGroup(groupKey, groupName, groupIcon, groupColor, "", result, fileInfo);
        }
        else if (matchingCategory != null)
        {
            // Destination matches a category
            groupKey = matchingCategory.Id;
            groupName = matchingCategory.Name;
            groupIcon = matchingCategory.Icon;
            groupColor = matchingCategory.Color;
            AddFileToGroup(groupKey, groupName, groupIcon, groupColor, relativeDest, result, fileInfo);
        }
        else
        {
            // Custom destination folder (from rule) - handle nested paths
            // Split path into segments for hierarchical display
            var pathSegments = relativeDest.Split(new[] { Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar }, StringSplitOptions.RemoveEmptyEntries);

            if (pathSegments.Length > 1)
            {
                // Nested path - create hierarchical structure
                AddFileToNestedFolder(pathSegments, relativeDest, result, fileInfo);
            }
            else
            {
                // Single-level folder
                groupKey = $"folder_{relativeDest}";
                groupName = relativeDest;
                groupIcon = "\U0001F4C2"; // 📂
                groupColor = "#60CDFF"; // Accent blue
                AddFileToGroup(groupKey, groupName, groupIcon, groupColor, relativeDest, result, fileInfo);
            }
        }
    }

    private void AddFileToGroup(string groupKey, string groupName, string groupIcon, string groupColor, string destination, FileOrganizeResult result, FileInfo fileInfo)
    {
        if (!_organizedPreview!.TryGetValue(groupKey, out var group))
        {
            group = new OrganizedFolder
            {
                CategoryId = groupKey,
                Name = groupName,
                Icon = groupIcon,
                Color = groupColor,
                Destination = destination,
                FileCount = 0,
                Files = new List<PreviewFile>(),
                IsRuleGroup = false
            };
            _organizedPreview[groupKey] = group;
        }

        // Use the final filename (may be renamed by rule)
        var finalName = Path.GetFileName(result.DestinationPath!);

        group.Files.Add(new PreviewFile
        {
            Name = finalName,
            OriginalPath = result.SourcePath,
            Extension = Path.GetExtension(finalName),
            Size = (ulong)fileInfo.Length,
            DateModified = fileInfo.LastWriteTime,
            IsAlreadyOrganized = false,
            MatchedByRule = result.MatchedBy == OrganizeMatchType.Rule,
            RuleName = result.MatchedRuleName
        });
        group.FileCount++;
    }

    private void AddFileToNestedFolder(string[] pathSegments, string fullRelativePath, FileOrganizeResult result, FileInfo fileInfo)
    {
        // Create the top-level folder if it doesn't exist
        var topFolderName = pathSegments[0];
        var topFolderKey = $"folder_{topFolderName}";

        if (!_organizedPreview!.TryGetValue(topFolderKey, out var topFolder))
        {
            topFolder = new OrganizedFolder
            {
                CategoryId = topFolderKey,
                Name = topFolderName,
                Icon = "\U0001F4C2", // 📂
                Color = "#60CDFF", // Accent blue
                Destination = topFolderName,
                FileCount = 0,
                Files = new List<PreviewFile>(),
                IsRuleGroup = false,
                ParentFolderKey = null
            };
            _organizedPreview[topFolderKey] = topFolder;
        }

        // Navigate/create the nested folder structure
        var currentFolder = topFolder;
        var currentPath = topFolderName;

        for (int i = 1; i < pathSegments.Length; i++)
        {
            var segmentName = pathSegments[i];
            var segmentPath = Path.Combine(currentPath, segmentName);
            var segmentKey = $"folder_{segmentPath}";

            if (!currentFolder.ChildFolders.TryGetValue(segmentKey, out var childFolder))
            {
                childFolder = new OrganizedFolder
                {
                    CategoryId = segmentKey,
                    Name = segmentName,
                    Icon = "\U0001F4C2", // 📂
                    Color = "#60CDFF", // Accent blue
                    Destination = segmentPath,
                    FileCount = 0,
                    Files = new List<PreviewFile>(),
                    IsRuleGroup = false,
                    ParentFolderKey = currentFolder.CategoryId
                };
                currentFolder.ChildFolders[segmentKey] = childFolder;
                // Also add to the main dictionary for easy lookup
                _organizedPreview[segmentKey] = childFolder;
            }

            currentFolder = childFolder;
            currentPath = segmentPath;
        }

        // Add the file to the innermost folder
        var finalName = Path.GetFileName(result.DestinationPath!);
        currentFolder.Files.Add(new PreviewFile
        {
            Name = finalName,
            OriginalPath = result.SourcePath,
            Extension = Path.GetExtension(finalName),
            Size = (ulong)fileInfo.Length,
            DateModified = fileInfo.LastWriteTime,
            IsAlreadyOrganized = false,
            MatchedByRule = result.MatchedBy == OrganizeMatchType.Rule,
            RuleName = result.MatchedRuleName
        });
        currentFolder.FileCount++;

        // Increment file count for all parent folders
        var parentKey = currentFolder.ParentFolderKey;
        while (parentKey != null && _organizedPreview.TryGetValue(parentKey, out var parentFolder))
        {
            parentFolder.FileCount++;
            parentKey = parentFolder.ParentFolderKey;
        }
    }

    private void AddUnmatchedToLegacyPreview(FileInfo fileInfo, string? sourceSubfolder)
    {
        // Add unmatched files to appropriate group based on their current location
        string groupKey;
        string groupName;
        string groupIcon;
        string groupColor;
        string groupDestination;

        if (string.IsNullOrEmpty(sourceSubfolder))
        {
            // File is in root
            groupKey = "_root_";
            groupName = "Root";
            groupIcon = "\U0001F4C1"; // 📁
            groupColor = "#6B7280"; // Gray
            groupDestination = "";
        }
        else
        {
            // Check if subfolder matches a category - use same group key as AddToLegacyPreview
            var allCategories = _categoryService.GetCategories();
            var matchingCategory = allCategories.FirstOrDefault(c =>
                c.IsEnabled && c.Destination.Equals(sourceSubfolder, StringComparison.OrdinalIgnoreCase));

            if (matchingCategory != null)
            {
                // Use category's group key so files merge with files being moved here
                groupKey = matchingCategory.Id;
                groupName = matchingCategory.Name;
                groupIcon = matchingCategory.Icon;
                groupColor = matchingCategory.Color;
                groupDestination = matchingCategory.Destination;
            }
            else
            {
                // Non-category subfolder
                groupKey = $"folder_{sourceSubfolder}";
                groupName = sourceSubfolder;
                groupIcon = "\U0001F4C2"; // 📂
                groupColor = "#6B7280"; // Gray
                groupDestination = sourceSubfolder;
            }
        }

        if (!_organizedPreview!.TryGetValue(groupKey, out var group))
        {
            group = new OrganizedFolder
            {
                CategoryId = groupKey,
                Name = groupName,
                Icon = groupIcon,
                Color = groupColor,
                Destination = groupDestination,
                FileCount = 0,
                Files = new List<PreviewFile>(),
                IsRuleGroup = false
            };
            _organizedPreview[groupKey] = group;
        }

        group.Files.Add(new PreviewFile
        {
            Name = fileInfo.Name,
            OriginalPath = fileInfo.FullName,
            Extension = fileInfo.Extension,
            Size = (ulong)fileInfo.Length,
            DateModified = fileInfo.LastWriteTime,
            IsAlreadyOrganized = true, // File is already in place, won't be moved
            MatchedByRule = false,
            RuleName = null
        });
        group.FileCount++;
    }


    private void UpdateAfterPanelUI()
    {
        AfterFiles.Clear();

        if (_organizedPreview == null || _organizedPreview.Count == 0)
        {
            AfterEmptyState.Visibility = Visibility.Visible;
            AfterFilesPanel.Visibility = Visibility.Collapsed;
            OrganizeButton.IsEnabled = false;
            return;
        }

        AfterEmptyState.Visibility = Visibility.Collapsed;
        AfterFilesPanel.Visibility = Visibility.Visible;
        OrganizeButton.IsEnabled = true;

        if (_afterCurrentPath == null)
        {
            // Show root level - category folders
            ShowAfterRootFolders();
        }
        else
        {
            // Show files inside a category folder
            ShowAfterCategoryFiles(_afterCurrentPath);
        }
    }

    private void ShowAfterRootFolders()
    {
        AfterFiles.Clear();

        // Show root-level files first (files that stay in root, e.g., rename only)
        if (_organizedPreview!.TryGetValue("_root_", out var rootGroup) && rootGroup.FileCount > 0)
        {
            foreach (var file in rootGroup.Files)
            {
                AfterFiles.Add(new FileItem
                {
                    Name = file.Name,
                    Path = file.OriginalPath,
                    IsFolder = false,
                    Size = file.Size,
                    DateModified = file.DateModified,
                    IsRuleMatch = file.MatchedByRule,
                    DisplayColor = file.MatchedByRule ? "#60CDFF" : null
                });
            }
        }

        // Sort destination folders by file count (most files first)
        // Only show top-level folders (no parent) to avoid showing nested folders at root
        var folders = _organizedPreview!.Values
            .Where(g => g.FileCount > 0 && g.CategoryId != "_root_" && g.ParentFolderKey == null)
            .OrderByDescending(g => g.FileCount)
            .ToList();

        // Add destination folders
        foreach (var folder in folders)
        {
            // Use folder.Name for special groups (delete), otherwise use destination
            var displayName = folder.CategoryId == "_delete_"
                ? folder.Name
                : string.IsNullOrEmpty(folder.Destination) ? folder.Name : folder.Destination;

            AfterFiles.Add(new FileItem
            {
                Name = $"{folder.Icon} {displayName}",
                Path = folder.CategoryId,
                IsFolder = true,
                DateModified = DateTime.Now,
                IsRuleMatch = false,
                DisplayColor = folder.Color
            });
        }
    }

    private void ShowAfterCategoryFiles(string categoryId)
    {
        AfterFiles.Clear();

        if (_organizedPreview!.TryGetValue(categoryId, out var folder))
        {
            // Add a ".." entry to go back to parent (or root)
            AfterFiles.Add(new FileItem
            {
                Name = "..",
                Path = folder.ParentFolderKey ?? "__ROOT__",
                IsFolder = true,
                DateModified = DateTime.Now
            });

            // Add child folders first (sorted by file count)
            var childFolders = folder.ChildFolders.Values
                .Where(cf => cf.FileCount > 0)
                .OrderByDescending(cf => cf.FileCount)
                .ToList();

            foreach (var childFolder in childFolders)
            {
                AfterFiles.Add(new FileItem
                {
                    Name = $"{childFolder.Icon} {childFolder.Name}",
                    Path = childFolder.CategoryId,
                    IsFolder = true,
                    DateModified = DateTime.Now,
                    IsRuleMatch = false,
                    DisplayColor = childFolder.Color
                });
            }

            // Add files in this group
            foreach (var file in folder.Files.OrderBy(f => f.Name))
            {
                AfterFiles.Add(new FileItem
                {
                    Name = file.Name,
                    Path = file.OriginalPath,
                    Extension = file.Extension,
                    IsFolder = false,
                    Size = file.Size,
                    DateModified = file.DateModified,
                    IsRuleMatch = file.MatchedByRule,
                    MatchedRuleName = file.RuleName,
                    IsAlreadyOrganized = file.IsAlreadyOrganized
                });
            }
        }
    }

    private void AfterFilesPanel_FolderOpened(object? sender, FileItem folder)
    {
        if (folder.Path == "__ROOT__")
        {
            // Go back to root
            _afterCurrentPath = null;
        }
        else if (folder.Path == "__PARENT__")
        {
            // Legacy: Go back to root (for backwards compatibility)
            _afterCurrentPath = null;
        }
        else
        {
            // Navigate into category folder
            _afterCurrentPath = folder.Path; // This is the category ID
        }

        UpdateAfterPanelUI();
    }

    private async void OrganizeButton_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedFolder == null || _organizePreview == null || _organizePreview.Results.Count == 0) return;
        if (_isOperationInProgress) return;

        var settings = _settingsService.GetSettings();
        var filesToOrganize = _organizePreview.Results.Count(r => r.WillBeOrganized);

        // Show confirmation dialog if enabled
        if (settings.ConfirmBeforeOrganize)
        {
            var dialog = new ContentDialog
            {
                Title = "Confirm Organization",
                Content = $"This will organize {filesToOrganize} file{(filesToOrganize == 1 ? "" : "s")}.\n\nAre you sure you want to continue?",
                PrimaryButtonText = "Organize",
                CloseButtonText = "Cancel",
                DefaultButton = ContentDialogButton.Primary,
                XamlRoot = this.XamlRoot
            };

            var result = await dialog.ShowAsync();
            if (result != ContentDialogResult.Primary)
            {
                return;
            }
        }

        _isOperationInProgress = true;
        OrganizeButton.IsEnabled = false;
        UndoButton.IsEnabled = false;
        OrganizeButton.Content = "Organizing...";

        var movedCount = 0;
        var errorCount = 0;
        var totalFiles = _organizePreview.Results.Count(r => r.WillBeOrganized);

        // Clear previous undo history and start fresh
        _lastMoveOperations = new List<MoveOperation>();
        var moveOps = _lastMoveOperations;
        var selectedFolder = _selectedFolder;
        var folderPath = _selectedFolder.Path;

        try
        {
            _lastOrganizedPath = folderPath;

            // Process each file based on its match result
            foreach (var result in _organizePreview.Results.Where(r => r.WillBeOrganized))
            {
                try
                {
                    var fileInfo = new FileInfo(result.SourcePath);
                    if (!fileInfo.Exists) continue;

                    if (result.MatchedBy == OrganizeMatchType.Rule)
                    {
                        // Execute rule actions
                        await ExecuteRuleActionsAsync(result, fileInfo, folderPath, moveOps);
                        movedCount++;
                    }
                    else if (result.MatchedBy == OrganizeMatchType.Category)
                    {
                        // Simple category move
                        var destPath = result.DestinationPath!;
                        var destDir = Path.GetDirectoryName(destPath)!;

                        // Skip if source and destination are the same
                        if (result.SourcePath.Equals(destPath, StringComparison.OrdinalIgnoreCase))
                        {
                            continue;
                        }

                        Directory.CreateDirectory(destDir);

                        var finalPath = GetUniqueFilePath(destPath, result.SourcePath);
                        File.Move(result.SourcePath, finalPath);

                        moveOps.Add(new MoveOperation
                        {
                            OriginalFolderPath = fileInfo.DirectoryName!,
                            OriginalFileName = fileInfo.Name,
                            NewFolderPath = destDir,
                            NewFileName = Path.GetFileName(finalPath)
                        });

                        movedCount++;
                    }

                    // Update progress periodically
                    if (movedCount % 10 == 0)
                    {
                        OrganizeButton.Content = $"Organizing... {movedCount}/{totalFiles}";
                    }
                }
                catch
                {
                    errorCount++;
                }
            }

            // Clean up empty folders after organizing
            if (_selectedFolder != null)
            {
                await CleanupEmptyFoldersAsync(_selectedFolder);
            }

            // Success state
            if (errorCount > 0)
            {
                OrganizeButton.Content = $"Done ({errorCount} skipped)";
            }
            else
            {
                OrganizeButton.Content = "Organized!";
            }

            // Show undo button only if we moved at least one file
            UndoButton.IsEnabled = true;
            UndoButton.Content = "Undo";
            UndoButton.Visibility = moveOps.Count > 0 ? Visibility.Visible : Visibility.Collapsed;

            // Refresh both panels
            await LoadFolderContentsAsync(_selectedFolder);
            await GeneratePreviewAsync();

            // Reset after delay
            await Task.Delay(2000);
            OrganizeButton.Content = "Organize Now";
            OrganizeButton.IsEnabled = true;
            _isOperationInProgress = false;
        }
        catch (Exception)
        {
            OrganizeButton.Content = $"Error ({movedCount} moved)";
            OrganizeButton.IsEnabled = true;

            UndoButton.IsEnabled = true;
            UndoButton.Content = "Undo";
            UndoButton.Visibility = moveOps?.Count > 0 ? Visibility.Visible : Visibility.Collapsed;

            try
            {
                await LoadFolderContentsAsync(_selectedFolder);
                await GeneratePreviewAsync();
            }
            catch
            {
                // Ignore refresh errors
            }

            _isOperationInProgress = false;
        }
    }

    private async Task ExecuteRuleActionsAsync(FileOrganizeResult result, FileInfo fileInfo, string baseFolderPath, List<MoveOperation> moveOps)
    {
        // Track the ORIGINAL file location for undo (before any actions)
        var originalFilePath = fileInfo.FullName;
        var originalFileName = fileInfo.Name;
        var originalDirectory = fileInfo.DirectoryName!;

        // Track the current file path as actions modify it
        var currentFilePath = fileInfo.FullName;
        var currentFileName = fileInfo.Name;
        var currentDirectory = fileInfo.DirectoryName!;

        // Keep original fileInfo for pattern expansion (uses original dates/attributes)
        var originalFileInfo = fileInfo;

        // Track all folders created during this file's processing
        var allCreatedFolders = new List<string>();

        // Track all files created by copy operations
        var allCopiedFiles = new List<string>();

        // Track deleted files (staging path -> original path)
        var allDeletedFiles = new Dictionary<string, string>();

        // Track if file was deleted
        var fileWasDeleted = false;

        foreach (var action in result.Actions)
        {
            switch (action.Type)
            {
                case ActionType.MoveToFolder:
                    {
                        var destFolder = action.Value;
                        if (!Path.IsPathRooted(destFolder))
                        {
                            destFolder = Path.Combine(baseFolderPath, destFolder);
                        }
                        var targetPath = Path.Combine(destFolder, currentFileName);

                        // Skip if already in destination
                        if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                        File.Move(currentFilePath, destPath);

                        // Update current file location
                        currentFilePath = destPath;
                        currentFileName = Path.GetFileName(destPath);
                        currentDirectory = destFolder;
                    }
                    break;

                case ActionType.CopyToFolder:
                    {
                        var destFolder = action.Value;
                        if (!Path.IsPathRooted(destFolder))
                        {
                            destFolder = Path.Combine(baseFolderPath, destFolder);
                        }
                        var targetPath = Path.Combine(destFolder, currentFileName);

                        // Skip if source and destination are the same
                        if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                        File.Copy(currentFilePath, destPath);

                        // Track the copied file for undo (will be deleted on undo)
                        allCopiedFiles.Add(destPath);
                        // Note: Copy doesn't change currentFilePath - original file stays where it is
                    }
                    break;

                case ActionType.MoveToCategory:
                    {
                        var categoryId = action.Value;
                        var category = _categoryService.GetCategories().FirstOrDefault(c => c.Id == categoryId);
                        if (category != null)
                        {
                            var destFolder = Path.IsPathRooted(category.Destination)
                                ? category.Destination
                                : Path.Combine(baseFolderPath, category.Destination);
                            var targetPath = Path.Combine(destFolder, currentFileName);

                            // Skip if already in destination
                            if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                                break;

                            Directory.CreateDirectory(destFolder);
                            var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                            File.Move(currentFilePath, destPath);

                            // Update current file location
                            currentFilePath = destPath;
                            currentFileName = Path.GetFileName(destPath);
                            currentDirectory = destFolder;
                        }
                    }
                    break;

                case ActionType.SortIntoSubfolder:
                    {
                        var subfolderName = RuleService.ExpandPattern(action.Value, originalFileInfo);
                        // Normalize path separators (user might use / in pattern)
                        subfolderName = subfolderName.Replace('/', Path.DirectorySeparatorChar);
                        var destFolder = Path.Combine(baseFolderPath, subfolderName);
                        var targetPath = Path.Combine(destFolder, currentFileName);

                        // Skip if already in destination
                        if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        // Track which folders we create for undo
                        var createdFolders = CreateDirectoryAndTrack(destFolder, baseFolderPath);
                        allCreatedFolders.AddRange(createdFolders);

                        var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                        File.Move(currentFilePath, destPath);

                        // Update current file location
                        currentFilePath = destPath;
                        currentFileName = Path.GetFileName(destPath);
                        currentDirectory = destFolder;
                    }
                    break;

                case ActionType.Rename:
                    {
                        var newName = RuleService.ExpandPattern(action.Value, originalFileInfo);
                        var targetPath = Path.Combine(currentDirectory, newName);

                        // Skip if the name is exactly the same (case-sensitive)
                        if (currentFilePath.Equals(targetPath, StringComparison.Ordinal))
                            break;

                        // Check if this is a case-only rename (same name, different case)
                        var isCaseOnlyRename = currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase);

                        if (isCaseOnlyRename)
                        {
                            // Windows requires two-step rename for case changes
                            var tempPath = currentFilePath + ".tmp_rename";
                            File.Move(currentFilePath, tempPath);
                            File.Move(tempPath, targetPath);
                            currentFilePath = targetPath;
                            currentFileName = Path.GetFileName(targetPath);
                        }
                        else
                        {
                            var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                            File.Move(currentFilePath, destPath);

                            // Update current file location
                            currentFilePath = destPath;
                            currentFileName = Path.GetFileName(destPath);
                        }
                    }
                    break;

                case ActionType.Delete:
                    {
                        // Send to Recycle Bin for user safety
                        await MoveToRecycleBinAsync(currentFilePath);

                        // Track the original path for reference (cannot be auto-restored, user must restore from Recycle Bin)
                        allDeletedFiles[currentFilePath] = currentFilePath;
                        fileWasDeleted = true;
                        break;
                    }

                case ActionType.Ignore:
                case ActionType.Continue:
                    // These don't perform file operations
                    break;
            }
        }

        // After all actions are complete, add ONE MoveOperation for undo
        // This captures the full transformation from original to final location
        // Only add undo operation if the file was moved/renamed, copies were made, or files were deleted
        if (!originalFilePath.Equals(currentFilePath, StringComparison.OrdinalIgnoreCase) || allCopiedFiles.Count > 0 || allDeletedFiles.Count > 0)
        {
            System.Diagnostics.Debug.WriteLine($"Recording undo: {originalFileName} -> {currentFileName}");
            System.Diagnostics.Debug.WriteLine($"  From: {originalDirectory}");
            System.Diagnostics.Debug.WriteLine($"  To: {currentDirectory}");
            System.Diagnostics.Debug.WriteLine($"  Copied files: {allCopiedFiles.Count}");
            System.Diagnostics.Debug.WriteLine($"  Deleted files: {allDeletedFiles.Count}");

            moveOps.Add(new MoveOperation
            {
                OriginalFolderPath = originalDirectory,
                OriginalFileName = originalFileName,
                NewFolderPath = fileWasDeleted ? "" : currentDirectory, // Empty if file was deleted
                NewFileName = fileWasDeleted ? "" : currentFileName,    // Empty if file was deleted
                CreatedFolders = allCreatedFolders,
                CopiedFiles = allCopiedFiles,
                DeletedFiles = allDeletedFiles
            });
        }
    }

    private static string GetUniqueFilePath(string path, string? sourcePathToExclude = null)
    {
        // If the file doesn't exist, or it's the same as the source file (being moved), return as-is
        if (!File.Exists(path)) return path;
        if (sourcePathToExclude != null && path.Equals(sourcePathToExclude, StringComparison.OrdinalIgnoreCase)) return path;

        var directory = Path.GetDirectoryName(path) ?? "";
        var name = Path.GetFileNameWithoutExtension(path);
        var extension = Path.GetExtension(path);

        // Check if name already ends with a number suffix like " (1)" and strip it
        var baseName = name;
        var existingSuffixMatch = System.Text.RegularExpressions.Regex.Match(name, @"^(.+)\s+\(\d+\)$");
        if (existingSuffixMatch.Success)
        {
            baseName = existingSuffixMatch.Groups[1].Value;
        }

        var counter = 1;
        string newPath;

        do
        {
            newPath = Path.Combine(directory, $"{baseName} ({counter}){extension}");
            counter++;
        }
        while (File.Exists(newPath) && (sourcePathToExclude == null || !newPath.Equals(sourcePathToExclude, StringComparison.OrdinalIgnoreCase)));

        return newPath;
    }

    /// <summary>
    /// Creates a directory path and tracks which folders were actually created (didn't exist before).
    /// Returns list of created folders from innermost to outermost for proper undo cleanup.
    /// </summary>
    private static List<string> CreateDirectoryAndTrack(string targetPath, string basePath)
    {
        var createdFolders = new List<string>();

        // Normalize paths
        targetPath = Path.GetFullPath(targetPath);
        basePath = Path.GetFullPath(basePath);

        // Build list of directories to check (from target up to base)
        var directoriesToCreate = new List<string>();
        var currentDir = targetPath;

        while (!string.IsNullOrEmpty(currentDir) &&
               !currentDir.Equals(basePath, StringComparison.OrdinalIgnoreCase) &&
               currentDir.StartsWith(basePath, StringComparison.OrdinalIgnoreCase))
        {
            if (!Directory.Exists(currentDir))
            {
                directoriesToCreate.Add(currentDir);
            }
            currentDir = Path.GetDirectoryName(currentDir);
        }

        // Create directories from outermost to innermost
        directoriesToCreate.Reverse();
        foreach (var dir in directoriesToCreate)
        {
            if (!Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir);
                // Store in reverse order (innermost first) for deletion during undo
                createdFolders.Insert(0, dir);
            }
        }

        return createdFolders;
    }

    /// <summary>
    /// Checks if a directory is empty (no files or subdirectories).
    /// </summary>
    private static bool IsDirectoryEmpty(string path)
    {
        return !Directory.EnumerateFileSystemEntries(path).Any();
    }

    private static Task MoveToRecycleBinAsync(string filePath)
    {
        return Task.Run(() =>
        {
            // Use Shell32 to move to recycle bin
            Microsoft.VisualBasic.FileIO.FileSystem.DeleteFile(
                filePath,
                Microsoft.VisualBasic.FileIO.UIOption.OnlyErrorDialogs,
                Microsoft.VisualBasic.FileIO.RecycleOption.SendToRecycleBin);
        });
    }

    private async void UndoButton_Click(object sender, RoutedEventArgs e)
    {
        if (_lastMoveOperations == null || _lastMoveOperations.Count == 0)
        {
            UndoButton.Visibility = Visibility.Collapsed;
            return;
        }
        if (_isOperationInProgress) return;

        _isOperationInProgress = true;
        UndoButton.IsEnabled = false;
        UndoButton.Content = "Undoing...";
        OrganizeButton.IsEnabled = false;

        var restoredCount = 0;
        var errorCount = 0;
        var deletedFileCount = 0;
        var totalFiles = _lastMoveOperations.Count;

        // Collect all created folders for cleanup (innermost first)
        var allCreatedFolders = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        try
        {
            // Process in reverse order (LIFO) to handle any dependencies
            for (int i = _lastMoveOperations.Count - 1; i >= 0; i--)
            {
                var op = _lastMoveOperations[i];

                // Collect folders that were created by this operation
                foreach (var createdFolder in op.CreatedFolders)
                {
                    allCreatedFolders.Add(createdFolder);
                }

                // Delete any files that were created by copy operations
                foreach (var copiedFile in op.CopiedFiles)
                {
                    try
                    {
                        if (File.Exists(copiedFile))
                        {
                            File.Delete(copiedFile);
                        }
                    }
                    catch
                    {
                        // Ignore errors deleting copied files
                    }
                }

                // Note: Deleted files were sent to Recycle Bin - they cannot be auto-restored
                // The user will need to manually restore them from the Recycle Bin
                if (op.DeletedFiles.Count > 0)
                {
                    deletedFileCount += op.DeletedFiles.Count;
                    System.Diagnostics.Debug.WriteLine($"Note: {op.DeletedFiles.Count} file(s) were sent to Recycle Bin and need manual restoration");
                }

                // Only try to restore if the file was actually moved (not just copied or deleted)
                // Files that were deleted have empty NewFolderPath/NewFileName
                if (string.IsNullOrEmpty(op.NewFolderPath) && string.IsNullOrEmpty(op.NewFileName))
                {
                    // File was deleted - restoration handled above
                    restoredCount++;
                    continue;
                }

                if (op.OriginalFolderPath == op.NewFolderPath && op.OriginalFileName == op.NewFileName)
                {
                    // File wasn't moved, only copied - nothing to restore
                    restoredCount++;
                    continue;
                }

                try
                {
                    // Get the file from its current location
                    var currentFolder = await StorageFolder.GetFolderFromPathAsync(op.NewFolderPath);
                    var file = await currentFolder.GetFileAsync(op.NewFileName);

                    // Get the original folder
                    var originalFolder = await StorageFolder.GetFolderFromPathAsync(op.OriginalFolderPath);

                    // Move back to original location
                    await file.MoveAsync(originalFolder, op.OriginalFileName, NameCollisionOption.GenerateUniqueName);

                    restoredCount++;

                    // Update progress periodically
                    if (restoredCount % 10 == 0)
                    {
                        UndoButton.Content = $"Undoing... {restoredCount}/{totalFiles}";
                    }
                }
                catch (Exception ex)
                {
                    // Log error details for debugging
                    System.Diagnostics.Debug.WriteLine($"Undo failed for {op.NewFileName}: {ex.Message}");
                    System.Diagnostics.Debug.WriteLine($"  From: {op.NewFolderPath}\\{op.NewFileName}");
                    System.Diagnostics.Debug.WriteLine($"  To: {op.OriginalFolderPath}\\{op.OriginalFileName}");

                    // Show debug info to user
                    try
                    {
                        var debugDialog = new ContentDialog
                        {
                            Title = "Undo Debug Info",
                            Content = $"Failed to restore: {op.NewFileName}\n\nError: {ex.Message}\n\nFrom: {op.NewFolderPath}\\{op.NewFileName}\nTo: {op.OriginalFolderPath}\\{op.OriginalFileName}",
                            CloseButtonText = "OK",
                            XamlRoot = this.XamlRoot
                        };
                        _ = debugDialog.ShowAsync();
                    }
                    catch { }

                    // Skip files that can't be restored
                    errorCount++;
                }
            }

            // Clean up folders that were created by SortIntoSubfolder actions
            // Sort by path length descending to delete innermost folders first
            var sortedFolders = allCreatedFolders
                .OrderByDescending(f => f.Length)
                .ToList();

            foreach (var folderPath in sortedFolders)
            {
                try
                {
                    if (Directory.Exists(folderPath) && IsDirectoryEmpty(folderPath))
                    {
                        Directory.Delete(folderPath);
                    }
                }
                catch
                {
                    // Ignore errors when cleaning up folders
                }
            }

            // Do general cleanup for empty folders
            if (_selectedFolder != null)
            {
                await CleanupEmptyFoldersAsync(_selectedFolder);
            }

            // Clear the undo history
            _lastMoveOperations = null;

            // Update UI
            if (errorCount > 0)
            {
                UndoButton.Content = $"Restored ({errorCount} failed)";
            }
            else
            {
                UndoButton.Content = "Restored!";
            }

            // Refresh panels
            if (_selectedFolder != null)
            {
                await LoadFolderContentsAsync(_selectedFolder);
                await GeneratePreviewAsync();
            }

            // Reset after delay
            await Task.Delay(2000);
            UndoButton.Content = "Undo";
            UndoButton.Visibility = Visibility.Collapsed;
            OrganizeButton.IsEnabled = true;
            _isOperationInProgress = false;
        }
        catch (Exception)
        {
            UndoButton.Content = $"Error ({restoredCount} restored)";
            UndoButton.IsEnabled = true;
            OrganizeButton.IsEnabled = true;

            // Still refresh to show current state
            try
            {
                if (_selectedFolder != null)
                {
                    await LoadFolderContentsAsync(_selectedFolder);
                    await GeneratePreviewAsync();
                }
            }
            catch
            {
                // Ignore refresh errors
            }

            _isOperationInProgress = false;
        }
    }

    private async Task CleanupEmptyFoldersAsync(StorageFolder parentFolder)
    {
        try
        {
            var subFolders = await parentFolder.GetFoldersAsync();

            foreach (var folder in subFolders)
            {
                try
                {
                    // First, recursively clean up any empty subfolders within this folder
                    await CleanupEmptyFoldersAsync(folder);

                    // Now check if this folder is empty (no files and no subfolders remaining)
                    var items = await folder.GetItemsAsync();
                    if (items.Count == 0)
                    {
                        await folder.DeleteAsync();
                    }
                }
                catch
                {
                    // Ignore errors deleting individual folders
                }
            }
        }
        catch
        {
            // Ignore errors listing folders
        }
    }

    private static string TruncatePath(string path, int maxLength)
    {
        if (path.Length <= maxLength) return path;

        var fileName = Path.GetFileName(path);
        if (fileName.Length >= maxLength - 3)
        {
            return "..." + fileName[^(maxLength - 3)..];
        }

        return "..." + path[^maxLength..];
    }

    private void SetupFolderWatcher(string folderPath)
    {
        // Dispose existing watcher if any
        DisposeFolderWatcher();

        _folderWatcher = new FileSystemWatcher(folderPath)
        {
            NotifyFilter = NotifyFilters.FileName | NotifyFilters.DirectoryName | NotifyFilters.LastWrite,
            IncludeSubdirectories = false,
            EnableRaisingEvents = true
        };

        _folderWatcher.Created += OnFolderChanged;
        _folderWatcher.Deleted += OnFolderChanged;
        _folderWatcher.Renamed += OnFolderChanged;
        _folderWatcher.Changed += OnFolderChanged;
    }

    private void DisposeFolderWatcher()
    {
        if (_folderWatcher != null)
        {
            _folderWatcher.EnableRaisingEvents = false;
            _folderWatcher.Created -= OnFolderChanged;
            _folderWatcher.Deleted -= OnFolderChanged;
            _folderWatcher.Renamed -= OnFolderChanged;
            _folderWatcher.Changed -= OnFolderChanged;
            _folderWatcher.Dispose();
            _folderWatcher = null;
        }

        _debounceTokenSource?.Cancel();
        _debounceTokenSource?.Dispose();
        _debounceTokenSource = null;
    }

    private void OnFolderChanged(object sender, FileSystemEventArgs e)
    {
        // Debounce rapid changes - wait for 300ms of quiet before refreshing
        _debounceTokenSource?.Cancel();
        _debounceTokenSource = new CancellationTokenSource();
        var token = _debounceTokenSource.Token;

        Task.Run(async () =>
        {
            try
            {
                await Task.Delay(DebounceDelayMs, token);

                // Marshal back to UI thread
                DispatcherQueue.TryEnqueue(async () =>
                {
                    if (_selectedFolder != null)
                    {
                        await LoadFolderContentsAsync(_selectedFolder);
                        await GeneratePreviewAsync();
                    }
                });
            }
            catch (TaskCanceledException)
            {
                // Debounce cancelled, another change came in
            }
        }, token);
    }
}

public class OrganizedFolder
{
    public string CategoryId { get; set; } = "";
    public string Name { get; set; } = "";
    public string Icon { get; set; } = "";
    public string Color { get; set; } = "";
    public string Destination { get; set; } = "";
    public int FileCount { get; set; }
    public List<PreviewFile> Files { get; set; } = new();
    public bool IsRuleGroup { get; set; }
    /// <summary>
    /// Child folders for hierarchical display (used by SortIntoSubfolder with nested paths)
    /// </summary>
    public Dictionary<string, OrganizedFolder> ChildFolders { get; set; } = new();
    /// <summary>
    /// Parent folder key (for navigation)
    /// </summary>
    public string? ParentFolderKey { get; set; }
}

public class PreviewFile
{
    public string Name { get; set; } = "";
    public string OriginalPath { get; set; } = "";
    public string Extension { get; set; } = "";
    public ulong Size { get; set; }
    public DateTime DateModified { get; set; }
    public bool IsAlreadyOrganized { get; set; }
    public bool MatchedByRule { get; set; }
    public string? RuleName { get; set; }
}

/// <summary>
/// Tracks a single file move operation for undo functionality
/// </summary>
public class MoveOperation
{
    public string OriginalFolderPath { get; set; } = "";
    public string OriginalFileName { get; set; } = "";
    public string NewFolderPath { get; set; } = "";
    public string NewFileName { get; set; } = "";
    /// <summary>
    /// List of folder paths that were created for this operation (from innermost to outermost).
    /// Used by undo to clean up created folders in reverse order.
    /// </summary>
    public List<string> CreatedFolders { get; set; } = new();
    /// <summary>
    /// List of file paths that were created by copy operations.
    /// These files will be deleted on undo.
    /// </summary>
    public List<string> CopiedFiles { get; set; } = new();
    /// <summary>
    /// Files that were "deleted" (moved to undo staging folder).
    /// Key = staging path, Value = original path
    /// </summary>
    public Dictionary<string, string> DeletedFiles { get; set; } = new();
}
