using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using FolderFresh.Models;

namespace FolderFresh.Services;

public class CategoryService
{
    private const string AppFolderName = "FolderFresh";
    private const string CategoriesFileName = "categories.json";

    private readonly string _categoriesFilePath;
    private List<Category> _categories = new();

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public CategoryService()
    {
        var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var appFolderPath = Path.Combine(appDataPath, AppFolderName);

        // Ensure directory exists
        if (!Directory.Exists(appFolderPath))
        {
            Directory.CreateDirectory(appFolderPath);
        }

        _categoriesFilePath = Path.Combine(appFolderPath, CategoriesFileName);
    }

    /// <summary>
    /// Loads categories from JSON file. Creates defaults if file doesn't exist.
    /// </summary>
    public async Task<List<Category>> LoadCategoriesAsync()
    {
        try
        {
            if (!File.Exists(_categoriesFilePath))
            {
                // First run - create defaults
                _categories = GetDefaultCategories();
                await SaveCategoriesAsync(_categories);
                return _categories;
            }

            var json = await File.ReadAllTextAsync(_categoriesFilePath);
            var data = JsonSerializer.Deserialize<CategoriesFile>(json, JsonOptions);

            if (data?.Categories != null && data.Categories.Count > 0)
            {
                _categories = data.Categories;
            }
            else
            {
                // File exists but empty/corrupt - reset to defaults
                _categories = GetDefaultCategories();
                await SaveCategoriesAsync(_categories);
            }

            return _categories;
        }
        catch (Exception)
        {
            // On any error, return defaults
            _categories = GetDefaultCategories();
            return _categories;
        }
    }

    /// <summary>
    /// Saves categories to JSON file.
    /// </summary>
    public async Task SaveCategoriesAsync(List<Category> categories)
    {
        try
        {
            _categories = categories;
            var data = new CategoriesFile { Categories = categories };
            var json = JsonSerializer.Serialize(data, JsonOptions);
            await File.WriteAllTextAsync(_categoriesFilePath, json);
        }
        catch (Exception)
        {
            // Log error if needed
        }
    }

    /// <summary>
    /// Adds a new category and saves to file.
    /// </summary>
    public async Task<Category> AddCategoryAsync(Category category)
    {
        // Generate ID if not set
        if (string.IsNullOrEmpty(category.Id))
        {
            category.Id = Guid.NewGuid().ToString();
        }

        category.IsDefault = false;
        _categories.Add(category);
        await SaveCategoriesAsync(_categories);
        return category;
    }

    /// <summary>
    /// Updates an existing category and saves to file.
    /// </summary>
    public async Task UpdateCategoryAsync(Category category)
    {
        var index = _categories.FindIndex(c => c.Id == category.Id);
        if (index >= 0)
        {
            _categories[index] = category;
            await SaveCategoriesAsync(_categories);
        }
    }

    /// <summary>
    /// Deletes a category by ID and saves to file. Cannot delete default categories.
    /// </summary>
    public async Task DeleteCategoryAsync(string categoryId)
    {
        var category = _categories.FirstOrDefault(c => c.Id == categoryId);
        if (category != null && !category.IsDefault)
        {
            _categories.Remove(category);
            await SaveCategoriesAsync(_categories);
        }
    }

    /// <summary>
    /// Gets all loaded categories.
    /// </summary>
    public List<Category> GetCategories()
    {
        return _categories;
    }

    /// <summary>
    /// Gets the appropriate category for a file based on its extension.
    /// Checks custom categories first, then defaults, then fallback.
    /// </summary>
    public Category GetCategoryForFile(string extension)
    {
        if (string.IsNullOrEmpty(extension))
        {
            return GetFallbackCategory();
        }

        // Normalize extension
        extension = extension.ToLowerInvariant();
        if (!extension.StartsWith('.'))
        {
            extension = "." + extension;
        }

        // Check custom categories first (non-default, in order added)
        var customCategory = _categories
            .Where(c => !c.IsDefault && c.IsEnabled)
            .FirstOrDefault(c => c.Extensions.Contains(extension, StringComparer.OrdinalIgnoreCase));

        if (customCategory != null)
        {
            return customCategory;
        }

        // Check default categories (excluding fallback)
        var defaultCategory = _categories
            .Where(c => c.IsDefault && !c.IsFallback && c.IsEnabled)
            .FirstOrDefault(c => c.Extensions.Contains(extension, StringComparer.OrdinalIgnoreCase));

        if (defaultCategory != null)
        {
            return defaultCategory;
        }

        // Return fallback category
        return GetFallbackCategory();
    }

    /// <summary>
    /// Gets the fallback "Other" category.
    /// </summary>
    public Category GetFallbackCategory()
    {
        return _categories.FirstOrDefault(c => c.IsFallback)
            ?? _categories.FirstOrDefault(c => c.Id == "other")
            ?? new Category
            {
                Id = "other",
                Name = "Other",
                Icon = "\u26AB",
                Color = "#6B7280",
                Extensions = new List<string>(),
                Destination = "Other",
                IsDefault = true,
                IsFallback = true
            };
    }

    /// <summary>
    /// Resets categories to defaults and saves to file.
    /// </summary>
    public async Task ResetToDefaultsAsync()
    {
        _categories = GetDefaultCategories();
        await SaveCategoriesAsync(_categories);
    }

    /// <summary>
    /// Gets default categories list.
    /// </summary>
    public List<Category> GetDefaultCategories()
    {
        return new List<Category>
        {
            new Category
            {
                Id = "documents",
                Name = "Documents",
                Icon = "\U0001F4C4", // 📄
                Color = "#F59E0B",
                Extensions = new List<string>
                {
                    ".pdf", ".doc", ".docx", ".txt", ".rtf",
                    ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods"
                },
                Destination = "Documents",
                IsDefault = true
            },
            new Category
            {
                Id = "images",
                Name = "Images",
                Icon = "\U0001F5BC", // 🖼️
                Color = "#3B82F6",
                Extensions = new List<string>
                {
                    ".jpg", ".jpeg", ".png", ".gif", ".bmp",
                    ".svg", ".webp", ".ico", ".tiff"
                },
                Destination = "Images",
                IsDefault = true
            },
            new Category
            {
                Id = "audio",
                Name = "Audio",
                Icon = "\U0001F3B5", // 🎵
                Color = "#10B981",
                Extensions = new List<string>
                {
                    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"
                },
                Destination = "Audio",
                IsDefault = true
            },
            new Category
            {
                Id = "video",
                Name = "Video",
                Icon = "\U0001F3AC", // 🎬
                Color = "#EF4444",
                Extensions = new List<string>
                {
                    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"
                },
                Destination = "Video",
                IsDefault = true
            },
            new Category
            {
                Id = "archives",
                Name = "Archives",
                Icon = "\U0001F4E6", // 📦
                Color = "#8B5CF6",
                Extensions = new List<string>
                {
                    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"
                },
                Destination = "Archives",
                IsDefault = true
            },
            new Category
            {
                Id = "other",
                Name = "Other",
                Icon = "\u26AB", // ⚫
                Color = "#6B7280",
                Extensions = new List<string>(),
                Destination = "Other",
                IsDefault = true,
                IsFallback = true
            }
        };
    }

    /// <summary>
    /// Gets all default categories.
    /// </summary>
    public List<Category> GetDefaultCategoriesFromLoaded()
    {
        return _categories.Where(c => c.IsDefault).ToList();
    }

    /// <summary>
    /// Gets all custom (non-default) categories.
    /// </summary>
    public List<Category> GetCustomCategories()
    {
        return _categories.Where(c => !c.IsDefault).ToList();
    }

    /// <summary>
    /// Gets all loaded categories.
    /// </summary>
    public List<Category> GetAllCategories()
    {
        return _categories.ToList();
    }
}

/// <summary>
/// Wrapper class for JSON serialization.
/// </summary>
internal class CategoriesFile
{
    public List<Category> Categories { get; set; } = new();
}
