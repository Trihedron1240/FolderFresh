using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.Json;

namespace FolderFresh.Services;

/// <summary>
/// Service for managing application localization using JSON resource files.
/// </summary>
public class LocalizationService
{
    private static LocalizationService? _instance;
    private Dictionary<string, string> _strings = new();
    private string _currentLanguage = "en-US";

    /// <summary>
    /// Gets the singleton instance of the localization service.
    /// </summary>
    public static LocalizationService Instance => _instance ??= new LocalizationService();

    /// <summary>
    /// Available languages with their display names.
    /// </summary>
    public static readonly Dictionary<string, string> AvailableLanguages = new()
    {
        { "en-US", "English" },
        { "de-DE", "Deutsch" },
        { "uk-UA", "Українська" },
        { "fr-FR", "Français" }
    };

    /// <summary>
    /// Gets the current language code.
    /// </summary>
    public string CurrentLanguage => _currentLanguage;

    /// <summary>
    /// Event raised when the language changes.
    /// </summary>
    public event EventHandler? LanguageChanged;

    private LocalizationService()
    {
        LoadLanguage("en-US");
    }

    /// <summary>
    /// Gets a localized string by key.
    /// </summary>
    public string GetString(string key)
    {
        if (_strings.TryGetValue(key, out var value))
        {
            return value;
        }
        System.Diagnostics.Debug.WriteLine($"[LocalizationService] Missing key: {key}");
        return key;
    }

    /// <summary>
    /// Gets a localized string with format arguments.
    /// </summary>
    public string GetString(string key, params object[] args)
    {
        var format = GetString(key);
        try
        {
            return string.Format(format, args);
        }
        catch (Exception)
        {
            return format;
        }
    }

    /// <summary>
    /// Sets the application language.
    /// </summary>
    public void SetLanguage(string languageCode)
    {
        if (!AvailableLanguages.ContainsKey(languageCode))
        {
            System.Diagnostics.Debug.WriteLine($"[LocalizationService] Unknown language: {languageCode}");
            return;
        }

        LoadLanguage(languageCode);
        _currentLanguage = languageCode;

        // Also set Windows language override for any system components
        try
        {
            Windows.Globalization.ApplicationLanguages.PrimaryLanguageOverride = languageCode;
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[LocalizationService] Could not set PrimaryLanguageOverride: {ex.Message}");
        }

        System.Diagnostics.Debug.WriteLine($"[LocalizationService] Language set to: {languageCode}");
        LanguageChanged?.Invoke(this, EventArgs.Empty);
    }

    private void LoadLanguage(string languageCode)
    {
        try
        {
            var exePath = Environment.ProcessPath;
            if (string.IsNullOrEmpty(exePath))
            {
                System.Diagnostics.Debug.WriteLine("[LocalizationService] Could not get process path");
                LoadDefaultStrings();
                return;
            }

            var appDir = Path.GetDirectoryName(exePath)!;
            var langFile = Path.Combine(appDir, "Languages", $"{languageCode}.json");

            if (!File.Exists(langFile))
            {
                System.Diagnostics.Debug.WriteLine($"[LocalizationService] Language file not found: {langFile}");
                // Fall back to English if the requested language file doesn't exist
                if (languageCode != "en-US")
                {
                    langFile = Path.Combine(appDir, "Languages", "en-US.json");
                }

                if (!File.Exists(langFile))
                {
                    System.Diagnostics.Debug.WriteLine("[LocalizationService] English language file not found, using defaults");
                    LoadDefaultStrings();
                    return;
                }
            }

            var json = File.ReadAllText(langFile);
            var strings = JsonSerializer.Deserialize<Dictionary<string, string>>(json);

            if (strings != null)
            {
                _strings = strings;
                System.Diagnostics.Debug.WriteLine($"[LocalizationService] Loaded {_strings.Count} strings for {languageCode}");
            }
            else
            {
                LoadDefaultStrings();
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[LocalizationService] Error loading language: {ex.Message}");
            LoadDefaultStrings();
        }
    }

    private void LoadDefaultStrings()
    {
        // Default English strings as fallback
        _strings = new Dictionary<string, string>
        {
            // Navigation
            { "Nav_Home", "Home" },
            { "Nav_Folders", "Folders" },
            { "Nav_Rules", "Rules" },
            { "Nav_Categories", "Categories" },
            { "Nav_Profiles", "Profiles" },
            { "Nav_Snapshots", "Snapshots" },
            { "Nav_Settings", "Settings" },

            // Main Page
            { "SelectFolder", "Select Folder..." },
            { "Current", "CURRENT" },
            { "After", "AFTER" },
            { "SelectFolderToPreview", "Select a folder to preview" },
            { "OrganizedPreview", "Organized preview" },
            { "OrganizeNow", "Organize Now" },
            { "Undo", "Undo" },

            // Settings
            { "Settings_Title", "Settings" },
            { "Settings_Language", "LANGUAGE" },
            { "Settings_LanguageDesc", "Choose your preferred language" },
            { "Settings_LanguageRestart", "Restart the app for changes to take effect" },
            { "Settings_OrganizationMode", "ORGANIZATION MODE" },
            { "Settings_OrganizationModeDesc", "Choose how files are matched for organization" },
            { "Settings_RulesFirst", "Rules first, then categories" },
            { "Settings_RulesFirstDesc", "Recommended - Rules are checked first, unmatched files use categories" },
            { "Settings_CategoriesOnly", "Categories only" },
            { "Settings_CategoriesOnlyDesc", "Simple mode - Only use category-based organization" },
            { "Settings_RulesOnly", "Rules only" },
            { "Settings_RulesOnlyDesc", "Advanced - Only files matching rules are organized" },
            { "Settings_Notifications", "NOTIFICATIONS" },
            { "Settings_ShowNotifications", "Show notifications when organizing" },
            { "Settings_ShowNotificationsDesc", "Display a notification when files are organized" },
            { "Settings_FileScanning", "FILE SCANNING" },
            { "Settings_IncludeSubfolders", "Include subfolders" },
            { "Settings_IncludeSubfoldersDesc", "Organize files inside subfolders, not just root" },
            { "Settings_IgnoreHidden", "Ignore hidden files" },
            { "Settings_IgnoreHiddenDesc", "Skip files and folders marked as hidden" },
            { "Settings_IgnoreSystem", "Ignore system files" },
            { "Settings_IgnoreSystemDesc", "Skip files and folders marked as system" },
            { "Settings_SystemTray", "SYSTEM TRAY" },
            { "Settings_MinimizeToTray", "Minimize to tray" },
            { "Settings_MinimizeToTrayDesc", "Minimize to system tray instead of taskbar" },
            { "Settings_CloseToTray", "Close to tray" },
            { "Settings_CloseToTrayDesc", "Keep running in tray when closing the window" },
            { "Settings_StartMinimized", "Start minimized" },
            { "Settings_StartMinimizedDesc", "Start the app minimized to tray" },
            { "Settings_RunOnStartup", "Run on startup" },
            { "Settings_RunOnStartupDesc", "Automatically start FolderFresh when you log in" },
            { "Settings_Safety", "SAFETY" },
            { "Settings_RecycleBin", "Move to Recycle Bin instead of permanent delete" },
            { "Settings_RecycleBinDesc", "When using Delete action, files go to Recycle Bin" },
            { "Settings_Confirm", "Confirm before organizing" },
            { "Settings_ConfirmDesc", "Show confirmation dialog before moving files" },
            { "Settings_About", "ABOUT" },
            { "Settings_Version", "Version 3.0.2-beta" },
            { "Settings_Description", "A powerful file organization tool with rules and categories" },
        };
    }

    /// <summary>
    /// Gets the current system language if it's supported, otherwise returns English.
    /// </summary>
    public string GetSystemLanguageOrDefault()
    {
        try
        {
            var systemLanguage = CultureInfo.CurrentUICulture.Name;

            if (AvailableLanguages.ContainsKey(systemLanguage))
            {
                return systemLanguage;
            }

            var languageFamily = systemLanguage.Split('-')[0];
            foreach (var lang in AvailableLanguages.Keys)
            {
                if (lang.StartsWith(languageFamily, StringComparison.OrdinalIgnoreCase))
                {
                    return lang;
                }
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[LocalizationService] Error getting system language: {ex.Message}");
        }

        return "en-US";
    }

    /// <summary>
    /// Gets the display name for a language code.
    /// </summary>
    public string GetLanguageDisplayName(string languageCode)
    {
        return AvailableLanguages.TryGetValue(languageCode, out var name) ? name : languageCode;
    }
}

/// <summary>
/// Extension class for easy access to localized strings.
/// </summary>
public static class Loc
{
    /// <summary>
    /// Gets a localized string by key.
    /// </summary>
    public static string Get(string key) => LocalizationService.Instance.GetString(key);

    /// <summary>
    /// Gets a localized string with format arguments.
    /// </summary>
    public static string Get(string key, params object[] args) => LocalizationService.Instance.GetString(key, args);
}
