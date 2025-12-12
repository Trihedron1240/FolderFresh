using System;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using FolderFreshLite.Models;

namespace FolderFreshLite.Services;

/// <summary>
/// Service for managing application settings
/// </summary>
public class SettingsService
{
    private readonly string _settingsPath;
    private AppSettings? _cachedSettings;

    public SettingsService()
    {
        var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var folderFreshPath = Path.Combine(appDataPath, "FolderFresh");
        Directory.CreateDirectory(folderFreshPath);
        _settingsPath = Path.Combine(folderFreshPath, "settings.json");
    }

    /// <summary>
    /// Loads application settings from disk
    /// </summary>
    public async Task<AppSettings> LoadSettingsAsync()
    {
        if (_cachedSettings != null)
        {
            return _cachedSettings;
        }

        if (!File.Exists(_settingsPath))
        {
            _cachedSettings = AppSettings.GetDefaults();
            await SaveSettingsAsync(_cachedSettings);
            return _cachedSettings;
        }

        try
        {
            var json = await File.ReadAllTextAsync(_settingsPath);
            _cachedSettings = JsonSerializer.Deserialize<AppSettings>(json) ?? AppSettings.GetDefaults();
            return _cachedSettings;
        }
        catch
        {
            _cachedSettings = AppSettings.GetDefaults();
            return _cachedSettings;
        }
    }

    /// <summary>
    /// Saves application settings to disk
    /// </summary>
    public async Task SaveSettingsAsync(AppSettings settings)
    {
        _cachedSettings = settings;

        var options = new JsonSerializerOptions
        {
            WriteIndented = true
        };

        var json = JsonSerializer.Serialize(settings, options);
        await File.WriteAllTextAsync(_settingsPath, json);
    }

    /// <summary>
    /// Gets settings synchronously (uses cached if available)
    /// </summary>
    public AppSettings GetSettings()
    {
        if (_cachedSettings != null)
        {
            return _cachedSettings;
        }

        if (!File.Exists(_settingsPath))
        {
            _cachedSettings = AppSettings.GetDefaults();
            return _cachedSettings;
        }

        try
        {
            var json = File.ReadAllText(_settingsPath);
            _cachedSettings = JsonSerializer.Deserialize<AppSettings>(json) ?? AppSettings.GetDefaults();
            return _cachedSettings;
        }
        catch
        {
            _cachedSettings = AppSettings.GetDefaults();
            return _cachedSettings;
        }
    }

    /// <summary>
    /// Clears the cached settings, forcing a reload from disk on next access
    /// </summary>
    public void ClearCache()
    {
        _cachedSettings = null;
    }
}
