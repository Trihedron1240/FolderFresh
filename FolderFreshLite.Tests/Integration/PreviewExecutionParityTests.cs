using FolderFreshLite.Models;
using FolderFreshLite.Services;
using FolderFreshLite.Tests.Helpers;

namespace FolderFreshLite.Tests.Integration;

/// <summary>
/// Critical tests that verify the preview calculation matches actual execution.
/// These tests ensure that what users see in the preview is exactly what happens when they organize.
///
/// Both relative and absolute paths are supported:
/// - Relative paths (e.g., "Documents") are combined with baseOutputPath
/// - Absolute paths (e.g., "C:\Backup") are used as-is
/// </summary>
public class PreviewExecutionParityTests : IDisposable
{
    private readonly TestFileHelper _helper;
    private readonly RuleService _ruleService;

    public PreviewExecutionParityTests()
    {
        _helper = new TestFileHelper();
        _ruleService = new RuleService();
    }

    public void Dispose() => _helper.Dispose();

    #region Move Action Parity

    [Fact]
    public async Task MoveToFolder_RelativePath_PreviewMatchesExecution()
    {
        // Arrange
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;
        var originalPath = file.FullName;

        // Use relative path - should be combined with basePath
        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .Build();

        // Get preview prediction
        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        Assert.Single(predictedPaths);
        var predictedPath = predictedPaths[0];

        // Verify preview shows correct combined path
        Assert.Equal(Path.Combine(basePath, "Documents", "document.pdf"), predictedPath);

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify parity
        Assert.True(result.Success, $"Execution failed: {string.Join(", ", result.Errors)}");
        Assert.True(File.Exists(predictedPath), $"File should exist at predicted path: {predictedPath}");
        Assert.False(File.Exists(originalPath), $"Original file should no longer exist at: {originalPath}");
    }

    [Fact]
    public async Task MoveToFolder_AbsolutePath_PreviewMatchesExecution()
    {
        // Arrange
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;
        var originalPath = file.FullName;
        var absoluteDest = _helper.CreateSubdirectory("AbsoluteDestination");

        // Use absolute path - should be used as-is
        var rule = RuleBuilder.Create()
            .WithMoveToFolder(absoluteDest)
            .Build();

        // Get preview prediction
        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        Assert.Single(predictedPaths);
        var predictedPath = predictedPaths[0];

        // Verify preview shows absolute path
        Assert.Equal(Path.Combine(absoluteDest, "document.pdf"), predictedPath);

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify parity
        Assert.True(result.Success, $"Execution failed: {string.Join(", ", result.Errors)}");
        Assert.True(File.Exists(predictedPath), $"File should exist at predicted path: {predictedPath}");
        Assert.False(File.Exists(originalPath), $"Original file should no longer exist at: {originalPath}");
    }

    [Fact]
    public async Task MoveToFolder_CreatesDestinationFolder()
    {
        // Arrange
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        // Use relative nested path - folder doesn't exist yet
        var rule = RuleBuilder.Create()
            .WithMoveToFolder("NewFolder/Subfolder")
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        var predictedPath = predictedPaths[0];

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify
        Assert.True(result.Success);
        Assert.True(File.Exists(predictedPath), $"File should exist at: {predictedPath}");
    }

    #endregion

    #region Copy Action Parity

    [Fact]
    public async Task CopyToFolder_RelativePath_PreviewMatchesExecution()
    {
        // Arrange
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        // Use relative path
        var rule = RuleBuilder.Create()
            .WithCopyToFolder("Backup")
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        Assert.Single(predictedPaths);
        var predictedCopyPath = predictedPaths[0];

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify
        Assert.True(result.Success);
        Assert.True(File.Exists(predictedCopyPath), $"Copy should exist at: {predictedCopyPath}");
        // Original file still exists after copy (copy doesn't move)
        file.Refresh();
        Assert.True(file.Exists, "Original file should still exist after copy");
    }

    [Fact]
    public async Task MoveAndCopy_BothDestinationsExist()
    {
        // Arrange
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        // Use relative paths for both
        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .WithCopyToFolder("Backup")
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        Assert.Equal(2, predictedPaths.Count);

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify both destinations
        Assert.True(result.Success);
        Assert.True(File.Exists(predictedPaths[0]), $"Move destination should exist: {predictedPaths[0]}");
        Assert.True(File.Exists(predictedPaths[1]), $"Copy destination should exist: {predictedPaths[1]}");
    }

    #endregion

    #region Rename Action Parity

    [Fact]
    public async Task Rename_PreviewMatchesExecution()
    {
        // Arrange
        var file = _helper.CreateFile("old_name.pdf");
        var basePath = _helper.TestDirectory;
        var originalPath = file.FullName;  // Capture before any operation

        var rule = RuleBuilder.Create()
            .WithRename("new_name.pdf")
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        var predictedPath = predictedPaths[0];

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify with detailed diagnostics
        var allFiles = Directory.GetFiles(basePath, "*", SearchOption.AllDirectories);
        var actionsTaken = string.Join(", ", result.ActionsTaken);
        var filesInDir = string.Join(", ", allFiles.Select(Path.GetFileName));

        Assert.True(result.Success, $"Execution failed. Errors: [{string.Join(", ", result.Errors)}]. Actions: [{actionsTaken}]. Files: [{filesInDir}]");
        Assert.True(File.Exists(predictedPath), $"Renamed file should exist at: {predictedPath}. Actions: [{actionsTaken}]. Files: [{filesInDir}]");
        Assert.False(File.Exists(originalPath), $"Original file should no longer exist at: {originalPath}. Actions: [{actionsTaken}]. Files: [{filesInDir}]");
    }

    [Fact]
    public async Task Rename_WithPatterns_PreviewMatchesExecution()
    {
        // Arrange
        var file = _helper.CreateFileWithDates("document.pdf", modifiedDate: new DateTime(2024, 6, 15));
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithRename("{Name}_{Date}.{ext}")
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        var predictedPath = predictedPaths[0];

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify
        Assert.True(result.Success);
        Assert.True(File.Exists(predictedPath), $"Renamed file should exist at: {predictedPath}");
        Assert.Contains("document_2024-06-15.pdf", predictedPath);
    }

    #endregion

    #region SortIntoSubfolder Parity

    [Fact]
    public async Task SortIntoSubfolder_PreviewMatchesExecution()
    {
        // Arrange
        var file = _helper.CreateFile("photo.jpg");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithSortIntoSubfolder("{Kind}")
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        var predictedPath = predictedPaths[0];

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify
        Assert.True(result.Success);
        Assert.True(File.Exists(predictedPath), $"Sorted file should exist at: {predictedPath}");
        Assert.Contains("Image", predictedPath);
    }

    [Fact]
    public async Task SortIntoSubfolder_NestedPattern_PreviewMatchesExecution()
    {
        // Arrange
        var file = _helper.CreateFileWithDates("photo.jpg", modifiedDate: new DateTime(2024, 6, 15));
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithSortIntoSubfolder("{Year}/{Month}/{Kind}")
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        var predictedPath = predictedPaths[0];

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify
        Assert.True(result.Success);
        Assert.True(File.Exists(predictedPath), $"Sorted file should exist at: {predictedPath}");
        Assert.Contains(Path.Combine("2024", "06", "Image"), predictedPath);
    }

    #endregion

    #region Chained Actions Parity

    [Fact]
    public async Task RenameThenMove_PreviewMatchesExecution()
    {
        // Arrange
        var file = _helper.CreateFile("old.pdf");
        var basePath = _helper.TestDirectory;

        // Use relative path
        var rule = RuleBuilder.Create()
            .WithRename("new.pdf")
            .WithMoveToFolder("Documents")
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        var predictedPath = predictedPaths[0];

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify
        Assert.True(result.Success);
        Assert.True(File.Exists(predictedPath), $"File should exist at: {predictedPath}");
        Assert.EndsWith("new.pdf", predictedPath);
        Assert.Contains("Documents", predictedPath);
    }

    [Fact]
    public async Task RenameThenMoveAndCopy_AllDestinationsExist()
    {
        // Arrange
        var file = _helper.CreateFile("original.pdf");
        var basePath = _helper.TestDirectory;

        // Use relative paths
        var rule = RuleBuilder.Create()
            .WithRename("renamed.pdf")
            .WithMoveToFolder("Documents")
            .WithCopyToFolder("Backup")
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        Assert.Equal(2, predictedPaths.Count);

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify all destinations
        Assert.True(result.Success);
        foreach (var path in predictedPaths)
        {
            Assert.True(File.Exists(path), $"File should exist at: {path}");
            Assert.EndsWith("renamed.pdf", path);
        }
    }

    #endregion

    #region Conflict Resolution Tests

    /// <summary>
    /// IMPORTANT: This test documents a known discrepancy between preview and execution.
    /// The preview does NOT account for filename conflicts, but execution handles them.
    /// </summary>
    [Fact]
    public async Task ConflictResolution_PreviewDoesNotAccountForExistingFiles()
    {
        // Arrange - Create a file that already exists at the destination
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        // Create destination folder and a file that will conflict
        _helper.CreateSubdirectory("Documents");
        File.WriteAllText(Path.Combine(basePath, "Documents", "document.pdf"), "existing");

        // Use relative path
        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .Build();

        // Get preview - it predicts the simple path
        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        var predictedPath = predictedPaths[0];

        // Execute - execution should rename to avoid conflict
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // The prediction shows the ideal destination
        Assert.Equal(Path.Combine(basePath, "Documents", "document.pdf"), predictedPath);

        // But execution may create "document (1).pdf" if conflict resolution is "rename"
        Assert.True(result.Success);

        // NOTE: The actual file may be at "document (1).pdf" - this is a known difference
        // This test documents this behavior for awareness
        var actualFiles = Directory.GetFiles(Path.Combine(basePath, "Documents"), "document*.pdf");
        Assert.True(actualFiles.Length >= 2, "Should have original and new file (possibly renamed)");
    }

    #endregion

    #region Edge Cases

    [Fact]
    public async Task EmptyRule_NoChanges()
    {
        // Arrange
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;
        var originalPath = file.FullName;

        var rule = RuleBuilder.Create().Build();  // No actions

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify
        Assert.Empty(predictedPaths);
        Assert.True(result.Success);
        Assert.True(File.Exists(originalPath), "File should remain at original location");
    }

    [Fact]
    public async Task Ignore_FileStaysInPlace()
    {
        // Arrange
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;
        var originalPath = file.FullName;

        var rule = RuleBuilder.Create()
            .WithIgnore()
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify
        Assert.Empty(predictedPaths);  // Ignore returns empty
        Assert.True(result.Success);
        Assert.True(result.WasIgnored);
        Assert.True(File.Exists(originalPath), "Ignored file should stay in place");
    }

    [Fact]
    public async Task Continue_DoesNotAffectFileLocation()
    {
        // Arrange
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        // Use relative path
        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .WithContinue()
            .Build();

        var predictedPaths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
        var predictedPath = predictedPaths[0];

        // Execute
        var result = await _ruleService.ExecuteActionsAsync(rule, file, basePath);

        // Verify
        Assert.True(result.Success);
        Assert.True(result.ShouldContinue);
        Assert.True(File.Exists(predictedPath), "File should be moved even with Continue action");
    }

    #endregion

    #region Full Folder State Validation

    [Fact]
    public async Task MultiplRules_FinalFolderStateMatchesPrediction()
    {
        // Arrange - Create multiple files
        var pdf = _helper.CreateFile("report.pdf");
        var jpg = _helper.CreateFile("photo.jpg");
        var docx = _helper.CreateFile("document.docx");
        var txt = _helper.CreateFile("notes.txt");
        var basePath = _helper.TestDirectory;

        // Create rules for different file types using relative paths
        var pdfRule = RuleBuilder.Create("PDF Rule")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("Documents/PDFs")
            .WithPriority(0)
            .Build();

        var imageRule = RuleBuilder.Create("Image Rule")
            .WithCondition(ConditionAttribute.Kind, ConditionOperator.Is, "Image")
            .WithMoveToFolder("Images")
            .WithPriority(1)
            .Build();

        var docRule = RuleBuilder.Create("Document Rule")
            .WithCondition(ConditionAttribute.Kind, ConditionOperator.Is, "Document")
            .WithMoveToFolder("Documents/Word")
            .WithPriority(2)
            .Build();

        var textRule = RuleBuilder.Create("Text Rule")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "txt")
            .WithSortIntoSubfolder("Text/{Name}")
            .WithPriority(3)
            .Build();

        var rules = new List<Rule> { pdfRule, imageRule, docRule, textRule };

        // Predict destinations
        var predictions = new Dictionary<string, string>();
        foreach (var file in new[] { pdf, jpg, docx, txt })
        {
            var matchingRule = _ruleService.GetMatchingRule(file, rules);
            if (matchingRule != null)
            {
                var paths = _ruleService.CalculateAllDestinationPaths(matchingRule, file, basePath);
                if (paths.Count > 0)
                {
                    predictions[file.Name] = paths[0];
                }
            }
        }

        // Execute
        foreach (var file in new[] { pdf, jpg, docx, txt })
        {
            var matchingRule = _ruleService.GetMatchingRule(file, rules);
            if (matchingRule != null)
            {
                await _ruleService.ExecuteActionsAsync(matchingRule, file, basePath);
            }
        }

        // Verify each prediction
        foreach (var prediction in predictions)
        {
            Assert.True(File.Exists(prediction.Value),
                $"File {prediction.Key} should exist at predicted location: {prediction.Value}");
        }
    }

    #endregion
}
