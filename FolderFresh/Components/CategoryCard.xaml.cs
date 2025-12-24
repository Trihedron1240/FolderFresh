using System;
using System.Collections.Generic;
using System.Linq;
using FolderFresh.Models;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Windows.UI;

namespace FolderFresh.Components;

public sealed partial class CategoryCard : UserControl
{
    private const int MaxVisibleExtensions = 8;

    public static readonly DependencyProperty CategoryProperty =
        DependencyProperty.Register(
            nameof(Category),
            typeof(Category),
            typeof(CategoryCard),
            new PropertyMetadata(null, OnCategoryChanged));

    public Category? Category
    {
        get => (Category?)GetValue(CategoryProperty);
        set => SetValue(CategoryProperty, value);
    }

    public event EventHandler<Category>? EditClicked;
    public event EventHandler<Category>? DeleteClicked;
    public event EventHandler<Category>? EnabledChanged;

    public CategoryCard()
    {
        this.InitializeComponent();
    }

    private static void OnCategoryChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is CategoryCard card && e.NewValue is Category category)
        {
            card.UpdateDisplay(category);
        }
    }

    private void UpdateDisplay(Category category)
    {
        // Update toggle state
        EnabledToggle.IsOn = category.IsEnabled;

        // Update color circle
        if (!string.IsNullOrEmpty(category.Color))
        {
            try
            {
                var color = ParseHexColor(category.Color);
                ColorCircle.Fill = new SolidColorBrush(color);
            }
            catch
            {
                ColorCircle.Fill = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102));
            }
        }

        // Update name
        NameText.Text = category.Name;

        // Update extensions pills (max 8, then "+X more")
        UpdateExtensionsPills(category.Extensions);

        // Update destination
        DestinationText.Text = $"→ {category.Destination}";

        // Show/hide action buttons based on whether it's a default category
        if (category.IsDefault)
        {
            LockIcon.Visibility = Visibility.Visible;
            EditButton.Visibility = Visibility.Collapsed;
            DeleteButton.Visibility = Visibility.Collapsed;
        }
        else
        {
            LockIcon.Visibility = Visibility.Collapsed;
            EditButton.Visibility = Visibility.Visible;
            DeleteButton.Visibility = Visibility.Visible;
        }

        // Update visual state based on enabled
        UpdateEnabledState();
    }

    private void UpdateEnabledState()
    {
        var opacity = Category?.IsEnabled == true ? 1.0 : 0.5;
        NameText.Opacity = opacity;
        ColorCircle.Opacity = opacity;
        ExtensionsList.Opacity = opacity;
        DestinationText.Opacity = opacity;
    }

    private void EnabledToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (Category == null) return;

        Category.IsEnabled = EnabledToggle.IsOn;
        UpdateEnabledState();
        EnabledChanged?.Invoke(this, Category);
    }

    private void UpdateExtensionsPills(List<string> extensions)
    {
        var displayItems = new List<string>();

        if (extensions.Count <= MaxVisibleExtensions)
        {
            displayItems.AddRange(extensions);
        }
        else
        {
            displayItems.AddRange(extensions.Take(MaxVisibleExtensions));
            var remaining = extensions.Count - MaxVisibleExtensions;
            displayItems.Add($"+{remaining} more");
        }

        ExtensionsList.ItemsSource = displayItems;
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
        else if (hex.Length == 8)
        {
            return Color.FromArgb(
                Convert.ToByte(hex.Substring(0, 2), 16),
                Convert.ToByte(hex.Substring(2, 2), 16),
                Convert.ToByte(hex.Substring(4, 2), 16),
                Convert.ToByte(hex.Substring(6, 2), 16));
        }

        return Color.FromArgb(255, 102, 102, 102); // Default gray
    }

    private void ActionButton_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        if (sender is Button button && button.Content is FontIcon icon)
        {
            icon.Foreground = new SolidColorBrush(Color.FromArgb(255, 153, 153, 153)); // #999999
        }
    }

    private void ActionButton_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        if (sender is Button button && button.Content is FontIcon icon)
        {
            icon.Foreground = new SolidColorBrush(Color.FromArgb(255, 102, 102, 102)); // #666666
        }
    }

    private void EditButton_Click(object sender, RoutedEventArgs e)
    {
        if (Category != null)
        {
            EditClicked?.Invoke(this, Category);
        }
    }

    private void DeleteButton_Click(object sender, RoutedEventArgs e)
    {
        if (Category != null)
        {
            DeleteClicked?.Invoke(this, Category);
        }
    }
}
