# ToolTip Event Filter Fix - PySide6

## Problem

When using `ToolTip.attach_to()` with PySide6, the following error occurred:

```
TypeError: 'PySide6.QtCore.QObject.installEventFilter' called with wrong argument types:
PySide6.QtCore.QObject.installEventFilter(TooltipEventFilter)
Supported signatures:
PySide6.QtCore.QObject.installEventFilter(filterObj: PySide6.QtCore.QObject, /)
```

### Root Cause

The `TooltipEventFilter` class was implemented as a plain Python class without inheriting from `QObject`. In PySide6, event filters **must inherit from `QObject`** to be compatible with the `installEventFilter()` method.

```python
# WRONG - plain class, not a QObject
class TooltipEventFilter:
    def __init__(self, tooltip_obj):
        self.tooltip = tooltip_obj

    def eventFilter(self, obj, event):
        # ... event handling ...
        return False
```

## Solution

The `TooltipEventFilter` class now properly inherits from `QObject`:

```python
# CORRECT - inherits from QObject
class TooltipEventFilter(QObject):
    """Event filter for detecting mouse enter/leave events on widgets."""

    def __init__(self, tooltip_obj):
        super().__init__()
        self.tooltip = tooltip_obj

    def eventFilter(self, obj, event):
        """Handle mouse enter/leave events."""
        if event.type() == QEvent.Enter:
            self.tooltip.show_tooltip(event)
        elif event.type() == QEvent.Leave:
            self.tooltip.hide_tooltip()
        return False
```

## Changes Made

**File: `src/folderfresh/ui_qt/tooltip.py`**

### 1. Import Addition
Added required PySide6 imports:
```python
from PySide6.QtCore import Qt, QTimer, QPoint, QObject, QEvent
```

### 2. Event Filter Class Update
Changed `TooltipEventFilter` to inherit from `QObject`:
- Added `class TooltipEventFilter(QObject):`
- Added `super().__init__()` in `__init__` method
- Added comprehensive docstrings
- Removed redundant import of `QEvent` from within the method

## How It Works

1. **Event Filter Inheritance**: By inheriting from `QObject`, `TooltipEventFilter` becomes a valid PySide6 event filter
2. **Event Handling**: The `eventFilter()` method is called automatically when events occur on the target widget
3. **Mouse Events**:
   - `QEvent.Enter`: Triggered when mouse enters widget → shows tooltip
   - `QEvent.Leave`: Triggered when mouse leaves widget → hides tooltip
4. **Prevention of Garbage Collection**: The event filter is stored as `widget._tooltip_filter` to keep it alive

## API Signature

```python
@staticmethod
def attach_to(widget: QWidget, text: str) -> "ToolTip":
    """
    Attach tooltip to a widget with automatic show/hide on hover.

    Args:
        widget: Widget to attach tooltip to
        text: Tooltip text

    Returns:
        The created ToolTip instance
    """
```

## Usage Example

```python
from folderfresh.ui_qt.tooltip import ToolTip
from PySide6.QtWidgets import QPushButton

button = QPushButton("My Button")

# Attach tooltip - now works correctly with PySide6!
ToolTip.attach_to(
    button,
    "This button performs an action"
)
```

## Verification

✅ All tests pass
✅ Event filter properly recognized by PySide6
✅ `installEventFilter()` accepts the filter without errors
✅ Mouse enter/leave events detected correctly
✅ Tooltip shows/hides on hover as expected
✅ All other ui_qt components still import successfully

## Technical Details

### PySide6 vs PyQt5 Differences

PySide6 is stricter about type checking for event filters:

| Feature | PyQt5 | PySide6 |
|---------|-------|---------|
| Event Filter Type | Can be any Python class | **Must inherit from QObject** |
| Import | `from PyQt5.QtCore import pyqtSignal` | `from PySide6.QtCore import Signal` |
| Decorator | `@pyqtSlot` | `@Slot` |
| Event Constant | Both use `QEvent` | Both use `QEvent` |

### Why `QObject` is Required

- PySide6 validates that event filters are instances of `QObject`
- This allows proper memory management and signal/slot integration
- Ensures compatibility with Qt's meta-object system

## Files Modified

- `src/folderfresh/ui_qt/tooltip.py` (Lines 7, 96-126)

## Backward Compatibility

✅ Fully backward compatible with existing code
✅ API signature unchanged
✅ Behavior unchanged
✅ Only internal implementation improved

## Conclusion

The ToolTip event filter now works correctly with PySide6 by properly inheriting from `QObject`. This fix ensures that tooltips display correctly when hovering over widgets in the FolderFresh UI.
