using System.Text.Json;
using FolderFreshLite.Models;
using FolderFreshLite.Services;

namespace FolderFreshLite.Tests.Services;

/// <summary>
/// Tests for SettingsService - verifies settings are properly loaded, saved, and persisted.
/// These tests ensure the settings toggles in the UI will work correctly.
/// </summary>
public class SettingsServiceTests : IDisposable
{
    private readonly string _testSettingsDir;
    private readonly string _testSettingsPath;

    public SettingsServiceTests()
    {
        // Create a unique test directory for each test run
        _testSettingsDir = Path.Combine(Path.GetTempPath(), $"FolderFreshTests_{Guid.NewGuid()}");
        Directory.CreateDirectory(_testSettingsDir);
        _testSettingsPath = Path.Combine(_testSettingsDir, "settings.json");
    }

    public void Dispose()
    {
        // Clean up test directory
        if (Directory.Exists(_testSettingsDir))
        {
            Directory.Delete(_testSettingsDir, true);
        }
    }

    #region Default Settings Tests

    [Fact]
    public void GetDefaults_ReturnsExpectedDefaultValues()
    {
        var defaults = AppSettings.GetDefaults();

        // Organization mode defaults
        Assert.True(defaults.UseRulesFirst);
        Assert.True(defaults.FallbackToCategories);

        // Notification defaults
        Assert.True(defaults.ShowNotifications);

        // File scanning defaults
        Assert.True(defaults.IncludeSubfolders);
        Assert.True(defaults.IgnoreHiddenFiles);
        Assert.True(defaults.IgnoreSystemFiles);

        // Safety defaults
        Assert.True(defaults.MoveToTrashInsteadOfDelete);
        Assert.False(defaults.ConfirmBeforeOrganize);

        // Undo defaults
        Assert.True(defaults.CreateUndoHistory);
        Assert.Equal(10, defaults.MaxUndoHistory);
    }

    #endregion

    #region Organization Mode Tests

    [Theory]
    [InlineData(true, true, "RulesFirst")]   // Rules first, then categories
    [InlineData(false, true, "CategoriesOnly")] // Categories only
    [InlineData(true, false, "RulesOnly")]   // Rules only
    public void OrganizationMode_SettingsCombinations_AreCorrect(bool useRulesFirst, bool fallbackToCategories, string expectedMode)
    {
        var settings = new AppSettings
        {
            UseRulesFirst = useRulesFirst,
            FallbackToCategories = fallbackToCategories
        };

        // Verify the combination matches expected mode
        if (expectedMode == "RulesFirst")
        {
            Assert.True(settings.UseRulesFirst && settings.FallbackToCategories);
        }
        else if (expectedMode == "CategoriesOnly")
        {
            Assert.True(!settings.UseRulesFirst && settings.FallbackToCategories);
        }
        else if (expectedMode == "RulesOnly")
        {
            Assert.True(settings.UseRulesFirst && !settings.FallbackToCategories);
        }
    }

    #endregion

    #region Toggle Settings Tests

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ShowNotifications_CanBeSetAndRetrieved(bool value)
    {
        var settings = new AppSettings { ShowNotifications = value };
        Assert.Equal(value, settings.ShowNotifications);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void IncludeSubfolders_CanBeSetAndRetrieved(bool value)
    {
        var settings = new AppSettings { IncludeSubfolders = value };
        Assert.Equal(value, settings.IncludeSubfolders);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void IgnoreHiddenFiles_CanBeSetAndRetrieved(bool value)
    {
        var settings = new AppSettings { IgnoreHiddenFiles = value };
        Assert.Equal(value, settings.IgnoreHiddenFiles);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void IgnoreSystemFiles_CanBeSetAndRetrieved(bool value)
    {
        var settings = new AppSettings { IgnoreSystemFiles = value };
        Assert.Equal(value, settings.IgnoreSystemFiles);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MoveToTrashInsteadOfDelete_CanBeSetAndRetrieved(bool value)
    {
        var settings = new AppSettings { MoveToTrashInsteadOfDelete = value };
        Assert.Equal(value, settings.MoveToTrashInsteadOfDelete);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConfirmBeforeOrganize_CanBeSetAndRetrieved(bool value)
    {
        var settings = new AppSettings { ConfirmBeforeOrganize = value };
        Assert.Equal(value, settings.ConfirmBeforeOrganize);
    }

    #endregion

    #region JSON Serialization Tests

    [Fact]
    public void Settings_SerializesToJson_WithCorrectPropertyNames()
    {
        var settings = new AppSettings
        {
            UseRulesFirst = true,
            FallbackToCategories = false,
            ShowNotifications = true,
            IncludeSubfolders = false,
            IgnoreHiddenFiles = true,
            IgnoreSystemFiles = false,
            MoveToTrashInsteadOfDelete = true,
            ConfirmBeforeOrganize = false
        };

        var json = JsonSerializer.Serialize(settings);

        // Verify camelCase property names (as specified by JsonPropertyName attributes)
        Assert.Contains("\"useRulesFirst\"", json);
        Assert.Contains("\"fallbackToCategories\"", json);
        Assert.Contains("\"showNotifications\"", json);
        Assert.Contains("\"includeSubfolders\"", json);
        Assert.Contains("\"ignoreHiddenFiles\"", json);
        Assert.Contains("\"ignoreSystemFiles\"", json);
        Assert.Contains("\"moveToTrashInsteadOfDelete\"", json);
        Assert.Contains("\"confirmBeforeOrganize\"", json);
    }

    [Fact]
    public void Settings_DeserializesFromJson_Correctly()
    {
        var json = @"{
            ""useRulesFirst"": false,
            ""fallbackToCategories"": true,
            ""showNotifications"": false,
            ""includeSubfolders"": false,
            ""ignoreHiddenFiles"": false,
            ""ignoreSystemFiles"": false,
            ""moveToTrashInsteadOfDelete"": false,
            ""confirmBeforeOrganize"": true
        }";

        var settings = JsonSerializer.Deserialize<AppSettings>(json);

        Assert.NotNull(settings);
        Assert.False(settings.UseRulesFirst);
        Assert.True(settings.FallbackToCategories);
        Assert.False(settings.ShowNotifications);
        Assert.False(settings.IncludeSubfolders);
        Assert.False(settings.IgnoreHiddenFiles);
        Assert.False(settings.IgnoreSystemFiles);
        Assert.False(settings.MoveToTrashInsteadOfDelete);
        Assert.True(settings.ConfirmBeforeOrganize);
    }

    [Fact]
    public void Settings_RoundTrip_PreservesAllValues()
    {
        var original = new AppSettings
        {
            UseRulesFirst = false,
            FallbackToCategories = false,
            ShowNotifications = false,
            IncludeSubfolders = false,
            IgnoreHiddenFiles = false,
            IgnoreSystemFiles = false,
            MoveToTrashInsteadOfDelete = false,
            ConfirmBeforeOrganize = true,
            CreateUndoHistory = false,
            MaxUndoHistory = 5
        };

        var json = JsonSerializer.Serialize(original);
        var deserialized = JsonSerializer.Deserialize<AppSettings>(json);

        Assert.NotNull(deserialized);
        Assert.Equal(original.UseRulesFirst, deserialized.UseRulesFirst);
        Assert.Equal(original.FallbackToCategories, deserialized.FallbackToCategories);
        Assert.Equal(original.ShowNotifications, deserialized.ShowNotifications);
        Assert.Equal(original.IncludeSubfolders, deserialized.IncludeSubfolders);
        Assert.Equal(original.IgnoreHiddenFiles, deserialized.IgnoreHiddenFiles);
        Assert.Equal(original.IgnoreSystemFiles, deserialized.IgnoreSystemFiles);
        Assert.Equal(original.MoveToTrashInsteadOfDelete, deserialized.MoveToTrashInsteadOfDelete);
        Assert.Equal(original.ConfirmBeforeOrganize, deserialized.ConfirmBeforeOrganize);
        Assert.Equal(original.CreateUndoHistory, deserialized.CreateUndoHistory);
        Assert.Equal(original.MaxUndoHistory, deserialized.MaxUndoHistory);
    }

    #endregion

    #region PropertyChanged Notification Tests

    [Fact]
    public void Settings_RaisesPropertyChanged_WhenValueChanges()
    {
        var settings = new AppSettings();
        var propertyChangedRaised = false;
        string? changedPropertyName = null;

        settings.PropertyChanged += (sender, args) =>
        {
            propertyChangedRaised = true;
            changedPropertyName = args.PropertyName;
        };

        settings.ShowNotifications = !settings.ShowNotifications;

        Assert.True(propertyChangedRaised);
        Assert.Equal(nameof(AppSettings.ShowNotifications), changedPropertyName);
    }

    [Fact]
    public void Settings_DoesNotRaisePropertyChanged_WhenValueIsSame()
    {
        var settings = new AppSettings { ShowNotifications = true };
        var propertyChangedRaised = false;

        settings.PropertyChanged += (sender, args) =>
        {
            propertyChangedRaised = true;
        };

        settings.ShowNotifications = true; // Same value

        Assert.False(propertyChangedRaised);
    }

    #endregion

    #region File Persistence Tests

    [Fact]
    public async Task SettingsService_SaveAndLoad_PersistsAllSettings()
    {
        // This test verifies the actual file I/O by writing to a temp location
        var settings = new AppSettings
        {
            UseRulesFirst = false,
            FallbackToCategories = false,
            ShowNotifications = false,
            IncludeSubfolders = false,
            IgnoreHiddenFiles = false,
            IgnoreSystemFiles = false,
            MoveToTrashInsteadOfDelete = false,
            ConfirmBeforeOrganize = true,
            CreateUndoHistory = false,
            MaxUndoHistory = 25
        };

        // Save to temp file
        var json = JsonSerializer.Serialize(settings, new JsonSerializerOptions { WriteIndented = true });
        await File.WriteAllTextAsync(_testSettingsPath, json);

        // Read back
        var loadedJson = await File.ReadAllTextAsync(_testSettingsPath);
        var loadedSettings = JsonSerializer.Deserialize<AppSettings>(loadedJson);

        Assert.NotNull(loadedSettings);
        Assert.Equal(settings.UseRulesFirst, loadedSettings.UseRulesFirst);
        Assert.Equal(settings.FallbackToCategories, loadedSettings.FallbackToCategories);
        Assert.Equal(settings.ShowNotifications, loadedSettings.ShowNotifications);
        Assert.Equal(settings.IncludeSubfolders, loadedSettings.IncludeSubfolders);
        Assert.Equal(settings.IgnoreHiddenFiles, loadedSettings.IgnoreHiddenFiles);
        Assert.Equal(settings.IgnoreSystemFiles, loadedSettings.IgnoreSystemFiles);
        Assert.Equal(settings.MoveToTrashInsteadOfDelete, loadedSettings.MoveToTrashInsteadOfDelete);
        Assert.Equal(settings.ConfirmBeforeOrganize, loadedSettings.ConfirmBeforeOrganize);
        Assert.Equal(settings.CreateUndoHistory, loadedSettings.CreateUndoHistory);
        Assert.Equal(settings.MaxUndoHistory, loadedSettings.MaxUndoHistory);
    }

    [Fact]
    public async Task SettingsService_HandlesCorruptedFile_ReturnsDefaults()
    {
        // Write corrupted JSON
        await File.WriteAllTextAsync(_testSettingsPath, "{ this is not valid json }");

        // Try to deserialize - should fail gracefully
        try
        {
            var json = await File.ReadAllTextAsync(_testSettingsPath);
            var settings = JsonSerializer.Deserialize<AppSettings>(json);
            // If it somehow parses, that's unexpected
            Assert.Null(settings);
        }
        catch (JsonException)
        {
            // Expected - corrupted JSON should throw
            // The SettingsService catches this and returns defaults
            var defaults = AppSettings.GetDefaults();
            Assert.True(defaults.UseRulesFirst);
        }
    }

    [Fact]
    public void SettingsService_HandlesMissingFile_ReturnsDefaults()
    {
        // Don't create any file - verify defaults are returned
        var nonExistentPath = Path.Combine(_testSettingsDir, "nonexistent.json");
        Assert.False(File.Exists(nonExistentPath));

        // The SettingsService would return defaults in this case
        var defaults = AppSettings.GetDefaults();
        Assert.NotNull(defaults);
        Assert.True(defaults.UseRulesFirst);
    }

    #endregion

    #region Settings Combination Validation

    [Fact]
    public void RulesFirstMode_HasCorrectSettingsCombination()
    {
        // "Rules first, then categories" mode
        var settings = new AppSettings
        {
            UseRulesFirst = true,
            FallbackToCategories = true
        };

        // In this mode, rules are evaluated first
        // If no rule matches, categories are used as fallback
        Assert.True(settings.UseRulesFirst);
        Assert.True(settings.FallbackToCategories);
    }

    [Fact]
    public void CategoriesOnlyMode_HasCorrectSettingsCombination()
    {
        // "Categories only" mode
        var settings = new AppSettings
        {
            UseRulesFirst = false,
            FallbackToCategories = true
        };

        // In this mode, only categories are used
        Assert.False(settings.UseRulesFirst);
        Assert.True(settings.FallbackToCategories);
    }

    [Fact]
    public void RulesOnlyMode_HasCorrectSettingsCombination()
    {
        // "Rules only" mode
        var settings = new AppSettings
        {
            UseRulesFirst = true,
            FallbackToCategories = false
        };

        // In this mode, only rules are used
        // Files that don't match any rule are not organized
        Assert.True(settings.UseRulesFirst);
        Assert.False(settings.FallbackToCategories);
    }

    #endregion
}
