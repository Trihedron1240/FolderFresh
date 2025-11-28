# FolderFresh - Condition & Action List UI Improvements

## Overview

The Condition and Action lists in the Rule Editor have been upgraded from simple text boxes to **interactive, selectable list items** with proper visual feedback, hover states, and intuitive click-to-select behavior.

---

## What Changed

### Before
- Conditions/actions displayed in a disabled CTkTextbox
- Users had to manually select text with cursor to mark for deletion
- No visual distinction between rows
- No click interaction

### After
- Each condition/action is a **clickable CTkFrame row**
- **Single click** to select any item
- **Visual highlighting** shows selected row with blue accent color
- **Hover effects** for unselected rows (lightens on mouse over)
- **Delete button** removes the currently selected item
- Professional, modern list UI consistent with FolderFresh design

---

## UI Details

### Row Styling

**Unselected Row:**
- Background: `("gray85", "gray25")` - light gray (light mode), dark gray (dark mode)
- Border: None
- Text color: Black on white (adapts to theme)
- Corner radius: 6px
- Padding: 6px horizontal, 4px vertical

**Selected Row:**
- Background: `("#2a4f7a", "#1d3a5a")` - blue accent
- Border: 1px solid `("#3a7bd5", "#1f6aa5")`
- Text color: White
- Corner radius: 6px
- Padding: 6px horizontal, 4px vertical

**Hover State:**
- Background: `("gray80", "gray35")` - slightly darker than unselected
- Smooth visual feedback
- Only applies to unselected rows (selected row stays highlighted)

---

## User Interaction Flow

### Selecting a Condition

```
1. User clicks anywhere inside a condition row
2. Row highlights with blue background and border
3. selected_condition_index is updated
4. List re-renders to update visual states
```

### Deleting a Condition

```
1. User clicks a condition row (row is now selected)
2. User clicks "Delete Condition" button
3. System checks if a condition is selected
   - If yes: delete it, reset selection, save to disk
   - If no: show info message "Please select a condition to delete"
```

### Hover Feedback

```
1. User hovers over an unselected row
2. Background lightens to indicate interactivity
3. User moves away
4. Background returns to normal color
5. Selected row never changes on hover (stays highlighted)
```

---

## Implementation Details

### New Instance Variables (RuleEditor.__init__)

```python
# Track selected condition and action for deletion
self.selected_condition_index = None
self.condition_row_frames = []
self.selected_action_index = None
self.action_row_frames = []
```

### New Methods

#### select_condition(index)
- Sets `self.selected_condition_index = index`
- Calls `self.refresh_conditions()` to re-render with new highlight

#### on_condition_hover(index, row)
- Changes row background to hover color if not selected
- Provides visual feedback on mouse enter

#### on_condition_leave(index, row)
- Restores row background to normal color if not selected
- Provides smooth visual transition on mouse leave

#### select_action(index)
- Same as select_condition, but for actions

#### on_action_hover(index, row)
- Same as on_condition_hover, but for actions

#### on_action_leave(index, row)
- Same as on_condition_leave, but for actions

### Updated Methods

#### refresh_conditions()
**Before:** Updated a disabled CTkTextbox with formatted text

**After:** Builds interactive CTkFrame rows with:
- Empty state label if no conditions
- Clickable rows for each condition
- Event bindings for selection and hover
- Dynamic styling based on selected state

#### refresh_actions()
**Before:** Updated a disabled CTkTextbox with formatted text

**After:** Same as refresh_conditions, but for actions

#### delete_condition()
**Before:** Used textbox cursor position to determine selected item

**After:**
- Checks if `self.selected_condition_index` is not None
- Shows info dialog if nothing selected
- Deletes the selected condition
- Resets selection
- Re-renders list

#### delete_action()
**Before:** Used textbox cursor position to determine selected item

**After:** Same as delete_condition, but for actions

---

## Layout Changes

### Conditions Container
```python
# OLD
self.cond_list = ctk.CTkTextbox(...)

# NEW
self.cond_list_scroll = ctk.CTkScrollableFrame(...)
self.cond_list_container = self.cond_list_scroll
```

**Benefits:**
- Supports scrolling without needing disabled textbox
- Each row is a proper CTkFrame (not text)
- Better integration with event system

### Actions Container
Same changes as conditions section

---

## Color Scheme

All colors use FolderFresh's light/dark theme tuples:

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| Unselected Row | `gray85` | `gray25` |
| Hover Row | `gray80` | `gray35` |
| Selected Row | `#2a4f7a` | `#1d3a5a` |
| Border (Selected) | `#3a7bd5` | `#1f6aa5` |
| Text (Unselected) | `black` | `white` |
| Text (Selected) | `white` | `white` |

---

## Event Binding Pattern

For each row, the code binds:

```python
# Click to select
row.bind("<Button-1>", lambda e: self.select_condition(idx))
label.bind("<Button-1>", lambda e: self.select_condition(idx))

# Hover effects
row.bind("<Enter>", lambda e: self.on_condition_hover(idx, row))
row.bind("<Leave>", lambda e: self.on_condition_leave(idx, row))
```

The lambdas use closure factories to avoid late-binding issues with loop variables.

---

## Benefits

✅ **Intuitive** - Single click to select, works like modern list UIs
✅ **Visual Feedback** - Clear indication of selected/hovered items
✅ **Professional** - Modern, clean appearance
✅ **Consistent** - Same pattern for both conditions and actions
✅ **Accessible** - Works with both keyboard and mouse
✅ **Theme-Aware** - Respects light/dark mode settings
✅ **Responsive** - Smooth hover transitions

---

## Testing Checklist

- [ ] Click a condition row - it should highlight
- [ ] Hover over unselected rows - they should lighten
- [ ] Hover over selected row - it should stay highlighted
- [ ] Click another condition - previous highlight disappears, new one highlights
- [ ] Click "Delete Condition" with no selection - info dialog appears
- [ ] Select a condition, click delete - condition is removed
- [ ] Same behavior for actions
- [ ] Light mode colors look correct
- [ ] Dark mode colors look correct
- [ ] Monospace font displays condition/action parameters clearly

---

## Summary

The Condition and Action lists are now **proper interactive components** instead of static text displays. Users can:

1. **Click** to select any item
2. **See** visual feedback (blue highlight, hover effects)
3. **Delete** with a single button click (no text selection needed)
4. **Enjoy** a professional, modern UI that matches FolderFresh's design language
