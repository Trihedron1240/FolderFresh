using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using FolderFresh.Models;
using FolderFresh.Services;
using FolderFresh.SetupAdvisor;

namespace FolderFresh.ViewModels;

public sealed class SmartSetupViewModel : ObservableObject
{
    private readonly SetupAdvisorService _advisor = new();
    private CategoryService? _categoryService;
    private RuleService? _ruleService;
    private SettingsService? _settingsService;

    private string? _selectedFolderPath;
    private bool _includeSubfolders = true;
    private int _maxFiles = 500;
    private bool _isBusy;
    private string _statusMessage = "Select a folder and analyze it to generate starter categories and rules.";

    public ObservableCollection<SmartSetupCategoryItem> CategorySuggestions { get; } = new();
    public ObservableCollection<SmartSetupRuleItem> RuleSuggestions { get; } = new();

    public event EventHandler? SuggestionsApplied;

    public SmartSetupViewModel()
    {
        CategorySuggestions.CollectionChanged += (_, _) => RaiseStateProperties();
        RuleSuggestions.CollectionChanged += (_, _) => RaiseStateProperties();
    }

    public string? SelectedFolderPath
    {
        get => _selectedFolderPath;
        private set
        {
            if (SetProperty(ref _selectedFolderPath, value))
            {
                RaiseStateProperties();
            }
        }
    }

    public bool IncludeSubfolders
    {
        get => _includeSubfolders;
        set
        {
            if (SetProperty(ref _includeSubfolders, value))
            {
                RaiseStateProperties();
            }
        }
    }

    public int MaxFiles
    {
        get => _maxFiles;
        set
        {
            var normalized = Math.Max(1, value);
            if (SetProperty(ref _maxFiles, normalized))
            {
                RaiseStateProperties();
            }
        }
    }

    public bool IsBusy
    {
        get => _isBusy;
        private set
        {
            if (SetProperty(ref _isBusy, value))
            {
                RaiseStateProperties();
            }
        }
    }

    public string StatusMessage
    {
        get => _statusMessage;
        private set => SetProperty(ref _statusMessage, value);
    }

    public string MaxFilesSummary => $"Max files scanned: {MaxFiles}";
    public bool HasSelectedFolder => !string.IsNullOrWhiteSpace(SelectedFolderPath) && Directory.Exists(SelectedFolderPath);
    public bool HasSuggestions => CategorySuggestions.Count > 0 || RuleSuggestions.Count > 0;
    public bool CanAnalyze => !IsBusy && HasSelectedFolder;
    public bool CanApply => !IsBusy && (CategorySuggestions.Any(c => c.IsSelected) || RuleSuggestions.Any(r => r.IsSelected));

    public void Initialize(CategoryService categoryService, RuleService ruleService, SettingsService settingsService)
    {
        _categoryService = categoryService;
        _ruleService = ruleService;
        _settingsService = settingsService;

        var settings = _settingsService.GetSettings();
        IncludeSubfolders = settings.IncludeSubfolders;
    }

    public void SetSelectedFolder(string? folderPath)
    {
        SelectedFolderPath = folderPath;
        if (HasSelectedFolder && !HasSuggestions)
        {
            StatusMessage = $"Ready to analyze {folderPath}";
        }
        else if (!HasSelectedFolder)
        {
            StatusMessage = "Select a folder and analyze it to generate starter categories and rules.";
        }
    }

    public async Task AnalyzeAsync()
    {
        if (!CanAnalyze || string.IsNullOrWhiteSpace(SelectedFolderPath))
        {
            StatusMessage = "Select a folder first.";
            return;
        }

        try
        {
            IsBusy = true;
            StatusMessage = "Analyzing folder contents...";
            ClearSuggestions();

            var result = await _advisor.AnalyzeAsync(new FolderAnalysisOptions
            {
                SourcePath = SelectedFolderPath,
                Recursive = IncludeSubfolders,
                MaxFiles = MaxFiles
            });

            foreach (var category in result.Categories)
            {
                var item = new SmartSetupCategoryItem(category);
                HookCategoryItem(item);
                CategorySuggestions.Add(item);
            }

            foreach (var rule in result.Rules)
            {
                var targetName = CategorySuggestions.FirstOrDefault(c => c.Key == rule.TargetCategoryKey)?.Name ?? rule.TargetCategoryKey;
                var item = new SmartSetupRuleItem(rule, targetName);
                HookRuleItem(item);
                RuleSuggestions.Add(item);
            }

            StatusMessage = result.Categories.Count == 0
                ? "No strong suggestions were found for this folder."
                : $"Found {result.Categories.Count} category suggestions and {result.Rules.Count} rule suggestions.";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Smart Setup failed: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    public async Task ApplyAsync()
    {
        if (_categoryService == null || _ruleService == null)
        {
            StatusMessage = "Smart Setup is not initialized yet.";
            return;
        }

        if (!CanApply)
        {
            StatusMessage = "Select at least one category or rule to apply.";
            return;
        }

        try
        {
            IsBusy = true;
            StatusMessage = "Applying selected suggestions...";

            var categories = _categoryService.GetAllCategories();
            if (categories.Count == 0)
            {
                categories = await _categoryService.LoadCategoriesAsync();
            }

            var rules = _ruleService.GetRules();
            if (rules.Count == 0)
            {
                rules = await _ruleService.LoadRulesAsync();
            }

            var selectedRules = RuleSuggestions.Where(r => r.IsSelected).ToList();
            var requiredCategoryKeys = CategorySuggestions
                .Where(c => c.IsSelected || selectedRules.Any(r => r.TargetCategoryKey == c.Key))
                .Select(c => c.Key)
                .ToHashSet(StringComparer.OrdinalIgnoreCase);

            var createdCategories = new Dictionary<string, Category>(StringComparer.OrdinalIgnoreCase);
            var createdCategoryCount = 0;
            var createdRuleCount = 0;

            foreach (var categoryItem in CategorySuggestions.Where(c => requiredCategoryKeys.Contains(c.Key)))
            {
                var existingCategory = categories.FirstOrDefault(c =>
                    c.Name.Equals(categoryItem.Name, StringComparison.OrdinalIgnoreCase) &&
                    c.Destination.Equals(categoryItem.Destination, StringComparison.OrdinalIgnoreCase));

                if (existingCategory == null)
                {
                    existingCategory = new Category
                    {
                        Id = MakeUniqueCategoryId(categoryItem.Key, categories),
                        Name = categoryItem.Name,
                        Destination = categoryItem.Destination,
                        Icon = categoryItem.Icon,
                        Color = categoryItem.Color,
                        Extensions = categoryItem.Extensions.ToList(),
                        IsDefault = false,
                        IsEnabled = true
                    };

                    await _categoryService.AddCategoryAsync(existingCategory);
                    categories = _categoryService.GetAllCategories();
                    createdCategoryCount++;
                }

                createdCategories[categoryItem.Key] = existingCategory;
            }

            foreach (var ruleItem in selectedRules)
            {
                if (!createdCategories.TryGetValue(ruleItem.TargetCategoryKey, out var targetCategory))
                {
                    continue;
                }

                if (RuleExists(rules, ruleItem.MatchToken, targetCategory.Id))
                {
                    continue;
                }

                var rule = Rule.Create(ruleItem.Name);
                rule.Conditions = new ConditionGroup
                {
                    MatchType = ConditionMatchType.All,
                    Conditions = new List<Condition>
                    {
                        new()
                        {
                            Attribute = ConditionAttribute.Name,
                            Operator = ConditionOperator.Contains,
                            Value = ruleItem.MatchToken
                        }
                    }
                };
                rule.Actions = new List<RuleAction>
                {
                    new()
                    {
                        Type = ActionType.MoveToCategory,
                        Value = targetCategory.Id
                    }
                };

                await _ruleService.AddRuleAsync(rule);
                rules = _ruleService.GetRules();
                createdRuleCount++;
            }

            StatusMessage = $"Applied {createdCategoryCount} categories and {createdRuleCount} rules.";
            SuggestionsApplied?.Invoke(this, EventArgs.Empty);
        }
        catch (Exception ex)
        {
            StatusMessage = $"Apply failed: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    private static bool RuleExists(IEnumerable<Rule> rules, string matchToken, string categoryId)
    {
        return rules.Any(rule =>
            rule.Actions.Any(action => action.Type == ActionType.MoveToCategory && action.Value == categoryId) &&
            rule.Conditions.Conditions.Any(condition =>
                condition.Attribute == ConditionAttribute.Name &&
                condition.Operator == ConditionOperator.Contains &&
                condition.Value.Equals(matchToken, StringComparison.OrdinalIgnoreCase)));
    }

    private static string MakeUniqueCategoryId(string baseKey, List<Category> categories)
    {
        var candidate = baseKey;
        var suffix = 2;
        var existingIds = categories.Select(c => c.Id).ToHashSet(StringComparer.OrdinalIgnoreCase);

        while (existingIds.Contains(candidate))
        {
            candidate = $"{baseKey}-{suffix}";
            suffix++;
        }

        return candidate;
    }

    private void ClearSuggestions()
    {
        foreach (var category in CategorySuggestions)
        {
            category.PropertyChanged -= SuggestionItem_PropertyChanged;
        }

        foreach (var rule in RuleSuggestions)
        {
            rule.PropertyChanged -= SuggestionItem_PropertyChanged;
        }

        CategorySuggestions.Clear();
        RuleSuggestions.Clear();
        RaiseStateProperties();
    }

    private void HookCategoryItem(SmartSetupCategoryItem item)
    {
        item.PropertyChanged += SuggestionItem_PropertyChanged;
    }

    private void HookRuleItem(SmartSetupRuleItem item)
    {
        item.PropertyChanged += SuggestionItem_PropertyChanged;
    }

    private void SuggestionItem_PropertyChanged(object? sender, System.ComponentModel.PropertyChangedEventArgs e)
    {
        if (sender is SmartSetupCategoryItem categoryItem && e.PropertyName == nameof(SmartSetupCategoryItem.Name))
        {
            foreach (var rule in RuleSuggestions.Where(r => r.TargetCategoryKey == categoryItem.Key))
            {
                rule.TargetCategoryName = categoryItem.Name;
            }
        }

        RaiseStateProperties();
    }

    private void RaiseStateProperties()
    {
        OnPropertyChanged(nameof(MaxFilesSummary));
        OnPropertyChanged(nameof(HasSelectedFolder));
        OnPropertyChanged(nameof(HasSuggestions));
        OnPropertyChanged(nameof(CanAnalyze));
        OnPropertyChanged(nameof(CanApply));
    }
}

public sealed class SmartSetupCategoryItem : ObservableObject
{
    private bool _isSelected = true;
    private string _name;
    private string _destination;

    public SmartSetupCategoryItem(SuggestedCategory suggestion)
    {
        Key = suggestion.Key;
        _name = suggestion.Name;
        _destination = suggestion.Destination;
        Icon = suggestion.Icon;
        Color = suggestion.Color;
        Extensions = suggestion.Extensions;
        Reason = suggestion.Reason;
        FileCount = suggestion.FileCount;
        SampleFiles = suggestion.SampleFiles;
    }

    public string Key { get; }
    public string Icon { get; }
    public string Color { get; }
    public IReadOnlyList<string> Extensions { get; }
    public string Reason { get; }
    public int FileCount { get; }
    public IReadOnlyList<string> SampleFiles { get; }
    public string ExtensionsDisplay => Extensions.Count == 0 ? "No extensions" : string.Join(", ", Extensions);

    public bool IsSelected
    {
        get => _isSelected;
        set => SetProperty(ref _isSelected, value);
    }

    public string Name
    {
        get => _name;
        set => SetProperty(ref _name, value);
    }

    public string Destination
    {
        get => _destination;
        set => SetProperty(ref _destination, value);
    }
}

public sealed class SmartSetupRuleItem : ObservableObject
{
    private bool _isSelected = true;
    private string _name;
    private string _matchToken;
    private string _targetCategoryName;

    public SmartSetupRuleItem(SuggestedRule suggestion, string targetCategoryName)
    {
        Key = suggestion.Key;
        TargetCategoryKey = suggestion.TargetCategoryKey;
        _name = suggestion.Name;
        _matchToken = suggestion.MatchToken;
        _targetCategoryName = targetCategoryName;
        Reason = suggestion.Reason;
        MatchCount = suggestion.MatchCount;
        SampleFiles = suggestion.SampleFiles;
    }

    public string Key { get; }
    public string TargetCategoryKey { get; }
    public string Reason { get; }
    public int MatchCount { get; }
    public IReadOnlyList<string> SampleFiles { get; }

    public bool IsSelected
    {
        get => _isSelected;
        set => SetProperty(ref _isSelected, value);
    }

    public string Name
    {
        get => _name;
        set => SetProperty(ref _name, value);
    }

    public string MatchToken
    {
        get => _matchToken;
        set
        {
            if (SetProperty(ref _matchToken, value))
            {
                OnPropertyChanged(nameof(RuleSummaryText));
            }
        }
    }

    public string TargetCategoryName
    {
        get => _targetCategoryName;
        set
        {
            if (SetProperty(ref _targetCategoryName, value))
            {
                OnPropertyChanged(nameof(RuleSummaryText));
            }
        }
    }

    public string RuleSummaryText => $"If a file name contains {MatchToken}, move it to {TargetCategoryName}.";
}
