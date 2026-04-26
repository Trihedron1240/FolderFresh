using FolderFresh.SetupAdvisor;

namespace FolderFresh.Tests.Services;

public class SetupAdvisorServiceTests : IDisposable
{
    private readonly string _rootPath;

    public SetupAdvisorServiceTests()
    {
        _rootPath = Path.Combine(Path.GetTempPath(), "FolderFreshSetupAdvisorTests", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_rootPath);
    }

    [Fact]
    public void Analyze_CreatesCategoryAndRuleSuggestionsForKnownPatterns()
    {
        CreateFile("Screenshot 2026-04-21 143210.png");
        CreateFile("Screenshot 2026-04-22 091155.png");
        CreateFile("Screenshot 2026-04-23 121010.png");
        CreateFile("Invoice_April_Contoso.pdf");
        CreateFile("Uber_Receipt_March.pdf");

        var service = new SetupAdvisorService();
        var result = service.Analyze(new FolderAnalysisOptions
        {
            SourcePath = _rootPath
        });

        var screenshotCategory = Assert.Single(result.Categories.Where(c => c.Key == "screenshots"));
        Assert.Equal("Screenshots", screenshotCategory.Name);

        var financeCategory = Assert.Single(result.Categories.Where(c => c.Key == "finance"));
        Assert.Equal("Finance", financeCategory.Name);

        var screenshotRule = Assert.Single(result.Rules.Where(r => r.TargetCategoryKey == screenshotCategory.Key));
        Assert.Equal("screenshots", screenshotRule.TargetCategoryKey);

        var financeRule = Assert.Single(result.Rules.Where(r => r.TargetCategoryKey == financeCategory.Key));
        Assert.True(financeRule.MatchToken is "invoice" or "receipt");
    }

    [Fact]
    public void Analyze_CreatesProjectSuggestionFromSharedStem()
    {
        CreateFile("ProjectPhoenix_Notes.md");
        CreateFile("ProjectPhoenix_Backlog.xlsx");
        CreateFile("ProjectPhoenix_Logo.png");

        var service = new SetupAdvisorService();
        var result = service.Analyze(new FolderAnalysisOptions
        {
            SourcePath = _rootPath
        });

        var projectCategory = Assert.Single(result.Categories.Where(c => c.Key == "projectphoenix"));
        Assert.Equal("Project Phoenix", projectCategory.Name);

        var projectRule = Assert.Single(result.Rules.Where(r => r.TargetCategoryKey == projectCategory.Key));
        Assert.Equal("projectphoenix", projectRule.MatchToken);
    }

    private void CreateFile(string relativeName, string? contents = "test")
    {
        var path = Path.Combine(_rootPath, relativeName);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, contents);
    }

    public void Dispose()
    {
        if (Directory.Exists(_rootPath))
        {
            Directory.Delete(_rootPath, recursive: true);
        }
    }
}
