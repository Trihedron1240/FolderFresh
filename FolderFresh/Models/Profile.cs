using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;

namespace FolderFresh.Models;

/// <summary>
/// Represents a profile containing a complete set of rules, categories, and settings.
/// Profiles are self-contained - switching profiles completely replaces all configuration.
/// </summary>
public class Profile : INotifyPropertyChanged
{
    private string _id = string.Empty;
    private string _name = string.Empty;
    private string _rulesJson = string.Empty;
    private string _categoriesJson = string.Empty;
    private string _settingsJson = string.Empty;
    private DateTime _createdAt = DateTime.Now;
    private DateTime _modifiedAt = DateTime.Now;

    /// <summary>
    /// Unique identifier for the profile (8-character alphanumeric)
    /// </summary>
    [JsonPropertyName("id")]
    public string Id
    {
        get => _id;
        set => SetProperty(ref _id, value);
    }

    /// <summary>
    /// Display name for the profile
    /// </summary>
    [JsonPropertyName("name")]
    public string Name
    {
        get => _name;
        set => SetProperty(ref _name, value);
    }

    /// <summary>
    /// Serialized JSON string containing the profile's rules
    /// </summary>
    [JsonPropertyName("rulesJson")]
    public string RulesJson
    {
        get => _rulesJson;
        set => SetProperty(ref _rulesJson, value);
    }

    /// <summary>
    /// Serialized JSON string containing the profile's categories
    /// </summary>
    [JsonPropertyName("categoriesJson")]
    public string CategoriesJson
    {
        get => _categoriesJson;
        set => SetProperty(ref _categoriesJson, value);
    }

    /// <summary>
    /// Serialized JSON string containing the profile's settings
    /// </summary>
    [JsonPropertyName("settingsJson")]
    public string SettingsJson
    {
        get => _settingsJson;
        set => SetProperty(ref _settingsJson, value);
    }

    /// <summary>
    /// When the profile was created
    /// </summary>
    [JsonPropertyName("createdAt")]
    public DateTime CreatedAt
    {
        get => _createdAt;
        set => SetProperty(ref _createdAt, value);
    }

    /// <summary>
    /// When the profile was last modified
    /// </summary>
    [JsonPropertyName("modifiedAt")]
    public DateTime ModifiedAt
    {
        get => _modifiedAt;
        set => SetProperty(ref _modifiedAt, value);
    }

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
    /// Creates a new profile with a generated ID
    /// </summary>
    public static Profile Create(string name)
    {
        return new Profile
        {
            Id = Guid.NewGuid().ToString("N")[..8],
            Name = name,
            CreatedAt = DateTime.Now,
            ModifiedAt = DateTime.Now
        };
    }
}
