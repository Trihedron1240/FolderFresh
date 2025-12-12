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
            var matchingRule = _ruleService.GetMatchingRule(fileInfo, rules);
            if (matchingRule != null)
            {
                // Check if this rule has an Ignore action - if so, file stays in place
                var hasIgnore = matchingRule.Actions.Any(a => a.Type == ActionType.Ignore);
                if (hasIgnore)
                {
                    // File is ignored by rule - show it staying in its current location
                    result.MatchedBy = OrganizeMatchType.Rule;
                    result.MatchedRuleName = matchingRule.Name;
                    result.MatchedRuleId = matchingRule.Id;
                    result.DestinationPath = null;
                    result.Actions = matchingRule.Actions.ToList();
                    _organizePreview!.Results.Add(result);
                    AddUnmatchedToLegacyPreview(fileInfo, sourceSubfolder);
                    return;
                }

                result.MatchedBy = OrganizeMatchType.Rule;
                result.MatchedRuleName = matchingRule.Name;
                result.MatchedRuleId = matchingRule.Id;
                result.DestinationPath = _ruleService.CalculateDestinationPath(matchingRule, fileInfo, baseFolderPath, _categoryService);
                result.Actions = matchingRule.Actions.ToList();

                // Check if this rule has a Continue action - if so, still check categories
                var hasContinue = matchingRule.Actions.Any(a => a.Type == ActionType.Continue);
                if (!hasContinue)
                {
                    _organizePreview!.Results.Add(result);
                    AddToLegacyPreview(result, fileInfo);
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
        }
        else if (isRootLevel)
        {
            // File stays in root (e.g., rename only)
            groupKey = "_root_";
            groupName = "Root";
            groupIcon = "\U0001F4C1"; // 📁
            groupColor = "#6B7280"; // Gray
        }
        else if (matchingCategory != null)
        {
            // Destination matches a category
            groupKey = matchingCategory.Id;
            groupName = matchingCategory.Name;
            groupIcon = matchingCategory.Icon;
            groupColor = matchingCategory.Color;
        }
        else
        {
            // Custom destination folder (from rule)
            groupKey = $"folder_{relativeDest}";
            groupName = relativeDest;
            groupIcon = "\U0001F4C2"; // 📂
            groupColor = "#60CDFF"; // Accent blue
        }

        if (!_organizedPreview!.TryGetValue(groupKey, out var group))
        {
            group = new OrganizedFolder
            {
                CategoryId = groupKey,
                Name = groupName,
                Icon = groupIcon,
                Color = groupColor,
                Destination = relativeDest,
                FileCount = 0,
                Files = new List<PreviewFile>(),
                IsRuleGroup = false // No longer grouping by rule
            };
            _organizedPreview[groupKey] = group;
        }

        // Use the final filename (may be renamed by rule)
        var finalName = Path.GetFileName(result.DestinationPath);

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
        var folders = _organizedPreview!.Values
            .Where(g => g.FileCount > 0 && g.CategoryId != "_root_")
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
            // Add a ".." entry to go back to root
            AfterFiles.Add(new FileItem
            {
                Name = "..",
                Path = "__PARENT__",
                IsFolder = true,
                DateModified = DateTime.Now
            });

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
        if (folder.Path == "__PARENT__")
        {
            // Go back to root
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
                        var targetPath = Path.Combine(destFolder, fileInfo.Name);

                        // Skip if already in destination
                        if (fileInfo.FullName.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, fileInfo.FullName);
                        File.Move(fileInfo.FullName, destPath);

                        moveOps.Add(new MoveOperation
                        {
                            OriginalFolderPath = fileInfo.DirectoryName!,
                            OriginalFileName = fileInfo.Name,
                            NewFolderPath = destFolder,
                            NewFileName = Path.GetFileName(destPath)
                        });
                    }
                    break;

                case ActionType.CopyToFolder:
                    {
                        var destFolder = action.Value;
                        if (!Path.IsPathRooted(destFolder))
                        {
                            destFolder = Path.Combine(baseFolderPath, destFolder);
                        }
                        var targetPath = Path.Combine(destFolder, fileInfo.Name);

                        // Skip if source and destination are the same
                        if (fileInfo.FullName.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, fileInfo.FullName);
                        File.Copy(fileInfo.FullName, destPath);
                        // Note: Copy doesn't need undo tracking as original remains
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
                            var targetPath = Path.Combine(destFolder, fileInfo.Name);

                            // Skip if already in destination
                            if (fileInfo.FullName.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                                break;

                            Directory.CreateDirectory(destFolder);
                            var destPath = GetUniqueFilePath(targetPath, fileInfo.FullName);
                            File.Move(fileInfo.FullName, destPath);

                            moveOps.Add(new MoveOperation
                            {
                                OriginalFolderPath = fileInfo.DirectoryName!,
                                OriginalFileName = fileInfo.Name,
                                NewFolderPath = destFolder,
                                NewFileName = Path.GetFileName(destPath)
                            });
                        }
                    }
                    break;

                case ActionType.SortIntoSubfolder:
                    {
                        var subfolderName = RuleService.ExpandPattern(action.Value, fileInfo);
                        var destFolder = Path.Combine(baseFolderPath, subfolderName);
                        var targetPath = Path.Combine(destFolder, fileInfo.Name);

                        // Skip if already in destination
                        if (fileInfo.FullName.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, fileInfo.FullName);
                        File.Move(fileInfo.FullName, destPath);

                        moveOps.Add(new MoveOperation
                        {
                            OriginalFolderPath = fileInfo.DirectoryName!,
                            OriginalFileName = fileInfo.Name,
                            NewFolderPath = destFolder,
                            NewFileName = Path.GetFileName(destPath)
                        });
                    }
                    break;

                case ActionType.Rename:
                    {
                        var newName = RuleService.ExpandPattern(action.Value, fileInfo);
                        var targetPath = Path.Combine(fileInfo.DirectoryName!, newName);

                        // Skip if the name is already the same
                        if (fileInfo.FullName.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        var destPath = GetUniqueFilePath(targetPath, fileInfo.FullName);
                        var originalName = fileInfo.Name;
                        File.Move(fileInfo.FullName, destPath);

                        moveOps.Add(new MoveOperation
                        {
                            OriginalFolderPath = fileInfo.DirectoryName!,
                            OriginalFileName = originalName,
                            NewFolderPath = fileInfo.DirectoryName!,
                            NewFileName = Path.GetFileName(destPath)
                        });
                    }
                    break;

                case ActionType.Delete:
                    {
                        var settings = _settingsService.GetSettings();
                        if (settings.MoveToTrashInsteadOfDelete)
                        {
                            // Move to recycle bin using Shell API
                            await MoveToRecycleBinAsync(fileInfo.FullName);
                        }
                        else
                        {
                            // Permanent delete
                            File.Delete(fileInfo.FullName);
                        }
                        // Note: Delete operations can't be undone via our simple undo system
                    }
                    break;

                case ActionType.Ignore:
                case ActionType.Continue:
                    // These don't perform file operations
                    break;
            }
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
        var totalFiles = _lastMoveOperations.Count;

        try
        {
            // Process in reverse order (LIFO) to handle any dependencies
            for (int i = _lastMoveOperations.Count - 1; i >= 0; i--)
            {
                var op = _lastMoveOperations[i];

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
                catch
                {
                    // Skip files that can't be restored
                    errorCount++;
                }
            }

            // Clean up empty folders that were created during organize
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
                    // Check if folder is empty (no files and no subfolders)
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
}
