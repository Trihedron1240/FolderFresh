using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using FolderFreshLite.Models;
using FolderFreshLite.Services;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace FolderFreshLite.Components;

public sealed partial class CategoriesContent : UserControl, INotifyPropertyChanged
{
    private readonly CategoryService _categoryService;

    public ObservableCollection<Category> DefaultCategories { get; } = new();
    public ObservableCollection<Category> CustomCategories { get; } = new();

    public bool HasCustomCategories => CustomCategories.Count > 0;
    public bool ShowEmptyState => CustomCategories.Count == 0;

    public event PropertyChangedEventHandler? PropertyChanged;
    public event EventHandler<Category>? CategoryEditRequested;
    public event EventHandler<Category>? CategoryDeleteRequested;
    public event EventHandler? NewCategoryRequested;

    public CategoriesContent()
    {
        this.InitializeComponent();

        _categoryService = new CategoryService();

        DefaultCategoriesList.ItemsSource = DefaultCategories;
        CustomCategoriesList.ItemsSource = CustomCategories;

        CustomCategories.CollectionChanged += (s, e) =>
        {
            OnPropertyChanged(nameof(HasCustomCategories));
            OnPropertyChanged(nameof(ShowEmptyState));
        };

        // Load categories when control is loaded
        this.Loaded += CategoriesContent_Loaded;
    }

    private async void CategoriesContent_Loaded(object sender, RoutedEventArgs e)
    {
        await LoadCategoriesAsync();
    }

    private async System.Threading.Tasks.Task LoadCategoriesAsync()
    {
        var categories = await _categoryService.LoadCategoriesAsync();

        DefaultCategories.Clear();
        CustomCategories.Clear();

        foreach (var category in categories)
        {
            if (category.IsDefault)
            {
                DefaultCategories.Add(category);
            }
            else
            {
                CustomCategories.Add(category);
            }
        }
    }

    private void NewCategoryButton_Click(object sender, RoutedEventArgs e)
    {
        // Show the form panel for new category
        FormPanel.ResetForm();
        FormPanel.Visibility = Visibility.Visible;

        NewCategoryRequested?.Invoke(this, EventArgs.Empty);
    }

    private void CategoryCard_EditClicked(object sender, Category category)
    {
        // Show the form panel for editing
        FormPanel.EditCategory(category);
        FormPanel.Visibility = Visibility.Visible;

        CategoryEditRequested?.Invoke(this, category);
    }

    private async void CategoryCard_DeleteClicked(object sender, Category category)
    {
        CategoryDeleteRequested?.Invoke(this, category);

        // If it's a custom category, remove it from the list and save
        if (!category.IsDefault && CustomCategories.Contains(category))
        {
            CustomCategories.Remove(category);
            await _categoryService.DeleteCategoryAsync(category.Id);
        }
    }

    private async void FormPanel_SaveClicked(object sender, Category category)
    {
        // Hide the form panel
        FormPanel.Visibility = Visibility.Collapsed;

        if (FormPanel.IsEditMode)
        {
            // Update existing category
            await _categoryService.UpdateCategoryAsync(category);

            // Refresh display
            var index = CustomCategories.IndexOf(category);
            if (index >= 0)
            {
                CustomCategories.RemoveAt(index);
                CustomCategories.Insert(index, category);
            }
        }
        else
        {
            // Add new category
            await _categoryService.AddCategoryAsync(category);
            CustomCategories.Add(category);
        }
    }

    private void FormPanel_CancelClicked(object? sender, EventArgs e)
    {
        // Hide the form panel
        FormPanel.Visibility = Visibility.Collapsed;
    }

    /// <summary>
    /// Adds a new custom category to the list
    /// </summary>
    public async System.Threading.Tasks.Task AddCustomCategoryAsync(Category category)
    {
        category.IsDefault = false;
        await _categoryService.AddCategoryAsync(category);
        CustomCategories.Add(category);
    }

    /// <summary>
    /// Removes a custom category from the list
    /// </summary>
    public async System.Threading.Tasks.Task<bool> RemoveCustomCategoryAsync(Category category)
    {
        if (CustomCategories.Remove(category))
        {
            await _categoryService.DeleteCategoryAsync(category.Id);
            return true;
        }
        return false;
    }

    /// <summary>
    /// Gets all categories (default + custom)
    /// </summary>
    public ObservableCollection<Category> GetAllCategories()
    {
        var all = new ObservableCollection<Category>();
        foreach (var cat in DefaultCategories) all.Add(cat);
        foreach (var cat in CustomCategories) all.Add(cat);
        return all;
    }

    /// <summary>
    /// Gets the CategoryService instance for external use
    /// </summary>
    public CategoryService GetCategoryService() => _categoryService;

    private void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
