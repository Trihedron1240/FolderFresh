using FolderFreshLite.Models;
using FolderFreshLite.Services;
using FolderFreshLite.Tests.Helpers;

namespace FolderFreshLite.Tests.Actions;

/// <summary>
/// Tests for destination path calculation.
/// These tests verify that CalculateAllDestinationPaths produces accurate predictions
/// of where files will end up after rule execution.
/// </summary>
public class DestinationCalculationTests : IDisposable
{
    private readonly TestFileHelper _helper;
    private readonly RuleService _ruleService;

    public DestinationCalculationTests()
    {
        _helper = new TestFileHelper();
        _ruleService = new RuleService();
    }

    public void Dispose() => _helper.Dispose();

    #region MoveToFolder Tests

    [Fact]
    public void MoveToFolder_RelativePath_CalculatesCorrectDestination()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(basePath, "Documents", "document.pdf"), destinations[0]);
    }

    [Fact]
    public void MoveToFolder_AbsolutePath_UsesAbsolutePath()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;
        var absoluteDest = Path.Combine(Path.GetTempPath(), "TestAbsolute");

        var rule = RuleBuilder.Create()
            .WithMoveToFolder(absoluteDest)
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(absoluteDest, "document.pdf"), destinations[0]);
    }

    [Fact]
    public void MoveToFolder_NestedPath_CalculatesFullPath()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Archives/2024/Documents")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        // Note: CalculateAllDestinationPaths preserves the slashes from the action value
        // The expected path uses forward slashes as in the action, combined with backslashes from basePath
        var expectedPath = Path.Combine(basePath, "Archives/2024/Documents", "document.pdf");
        Assert.Equal(expectedPath, destinations[0]);
    }

    #endregion

    #region CopyToFolder Tests

    [Fact]
    public void CopyToFolder_OnlyAction_ReturnsCopyDestination()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithCopyToFolder("Backup")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(basePath, "Backup", "document.pdf"), destinations[0]);
    }

    [Fact]
    public void MoveAndCopy_ReturnsBothDestinations()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .WithCopyToFolder("Backup")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Equal(2, destinations.Count);
        Assert.Equal(Path.Combine(basePath, "Documents", "document.pdf"), destinations[0]);  // Move is primary
        Assert.Equal(Path.Combine(basePath, "Backup", "document.pdf"), destinations[1]);     // Copy is secondary
    }

    [Fact]
    public void MultipleCopies_ReturnsAllDestinations()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .WithCopyToFolder("Backup1")
            .WithCopyToFolder("Backup2")
            .WithCopyToFolder("Backup3")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Equal(4, destinations.Count);
        Assert.Equal(Path.Combine(basePath, "Documents", "document.pdf"), destinations[0]);
        Assert.Equal(Path.Combine(basePath, "Backup1", "document.pdf"), destinations[1]);
        Assert.Equal(Path.Combine(basePath, "Backup2", "document.pdf"), destinations[2]);
        Assert.Equal(Path.Combine(basePath, "Backup3", "document.pdf"), destinations[3]);
    }

    #endregion

    #region SortIntoSubfolder Tests

    [Fact]
    public void SortIntoSubfolder_StaticName_Works()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithSortIntoSubfolder("PDFs")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(basePath, "PDFs", "document.pdf"), destinations[0]);
    }

    [Fact]
    public void SortIntoSubfolder_WithKindPattern_ExpandsCorrectly()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithSortIntoSubfolder("{Kind}")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(basePath, "PDF", "document.pdf"), destinations[0]);
    }

    [Fact]
    public void SortIntoSubfolder_WithExtensionPattern_ExpandsCorrectly()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithSortIntoSubfolder("{Extension}")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(basePath, "pdf", "document.pdf"), destinations[0]);
    }

    [Fact]
    public void SortIntoSubfolder_NestedPattern_Works()
    {
        var file = _helper.CreateFileWithDates("document.pdf", modifiedDate: new DateTime(2024, 6, 15));
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithSortIntoSubfolder("{Year}/{Month}")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(basePath, "2024", "06", "document.pdf"), destinations[0]);
    }

    [Fact]
    public void SortIntoSubfolder_ForwardSlash_NormalizedToBackslash()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithSortIntoSubfolder("Archives/2024/Q1")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        // Should use platform-appropriate separator
        Assert.Equal(Path.Combine(basePath, "Archives", "2024", "Q1", "document.pdf"), destinations[0]);
    }

    #endregion

    #region Rename Tests

    [Fact]
    public void Rename_StaticName_Works()
    {
        var file = _helper.CreateFile("old_name.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithRename("new_name.pdf")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(_helper.TestDirectory, "new_name.pdf"), destinations[0]);
    }

    [Fact]
    public void Rename_WithNamePattern_PreservesName()
    {
        var file = _helper.CreateFile("original.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithRename("backup_{Name}.{ext}")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(_helper.TestDirectory, "backup_original.pdf"), destinations[0]);
    }

    [Fact]
    public void Rename_WithDatePattern_Works()
    {
        var file = _helper.CreateFileWithDates("document.pdf", modifiedDate: new DateTime(2024, 6, 15));
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithRename("{Name}_{Date}.{ext}")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(_helper.TestDirectory, "document_2024-06-15.pdf"), destinations[0]);
    }

    #endregion

    #region Chained Actions Tests

    [Fact]
    public void RenameThenMove_AppliesRenameFirst()
    {
        var file = _helper.CreateFile("old_name.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithRename("new_name.pdf")
            .WithMoveToFolder("Documents")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        // File should be moved with the new name
        Assert.Equal(Path.Combine(basePath, "Documents", "new_name.pdf"), destinations[0]);
    }

    [Fact]
    public void MoveThenRename_AppliesInOrder()
    {
        var file = _helper.CreateFile("original.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .WithRename("renamed.pdf")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        // Move then rename - renamed file in Documents folder
        Assert.Equal(Path.Combine(basePath, "Documents", "renamed.pdf"), destinations[0]);
    }

    [Fact]
    public void RenameThenSort_RenamedFileInSubfolder()
    {
        var file = _helper.CreateFile("original.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithRename("archived_{Name}.{ext}")
            .WithSortIntoSubfolder("Archives/{Kind}")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(basePath, "Archives", "PDF", "archived_original.pdf"), destinations[0]);
    }

    [Fact]
    public void RenameThenCopy_CopyUsesRenamedName()
    {
        var file = _helper.CreateFile("original.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithRename("renamed.pdf")
            .WithMoveToFolder("Documents")
            .WithCopyToFolder("Backup")
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Equal(2, destinations.Count);
        // Both move and copy should use the renamed name
        Assert.Equal(Path.Combine(basePath, "Documents", "renamed.pdf"), destinations[0]);
        Assert.Equal(Path.Combine(basePath, "Backup", "renamed.pdf"), destinations[1]);
    }

    #endregion

    #region Special Actions Tests

    [Fact]
    public void Delete_ReturnsRecycleBinMarker()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithDelete()
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal("[RECYCLE BIN]", destinations[0]);
    }

    [Fact]
    public void Ignore_ReturnsEmptyList()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithIgnore()
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Empty(destinations);
    }

    [Fact]
    public void Continue_DoesNotAffectDestination()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .WithContinue()
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal(Path.Combine(basePath, "Documents", "document.pdf"), destinations[0]);
    }

    #endregion

    #region CalculateAllDestinations (with ActionType) Tests

    [Fact]
    public void CalculateAllDestinations_ReturnsActionTypes()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithMoveToFolder("Documents")
            .WithCopyToFolder("Backup")
            .Build();

        var destinations = _ruleService.CalculateAllDestinations(rule, file, basePath);

        Assert.Equal(2, destinations.Count);

        // First destination is the move
        Assert.Equal(Path.Combine(basePath, "Documents", "document.pdf"), destinations[0].Path);
        Assert.Equal(ActionType.MoveToFolder, destinations[0].ActionType);

        // Second destination is the copy
        Assert.Equal(Path.Combine(basePath, "Backup", "document.pdf"), destinations[1].Path);
        Assert.Equal(ActionType.CopyToFolder, destinations[1].ActionType);
    }

    [Fact]
    public void CalculateAllDestinations_Delete_ReturnsDeleteActionType()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithDelete()
            .Build();

        var destinations = _ruleService.CalculateAllDestinations(rule, file, basePath);

        Assert.Single(destinations);
        Assert.Equal("[RECYCLE BIN]", destinations[0].Path);
        Assert.Equal(ActionType.Delete, destinations[0].ActionType);
    }

    #endregion

    #region Edge Cases

    [Fact]
    public void NoActions_ReturnsEmptyList()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create().Build();  // No actions added

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Empty(destinations);
    }

    [Fact]
    public void DeleteThenCopy_DeleteIsTerminal()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithDelete()
            .WithCopyToFolder("Backup")  // This should be ignored
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        // Delete is terminal - no further actions
        Assert.Single(destinations);
        Assert.Equal("[RECYCLE BIN]", destinations[0]);
    }

    [Fact]
    public void IgnoreThenMove_IgnoreIsTerminal()
    {
        var file = _helper.CreateFile("document.pdf");
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create()
            .WithIgnore()
            .WithMoveToFolder("Documents")  // This should be ignored
            .Build();

        var destinations = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);

        Assert.Empty(destinations);  // Ignore returns empty
    }

    #endregion
}
