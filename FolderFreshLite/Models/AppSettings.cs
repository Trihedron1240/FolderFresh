using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;

namespace FolderFreshLite.Models;

/// <summary>
/// Application-wide settings
/// </summary>
public class AppSettings : INotifyPropertyChanged
{
    private bool _useRulesFirst = true;
    private bool _fallbackToCategories = true;
    private bool _showNotifications = true;
    private bool _confirmBeforeOrganize = false;
    private bool _moveToTrashInsteadOfDelete = true;
    private bool _createUndoHistory = true;
    private int _maxUndoHistory = 10;
    private bool _includeSubfolders = true;
    private bool _ignoreHiddenFiles = true;
    private bool _ignoreSystemFiles = true;

    /// <summary>
    /// Whether to evaluate rules before categories.
    /// If true: Rules are checked first, then categories as fallback.
    /// If false: Only categories are used (original behavior).
    /// </summary>
    [JsonPropertyName("useRulesFirst")]
    public bool UseRulesFirst
    {
        get => _useRulesFirst;
        set => SetProperty(ref _useRulesFirst, value);
    }

    /// <summary>
    /// Whether to fall back to category-based organization when no rule matches.
    /// Only applies when UseRulesFirst is true.
    /// </summary>
    [JsonPropertyName("fallbackToCategories")]
    public bool FallbackToCategories
    {
        get => _fallbackToCategories;
        set => SetProperty(ref _fallbackToCategories, value);
    }

    /// <summary>
    /// Whether to show system notifications for organize operations
    /// </summary>
    [JsonPropertyName("showNotifications")]
    public bool ShowNotifications
    {
        get => _showNotifications;
        set => SetProperty(ref _showNotifications, value);
    }

    /// <summary>
    /// Whether to show a confirmation dialog before organizing
    /// </summary>
    [JsonPropertyName("confirmBeforeOrganize")]
    public bool ConfirmBeforeOrganize
    {
        get => _confirmBeforeOrganize;
        set => SetProperty(ref _confirmBeforeOrganize, value);
    }

    /// <summary>
    /// Whether delete actions move to trash instead of permanent delete
    /// </summary>
    [JsonPropertyName("moveToTrashInsteadOfDelete")]
    public bool MoveToTrashInsteadOfDelete
    {
        get => _moveToTrashInsteadOfDelete;
        set => SetProperty(ref _moveToTrashInsteadOfDelete, value);
    }

    /// <summary>
    /// Whether to track undo history for organize operations
    /// </summary>
    [JsonPropertyName("createUndoHistory")]
    public bool CreateUndoHistory
    {
        get => _createUndoHistory;
        set => SetProperty(ref _createUndoHistory, value);
    }

    /// <summary>
    /// Maximum number of undo operations to keep in history
    /// </summary>
    [JsonPropertyName("maxUndoHistory")]
    public int MaxUndoHistory
    {
        get => _maxUndoHistory;
        set => SetProperty(ref _maxUndoHistory, value);
    }

    /// <summary>
    /// Whether to include files in subfolders when organizing
    /// </summary>
    [JsonPropertyName("includeSubfolders")]
    public bool IncludeSubfolders
    {
        get => _includeSubfolders;
        set => SetProperty(ref _includeSubfolders, value);
    }

    /// <summary>
    /// Whether to ignore hidden files when organizing
    /// </summary>
    [JsonPropertyName("ignoreHiddenFiles")]
    public bool IgnoreHiddenFiles
    {
        get => _ignoreHiddenFiles;
        set => SetProperty(ref _ignoreHiddenFiles, value);
    }

    /// <summary>
    /// Whether to ignore system files when organizing
    /// </summary>
    [JsonPropertyName("ignoreSystemFiles")]
    public bool IgnoreSystemFiles
    {
        get => _ignoreSystemFiles;
        set => SetProperty(ref _ignoreSystemFiles, value);
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? propertyName = null)
    {
        if (Equals(field, value)) return false;
        field = value;
        OnPropertyChanged(propertyName);
        return true;
    }

    /// <summary>
    /// Creates default settings
    /// </summary>
    public static AppSettings GetDefaults()
    {
        return new AppSettings
        {
            UseRulesFirst = true,
            FallbackToCategories = true,
            ShowNotifications = true,
            ConfirmBeforeOrganize = false,
            MoveToTrashInsteadOfDelete = true,
            CreateUndoHistory = true,
            MaxUndoHistory = 10,
            IncludeSubfolders = true,
            IgnoreHiddenFiles = true,
            IgnoreSystemFiles = true
        };
    }
}
