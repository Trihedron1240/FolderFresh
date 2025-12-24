using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using FolderFresh.Models;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Shapes;
using Windows.Storage;
using Windows.Storage.Pickers;
using Windows.UI;

namespace FolderFresh.Components;

public sealed partial class CategoryFormPanel : UserControl
{
    private Category? _editingCategory;
    private string _selectedIcon = "\U0001F4C4"; // 📄
    private string _selectedColor = "#5B9BD5";
    private readonly ObservableCollection<string> _extensions = new();

    private static readonly List<string> AvailableIcons = new()
    {
        "\U0001F4C4", // 📄
        "\U0001F4C1", // 📁
        "\U0001F5BC", // 🖼️
        "\U0001F3B5", // 🎵
        "\U0001F3AC", // 🎬
        "\U0001F4E6", // 📦
        "\U0001F4BC", // 💼
        "\U0001F9FE", // 🧾
        "\U0001F4CA", // 📊
        "\U0001F3AE", // 🎮
        "\U0001F4BE", // 💾
        "\u26AB"      // ⚫
    };

    private static readonly List<string> AvailableColors = new()
    {
        "#5B9BD5", // Blue
        "#70AD47", // Green
        "#ED7D31", // Orange
        "#FF6B6B", // Red
        "#9B59B6", // Purple
        "#00BCD4", // Cyan
        "#E91E63", // Pink
        "#795548"  // Brown
    };

    public static readonly DependencyProperty CategoryProperty =
        DependencyProperty.Register(
            nameof(Category),
            typeof(Category),
            typeof(CategoryFormPanel),
            new PropertyMetadata(null, OnCategoryChanged));

    public Category? Category
    {
        get => (Category?)GetValue(CategoryProperty);
        set => SetValue(CategoryProperty, value);
    }

    public static readonly DependencyProperty IsEditModeProperty =
        DependencyProperty.Register(
            nameof(IsEditMode),
            typeof(bool),
            typeof(CategoryFormPanel),
            new PropertyMetadata(false, OnIsEditModeChanged));

    public bool IsEditMode
    {
        get => (bool)GetValue(IsEditModeProperty);
        set => SetValue(IsEditModeProperty, value);
    }

    public event EventHandler<Category>? SaveClicked;
    public event EventHandler? CancelClicked;

    public CategoryFormPanel()
    {
        this.InitializeComponent();
        InitializeIconGrid();
        InitializeColorGrid();
        ExtensionPillsList.ItemsSource = _extensions;
    }

    private void InitializeIconGrid()
    {
        IconGrid.ItemsSource = AvailableIcons;
        IconGrid.SelectedIndex = 0;
    }

    private void InitializeColorGrid()
    {
        ColorGrid.Items.Clear();
        foreach (var colorHex in AvailableColors)
        {
            var color = ParseHexColor(colorHex);
            var ellipse = new Ellipse
            {
                Width = 28,
                Height = 28,
                Fill = new SolidColorBrush(color),
                Tag = colorHex
            };
            ColorGrid.Items.Add(ellipse);
        }
        ColorGrid.SelectedIndex = 0;
    }

    private static void OnCategoryChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is CategoryFormPanel panel)
        {
            panel.LoadCategory(e.NewValue as Category);
        }
    }

    private static void OnIsEditModeChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is CategoryFormPanel panel)
        {
            panel.HeaderText.Text = (bool)e.NewValue ? "Edit Category" : "New Category";
        }
    }

    private void LoadCategory(Category? category)
    {
        _editingCategory = category;
        _extensions.Clear();

        if (category != null)
        {
            NameTextBox.Text = category.Name;
            DestinationTextBox.Text = category.Destination;

            // Select icon
            var iconIndex = AvailableIcons.IndexOf(category.Icon);
            if (iconIndex >= 0)
            {
                IconGrid.SelectedIndex = iconIndex;
                _selectedIcon = category.Icon;
            }

            // Select color
            var colorIndex = AvailableColors.IndexOf(category.Color);
            if (colorIndex >= 0)
            {
                ColorGrid.SelectedIndex = colorIndex;
                _selectedColor = category.Color;
            }

            // Load extensions
            foreach (var ext in category.Extensions)
            {
                _extensions.Add(ext);
            }
        }
        else
        {
            // Reset form for new category
            NameTextBox.Text = "";
            DestinationTextBox.Text = "";
            IconGrid.SelectedIndex = 0;
            ColorGrid.SelectedIndex = 0;
            _selectedIcon = AvailableIcons[0];
            _selectedColor = AvailableColors[0];
        }
    }

    private void IconGrid_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (IconGrid.SelectedItem is string icon)
        {
            _selectedIcon = icon;
        }
    }

    private void ColorGrid_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ColorGrid.SelectedItem is Ellipse ellipse && ellipse.Tag is string colorHex)
        {
            _selectedColor = colorHex;
        }
    }

    private void ExtensionInputBox_KeyDown(object sender, KeyRoutedEventArgs e)
    {
        if (e.Key == Windows.System.VirtualKey.Enter || e.Key == (Windows.System.VirtualKey)188) // Enter or comma
        {
            AddExtension(ExtensionInputBox.Text);
            ExtensionInputBox.Text = "";
            e.Handled = true;
        }
    }

    private void AddExtension(string extension)
    {
        extension = extension.Trim().TrimEnd(',').ToLowerInvariant();

        if (string.IsNullOrWhiteSpace(extension))
            return;

        // Ensure it starts with a dot
        if (!extension.StartsWith('.'))
            extension = "." + extension;

        // Don't add duplicates
        if (!_extensions.Contains(extension))
        {
            _extensions.Add(extension);
        }
    }

    private void RemoveExtension_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.Tag is string extension)
        {
            _extensions.Remove(extension);
        }
    }

    private void AddExtensionButton_Click(object sender, RoutedEventArgs e)
    {
        AddExtension(ExtensionInputBox.Text);
        ExtensionInputBox.Text = "";
        ExtensionInputBox.Focus(FocusState.Programmatic);
    }

    private void SuggestionChip_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.Content is string extension)
        {
            AddExtension(extension);
        }
    }

    private async void BrowseFolder_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FolderPicker
        {
            SuggestedStartLocation = PickerLocationId.Desktop,
            ViewMode = PickerViewMode.List
        };
        picker.FileTypeFilter.Add("*");

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var folder = await picker.PickSingleFolderAsync();
        if (folder != null)
        {
            // Use just the folder name or a relative path
            DestinationTextBox.Text = folder.Name;
        }
    }

    private void CloseButton_Click(object sender, RoutedEventArgs e)
    {
        CancelClicked?.Invoke(this, EventArgs.Empty);
    }

    private void CancelButton_Click(object sender, RoutedEventArgs e)
    {
        CancelClicked?.Invoke(this, EventArgs.Empty);
    }

    private void SaveButton_Click(object sender, RoutedEventArgs e)
    {
        // Validate
        if (string.IsNullOrWhiteSpace(NameTextBox.Text))
        {
            // Could show validation error
            return;
        }

        // Create or update category
        var category = _editingCategory ?? new Category
        {
            Id = Guid.NewGuid().ToString(),
            IsDefault = false
        };

        category.Name = NameTextBox.Text.Trim();
        category.Icon = _selectedIcon;
        category.Color = _selectedColor;
        category.Extensions = _extensions.ToList();
        category.Destination = string.IsNullOrWhiteSpace(DestinationTextBox.Text)
            ? category.Name
            : DestinationTextBox.Text.Trim();

        SaveClicked?.Invoke(this, category);
    }

    private static Color ParseHexColor(string hex)
    {
        hex = hex.TrimStart('#');

        if (hex.Length == 6)
        {
            return Color.FromArgb(
                255,
                Convert.ToByte(hex.Substring(0, 2), 16),
                Convert.ToByte(hex.Substring(2, 2), 16),
                Convert.ToByte(hex.Substring(4, 2), 16));
        }

        return Color.FromArgb(255, 91, 155, 213); // Default blue
    }

    /// <summary>
    /// Resets the form to create a new category
    /// </summary>
    public void ResetForm()
    {
        IsEditMode = false;
        Category = null;
        LoadCategory(null);
    }

    /// <summary>
    /// Loads a category for editing
    /// </summary>
    public void EditCategory(Category category)
    {
        IsEditMode = true;
        Category = category;
    }
}
