using FolderFreshLite.Models;
using FolderFreshLite.Services;
using FolderFreshLite.Tests.Helpers;

namespace FolderFreshLite.Tests.Conditions;

/// <summary>
/// Tests for ConditionGroup logic (All/Any/None combinations)
/// </summary>
public class ConditionGroupTests : IDisposable
{
    private readonly TestFileHelper _helper;
    private readonly RuleService _ruleService;

    public ConditionGroupTests()
    {
        _helper = new TestFileHelper();
        _ruleService = new RuleService();
    }

    public void Dispose() => _helper.Dispose();

    #region MatchType.All (AND logic)

    [Fact]
    public void All_AllConditionsTrue_ReturnsTrue()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.All,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" },
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "doc" }
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);
    }

    [Fact]
    public void All_OneConditionFalse_ReturnsFalse()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.All,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" },
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "xyz" }  // False
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.False(result);
    }

    [Fact]
    public void All_AllConditionsFalse_ReturnsFalse()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.All,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "txt" },  // False
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "xyz" }  // False
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.False(result);
    }

    #endregion

    #region MatchType.Any (OR logic)

    [Fact]
    public void Any_AllConditionsTrue_ReturnsTrue()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.Any,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" },
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "doc" }
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);
    }

    [Fact]
    public void Any_OneConditionTrue_ReturnsTrue()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.Any,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "txt" },  // False
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "doc" }  // True
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);
    }

    [Fact]
    public void Any_AllConditionsFalse_ReturnsFalse()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.Any,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "txt" },  // False
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "xyz" }  // False
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.False(result);
    }

    #endregion

    #region MatchType.None (NOT ANY logic)

    [Fact]
    public void None_AllConditionsFalse_ReturnsTrue()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.None,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "txt" },  // False
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "xyz" }  // False
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);  // None match = true
    }

    [Fact]
    public void None_OneConditionTrue_ReturnsFalse()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.None,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" },  // True
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "xyz" }  // False
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.False(result);  // One matches = false
    }

    [Fact]
    public void None_AllConditionsTrue_ReturnsFalse()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.None,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" },
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "doc" }
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.False(result);  // All match = false
    }

    #endregion

    #region Nested Groups

    [Fact]
    public void NestedGroups_AllWithAny()
    {
        // Match: (extension is pdf OR txt) AND (name starts with doc)
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.All,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "doc" }
            },
            NestedGroups = new List<ConditionGroup>
            {
                new()
                {
                    MatchType = ConditionMatchType.Any,
                    Conditions = new List<Condition>
                    {
                        new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" },
                        new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "txt" }
                    }
                }
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);
    }

    [Fact]
    public void NestedGroups_AnyWithAll()
    {
        // Match: (extension is pdf AND name starts with doc) OR (extension is txt AND name starts with note)
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.Any,
            NestedGroups = new List<ConditionGroup>
            {
                new()
                {
                    MatchType = ConditionMatchType.All,
                    Conditions = new List<Condition>
                    {
                        new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" },
                        new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "doc" }
                    }
                },
                new()
                {
                    MatchType = ConditionMatchType.All,
                    Conditions = new List<Condition>
                    {
                        new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "txt" },
                        new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "note" }
                    }
                }
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);  // First nested group matches
    }

    [Fact]
    public void NestedGroups_NoneWithAny()
    {
        // Match: NOT (extension is exe OR extension is bat)
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.None,
            NestedGroups = new List<ConditionGroup>
            {
                new()
                {
                    MatchType = ConditionMatchType.Any,
                    Conditions = new List<Condition>
                    {
                        new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "exe" },
                        new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "bat" }
                    }
                }
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);  // Not exe or bat
    }

    [Fact]
    public void NestedGroups_DeepNesting()
    {
        // Complex: ((A AND B) OR (C AND D)) AND E
        var file = _helper.CreateFile("document.pdf", sizeInBytes: 1024);
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.All,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Size, Operator = ConditionOperator.IsGreaterThan, Value = "0", SecondaryValue = "B" }  // E
            },
            NestedGroups = new List<ConditionGroup>
            {
                new()  // (A AND B) OR (C AND D)
                {
                    MatchType = ConditionMatchType.Any,
                    NestedGroups = new List<ConditionGroup>
                    {
                        new()  // A AND B
                        {
                            MatchType = ConditionMatchType.All,
                            Conditions = new List<Condition>
                            {
                                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" },  // A
                                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "doc" }  // B
                            }
                        },
                        new()  // C AND D
                        {
                            MatchType = ConditionMatchType.All,
                            Conditions = new List<Condition>
                            {
                                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "txt" },  // C
                                new() { Attribute = ConditionAttribute.Name, Operator = ConditionOperator.StartsWith, Value = "note" }  // D
                            }
                        }
                    }
                }
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);
    }

    #endregion

    #region Empty Groups

    [Fact]
    public void EmptyGroup_MatchesEverything()
    {
        var file = _helper.CreateFile("anything.xyz");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.All,
            Conditions = new List<Condition>(),
            NestedGroups = new List<ConditionGroup>()
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);  // Empty group should match everything
    }

    [Fact]
    public void EmptyGroup_Any_MatchesEverything()
    {
        var file = _helper.CreateFile("anything.xyz");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.Any,
            Conditions = new List<Condition>()
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);
    }

    [Fact]
    public void EmptyGroup_None_MatchesEverything()
    {
        var file = _helper.CreateFile("anything.xyz");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.None,
            Conditions = new List<Condition>()
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);
    }

    #endregion

    #region Single Condition

    [Fact]
    public void SingleCondition_All_Works()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.All,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" }
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);
    }

    [Fact]
    public void SingleCondition_Any_Works()
    {
        var file = _helper.CreateFile("document.pdf");
        var group = new ConditionGroup
        {
            MatchType = ConditionMatchType.Any,
            Conditions = new List<Condition>
            {
                new() { Attribute = ConditionAttribute.Extension, Operator = ConditionOperator.Is, Value = "pdf" }
            }
        };

        var result = _ruleService.EvaluateConditionGroup(group, file);

        Assert.True(result);
    }

    #endregion
}
