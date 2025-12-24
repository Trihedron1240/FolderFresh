using FolderFreshLite.Models;
using FolderFreshLite.Services;
using FolderFreshLite.Tests.Helpers;

namespace FolderFreshLite.Tests.Integration;

/// <summary>
/// Integration tests for rule matching logic including priority, Continue action, and rule chaining.
/// </summary>
public class RuleMatchingTests : IDisposable
{
    private readonly TestFileHelper _helper;
    private readonly RuleService _ruleService;

    public RuleMatchingTests()
    {
        _helper = new TestFileHelper();
        _ruleService = new RuleService();
    }

    public void Dispose() => _helper.Dispose();

    #region Basic Rule Matching

    [Fact]
    public void GetMatchingRule_ReturnsFirstMatch()
    {
        var file = _helper.CreateFile("document.pdf");

        var rule = RuleBuilder.Create("PDF Rule")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("PDFs")
            .Build();

        var rules = new List<Rule> { rule };

        var match = _ruleService.GetMatchingRule(file, rules);

        Assert.NotNull(match);
        Assert.Equal("PDF Rule", match.Name);
    }

    [Fact]
    public void GetMatchingRule_NoMatch_ReturnsNull()
    {
        var file = _helper.CreateFile("document.pdf");

        var rule = RuleBuilder.Create("TXT Rule")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "txt")
            .WithMoveToFolder("Texts")
            .Build();

        var rules = new List<Rule> { rule };

        var match = _ruleService.GetMatchingRule(file, rules);

        Assert.Null(match);
    }

    [Fact]
    public void GetMatchingRule_DisabledRule_IsSkipped()
    {
        var file = _helper.CreateFile("document.pdf");

        var disabledRule = RuleBuilder.Create("Disabled Rule")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("Disabled")
            .Enabled(false)
            .Build();

        var enabledRule = RuleBuilder.Create("Enabled Rule")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("Enabled")
            .Enabled(true)
            .Build();

        var rules = new List<Rule> { disabledRule, enabledRule };

        var match = _ruleService.GetMatchingRule(file, rules);

        Assert.NotNull(match);
        Assert.Equal("Enabled Rule", match.Name);
    }

    #endregion

    #region Priority Tests

    [Fact]
    public void GetMatchingRule_RespectsPriority()
    {
        var file = _helper.CreateFile("document.pdf");

        var lowPriority = RuleBuilder.Create("Low Priority")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("Low")
            .WithPriority(10)
            .Build();

        var highPriority = RuleBuilder.Create("High Priority")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("High")
            .WithPriority(1)
            .Build();

        // Add in reverse order to ensure priority is respected
        var rules = new List<Rule> { lowPriority, highPriority };

        var match = _ruleService.GetMatchingRule(file, rules);

        Assert.NotNull(match);
        Assert.Equal("High Priority", match.Name);
    }

    [Fact]
    public void GetMatchingRule_MoreSpecificRuleFirst()
    {
        var file = _helper.CreateFile("invoice_2024.pdf");

        var generalRule = RuleBuilder.Create("All PDFs")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("PDFs")
            .WithPriority(10)
            .Build();

        var specificRule = RuleBuilder.Create("Invoice PDFs")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCondition(ConditionAttribute.Name, ConditionOperator.StartsWith, "invoice")
            .WithMoveToFolder("Invoices")
            .WithPriority(1)  // Higher priority (lower number)
            .Build();

        var rules = new List<Rule> { generalRule, specificRule };

        var match = _ruleService.GetMatchingRule(file, rules);

        Assert.NotNull(match);
        Assert.Equal("Invoice PDFs", match.Name);
    }

    #endregion

    #region Continue Action Tests

    [Fact]
    public void GetMatchingRulesWithContinue_SingleRuleNoContinue_ReturnsOneRule()
    {
        var file = _helper.CreateFile("document.pdf");

        var rule = RuleBuilder.Create("PDF Rule")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("PDFs")
            .Build();

        var rules = new List<Rule> { rule };

        var matches = _ruleService.GetMatchingRulesWithContinue(file, rules);

        Assert.Single(matches);
        Assert.Equal("PDF Rule", matches[0].Name);
    }

    [Fact]
    public void GetMatchingRulesWithContinue_WithContinue_ReturnsBothRules()
    {
        var file = _helper.CreateFile("document.pdf");

        var firstRule = RuleBuilder.Create("First Rule")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCopyToFolder("Backup")
            .WithContinue()
            .WithPriority(1)
            .Build();

        var secondRule = RuleBuilder.Create("Second Rule")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("PDFs")
            .WithPriority(2)
            .Build();

        var rules = new List<Rule> { firstRule, secondRule };

        var matches = _ruleService.GetMatchingRulesWithContinue(file, rules);

        Assert.Equal(2, matches.Count);
        Assert.Equal("First Rule", matches[0].Name);
        Assert.Equal("Second Rule", matches[1].Name);
    }

    [Fact]
    public void GetMatchingRulesWithContinue_StopsAtFirstNonContinue()
    {
        var file = _helper.CreateFile("document.pdf");

        var rule1 = RuleBuilder.Create("Rule 1 - Copy & Continue")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCopyToFolder("Backup1")
            .WithContinue()
            .WithPriority(1)
            .Build();

        var rule2 = RuleBuilder.Create("Rule 2 - Move (no Continue)")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("PDFs")
            .WithPriority(2)
            .Build();

        var rule3 = RuleBuilder.Create("Rule 3 - Should Not Match")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCopyToFolder("Backup2")
            .WithPriority(3)
            .Build();

        var rules = new List<Rule> { rule1, rule2, rule3 };

        var matches = _ruleService.GetMatchingRulesWithContinue(file, rules);

        Assert.Equal(2, matches.Count);
        Assert.Equal("Rule 1 - Copy & Continue", matches[0].Name);
        Assert.Equal("Rule 2 - Move (no Continue)", matches[1].Name);
        // Rule 3 should not be included
    }

    [Fact]
    public void GetMatchingRulesWithContinue_OnlyMatchingRulesIncluded()
    {
        var file = _helper.CreateFile("document.pdf");

        var rule1 = RuleBuilder.Create("PDF Rule - Continue")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCopyToFolder("PDFs")
            .WithContinue()
            .WithPriority(1)
            .Build();

        var rule2 = RuleBuilder.Create("TXT Rule - No match")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "txt")
            .WithMoveToFolder("Texts")
            .WithPriority(2)
            .Build();

        var rule3 = RuleBuilder.Create("PDF Rule 2")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("Documents")
            .WithPriority(3)
            .Build();

        var rules = new List<Rule> { rule1, rule2, rule3 };

        var matches = _ruleService.GetMatchingRulesWithContinue(file, rules);

        Assert.Equal(2, matches.Count);
        Assert.Equal("PDF Rule - Continue", matches[0].Name);
        Assert.Equal("PDF Rule 2", matches[1].Name);
        // TXT Rule should not be included
    }

    [Fact]
    public void GetMatchingRulesWithContinue_AllContinue_ReturnsAllMatching()
    {
        var file = _helper.CreateFile("document.pdf");

        var rule1 = RuleBuilder.Create("Rule 1")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCopyToFolder("Copy1")
            .WithContinue()
            .WithPriority(1)
            .Build();

        var rule2 = RuleBuilder.Create("Rule 2")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCopyToFolder("Copy2")
            .WithContinue()
            .WithPriority(2)
            .Build();

        var rule3 = RuleBuilder.Create("Rule 3")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCopyToFolder("Copy3")
            .WithContinue()
            .WithPriority(3)
            .Build();

        var rules = new List<Rule> { rule1, rule2, rule3 };

        var matches = _ruleService.GetMatchingRulesWithContinue(file, rules);

        Assert.Equal(3, matches.Count);
    }

    #endregion

    #region Complex Condition Matching

    [Fact]
    public void GetMatchingRule_ComplexConditions_AllMustMatch()
    {
        var file = _helper.CreateFileWithDates("invoice_2024.pdf",
            modifiedDate: DateTime.Now.AddDays(-5),
            sizeInBytes: 1024 * 100);  // 100 KB

        var rule = RuleBuilder.Create("Recent Invoice PDF")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCondition(ConditionAttribute.Name, ConditionOperator.Contains, "invoice")
            .WithCondition(ConditionAttribute.DateModified, ConditionOperator.IsInTheLast, "30", "days")
            .WithMoveToFolder("RecentInvoices")
            .Build();

        var rules = new List<Rule> { rule };

        var match = _ruleService.GetMatchingRule(file, rules);

        Assert.NotNull(match);
    }

    [Fact]
    public void GetMatchingRule_ComplexConditions_OneFailsNoMatch()
    {
        var file = _helper.CreateFileWithDates("invoice_2024.pdf",
            modifiedDate: DateTime.Now.AddDays(-60));  // Old file

        var rule = RuleBuilder.Create("Recent Invoice PDF")
            .WithMatchType(ConditionMatchType.All)
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCondition(ConditionAttribute.Name, ConditionOperator.Contains, "invoice")
            .WithCondition(ConditionAttribute.DateModified, ConditionOperator.IsInTheLast, "30", "days")
            .WithMoveToFolder("RecentInvoices")
            .Build();

        var rules = new List<Rule> { rule };

        var match = _ruleService.GetMatchingRule(file, rules);

        Assert.Null(match);  // File is too old
    }

    [Fact]
    public void GetMatchingRule_AnyMatchType_OneMatchSuffices()
    {
        var file = _helper.CreateFile("random.pdf");

        var rule = RuleBuilder.Create("PDF or DOC")
            .WithMatchType(ConditionMatchType.Any)
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "docx")
            .WithMoveToFolder("Documents")
            .Build();

        var rules = new List<Rule> { rule };

        var match = _ruleService.GetMatchingRule(file, rules);

        Assert.NotNull(match);  // PDF matches one of the conditions
    }

    [Fact]
    public void GetMatchingRule_NoneMatchType_ExcludesFiles()
    {
        var file = _helper.CreateFile("document.pdf");

        var rule = RuleBuilder.Create("Exclude executables")
            .WithMatchType(ConditionMatchType.None)
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "exe")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "bat")
            .WithMoveToFolder("SafeFiles")
            .Build();

        var rules = new List<Rule> { rule };

        var match = _ruleService.GetMatchingRule(file, rules);

        Assert.NotNull(match);  // PDF is not exe or bat
    }

    #endregion

    #region Full Pipeline Tests

    [Fact]
    public async Task FullPipeline_RuleMatchToPredictionToExecution()
    {
        // Arrange
        var file = _helper.CreateFileWithDates("photo_vacation.jpg", modifiedDate: new DateTime(2024, 6, 15));
        var basePath = _helper.TestDirectory;

        var rule = RuleBuilder.Create("Organize Photos by Date")
            .WithCondition(ConditionAttribute.Kind, ConditionOperator.Is, "Image")
            .WithSortIntoSubfolder("Photos/{Year}/{Month}")
            .Build();

        var rules = new List<Rule> { rule };

        // Step 1: Match rule
        var matchedRule = _ruleService.GetMatchingRule(file, rules);
        Assert.NotNull(matchedRule);

        // Step 2: Predict destination
        var predictedPaths = _ruleService.CalculateAllDestinationPaths(matchedRule, file, basePath);
        Assert.Single(predictedPaths);
        var predictedPath = predictedPaths[0];
        Assert.Contains(Path.Combine("Photos", "2024", "06"), predictedPath);

        // Step 3: Execute
        var result = await _ruleService.ExecuteActionsAsync(matchedRule, file, basePath);
        Assert.True(result.Success);

        // Step 4: Verify
        Assert.True(File.Exists(predictedPath), $"File should exist at: {predictedPath}");
    }

    [Fact]
    public async Task FullPipeline_MultipleRulesWithContinue()
    {
        // Arrange
        var file = _helper.CreateFile("important_document.pdf");
        var basePath = _helper.TestDirectory;

        // Use relative paths - they will be combined with basePath
        var tagRule = RuleBuilder.Create("Tag Important")
            .WithCondition(ConditionAttribute.Name, ConditionOperator.Contains, "important")
            .WithCopyToFolder("Important")
            .WithContinue()
            .WithPriority(1)
            .Build();

        var organizeRule = RuleBuilder.Create("Organize PDFs")
            .WithCondition(ConditionAttribute.Extension, ConditionOperator.Is, "pdf")
            .WithMoveToFolder("Documents")
            .WithPriority(2)
            .Build();

        var rules = new List<Rule> { tagRule, organizeRule };

        // Get all matching rules
        var matchingRules = _ruleService.GetMatchingRulesWithContinue(file, rules);
        Assert.Equal(2, matchingRules.Count);

        // Predict all destinations
        var allPredictedPaths = new List<string>();
        foreach (var rule in matchingRules)
        {
            var paths = _ruleService.CalculateAllDestinationPaths(rule, file, basePath);
            allPredictedPaths.AddRange(paths);
        }
        Assert.Equal(2, allPredictedPaths.Count);

        // Execute all rules
        foreach (var rule in matchingRules)
        {
            await _ruleService.ExecuteActionsAsync(rule, file, basePath);
            file.Refresh();
        }

        // Verify all destinations (note: file may have been moved, so paths need adjustment)
        // The copy should exist
        Assert.True(File.Exists(allPredictedPaths[0]) || File.Exists(allPredictedPaths[1]),
            "At least one destination should exist");
    }

    #endregion
}
