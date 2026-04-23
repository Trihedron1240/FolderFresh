using FolderFresh.Services;

namespace FolderFreshLite.Tests.Services;

public sealed class CategoryServiceTests : IDisposable
{
    private readonly string _testCategoryDir;

    public CategoryServiceTests()
    {
        _testCategoryDir = Path.Combine(Path.GetTempPath(), $"FolderFreshCategories_{Guid.NewGuid():N}");
        Directory.CreateDirectory(_testCategoryDir);
    }

    public void Dispose()
    {
        if (Directory.Exists(_testCategoryDir))
        {
            Directory.Delete(_testCategoryDir, true);
        }
    }

    [Fact]
    public async Task UpdateCategoryAsync_DefaultCategoryPersistsEditsAcrossReload()
    {
        var service = new CategoryService(_testCategoryDir);
        var categories = await service.LoadCategoriesAsync();
        var documents = Assert.Single(categories.Where(category => category.Id == "documents"));

        documents.Name = "Work Docs";
        documents.Destination = "Work Documents";
        documents.Extensions.Add(".md");

        await service.UpdateCategoryAsync(documents);

        var reloadedService = new CategoryService(_testCategoryDir);
        var reloadedCategories = await reloadedService.LoadCategoriesAsync();
        var reloadedDocuments = Assert.Single(reloadedCategories.Where(category => category.Id == "documents"));

        Assert.Equal("Work Docs", reloadedDocuments.Name);
        Assert.Equal("Work Documents", reloadedDocuments.Destination);
        Assert.Contains(".md", reloadedDocuments.Extensions);
        Assert.Equal("documents", reloadedService.GetCategoryForFile(".md").Id);
    }
}
