using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace FolderFreshLite.Models;

public class Category : INotifyPropertyChanged
{
    private string _id = string.Empty;
    private string _name = string.Empty;
    private string _icon = string.Empty;
    private string _color = string.Empty;
    private List<string> _extensions = new();
    private string _destination = string.Empty;
    private bool _isDefault;
    private bool _isEnabled = true;
    private bool _isFallback;

    public string Id
    {
        get => _id;
        set => SetProperty(ref _id, value);
    }

    public string Name
    {
        get => _name;
        set => SetProperty(ref _name, value);
    }

    public string Icon
    {
        get => _icon;
        set => SetProperty(ref _icon, value);
    }

    public string Color
    {
        get => _color;
        set => SetProperty(ref _color, value);
    }

    public List<string> Extensions
    {
        get => _extensions;
        set => SetProperty(ref _extensions, value);
    }

    public string Destination
    {
        get => _destination;
        set => SetProperty(ref _destination, value);
    }

    public bool IsDefault
    {
        get => _isDefault;
        set => SetProperty(ref _isDefault, value);
    }

    public bool IsEnabled
    {
        get => _isEnabled;
        set => SetProperty(ref _isEnabled, value);
    }

    /// <summary>
    /// Indicates this is the fallback category for unmatched files (typically "Other")
    /// </summary>
    public bool IsFallback
    {
        get => _isFallback;
        set => SetProperty(ref _isFallback, value);
    }

    /// <summary>
    /// Display string showing the extensions (e.g., ".pdf, .doc, .docx")
    /// </summary>
    public string ExtensionsDisplay => Extensions.Count > 0
        ? string.Join(", ", Extensions)
        : "No extensions";

    /// <summary>
    /// Count of extensions in this category
    /// </summary>
    public int ExtensionCount => Extensions.Count;

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
    /// Creates a default set of categories for file organization
    /// </summary>
    public static List<Category> GetDefaultCategories()
    {
        return new List<Category>
        {
            new Category
            {
                Id = "documents",
                Name = "Documents",
                Icon = "\U0001F4C4", // 📄
                Color = "#5B9BD5",
                Extensions = new List<string> { ".pdf", ".doc", ".docx", ".txt", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx" },
                Destination = "Documents",
                IsDefault = true
            },
            new Category
            {
                Id = "images",
                Name = "Images",
                Icon = "\U0001F5BC", // 🖼️
                Color = "#9B59B6",
                Extensions = new List<string> { ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp" },
                Destination = "Images",
                IsDefault = true
            },
            new Category
            {
                Id = "audio",
                Name = "Audio",
                Icon = "\U0001F3B5", // 🎵
                Color = "#E91E63",
                Extensions = new List<string> { ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a" },
                Destination = "Audio",
                IsDefault = true
            },
            new Category
            {
                Id = "video",
                Name = "Video",
                Icon = "\U0001F3AC", // 🎬
                Color = "#00BCD4",
                Extensions = new List<string> { ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv" },
                Destination = "Video",
                IsDefault = true
            },
            new Category
            {
                Id = "archives",
                Name = "Archives",
                Icon = "\U0001F4E6", // 📦
                Color = "#795548",
                Extensions = new List<string> { ".zip", ".rar", ".7z", ".tar", ".gz" },
                Destination = "Archives",
                IsDefault = true
            },
            new Category
            {
                Id = "other",
                Name = "Other",
                Icon = "\u26AB", // ⚫
                Color = "#6B7280",
                Extensions = new List<string>(), // Fallback for everything else
                Destination = "Other",
                IsDefault = true,
                IsFallback = true
            }
        };
    }
}
