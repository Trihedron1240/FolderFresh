using FolderFreshLite.Models;
using FolderFreshLite.Services;
using FolderFreshLite.Tests.Helpers;

namespace FolderFreshLite.Tests.Conditions;

/// <summary>
/// Tests for Size condition with various units (B, KB, MB, GB)
/// </summary>
public class SizeConditionTests : IDisposable
{
    private readonly TestFileHelper _helper;
    private readonly RuleService _ruleService;

    // Size constants for clarity
    private const long KB = 1024;
    private const long MB = 1024 * 1024;
    private const long GB = 1024 * 1024 * 1024;

    public SizeConditionTests()
    {
        _helper = new TestFileHelper();
        _ruleService = new RuleService();
    }

    public void Dispose() => _helper.Dispose();

    #region IsGreaterThan Tests

    [Theory]
    [InlineData(1000, "500", "B", true)]
    [InlineData(500, "500", "B", false)]   // Equal is not greater
    [InlineData(100, "500", "B", false)]
    public void Size_IsGreaterThan_Bytes(long fileSizeBytes, string conditionValue, string unit, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsGreaterThan,
            Value = conditionValue,
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(2 * KB, "1", "KB", true)]
    [InlineData(KB, "1", "KB", false)]       // Equal is not greater
    [InlineData(500, "1", "KB", false)]
    public void Size_IsGreaterThan_KB(long fileSizeBytes, string conditionValue, string unit, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsGreaterThan,
            Value = conditionValue,
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(2 * MB, "1", "MB", true)]
    [InlineData(MB, "1", "MB", false)]
    [InlineData(500 * KB, "1", "MB", false)]
    public void Size_IsGreaterThan_MB(long fileSizeBytes, string conditionValue, string unit, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsGreaterThan,
            Value = conditionValue,
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(2 * GB, "1", "GB", true)]
    [InlineData(GB, "1", "GB", false)]
    [InlineData(500 * MB, "1", "GB", false)]
    public void Size_IsGreaterThan_GB(long fileSizeBytes, string conditionValue, string unit, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsGreaterThan,
            Value = conditionValue,
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    #endregion

    #region IsLessThan Tests

    [Theory]
    [InlineData(100, "500", "B", true)]
    [InlineData(500, "500", "B", false)]   // Equal is not less
    [InlineData(1000, "500", "B", false)]
    public void Size_IsLessThan_Bytes(long fileSizeBytes, string conditionValue, string unit, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsLessThan,
            Value = conditionValue,
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(500, "1", "KB", true)]
    [InlineData(KB, "1", "KB", false)]
    [InlineData(2 * KB, "1", "KB", false)]
    public void Size_IsLessThan_KB(long fileSizeBytes, string conditionValue, string unit, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsLessThan,
            Value = conditionValue,
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(500 * KB, "1", "MB", true)]
    [InlineData(MB, "1", "MB", false)]
    [InlineData(2 * MB, "1", "MB", false)]
    public void Size_IsLessThan_MB(long fileSizeBytes, string conditionValue, string unit, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsLessThan,
            Value = conditionValue,
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    #endregion

    #region Is (Exact) Tests

    [Theory]
    [InlineData(1024, "1024", "B", true)]
    [InlineData(1024, "1", "KB", true)]
    [InlineData(1025, "1", "KB", false)]
    public void Size_Is_MatchesExactly(long fileSizeBytes, string conditionValue, string unit, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.Is,
            Value = conditionValue,
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    #endregion

    #region IsNot Tests

    [Theory]
    [InlineData(1024, "1024", "B", false)]
    [InlineData(1024, "500", "B", true)]
    [InlineData(1024, "1", "KB", false)]
    [InlineData(2048, "1", "KB", true)]
    public void Size_IsNot_Works(long fileSizeBytes, string conditionValue, string unit, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsNot,
            Value = conditionValue,
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    #endregion

    #region Embedded Unit Tests (e.g., "10MB")

    [Theory]
    [InlineData(2 * MB, "1MB", true)]
    [InlineData(500 * KB, "1MB", false)]
    [InlineData(2 * KB, "1KB", true)]
    [InlineData(500, "1KB", false)]
    [InlineData(2 * GB, "1GB", true)]
    public void Size_IsGreaterThan_EmbeddedUnit(long fileSizeBytes, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsGreaterThan,
            Value = conditionValue,
            SecondaryValue = null  // No separate unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(500 * KB, "1MB", true)]
    [InlineData(2 * MB, "1MB", false)]
    [InlineData(500, "1KB", true)]
    [InlineData(2 * KB, "1KB", false)]
    public void Size_IsLessThan_EmbeddedUnit(long fileSizeBytes, string conditionValue, bool expected)
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: fileSizeBytes);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsLessThan,
            Value = conditionValue,
            SecondaryValue = null
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    #endregion

    #region Edge Cases

    [Fact]
    public void Size_ZeroSizeFile()
    {
        var file = _helper.CreateFile("empty.txt", sizeInBytes: 0);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.Is,
            Value = "0",
            SecondaryValue = "B"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void Size_DefaultsToBytes_WhenNoUnit()
    {
        var file = _helper.CreateFile("test.txt", sizeInBytes: 1000);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Size,
            Operator = ConditionOperator.IsGreaterThan,
            Value = "500",
            SecondaryValue = null  // No unit specified
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    #endregion
}
