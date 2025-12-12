using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using System;
using System.Collections.Generic;
using FolderFreshLite.Models;

namespace FolderFreshLite.Components;

public sealed partial class ConditionRow : UserControl
{
    private Condition? _condition;
    private bool _isUpdating;

    public event EventHandler<Condition>? ConditionChanged;
    public event EventHandler<Condition>? DeleteRequested;

    // Operator options for each attribute type
    private static readonly Dictionary<ConditionAttribute, List<(ConditionOperator Op, string Display)>> OperatorsByAttribute = new()
    {
        {
            ConditionAttribute.Name, new()
            {
                (ConditionOperator.Is, "is"),
                (ConditionOperator.IsNot, "is not"),
                (ConditionOperator.Contains, "contains"),
                (ConditionOperator.DoesNotContain, "does not contain"),
                (ConditionOperator.StartsWith, "starts with"),
                (ConditionOperator.EndsWith, "ends with"),
                (ConditionOperator.MatchesPattern, "matches pattern")
            }
        },
        {
            ConditionAttribute.Extension, new()
            {
                (ConditionOperator.Is, "is"),
                (ConditionOperator.IsNot, "is not"),
                (ConditionOperator.Contains, "contains"),
                (ConditionOperator.StartsWith, "starts with"),
                (ConditionOperator.EndsWith, "ends with")
            }
        },
        {
            ConditionAttribute.FullName, new()
            {
                (ConditionOperator.Is, "is"),
                (ConditionOperator.IsNot, "is not"),
                (ConditionOperator.Contains, "contains"),
                (ConditionOperator.DoesNotContain, "does not contain"),
                (ConditionOperator.StartsWith, "starts with"),
                (ConditionOperator.EndsWith, "ends with"),
                (ConditionOperator.MatchesPattern, "matches pattern")
            }
        },
        {
            ConditionAttribute.Kind, new()
            {
                (ConditionOperator.Is, "is"),
                (ConditionOperator.IsNot, "is not")
            }
        },
        {
            ConditionAttribute.Size, new()
            {
                (ConditionOperator.IsGreaterThan, "is greater than"),
                (ConditionOperator.IsLessThan, "is less than")
            }
        },
        {
            ConditionAttribute.DateCreated, new()
            {
                (ConditionOperator.Is, "is"),
                (ConditionOperator.IsBefore, "is before"),
                (ConditionOperator.IsAfter, "is after"),
                (ConditionOperator.IsInTheLast, "is in the last")
            }
        },
        {
            ConditionAttribute.DateModified, new()
            {
                (ConditionOperator.Is, "is"),
                (ConditionOperator.IsBefore, "is before"),
                (ConditionOperator.IsAfter, "is after"),
                (ConditionOperator.IsInTheLast, "is in the last")
            }
        },
        {
            ConditionAttribute.DateAccessed, new()
            {
                (ConditionOperator.Is, "is"),
                (ConditionOperator.IsBefore, "is before"),
                (ConditionOperator.IsAfter, "is after"),
                (ConditionOperator.IsInTheLast, "is in the last")
            }
        }
    };

    public ConditionRow()
    {
        this.InitializeComponent();

        // Set default selection
        AttributeComboBox.SelectedIndex = 0;
    }

    public Condition? Condition
    {
        get => _condition;
        set
        {
            _condition = value;
            LoadCondition();
        }
    }

    private void LoadCondition()
    {
        if (_condition == null) return;

        _isUpdating = true;
        try
        {
            // Set attribute
            for (int i = 0; i < AttributeComboBox.Items.Count; i++)
            {
                if (AttributeComboBox.Items[i] is ComboBoxItem item &&
                    item.Tag?.ToString() == _condition.Attribute.ToString())
                {
                    AttributeComboBox.SelectedIndex = i;
                    break;
                }
            }

            // Operators will be populated by attribute change handler
            // Then set operator
            UpdateOperators();

            for (int i = 0; i < OperatorComboBox.Items.Count; i++)
            {
                if (OperatorComboBox.Items[i] is ComboBoxItem item &&
                    item.Tag is ConditionOperator op && op == _condition.Operator)
                {
                    OperatorComboBox.SelectedIndex = i;
                    break;
                }
            }

            // Set value based on attribute type
            UpdateValueInput();
            SetValueFromCondition();
        }
        finally
        {
            _isUpdating = false;
        }
    }

    private void SetValueFromCondition()
    {
        if (_condition == null) return;

        switch (_condition.Attribute)
        {
            case ConditionAttribute.Name:
            case ConditionAttribute.Extension:
            case ConditionAttribute.FullName:
                TextValueInput.Text = _condition.Value;
                break;

            case ConditionAttribute.Kind:
                for (int i = 0; i < KindValueComboBox.Items.Count; i++)
                {
                    if (KindValueComboBox.Items[i] is ComboBoxItem item &&
                        item.Tag?.ToString() == _condition.Value)
                    {
                        KindValueComboBox.SelectedIndex = i;
                        break;
                    }
                }
                break;

            case ConditionAttribute.Size:
                // Parse size value and unit
                ParseSizeValue(_condition.Value);
                break;

            case ConditionAttribute.DateCreated:
            case ConditionAttribute.DateModified:
            case ConditionAttribute.DateAccessed:
                if (_condition.Operator == ConditionOperator.IsInTheLast)
                {
                    RelativeDateValueInput.Text = _condition.Value;
                    for (int i = 0; i < RelativeDateUnitComboBox.Items.Count; i++)
                    {
                        if (RelativeDateUnitComboBox.Items[i] is ComboBoxItem item &&
                            item.Tag?.ToString() == _condition.SecondaryValue)
                        {
                            RelativeDateUnitComboBox.SelectedIndex = i;
                            break;
                        }
                    }
                }
                else if (DateTime.TryParse(_condition.Value, out var date))
                {
                    DateValuePicker.Date = date;
                }
                break;
        }
    }

    private void ParseSizeValue(string value)
    {
        if (string.IsNullOrEmpty(value))
        {
            SizeValueInput.Text = "";
            return;
        }

        // Try to parse "100MB" format
        var match = System.Text.RegularExpressions.Regex.Match(value, @"^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB)?$",
            System.Text.RegularExpressions.RegexOptions.IgnoreCase);

        if (match.Success)
        {
            SizeValueInput.Text = match.Groups[1].Value;
            var unit = match.Groups[2].Value.ToUpperInvariant();
            for (int i = 0; i < SizeUnitComboBox.Items.Count; i++)
            {
                if (SizeUnitComboBox.Items[i] is ComboBoxItem item &&
                    item.Tag?.ToString() == unit)
                {
                    SizeUnitComboBox.SelectedIndex = i;
                    break;
                }
            }
        }
        else
        {
            SizeValueInput.Text = value;
        }
    }

    private void AttributeComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (AttributeComboBox.SelectedItem is ComboBoxItem item && item.Tag is string tagStr)
        {
            if (Enum.TryParse<ConditionAttribute>(tagStr, out var attribute))
            {
                if (_condition != null && !_isUpdating)
                {
                    _condition.Attribute = attribute;
                    _condition.Value = "";
                    _condition.SecondaryValue = null;
                }

                UpdateOperators();
                UpdateValueInput();

                if (!_isUpdating)
                {
                    NotifyConditionChanged();
                }
            }
        }
    }

    private void UpdateOperators()
    {
        if (AttributeComboBox.SelectedItem is not ComboBoxItem item || item.Tag is not string tagStr)
            return;

        if (!Enum.TryParse<ConditionAttribute>(tagStr, out var attribute))
            return;

        OperatorComboBox.Items.Clear();

        if (OperatorsByAttribute.TryGetValue(attribute, out var operators))
        {
            foreach (var (op, display) in operators)
            {
                OperatorComboBox.Items.Add(new ComboBoxItem
                {
                    Content = display,
                    Tag = op
                });
            }
        }

        if (OperatorComboBox.Items.Count > 0)
        {
            OperatorComboBox.SelectedIndex = 0;
        }
    }

    private void OperatorComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (OperatorComboBox.SelectedItem is ComboBoxItem item && item.Tag is ConditionOperator op)
        {
            if (_condition != null && !_isUpdating)
            {
                _condition.Operator = op;
            }

            UpdateValueInput();

            if (!_isUpdating)
            {
                NotifyConditionChanged();
            }
        }
    }

    private void UpdateValueInput()
    {
        // Hide all value inputs first
        TextValueInput.Visibility = Visibility.Collapsed;
        KindValueComboBox.Visibility = Visibility.Collapsed;
        SizeValueGrid.Visibility = Visibility.Collapsed;
        DateValuePicker.Visibility = Visibility.Collapsed;
        RelativeDateGrid.Visibility = Visibility.Collapsed;

        if (AttributeComboBox.SelectedItem is not ComboBoxItem attrItem || attrItem.Tag is not string tagStr)
            return;

        if (!Enum.TryParse<ConditionAttribute>(tagStr, out var attribute))
            return;

        var selectedOperator = ConditionOperator.Is;
        if (OperatorComboBox.SelectedItem is ComboBoxItem opItem && opItem.Tag is ConditionOperator op)
        {
            selectedOperator = op;
        }

        switch (attribute)
        {
            case ConditionAttribute.Name:
            case ConditionAttribute.Extension:
            case ConditionAttribute.FullName:
                TextValueInput.Visibility = Visibility.Visible;
                TextValueInput.PlaceholderText = attribute == ConditionAttribute.Extension
                    ? ".pdf, .docx"
                    : "Enter value...";
                break;

            case ConditionAttribute.Kind:
                KindValueComboBox.Visibility = Visibility.Visible;
                if (KindValueComboBox.SelectedIndex < 0)
                    KindValueComboBox.SelectedIndex = 0;
                break;

            case ConditionAttribute.Size:
                SizeValueGrid.Visibility = Visibility.Visible;
                break;

            case ConditionAttribute.DateCreated:
            case ConditionAttribute.DateModified:
            case ConditionAttribute.DateAccessed:
                if (selectedOperator == ConditionOperator.IsInTheLast)
                {
                    RelativeDateGrid.Visibility = Visibility.Visible;
                }
                else
                {
                    DateValuePicker.Visibility = Visibility.Visible;
                }
                break;
        }
    }

    private void TextValueInput_TextChanged(object sender, TextChangedEventArgs e)
    {
        if (_condition != null && !_isUpdating)
        {
            _condition.Value = TextValueInput.Text;
            NotifyConditionChanged();
        }
    }

    private void KindValueComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_condition != null && !_isUpdating &&
            KindValueComboBox.SelectedItem is ComboBoxItem item)
        {
            _condition.Value = item.Tag?.ToString() ?? "";
            NotifyConditionChanged();
        }
    }

    private void SizeValueInput_TextChanged(object sender, TextChangedEventArgs e)
    {
        UpdateSizeValue();
    }

    private void SizeUnitComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        UpdateSizeValue();
    }

    private void UpdateSizeValue()
    {
        if (_condition != null && !_isUpdating)
        {
            var number = SizeValueInput.Text;
            var unit = (SizeUnitComboBox.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "MB";
            _condition.Value = $"{number}{unit}";
            NotifyConditionChanged();
        }
    }

    private void DateValuePicker_DateChanged(CalendarDatePicker sender, CalendarDatePickerDateChangedEventArgs args)
    {
        if (_condition != null && !_isUpdating && args.NewDate.HasValue)
        {
            _condition.Value = args.NewDate.Value.DateTime.ToString("yyyy-MM-dd");
            NotifyConditionChanged();
        }
    }

    private void RelativeDateValueInput_TextChanged(object sender, TextChangedEventArgs e)
    {
        UpdateRelativeDateValue();
    }

    private void RelativeDateUnitComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        UpdateRelativeDateValue();
    }

    private void UpdateRelativeDateValue()
    {
        if (_condition != null && !_isUpdating)
        {
            _condition.Value = RelativeDateValueInput.Text;
            _condition.SecondaryValue = (RelativeDateUnitComboBox.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "days";
            NotifyConditionChanged();
        }
    }

    private void NotifyConditionChanged()
    {
        if (_condition != null)
        {
            ConditionChanged?.Invoke(this, _condition);
        }
    }

    private void DeleteButton_Click(object sender, RoutedEventArgs e)
    {
        if (_condition != null)
        {
            DeleteRequested?.Invoke(this, _condition);
        }
    }

    private void UserControl_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        DeleteButton.Opacity = 1;
    }

    private void UserControl_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        DeleteButton.Opacity = 0;
    }

    private void DeleteButton_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        DeleteIcon.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 239, 68, 68));
    }

    private void DeleteButton_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        DeleteIcon.Foreground = new SolidColorBrush(Microsoft.UI.ColorHelper.FromArgb(255, 102, 102, 102));
    }

    /// <summary>
    /// Creates a new default condition
    /// </summary>
    public static Condition CreateDefaultCondition()
    {
        return new Condition
        {
            Attribute = ConditionAttribute.Extension,
            Operator = ConditionOperator.Is,
            Value = ".pdf"
        };
    }
}
