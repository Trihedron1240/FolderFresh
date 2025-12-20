using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;

namespace FolderFreshLite.Models;

public class Rule : INotifyPropertyChanged
{
    private string _id = string.Empty;
    private string _name = string.Empty;
    private bool _isEnabled = true;
    private int _priority;
    private ConditionGroup _conditions = new();
    private List<RuleAction> _actions = new();
    private DateTime _createdAt = DateTime.Now;
    private DateTime _modifiedAt = DateTime.Now;

    [JsonPropertyName("id")]
    public string Id
    {
        get => _id;
        set => SetProperty(ref _id, value);
    }

    [JsonPropertyName("name")]
    public string Name
    {
        get => _name;
        set => SetProperty(ref _name, value);
    }

    [JsonPropertyName("isEnabled")]
    public bool IsEnabled
    {
        get => _isEnabled;
        set => SetProperty(ref _isEnabled, value);
    }

    /// <summary>
    /// Rule priority - lower number = higher priority (evaluated first)
    /// </summary>
    [JsonPropertyName("priority")]
    public int Priority
    {
        get => _priority;
        set => SetProperty(ref _priority, value);
    }

    [JsonPropertyName("conditions")]
    public ConditionGroup Conditions
    {
        get => _conditions;
        set => SetProperty(ref _conditions, value);
    }

    [JsonPropertyName("actions")]
    public List<RuleAction> Actions
    {
        get => _actions;
        set => SetProperty(ref _actions, value);
    }

    [JsonPropertyName("createdAt")]
    public DateTime CreatedAt
    {
        get => _createdAt;
        set => SetProperty(ref _createdAt, value);
    }

    [JsonPropertyName("modifiedAt")]
    public DateTime ModifiedAt
    {
        get => _modifiedAt;
        set => SetProperty(ref _modifiedAt, value);
    }

    /// <summary>
    /// Display string showing the number of conditions
    /// </summary>
    [JsonIgnore]
    public string ConditionsDisplay => Conditions?.Conditions?.Count switch
    {
        null or 0 => "No conditions",
        1 => "1 condition",
        var n => $"{n} conditions"
    };

    /// <summary>
    /// Display string showing the number of actions
    /// </summary>
    [JsonIgnore]
    public string ActionsDisplay => Actions?.Count switch
    {
        null or 0 => "No actions",
        1 => "1 action",
        var n => $"{n} actions"
    };

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? propertyName = null)
    {
        if (Equals(field, value)) return false;
        field = value;
        OnPropertyChanged(propertyName);
        return true;
    }

    /// <summary>
    /// Creates a new rule with a generated ID
    /// </summary>
    public static Rule Create(string name)
    {
        return new Rule
        {
            Id = Guid.NewGuid().ToString("N")[..8],
            Name = name,
            IsEnabled = true,
            Priority = 0,
            Conditions = new ConditionGroup { MatchType = ConditionMatchType.All },
            Actions = new List<RuleAction>(),
            CreatedAt = DateTime.Now,
            ModifiedAt = DateTime.Now
        };
    }
}
