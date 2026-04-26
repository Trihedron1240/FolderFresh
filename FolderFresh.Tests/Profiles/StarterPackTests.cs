using System.Text.Json;
using FolderFresh.Services;

namespace FolderFresh.Tests.Profiles;

public class StarterPackTests
{
    [Fact]
    public void StarterPacks_AreReadableImportProfiles()
    {
        var starterPackDirectory = Path.Combine(AppContext.BaseDirectory, "StarterPacks");
        var packFiles = Directory.GetFiles(starterPackDirectory, "*.folderfresh");

        Assert.NotEmpty(packFiles);

        foreach (var packFile in packFiles)
        {
            using var document = JsonDocument.Parse(File.ReadAllText(packFile));
            var root = document.RootElement;

            Assert.True(root.TryGetProperty("name", out var name));
            Assert.False(string.IsNullOrWhiteSpace(name.GetString()));

            Assert.True(root.TryGetProperty("rules", out var rulesWrapper));
            Assert.True(rulesWrapper.TryGetProperty("rules", out var rules));
            Assert.True(rules.GetArrayLength() > 0);

            foreach (var rule in rules.EnumerateArray())
            {
                Assert.True(rule.TryGetProperty("conditions", out var conditions));
                Assert.True(rule.TryGetProperty("actions", out var actions));
                Assert.True(actions.GetArrayLength() > 0);

                foreach (var condition in conditions.GetProperty("conditions").EnumerateArray())
                {
                    var attribute = condition.GetProperty("attribute").GetString();
                    Assert.NotEqual("Contents", attribute);
                }
            }
        }
    }

    [Fact]
    public async Task StarterPack_CanBeImportedAsReadableProfileFormat()
    {
        var storageDirectory = Path.Combine(Path.GetTempPath(), $"FolderFreshStarterPack_{Guid.NewGuid():N}");
        Directory.CreateDirectory(storageDirectory);

        try
        {
            var categoryService = new CategoryService(storageDirectory);
            var ruleService = new RuleService(categoryService, storageDirectory);
            var settingsService = new SettingsService(storageDirectory);
            var profileService = new ProfileService(categoryService, ruleService, settingsService, storageDirectory);
            var packPath = Path.Combine(AppContext.BaseDirectory, "StarterPacks", "clean-downloads.folderfresh");

            var profile = await profileService.ImportProfileAsync(packPath);

            Assert.Equal("Clean Downloads", profile.Name);
            Assert.Contains("Documents and office files", profile.RulesJson);
            Assert.Contains("\"confirmBeforeOrganize\": true", profile.SettingsJson);
            Assert.Single(profileService.GetProfiles());
        }
        finally
        {
            if (Directory.Exists(storageDirectory))
            {
                Directory.Delete(storageDirectory, recursive: true);
            }
        }
    }
}
