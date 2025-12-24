using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using FolderFresh.Models;

namespace FolderFresh.Services;

/// <summary>
/// Service for managing profiles. A profile contains a complete set of rules, categories, and settings.
/// Switching profiles completely replaces the current configuration.
/// </summary>
public class ProfileService
{
    private const string AppFolderName = "FolderFresh";
    private const string ProfilesFileName = "profiles.json";
    public const string DefaultProfileId = "default";

    private readonly string _profilesFilePath;
    private readonly CategoryService _categoryService;
    private readonly RuleService _ruleService;
    private readonly SettingsService _settingsService;
    private List<Profile> _profiles = new();
    private string? _currentProfileId;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public ProfileService(CategoryService categoryService, RuleService ruleService, SettingsService settingsService)
    {
        _categoryService = categoryService;
        _ruleService = ruleService;
        _settingsService = settingsService;

        var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var appFolderPath = Path.Combine(appDataPath, AppFolderName);

        if (!Directory.Exists(appFolderPath))
        {
            Directory.CreateDirectory(appFolderPath);
        }

        _profilesFilePath = Path.Combine(appFolderPath, ProfilesFileName);
    }

    #region CRUD Operations

    /// <summary>
    /// Loads profiles from JSON file. Creates default profile if file doesn't exist.
    /// </summary>
    public async Task<List<Profile>> LoadProfilesAsync()
    {
        try
        {
            if (!File.Exists(_profilesFilePath))
            {
                // First run - create default profile from current defaults
                var defaultProfile = await CreateDefaultProfileAsync();
                _profiles = new List<Profile> { defaultProfile };
                _currentProfileId = defaultProfile.Id;
                await SaveProfilesAsync();

                // Set the current profile ID in settings
                var settings = _settingsService.GetSettings();
                settings.CurrentProfileId = defaultProfile.Id;
                await _settingsService.SaveSettingsAsync(settings);

                return _profiles;
            }

            var json = await File.ReadAllTextAsync(_profilesFilePath);
            var data = JsonSerializer.Deserialize<ProfilesFile>(json, JsonOptions);

            if (data?.Profiles != null && data.Profiles.Count > 0)
            {
                _profiles = data.Profiles;
                // Initialize current profile ID from settings
                var settings = _settingsService.GetSettings();
                _currentProfileId = settings.CurrentProfileId;
            }
            else
            {
                // File exists but empty/corrupt - reset to defaults
                var defaultProfile = await CreateDefaultProfileAsync();
                _profiles = new List<Profile> { defaultProfile };
                await SaveProfilesAsync();
            }

            return _profiles;
        }
        catch (Exception)
        {
            // On any error, return defaults
            var defaultProfile = await CreateDefaultProfileAsync();
            _profiles = new List<Profile> { defaultProfile };
            return _profiles;
        }
    }

    /// <summary>
    /// Saves all profiles to JSON file.
    /// </summary>
    public async Task SaveProfilesAsync()
    {
        try
        {
            var data = new ProfilesFile { Profiles = _profiles };
            var json = JsonSerializer.Serialize(data, JsonOptions);
            await File.WriteAllTextAsync(_profilesFilePath, json);
        }
        catch (Exception)
        {
            // Log error if needed
        }
    }

    /// <summary>
    /// Gets all loaded profiles.
    /// </summary>
    public List<Profile> GetProfiles()
    {
        return _profiles;
    }

    /// <summary>
    /// Gets a profile by ID.
    /// </summary>
    public Profile? GetProfile(string profileId)
    {
        return _profiles.FirstOrDefault(p => p.Id == profileId);
    }

    /// <summary>
    /// Creates a new profile from the current state of rules, categories, and settings.
    /// </summary>
    public async Task<Profile> CreateProfileFromCurrentStateAsync(string name)
    {
        var profile = Profile.Create(name);

        // Reload services from disk to get the latest state (UI may have made changes)
        await _ruleService.LoadRulesAsync();
        await _categoryService.LoadCategoriesAsync();
        _settingsService.ClearCache();

        // Capture current state as JSON
        profile.RulesJson = SerializeRules(_ruleService.GetRules());
        profile.CategoriesJson = SerializeCategories(_categoryService.GetCategories());
        profile.SettingsJson = SerializeSettings(_settingsService.GetSettings());

        _profiles.Add(profile);
        await SaveProfilesAsync();
        return profile;
    }

    /// <summary>
    /// Creates a new empty profile with default settings.
    /// </summary>
    public async Task<Profile> CreateProfileAsync(string name)
    {
        var profile = Profile.Create(name);

        // Use default values
        profile.RulesJson = SerializeRules(new List<Rule>());
        profile.CategoriesJson = SerializeCategories(Category.GetDefaultCategories());
        profile.SettingsJson = SerializeSettings(AppSettings.GetDefaults());

        _profiles.Add(profile);
        await SaveProfilesAsync();
        return profile;
    }

    /// <summary>
    /// Updates an existing profile with the current state of rules, categories, and settings.
    /// </summary>
    public async Task UpdateProfileFromCurrentStateAsync(string profileId)
    {
        var profile = _profiles.FirstOrDefault(p => p.Id == profileId);
        if (profile == null) return;

        // Reload services from disk to get the latest state (UI may have made changes)
        await _ruleService.LoadRulesAsync();
        await _categoryService.LoadCategoriesAsync();
        _settingsService.ClearCache();

        profile.RulesJson = SerializeRules(_ruleService.GetRules());
        profile.CategoriesJson = SerializeCategories(_categoryService.GetCategories());
        profile.SettingsJson = SerializeSettings(_settingsService.GetSettings());
        profile.ModifiedAt = DateTime.Now;

        await SaveProfilesAsync();
    }

    /// <summary>
    /// Updates an existing profile with new data.
    /// </summary>
    public async Task UpdateProfileAsync(Profile profile)
    {
        var index = _profiles.FindIndex(p => p.Id == profile.Id);
        if (index >= 0)
        {
            profile.ModifiedAt = DateTime.Now;
            _profiles[index] = profile;
            await SaveProfilesAsync();
        }
    }

    /// <summary>
    /// Renames a profile.
    /// </summary>
    public async Task RenameProfileAsync(string profileId, string newName)
    {
        var profile = _profiles.FirstOrDefault(p => p.Id == profileId);
        if (profile != null)
        {
            profile.Name = newName;
            profile.ModifiedAt = DateTime.Now;
            await SaveProfilesAsync();
        }
    }

    /// <summary>
    /// Deletes a profile by ID. Cannot delete the last remaining profile.
    /// </summary>
    public async Task<bool> DeleteProfileAsync(string profileId)
    {
        // Don't allow deleting the last profile
        if (_profiles.Count <= 1)
        {
            return false;
        }

        var profile = _profiles.FirstOrDefault(p => p.Id == profileId);
        if (profile != null)
        {
            _profiles.Remove(profile);
            await SaveProfilesAsync();
            return true;
        }

        return false;
    }

    /// <summary>
    /// Duplicates an existing profile with a new name.
    /// If duplicating the active profile, saves current state first to capture latest changes.
    /// </summary>
    public async Task<Profile> DuplicateProfileAsync(string profileId, string newName)
    {
        // If duplicating the active profile, save current state first to get latest changes
        var currentProfileId = GetCurrentProfileId();
        if (profileId == currentProfileId)
        {
            await SaveCurrentProfileStateAsync();
        }

        var source = _profiles.FirstOrDefault(p => p.Id == profileId);
        if (source == null)
        {
            throw new InvalidOperationException($"Profile not found: {profileId}");
        }

        var duplicate = Profile.Create(newName);
        duplicate.RulesJson = source.RulesJson;
        duplicate.CategoriesJson = source.CategoriesJson;
        duplicate.SettingsJson = source.SettingsJson;

        _profiles.Add(duplicate);
        await SaveProfilesAsync();
        return duplicate;
    }

    #endregion

    #region Profile Switching

    /// <summary>
    /// Switches to a profile by loading its rules, categories, and settings into the existing services.
    /// Saves the current profile's state before switching. Also updates the currentProfileId in settings.
    /// </summary>
    public async Task SwitchToProfileAsync(string profileId)
    {
        System.Diagnostics.Debug.WriteLine($"[ProfileService] SwitchToProfileAsync: switching to {profileId}, current={_currentProfileId}");

        // Save the current profile's state BEFORE switching
        await SaveCurrentProfileStateAsync();

        // Load the new profile
        await LoadProfileIntoServicesAsync(profileId);

        System.Diagnostics.Debug.WriteLine($"[ProfileService] SwitchToProfileAsync: completed, now on {_currentProfileId}");
    }

    /// <summary>
    /// Loads a profile's data into the services WITHOUT saving current state first.
    /// Use this on app startup to restore the last active profile.
    /// </summary>
    public async Task LoadProfileIntoServicesAsync(string profileId)
    {
        var profile = _profiles.FirstOrDefault(p => p.Id == profileId);
        if (profile == null)
        {
            throw new InvalidOperationException($"Profile not found: {profileId}");
        }

        // Update the cached current profile ID immediately
        _currentProfileId = profileId;

        // Deserialize and load rules
        var rules = DeserializeRules(profile.RulesJson);
        System.Diagnostics.Debug.WriteLine($"[ProfileService] LoadProfileIntoServicesAsync: loading profile '{profile.Name}' with {rules.Count} rules");

        await _ruleService.SaveRulesAsync(rules);
        await _ruleService.LoadRulesAsync();

        // Deserialize and load categories
        var categories = DeserializeCategories(profile.CategoriesJson);
        await _categoryService.SaveCategoriesAsync(categories);
        await _categoryService.LoadCategoriesAsync();

        // Deserialize and load settings from the profile
        // This ensures each profile has its own organization mode, toggles, etc.
        var profileSettings = DeserializeSettings(profile.SettingsJson);
        // Preserve the current profile ID (we just set it)
        profileSettings.CurrentProfileId = profileId;
        await _settingsService.SaveSettingsAsync(profileSettings);
    }

    /// <summary>
    /// Saves the current state of rules, categories, and settings to the currently active profile.
    /// Call this before switching profiles or when you want to persist changes.
    /// </summary>
    public async Task SaveCurrentProfileStateAsync()
    {
        var currentProfileId = GetCurrentProfileId();
        var currentProfile = _profiles.FirstOrDefault(p => p.Id == currentProfileId);

        if (currentProfile == null)
        {
            System.Diagnostics.Debug.WriteLine($"[ProfileService] SaveCurrentProfileStateAsync: profile not found for id={currentProfileId}");
            return;
        }

        // CRITICAL: Reload services from disk to get the latest state
        // This is necessary because UI components (RulesContent, CategoriesContent) create their own
        // service instances and save directly to JSON files, so our in-memory state may be stale
        await _ruleService.LoadRulesAsync();
        await _categoryService.LoadCategoriesAsync();
        _settingsService.ClearCache();

        var rules = _ruleService.GetRules();
        var categories = _categoryService.GetCategories();
        var settings = _settingsService.GetSettings();

        System.Diagnostics.Debug.WriteLine($"[ProfileService] SaveCurrentProfileStateAsync: profileId={currentProfileId}, rules count={rules.Count}");

        currentProfile.RulesJson = SerializeRules(rules);
        currentProfile.CategoriesJson = SerializeCategories(categories);
        currentProfile.SettingsJson = SerializeSettings(settings);
        currentProfile.ModifiedAt = DateTime.Now;
        await SaveProfilesAsync();
        System.Diagnostics.Debug.WriteLine($"[ProfileService] Saved profile '{currentProfile.Name}' with {rules.Count} rules");
    }

    /// <summary>
    /// Gets the current profile based on the currentProfileId in settings.
    /// Returns the default profile if no current profile is set or if the profile doesn't exist.
    /// </summary>
    public Profile? GetCurrentProfile()
    {
        var settings = _settingsService.GetSettings();
        var currentId = settings.CurrentProfileId;

        if (string.IsNullOrEmpty(currentId))
        {
            return _profiles.FirstOrDefault(p => p.Id == DefaultProfileId)
                   ?? _profiles.FirstOrDefault();
        }

        return _profiles.FirstOrDefault(p => p.Id == currentId)
               ?? _profiles.FirstOrDefault();
    }

    /// <summary>
    /// Gets the ID of the currently active profile.
    /// </summary>
    public string GetCurrentProfileId()
    {
        // Use cached value if available, otherwise get from settings
        if (!string.IsNullOrEmpty(_currentProfileId))
        {
            return _currentProfileId;
        }
        var settings = _settingsService.GetSettings();
        return settings.CurrentProfileId ?? DefaultProfileId;
    }

    #endregion

    #region Serialization Helpers

    private static string SerializeRules(List<Rule> rules)
    {
        var wrapper = new RulesWrapper { Rules = rules };
        return JsonSerializer.Serialize(wrapper, JsonOptions);
    }

    private static List<Rule> DeserializeRules(string json)
    {
        if (string.IsNullOrEmpty(json))
        {
            return new List<Rule>();
        }

        try
        {
            var wrapper = JsonSerializer.Deserialize<RulesWrapper>(json, JsonOptions);
            return wrapper?.Rules ?? new List<Rule>();
        }
        catch
        {
            return new List<Rule>();
        }
    }

    private static string SerializeCategories(List<Category> categories)
    {
        var wrapper = new CategoriesWrapper { Categories = categories };
        return JsonSerializer.Serialize(wrapper, JsonOptions);
    }

    private static List<Category> DeserializeCategories(string json)
    {
        if (string.IsNullOrEmpty(json))
        {
            return Category.GetDefaultCategories();
        }

        try
        {
            var wrapper = JsonSerializer.Deserialize<CategoriesWrapper>(json, JsonOptions);
            return wrapper?.Categories ?? Category.GetDefaultCategories();
        }
        catch
        {
            return Category.GetDefaultCategories();
        }
    }

    private static string SerializeSettings(AppSettings settings)
    {
        return JsonSerializer.Serialize(settings, JsonOptions);
    }

    private static AppSettings DeserializeSettings(string json)
    {
        if (string.IsNullOrEmpty(json))
        {
            return AppSettings.GetDefaults();
        }

        try
        {
            return JsonSerializer.Deserialize<AppSettings>(json, JsonOptions) ?? AppSettings.GetDefaults();
        }
        catch
        {
            return AppSettings.GetDefaults();
        }
    }

    #endregion

    #region Default Profile

    /// <summary>
    /// Creates the default profile by capturing the current state from the services.
    /// This preserves any existing rules/categories/settings from before profiles were implemented.
    /// </summary>
    private async Task<Profile> CreateDefaultProfileAsync()
    {
        var profile = new Profile
        {
            Id = DefaultProfileId,
            Name = "Default",
            CreatedAt = DateTime.Now,
            ModifiedAt = DateTime.Now
        };

        // Capture current state from services (preserves existing rules.json, categories.json, etc.)
        profile.RulesJson = SerializeRules(_ruleService.GetRules());
        profile.CategoriesJson = SerializeCategories(_categoryService.GetCategories());
        profile.SettingsJson = SerializeSettings(_settingsService.GetSettings());

        return profile;
    }

    /// <summary>
    /// Ensures a default profile exists. Creates one if needed.
    /// </summary>
    public async Task EnsureDefaultProfileExistsAsync()
    {
        if (!_profiles.Any(p => p.Id == DefaultProfileId))
        {
            var defaultProfile = await CreateDefaultProfileAsync();
            _profiles.Insert(0, defaultProfile);
            await SaveProfilesAsync();
        }
    }

    #endregion

    #region Import/Export

    /// <summary>
    /// Exports a profile to a .folderfresh file.
    /// </summary>
    public async Task ExportProfileAsync(string profileId, string filePath)
    {
        var profile = _profiles.FirstOrDefault(p => p.Id == profileId);
        if (profile == null)
        {
            throw new InvalidOperationException($"Profile not found: {profileId}");
        }

        var exportData = new ExportedProfile
        {
            Version = 1,
            Name = profile.Name,
            RulesJson = profile.RulesJson,
            CategoriesJson = profile.CategoriesJson,
            SettingsJson = profile.SettingsJson,
            ExportedAt = DateTime.Now
        };

        var json = JsonSerializer.Serialize(exportData, JsonOptions);
        await File.WriteAllTextAsync(filePath, json);
    }

    /// <summary>
    /// Imports a profile from a .folderfresh file.
    /// Returns the imported profile.
    /// </summary>
    public async Task<Profile> ImportProfileAsync(string filePath, string? overrideName = null)
    {
        var json = await File.ReadAllTextAsync(filePath);
        var exportData = JsonSerializer.Deserialize<ExportedProfile>(json, JsonOptions);

        if (exportData == null)
        {
            throw new InvalidOperationException("Invalid profile file format.");
        }

        // Use override name if provided, otherwise use the exported name
        var profileName = overrideName ?? exportData.Name ?? "Imported Profile";

        // Create new profile with imported data
        var profile = Profile.Create(profileName);
        profile.RulesJson = exportData.RulesJson ?? SerializeRules(new List<Rule>());
        profile.CategoriesJson = exportData.CategoriesJson ?? SerializeCategories(Category.GetDefaultCategories());
        profile.SettingsJson = exportData.SettingsJson ?? SerializeSettings(AppSettings.GetDefaults());

        _profiles.Add(profile);
        await SaveProfilesAsync();
        return profile;
    }

    /// <summary>
    /// Checks if a profile name already exists.
    /// </summary>
    public bool ProfileNameExists(string name)
    {
        return _profiles.Any(p => p.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
    }

    /// <summary>
    /// Generates a unique profile name by appending a number if needed.
    /// </summary>
    public string GetUniqueProfileName(string baseName)
    {
        if (!ProfileNameExists(baseName))
        {
            return baseName;
        }

        var counter = 2;
        string newName;
        do
        {
            newName = $"{baseName} ({counter})";
            counter++;
        } while (ProfileNameExists(newName));

        return newName;
    }

    #endregion

    #region Helper Classes

    /// <summary>
    /// Format for exported .folderfresh files.
    /// </summary>
    private class ExportedProfile
    {
        [JsonPropertyName("version")]
        public int Version { get; set; } = 1;

        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("rulesJson")]
        public string? RulesJson { get; set; }

        [JsonPropertyName("categoriesJson")]
        public string? CategoriesJson { get; set; }

        [JsonPropertyName("settingsJson")]
        public string? SettingsJson { get; set; }

        [JsonPropertyName("exportedAt")]
        public DateTime ExportedAt { get; set; }
    }

    private class ProfilesFile
    {
        [JsonPropertyName("profiles")]
        public List<Profile> Profiles { get; set; } = new();

        [JsonPropertyName("version")]
        public int Version { get; set; } = 1;
    }

    private class RulesWrapper
    {
        [JsonPropertyName("rules")]
        public List<Rule> Rules { get; set; } = new();
    }

    private class CategoriesWrapper
    {
        [JsonPropertyName("categories")]
        public List<Category> Categories { get; set; } = new();
    }

    #endregion
}
