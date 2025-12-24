using FolderFreshLite.Models;
using FolderFreshLite.Services;
using FolderFreshLite.Tests.Helpers;

namespace FolderFreshLite.Tests.Conditions;

/// <summary>
/// Tests for string-based conditions: Name, Extension, FullName
/// </summary>
public class StringConditionTests : IDisposable
{
    private readonly TestFileHelper _helper;
    private readonly RuleService _ruleService;

    public StringConditionTests()
    {
        _helper = new TestFileHelper();
        _ruleService = new RuleService();
    }

    public void Dispose() => _helper.Dispose();

    #region Name Conditions

    [Theory]
    [InlineData("document", "document", true)]
    [InlineData("Document", "document", true)]  // Case insensitive
    [InlineData("DOCUMENT", "document", true)]
    [InlineData("doc", "document", false)]
    [InlineData("document1", "document", false)]
    public void Name_Is_MatchesExactly(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile($"{fileName}.pdf");
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Name,
            Operator = ConditionOperator.Is,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("document", "document", false)]
    [InlineData("document", "other", true)]
    [InlineData("Document", "document", false)]  // Case insensitive
    public void Name_IsNot_Works(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile($"{fileName}.pdf");
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Name,
            Operator = ConditionOperator.IsNot,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("my_document_2024", "document", true)]
    [InlineData("my_document_2024", "DOC", true)]  // Case insensitive
    [InlineData("my_document_2024", "2024", true)]
    [InlineData("my_document_2024", "xyz", false)]
    public void Name_Contains_Works(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile($"{fileName}.pdf");
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Name,
            Operator = ConditionOperator.Contains,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("my_document_2024", "document", false)]
    [InlineData("my_document_2024", "xyz", true)]
    public void Name_DoesNotContain_Works(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile($"{fileName}.pdf");
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Name,
            Operator = ConditionOperator.DoesNotContain,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("document_2024", "doc", true)]
    [InlineData("document_2024", "DOC", true)]  // Case insensitive
    [InlineData("document_2024", "document", true)]
    [InlineData("document_2024", "2024", false)]
    public void Name_StartsWith_Works(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile($"{fileName}.pdf");
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Name,
            Operator = ConditionOperator.StartsWith,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("document_2024", "2024", true)]
    [InlineData("document_2024", "24", true)]
    [InlineData("document_2024", "doc", false)]
    public void Name_EndsWith_Works(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile($"{fileName}.pdf");
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Name,
            Operator = ConditionOperator.EndsWith,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("document_2024", "doc*", true)]
    [InlineData("document_2024", "*2024", true)]
    [InlineData("document_2024", "doc*2024", true)]
    [InlineData("document_2024", "*ment*", true)]
    [InlineData("document_2024", "doc?ment_2024", true)]  // ? matches single char
    [InlineData("document_2024", "xyz*", false)]
    [InlineData("file1", "file?", true)]
    [InlineData("file10", "file?", false)]  // ? only matches one char
    public void Name_MatchesPattern_Works(string fileName, string pattern, bool expected)
    {
        var file = _helper.CreateFile($"{fileName}.pdf");
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Name,
            Operator = ConditionOperator.MatchesPattern,
            Value = pattern
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Fact]
    public void Name_IsBlank_MatchesEmptyName()
    {
        // Files can't really have empty names, but extension-only files like ".gitignore"
        // have an empty name when we strip the extension
        var file = _helper.CreateFile(".gitignore");
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Name,
            Operator = ConditionOperator.IsBlank,
            Value = ""
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void Name_IsNotBlank_Works()
    {
        var file = _helper.CreateFile("document.pdf");
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Name,
            Operator = ConditionOperator.IsNotBlank,
            Value = ""
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    #endregion

    #region Extension Conditions

    [Theory]
    [InlineData("document.pdf", "pdf", true)]
    [InlineData("document.pdf", "PDF", true)]  // Case insensitive
    [InlineData("document.pdf", ".pdf", true)]  // With or without dot
    [InlineData("document.pdf", "doc", false)]
    [InlineData("document.PDF", "pdf", true)]  // File extension is also case insensitive
    public void Extension_Is_MatchesExactly(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Extension,
            Operator = ConditionOperator.Is,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("document.pdf", "pdf", false)]
    [InlineData("document.pdf", "doc", true)]
    public void Extension_IsNot_Works(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Extension,
            Operator = ConditionOperator.IsNot,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("document.jpeg", "peg", true)]
    [InlineData("document.jpeg", "jp", true)]
    [InlineData("document.jpeg", "xyz", false)]
    public void Extension_Contains_Works(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Extension,
            Operator = ConditionOperator.Contains,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    #endregion

    #region FullName Conditions

    [Theory]
    [InlineData("document.pdf", "document.pdf", true)]
    [InlineData("document.pdf", "DOCUMENT.PDF", true)]  // Case insensitive
    [InlineData("document.pdf", "document", false)]
    public void FullName_Is_MatchesExactly(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.FullName,
            Operator = ConditionOperator.Is,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("document.pdf", ".pdf", true)]
    [InlineData("document.pdf", "doc", true)]
    [InlineData("my_file.txt", "_file", true)]
    public void FullName_Contains_Works(string fileName, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.FullName,
            Operator = ConditionOperator.Contains,
            Value = conditionValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("document.pdf", "*.pdf", true)]
    [InlineData("document.pdf", "doc*.pdf", true)]
    [InlineData("document.pdf", "*.txt", false)]
    [InlineData("report_2024.xlsx", "report_????.xlsx", true)]
    public void FullName_MatchesPattern_Works(string fileName, string pattern, bool expected)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.FullName,
            Operator = ConditionOperator.MatchesPattern,
            Value = pattern
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    #endregion
}
