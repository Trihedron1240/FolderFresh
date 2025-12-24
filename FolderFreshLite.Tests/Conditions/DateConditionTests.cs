using FolderFreshLite.Models;
using FolderFreshLite.Services;
using FolderFreshLite.Tests.Helpers;

namespace FolderFreshLite.Tests.Conditions;

/// <summary>
/// Tests for Date conditions (DateCreated, DateModified, DateAccessed)
/// </summary>
public class DateConditionTests : IDisposable
{
    private readonly TestFileHelper _helper;
    private readonly RuleService _ruleService;

    public DateConditionTests()
    {
        _helper = new TestFileHelper();
        _ruleService = new RuleService();
    }

    public void Dispose() => _helper.Dispose();

    #region IsInTheLast Tests

    [Fact]
    public void DateModified_IsInTheLast_Days_RecentFile()
    {
        // File modified today should be in the last 7 days
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: DateTime.Now.AddDays(-1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "7",
            SecondaryValue = "days"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void DateModified_IsInTheLast_Days_OldFile()
    {
        // File modified 30 days ago should NOT be in the last 7 days
        var file = _helper.CreateFileWithDates("old.txt", modifiedDate: DateTime.Now.AddDays(-30));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "7",
            SecondaryValue = "days"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.False(result);
    }

    [Fact]
    public void DateModified_IsInTheLast_Weeks()
    {
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: DateTime.Now.AddDays(-10));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "2",
            SecondaryValue = "weeks"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);  // 10 days is within 2 weeks (14 days)
    }

    [Fact]
    public void DateModified_IsInTheLast_Months()
    {
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: DateTime.Now.AddDays(-45));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "2",
            SecondaryValue = "months"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);  // 45 days is within 2 months
    }

    [Fact]
    public void DateModified_IsInTheLast_Years()
    {
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: DateTime.Now.AddMonths(-6));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "1",
            SecondaryValue = "years"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);  // 6 months is within 1 year
    }

    [Fact]
    public void DateModified_IsInTheLast_Hours()
    {
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: DateTime.Now.AddHours(-2));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "4",
            SecondaryValue = "hours"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void DateModified_IsInTheLast_Minutes()
    {
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: DateTime.Now.AddMinutes(-5));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "10",
            SecondaryValue = "minutes"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Theory]
    [InlineData("day")]
    [InlineData("days")]
    [InlineData("Days")]
    [InlineData("DAYS")]
    public void DateModified_IsInTheLast_UnitVariants(string unit)
    {
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: DateTime.Now.AddDays(-1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "7",
            SecondaryValue = unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    #endregion

    #region IsBefore Tests

    [Fact]
    public void DateModified_IsBefore_OldFile()
    {
        var file = _helper.CreateFileWithDates("old.txt", modifiedDate: new DateTime(2020, 1, 1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsBefore,
            Value = "2021-01-01"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void DateModified_IsBefore_RecentFile()
    {
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: new DateTime(2024, 6, 1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsBefore,
            Value = "2021-01-01"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.False(result);
    }

    #endregion

    #region IsAfter Tests

    [Fact]
    public void DateModified_IsAfter_RecentFile()
    {
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: new DateTime(2024, 6, 1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsAfter,
            Value = "2021-01-01"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void DateModified_IsAfter_OldFile()
    {
        var file = _helper.CreateFileWithDates("old.txt", modifiedDate: new DateTime(2020, 1, 1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsAfter,
            Value = "2021-01-01"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.False(result);
    }

    #endregion

    #region DateCreated Tests

    [Fact]
    public void DateCreated_IsInTheLast()
    {
        var file = _helper.CreateFileWithDates("new.txt", createdDate: DateTime.Now.AddDays(-3));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateCreated,
            Operator = ConditionOperator.IsInTheLast,
            Value = "7",
            SecondaryValue = "days"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void DateCreated_IsBefore()
    {
        var file = _helper.CreateFileWithDates("old.txt", createdDate: new DateTime(2020, 1, 1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateCreated,
            Operator = ConditionOperator.IsBefore,
            Value = "2021-01-01"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void DateCreated_IsAfter()
    {
        var file = _helper.CreateFileWithDates("recent.txt", createdDate: new DateTime(2024, 6, 1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateCreated,
            Operator = ConditionOperator.IsAfter,
            Value = "2021-01-01"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    #endregion

    #region DateAccessed Tests

    [Fact]
    public void DateAccessed_IsInTheLast()
    {
        var file = _helper.CreateFileWithDates("accessed.txt", accessedDate: DateTime.Now.AddDays(-1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateAccessed,
            Operator = ConditionOperator.IsInTheLast,
            Value = "7",
            SecondaryValue = "days"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    #endregion

    #region Edge Cases

    [Fact]
    public void DateModified_IsInTheLast_ExactlyAtBoundary()
    {
        // File modified exactly 7 days ago should be included in "last 7 days"
        var file = _helper.CreateFileWithDates("boundary.txt", modifiedDate: DateTime.Now.AddDays(-7).AddMinutes(1));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "7",
            SecondaryValue = "days"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void DateModified_IsInTheLast_DefaultsToDays()
    {
        // When no unit specified, should default to days
        var file = _helper.CreateFileWithDates("recent.txt", modifiedDate: DateTime.Now.AddDays(-5));
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsInTheLast,
            Value = "7",
            SecondaryValue = null  // No unit
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }

    [Fact]
    public void DateModified_IsBefore_InvalidDate()
    {
        var file = _helper.CreateFileWithDates("test.txt", modifiedDate: DateTime.Now);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.DateModified,
            Operator = ConditionOperator.IsBefore,
            Value = "not-a-date"
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.False(result);  // Should return false for invalid date
    }

    #endregion
}
