using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Collections.Specialized;
using System.Linq;
using FolderFreshLite.Helpers;
using FolderFreshLite.Models;
using Microsoft.UI;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;

namespace FolderFreshLite.Components;

public enum SortColumn
{
    Name,
    DateModified,
    Type,
    Size
}

public sealed partial class FileExplorerPanel : UserControl
{
    private DateTime _lastClickTime = DateTime.MinValue;
    private FileItem? _lastClickedItem;
    private const int DoubleClickThresholdMs = 500;

    private SortColumn _currentSortColumn = SortColumn.Name;
    private bool _sortAscending = true;
    private ObservableCollection<FileItem>? _sourceCollection;
    private readonly ObservableCollection<FileItem> _sortedItems = new();

    public FileExplorerPanel()
    {
        this.InitializeComponent();
        this.Loaded += FileExplorerPanel_Loaded;
        FileListView.ItemsSource = _sortedItems;
    }

    private void FileExplorerPanel_Loaded(object sender, RoutedEventArgs e)
    {
        UpdateEmptyState();
        UpdateSortIndicators();
    }

    #region Dependency Properties

    public static readonly DependencyProperty ItemsSourceProperty =
        DependencyProperty.Register(
            nameof(ItemsSource),
            typeof(ObservableCollection<FileItem>),
            typeof(FileExplorerPanel),
            new PropertyMetadata(null, OnItemsSourceChanged));

    public ObservableCollection<FileItem>? ItemsSource
    {
        get => (ObservableCollection<FileItem>?)GetValue(ItemsSourceProperty);
        set => SetValue(ItemsSourceProperty, value);
    }

    private static void OnItemsSourceChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is FileExplorerPanel panel)
        {
            // Unsubscribe from old collection
            if (e.OldValue is INotifyCollectionChanged oldCollection)
            {
                oldCollection.CollectionChanged -= panel.OnCollectionChanged;
            }

            panel._sourceCollection = e.NewValue as ObservableCollection<FileItem>;

            // Subscribe to new collection
            if (e.NewValue is INotifyCollectionChanged newCollection)
            {
                newCollection.CollectionChanged += panel.OnCollectionChanged;
            }

            panel.ApplySorting();
            panel.UpdateEmptyState();
        }
    }

    private void OnCollectionChanged(object? sender, NotifyCollectionChangedEventArgs e)
    {
        ApplySorting();
        UpdateEmptyState();
    }

    public static readonly DependencyProperty SelectedItemsProperty =
        DependencyProperty.Register(
            nameof(SelectedItems),
            typeof(ObservableCollection<FileItem>),
            typeof(FileExplorerPanel),
            new PropertyMetadata(new ObservableCollection<FileItem>()));

    public ObservableCollection<FileItem> SelectedItems
    {
        get => (ObservableCollection<FileItem>)GetValue(SelectedItemsProperty);
        set => SetValue(SelectedItemsProperty, value);
    }

    public static readonly DependencyProperty EmptyStateTextProperty =
        DependencyProperty.Register(
            nameof(EmptyStateText),
            typeof(string),
            typeof(FileExplorerPanel),
            new PropertyMetadata("No files to display", OnEmptyStateTextChanged));

    public string EmptyStateText
    {
        get => (string)GetValue(EmptyStateTextProperty);
        set => SetValue(EmptyStateTextProperty, value);
    }

    private static void OnEmptyStateTextChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is FileExplorerPanel panel && panel.EmptyStateTextBlock != null)
        {
            panel.EmptyStateTextBlock.Text = (string)e.NewValue;
        }
    }

    #endregion

    #region Events

    public event EventHandler<FileItem>? FolderOpened;
    public event EventHandler<FileItem>? FileOpened;
    public event EventHandler<IList<FileItem>>? SelectionChanged;

    #endregion

    #region Sorting

    private void ColumnHeader_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.Tag is string columnTag)
        {
            var column = columnTag switch
            {
                "Name" => SortColumn.Name,
                "DateModified" => SortColumn.DateModified,
                "Type" => SortColumn.Type,
                "Size" => SortColumn.Size,
                _ => SortColumn.Name
            };

            if (_currentSortColumn == column)
            {
                _sortAscending = !_sortAscending;
            }
            else
            {
                _currentSortColumn = column;
                _sortAscending = true;
            }

            UpdateSortIndicators();
            ApplySorting();
        }
    }

    private void UpdateSortIndicators()
    {
        // Hide all sort icons
        NameSortIcon.Visibility = Visibility.Collapsed;
        DateSortIcon.Visibility = Visibility.Collapsed;
        TypeSortIcon.Visibility = Visibility.Collapsed;
        SizeSortIcon.Visibility = Visibility.Collapsed;

        // Show and update the active sort icon
        FontIcon activeIcon = _currentSortColumn switch
        {
            SortColumn.Name => NameSortIcon,
            SortColumn.DateModified => DateSortIcon,
            SortColumn.Type => TypeSortIcon,
            SortColumn.Size => SizeSortIcon,
            _ => NameSortIcon
        };

        activeIcon.Visibility = Visibility.Visible;
        activeIcon.Glyph = _sortAscending ? "\uE70D" : "\uE70E"; // Down arrow / Up arrow
    }

    private void ApplySorting()
    {
        if (_sourceCollection == null)
        {
            _sortedItems.Clear();
            return;
        }

        // Get folders and files separately
        var folders = _sourceCollection.Where(f => f.IsFolder);
        var files = _sourceCollection.Where(f => !f.IsFolder);

        // Sort folders
        var sortedFolders = SortItems(folders);
        // Sort files
        var sortedFiles = SortItems(files);

        // Combine: folders first, then files
        _sortedItems.Clear();
        foreach (var folder in sortedFolders)
        {
            _sortedItems.Add(folder);
        }
        foreach (var file in sortedFiles)
        {
            _sortedItems.Add(file);
        }
    }

    private IEnumerable<FileItem> SortItems(IEnumerable<FileItem> items)
    {
        return _currentSortColumn switch
        {
            SortColumn.Name => _sortAscending
                ? items.OrderBy(f => f.Name, StringComparer.OrdinalIgnoreCase)
                : items.OrderByDescending(f => f.Name, StringComparer.OrdinalIgnoreCase),

            SortColumn.DateModified => _sortAscending
                ? items.OrderBy(f => f.DateModified)
                : items.OrderByDescending(f => f.DateModified),

            SortColumn.Type => _sortAscending
                ? items.OrderBy(f => f.FileTypeDisplay, StringComparer.OrdinalIgnoreCase)
                : items.OrderByDescending(f => f.FileTypeDisplay, StringComparer.OrdinalIgnoreCase),

            SortColumn.Size => _sortAscending
                ? items.OrderBy(f => f.Size)
                : items.OrderByDescending(f => f.Size),

            _ => items.OrderBy(f => f.Name, StringComparer.OrdinalIgnoreCase)
        };
    }

    #endregion

    #region Event Handlers

    private void FileListView_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        SelectedItems.Clear();
        foreach (var item in FileListView.SelectedItems.OfType<FileItem>())
        {
            item.IsSelected = true;
            SelectedItems.Add(item);
        }

        // Deselect removed items
        foreach (var item in e.RemovedItems.OfType<FileItem>())
        {
            item.IsSelected = false;
        }

        SelectionChanged?.Invoke(this, SelectedItems.ToList());
    }

    private void FileListView_ItemClick(object sender, ItemClickEventArgs e)
    {
        if (e.ClickedItem is not FileItem item) return;

        var now = DateTime.Now;
        var timeSinceLastClick = (now - _lastClickTime).TotalMilliseconds;

        if (_lastClickedItem == item && timeSinceLastClick < DoubleClickThresholdMs)
        {
            HandleDoubleClick(item);
            _lastClickedItem = null;
            _lastClickTime = DateTime.MinValue;
        }
        else
        {
            _lastClickedItem = item;
            _lastClickTime = now;
        }
    }

    private void FileListView_DoubleTapped(object sender, DoubleTappedRoutedEventArgs e)
    {
        if (e.OriginalSource is FrameworkElement element &&
            element.DataContext is FileItem item)
        {
            HandleDoubleClick(item);
        }
    }

    private void HandleDoubleClick(FileItem item)
    {
        if (item.IsFolder)
        {
            FolderOpened?.Invoke(this, item);
        }
        else
        {
            FileOpened?.Invoke(this, item);
        }
    }

    private void Row_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        if (sender is Grid grid)
        {
            grid.Background = new SolidColorBrush(Windows.UI.Color.FromArgb(60, 255, 255, 255));
        }
    }

    private void Row_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        if (sender is Grid grid)
        {
            grid.Background = new SolidColorBrush(Colors.Transparent);
        }
    }

    #endregion

    #region Helper Methods

    private void UpdateEmptyState()
    {
        var hasItems = _sortedItems.Count > 0;
        EmptyState.Visibility = hasItems ? Visibility.Collapsed : Visibility.Visible;
        DetailsViewContainer.Visibility = hasItems ? Visibility.Visible : Visibility.Collapsed;
    }

    public void SelectAll()
    {
        FileListView.SelectAll();
    }

    public void ClearSelection()
    {
        FileListView.SelectedItems.Clear();
    }

    public void SelectItem(FileItem item)
    {
        if (!FileListView.SelectedItems.Contains(item))
        {
            FileListView.SelectedItems.Add(item);
        }
    }

    public void DeselectItem(FileItem item)
    {
        FileListView.SelectedItems.Remove(item);
    }

    public void RefreshSort()
    {
        ApplySorting();
    }

    #endregion
}
