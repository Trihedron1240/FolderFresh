# PySide6 Migration Plan for FolderFresh

## Executive Summary

This document outlines a **window-by-window migration strategy** from CustomTkinter to PySide6 (Qt for Python). The migration will be **incremental and non-destructive**, maintaining parallel implementations until migration is complete.

**Total Windows to Migrate:** 14 major UI components
**Strategy:** Migrate one window at a time, smallest-to-largest
**Parallel Approach:** Keep CustomTkinter code intact; build PySide6 replacements in `ui_qt/` directory
**Integration:** Switch windows only when PySide6 version is fully functional and tested

---

## Phase 1: Foundation & Infrastructure (Completed ✓)

### ✓ Done:
- [x] Created `ui_qt/` package structure
- [x] Implemented minimal `MainWindow` skeleton with QMainWindow
- [x] Created `SidebarWidget` with navigation buttons (Rules, Preview, Settings, Activity Log)
- [x] Integrated sidebar into main window with QSplitter for resizable layout
- [x] Established color scheme matching CustomTkinter theme

### Remaining Infrastructure Tasks:
- [ ] Create shared styling module (`ui_qt/styles.py`) for consistent theming
- [ ] Create color constants matching CustomTkinter palette
- [ ] Implement common dialog utilities (file dialogs, message boxes)
- [ ] Create base widget classes for reusable components

---

## Phase 2: Utility & Infrastructure Components

### Step 2.1: Shared Styling Module
**File:** `ui_qt/styles.py`

**Components:**
- Color palette constants (ACCENT, SUCCESS, PANEL_BG, CARD_BG, BORDER, TEXT, MUTED)
- Stylesheet factory functions
- Font definitions
- Common widget styling (buttons, entries, labels, etc.)
- Hover/active/pressed state management

**Dependencies:** None

**Testing:** Visual verification only (no logic to test)

**Estimated Complexity:** Low (copy colors from CustomTkinter gui.py)

---

### Step 2.2: Common Dialog Utilities
**File:** `ui_qt/dialogs.py`

**Components:**
- `show_confirmation_dialog(parent, title, message)` → bool
- `show_info_dialog(parent, title, message)` → None
- `show_error_dialog(parent, title, message)` → None
- `ask_save_changes_dialog(parent)` → bool | None
- `browse_folder_dialog(parent, title="Select Folder")` → Path | None
- `browse_file_dialog(parent, title="Select File")` → Path | None
- File/folder dialogs using QFileDialog

**Dependencies:** styles.py, config (for recent folders)

**Testing:** Manual testing of each dialog type

**Estimated Complexity:** Low (straightforward dialog wrappers)

---

### Step 2.3: Base Widget Classes
**File:** `ui_qt/base_widgets.py`

**Components:**
- `StyledButton(QWidget)` - Applies consistent button styling
- `StyledLabel(QLabel)` - Applies consistent label styling
- `StyledLineEdit(QLineEdit)` - Styled text input with placeholder
- `StyledTextEdit(QPlainTextEdit)` - Styled multiline text
- `StyledComboBox(QComboBox)` - Styled dropdown
- `StyledCheckBox(QCheckBox)` - Styled checkbox
- `ScrollableFrame(QScrollArea)` - Scrollable container with automatic sizing
- `CardFrame(QFrame)` - Card-style container (matching CustomTkinter cards)

**Dependencies:** styles.py

**Testing:** Visual verification

**Estimated Complexity:** Low (mostly styling wrappers)

---

## Phase 3: Main Window Components (Sequential Order)

### Step 3.1: Tooltip Widget
**File:** `ui_qt/tooltip.py`

**Replace:** `Tooltip` class from gui.py (lines 34-69)

**Components:**
- `ToolTip` class extending QWidget (floating label on hover)
- Show/hide on mouse enter/leave events
- Positioning logic (follows mouse)

**Dependencies:** styles.py, base_widgets.py

**Testing:**
- Hover over widget shows tooltip
- Tooltip disappears on mouse leave
- Tooltip position is reasonable

**Estimated Complexity:** Low

**Note:** This is used throughout the app for help text on checkboxes.

---

### Step 3.2: Status Bar Component
**File:** `ui_qt/status_bar.py`

**Replace:** Status bar in FolderFreshApp (lines 511-525)

**Components:**
- `StatusBar(QWidget)` class
- Progress bar (`QProgressBar`, 0-1 range)
- Progress label (e.g., "0/50")
- Status label ("Ready", "Running", etc.)
- Methods:
  - `set_status(text)` - Updates status label
  - `set_progress(value)` - Updates progress bar (0-1)
  - `set_progress_label(text)` - Updates progress text
  - `reset()` - Resets to initial state

**Dependencies:** styles.py, base_widgets.py

**Testing:**
- Status updates display correctly
- Progress bar animation works
- Progress label updates synchronously

**Estimated Complexity:** Low (no logic, pure UI state display)

---

### Step 3.3: Main Window (Complete Rewrite)
**File:** `ui_qt/main_window.py` (already started, needs completion)

**Replace:** `FolderFreshApp` from gui.py (lines 72-1358)

**Sections to Implement:**

1. **Header Section**
   - Title label ("FolderFresh")
   - Path entry (disabled, shows selected folder)
   - "Open Folder" button
   - "Choose Folder" button
   - Commands: `open_folder()`, `choose_folder()`

2. **Basic Options**
   - "Include subfolders" checkbox
   - "Ignore hidden/system files" checkbox
   - "Safe Mode (copy)" checkbox
   - "Smart Sorting" checkbox (with tooltip)
   - "Auto-tidy" checkbox
   - Signal: `options_changed` (emitted on any checkbox change)

3. **Action Buttons**
   - "Preview" button (blue, disabled until folder selected)
   - "Organise Files" button (green, disabled until folder selected)
   - "Undo Last" button (gray, may be disabled)
   - "Find Duplicates" button (light blue, disabled until folder selected)
   - "Clean Desktop" button (teal)
   - Signals: `preview_clicked`, `organise_clicked`, `undo_clicked`, `dupes_clicked`, `desktop_clicked`

4. **Preview Section**
   - "Preview" label
   - Preview text box (disabled, read-only)
   - Method: `set_preview_text(text)`

5. **Advanced Options** (collapsible)
   - Toggle button ("Advanced Options ▾/▴")
   - Hidden content:
     - "Manage Profiles" button
     - "Manage Watched Folders" button
     - "Run at startup" checkbox
     - "Run in background (tray)" checkbox
   - Signals for all buttons/checkboxes

6. **Help Button**
   - Circular "?" button (36x36)
   - Signal: `help_clicked`

7. **Footer**
   - GitHub link label (clickable)
   - Version label
   - "Report Bug" link (clickable)

8. **Status Bar**
   - Integrate StatusBar component
   - Method: `set_status(text)`

**Backend Logic to Connect:**
- Do NOT add logic yet in PySide6 version
- All buttons/checkboxes should emit signals; logic connection happens later
- State should be read from backend via methods, not stored in UI

**Dependencies:** sidebar.py, status_bar.py, tooltip.py, base_widgets.py, styles.py, dialogs.py

**Testing:**
- All UI elements render and are visible
- All signals are emitted when interactions occur
- Layout matches CustomTkinter (responsive)
- Hover/active states work on buttons
- Tooltips display correctly

**Estimated Complexity:** Medium (many components, but mostly layout)

---

## Phase 4: Secondary Windows (Non-Modal)

### Step 4.1: Help Window
**File:** `ui_qt/help_window.py`

**Replace:** Help window from gui.py (lines 1309-1337)

**Components:**
- Dialog title
- Help text (large QLabel or QTextEdit)
- "View Log File" button
- "Report Bug" button (opens browser link)
- "Close" button

**Signals:**
- `view_log_clicked`
- `report_bug_clicked`

**Dependencies:** base_widgets.py, styles.py, dialogs.py

**Estimated Complexity:** Low

---

### Step 4.2: Watched Folders Window
**File:** `ui_qt/watched_folders_window.py`

**Replace:** Watched folders window from gui.py (lines 679-786)

**Components:**
- Title label
- Scrollable list of folders:
  - Folder path label
  - Profile dropdown (combo box) for each folder
  - Status indicator (small circle, green/gray)
- Button row:
  - "Add Folder" button
  - "Remove Folder" button
  - "Close" button

**Methods:**
- `refresh_list(folders, profile_map, status)` - Rebuilds folder list
- `get_selected_folder()` - Returns currently selected folder
- `add_folder(path, profile)` - Adds folder to list
- `remove_folder(path)` - Removes folder from list

**Signals:**
- `add_folder_clicked`
- `remove_folder_clicked`
- `profile_changed(folder_path, profile_id)` - Emitted when dropdown changes
- `closed`

**Dependencies:** base_widgets.py, styles.py, dialogs.py

**Estimated Complexity:** Low-Medium (list handling, profile dropdowns)

---

## Phase 5: Modal Dialog Editors

### Step 5.1: Action Editor
**File:** `ui_qt/action_editor.py`

**Replace:** ActionEditor from action_editor.py (lines 44-315)

**Components:**
- Title label ("Create a New Action")
- Action type dropdown (combo box)
- Parameter input section:
  - Parameter label (updates based on action type)
  - Parameter entry/input (disabled for parameter-less actions)
- Description area:
  - Description label
  - Description text (disabled text edit)
- Buttons:
  - "Add Action" button
  - "Cancel" button

**Methods:**
- `_on_type_change(action_type)` - Updates UI based on selected action type
- `get_action()` - Returns constructed Action object

**Signals:**
- `action_created(action: Action)` - Emitted when "Add Action" is clicked
- `cancelled` - Emitted when "Cancel" is clicked

**State:**
- ACTION_TYPES dict (mapping action name to action class)
- Parameter label text per action type

**Dependencies:** base_widgets.py, styles.py, rule_engine module (for Action classes)

**Estimated Complexity:** Medium (type-based UI changes)

---

### Step 5.2: Condition Selector Popup
**File:** `ui_qt/condition_selector.py`

**Replace:** ConditionSelectorPopup from condition_selector_popup.py

**Components:**
- Title label ("Select Condition Type")
- Categorized scrollable list:
  - **Name** category:
    - Name Contains
    - Name Starts With
    - Name Ends With
    - Name Equals
    - Regex Match
  - **File Properties** category:
    - Extension Is
    - File Size > X bytes
    - File Age > X days
    - Last Modified Before
  - **File Attributes** category:
    - Is Hidden
    - Is Read-Only
    - Is Directory
  - **Path** category:
    - Parent Folder Contains
    - File is in folder containing
  - **Content & Patterns** category:
    - Content Contains
    - Date Pattern
  - **Metadata & Tags** category:
    - Color Is
    - Has Tag
    - Metadata Contains
    - Metadata Field Equals
    - Is Duplicate
- "Close" button (or close by clicking item or pressing Escape)

**Methods:**
- `_select_condition(condition_name)` - Emits signal and closes

**Signals:**
- `condition_selected(condition_name: str)`

**Styling:**
- Category headers (bold, darker background)
- Condition items (selectable, hover effect)

**Estimated Complexity:** Low (pure list UI, no logic)

---

### Step 5.3: Condition Editor
**File:** `ui_qt/condition_editor.py`

**Replace:** ConditionEditor from condition_editor.py (lines 292-712)

**Components:**
- Title label ("Create a New Condition")
- Condition type dropdown
  - Event: `currentIndexChanged` → `_on_type_changed()`
- Dynamic parameter fields section (updated based on condition type):
  - **Text fields:** QLineEdit with placeholder
  - **Numeric fields:** QLineEdit with integer validation
  - **Size fields:** QLineEdit + QComboBox (unit selector: Bytes/KB/MB/GB)
  - **Date fields:** QLineEdit with ISO format placeholder
  - **Dropdown fields:** QComboBox with predefined options
  - **Checkbox fields:** QCheckBox
  - **No-parameter conditions:** No input widgets
- Description area:
  - Description label ("About this condition")
  - Description text (QPlainTextEdit, disabled)
- Buttons:
  - "Add Condition" button
  - "Cancel" button

**Methods:**
- `_on_type_changed(condition_type)` - Rebuilds parameter fields dynamically
- `_clear_fields()` - Destroys existing field widgets
- `_create_text_field(label, spec)` - Creates and returns QLineEdit
- `_create_numeric_field(label, spec)` - Creates QLineEdit with validation
- `_create_size_field(label, spec)` - Creates QLineEdit + QComboBox for size input
- `_create_dropdown_field(label, spec)` - Creates QComboBox
- `_create_checkbox_field(label, spec)` - Creates QCheckBox
- `_update_description(condition_type)` - Updates help text
- `_get_field_value(label)` - Retrieves widget value
- `_collect_parameters(condition_type)` - Gathers all form values
- `_instantiate_condition()` - Creates appropriate Condition subclass
- `_convert_to_bytes(value, unit)` - Size unit conversion
- `get_condition()` - Returns constructed Condition object

**UI Schema (UI_SCHEMA dict):**
Maps each condition type to parameter field specs:
```python
UI_SCHEMA = {
    "Name Contains": [{"label": "Text to search for:", "type": "text", "placeholder": "e.g., backup"}],
    "Name Starts With": [{"label": "Text:", "type": "text"}],
    # ... (copy from condition_editor.py lines 71-153)
}
```

**Dependencies:** base_widgets.py, styles.py, rule_engine module (for Condition classes)

**Estimated Complexity:** High (complex dynamic UI generation, multiple input types)

---

### Step 5.4: Rule Editor
**File:** `ui_qt/rule_editor.py`

**Replace:** RuleEditor from rule_editor.py + RuleEditorPopup from rule_editor_popup.py

**Components:**

1. **Name Section:**
   - Label: "Rule Name"
   - Name entry (QLineEdit)
   - Event: `textChanged` → `_on_field_change()`

2. **Match Mode Section:**
   - Label: "Match Mode"
   - Mode dropdown (QComboBox: ["all", "any"])
   - Help text ("Conditions must match: ALL = AND, ANY = OR")
   - Event: `currentIndexChanged` → `_on_field_change()`

3. **Stop-on-Match Section:**
   - "Stop on match" checkbox (QCheckBox)
   - Help text
   - Event: `stateChanged` → `_on_field_change()`

4. **Conditions Section:**
   - Label: "Conditions"
   - Scrollable list (QScrollArea with QVBoxLayout):
     - Each condition row:
       - QFrame (selectable, color-coded border)
       - QLabel (condition display text)
       - Events:
         - `mousePressEvent` → `select_condition(index)`
         - `enterEvent` → hover color change
         - `leaveEvent` → normal color
   - Button frame:
     - "+ Add Condition" button
     - "- Delete Condition" button

5. **Actions Section:**
   - Similar structure to conditions
   - Label: "Actions"
   - Scrollable list with clickable rows
   - Button frame:
     - "+ Add Action" button
     - "- Delete Action" button

6. **Simulate Button:**
   - "Simulate Rule" button

7. **Dialog Buttons** (in RuleEditorPopup):
   - "Save & Close" button
   - "Cancel" button

**Methods:**
- `_on_field_change()` - Auto-saves if rule is valid
- `refresh_conditions()` - Rebuilds condition list display
- `refresh_actions()` - Rebuilds action list display
- `select_condition(index)` - Highlights condition at index
- `select_action(index)` - Highlights action at index
- `on_condition_hover(index, enter=True)` - Hover effect
- `on_action_hover(index, enter=True)` - Hover effect
- `add_condition()` - Opens ConditionEditor dialog
- `add_action()` - Opens ActionEditor dialog
- `delete_condition()` - Removes selected condition
- `delete_action()` - Removes selected action
- `simulate_rule()` - Opens RuleSimulator dialog
- `get_rule()` - Returns constructed Rule object
- `rule_is_valid()` - Validation

**State Management:**
- `self.rule: Rule` - The rule being edited
- `self.selected_condition_index: Optional[int]` - Currently selected
- `self.selected_action_index: Optional[int]` - Currently selected
- `self.condition_row_frames: list` - List of row widgets
- `self.action_row_frames: list` - List of row widgets

**Signals:**
- `rule_changed` - Emitted when rule is modified
- `saved(rule: Rule)` - Emitted when "Save & Close" clicked
- `cancelled` - Emitted when "Cancel" clicked

**Dependencies:** condition_editor.py, action_editor.py, base_widgets.py, styles.py, rule_engine module

**Estimated Complexity:** High (complex layout, nested editors, selection management)

---

### Step 5.5: Rule Simulator
**File:** `ui_qt/rule_simulator.py`

**Replace:** RuleSimulator from rule_simulator.py

**Components:**
- Title: "Simulate: {rule.name}"
- File selection area:
  - Label: "Test File"
  - File path label
  - "Browse for a file..." button
- Rule info area:
  - Label: "Rule Info"
  - Info display (number of conditions, actions)
- Simulation results area:
  - Label: "Simulation Results"
  - Results text (QPlainTextEdit, disabled)
  - Shows condition matches and actions that would execute
- Buttons:
  - "Run Simulation" button
  - "Close" button

**Methods:**
- `_browse_file()` - Opens file dialog
- `_run_simulation()` - Executes rule on test file
- `_update_results(results_text)` - Updates results display

**Signals:**
- `closed`

**Dependencies:** base_widgets.py, styles.py, dialogs.py, rule_engine module

**Estimated Complexity:** Medium (file I/O, rule execution integration)

---

## Phase 6: Manager Windows

### Step 6.1: Rule Manager
**File:** `ui_qt/rule_manager.py`

**Replace:** RuleManager from rule_manager.py

**Components:**
- Title: "Rules"
- Help text: "Rules run top to bottom. Order = priority."
- Rule list (scrollable):
  - Each rule item:
    - QFrame (selectable, highlight on click)
    - QLabel (rule name)
    - Events: `mousePressEvent` → select, `doubleClick` → edit
- Button frame:
  - "+ Add" button → `add_rule()`
  - "- Delete" button → `delete_rule()`
  - "↑ Up" button → `move_rule_up()`
  - "↓ Down" button → `move_rule_down()`
  - "📋 Activity Log" button → `open_activity_log()`

**Methods:**
- `refresh_list()` - Rebuilds rule list from profile
- `add_rule()` - Opens RuleEditor for new rule
- `delete_rule()` - Removes selected rule
- `move_rule_up()` - Moves selected rule up
- `move_rule_down()` - Moves selected rule down
- `open_activity_log()` - Opens ActivityLogWindow

**State:**
- `self.selected_rule_index: Optional[int]` - Currently selected
- `self.rule_buttons: list` - List of rule row widgets
- `self.profile_id: str` - Profile being edited

**Signals:**
- `rule_selected(index: int)`
- `rule_added`
- `rule_deleted`
- `rule_moved`

**Dependencies:** rule_editor.py, base_widgets.py, styles.py

**Estimated Complexity:** Medium (list management, rule ordering)

---

### Step 6.2: Activity Log Window
**File:** `ui_qt/activity_log_window.py`

**Replace:** ActivityLogWindow (needs to be created or migrated from activity_log_window.py)

**Components:**
- Title: "Activity Log"
- Log text area (QPlainTextEdit, disabled, read-only)
- Filtering/search:
  - Search entry (QLineEdit, placeholder "Search...")
  - Filter dropdown (QComboBox: "All", "Moved", "Deleted", "Renamed", etc.)
- Button row:
  - "Clear Log" button
  - "Export Log" button (saves to file)
  - "Close" button

**Methods:**
- `refresh_log()` - Loads and displays activity log
- `filter_log(filter_type)` - Filters log by action type
- `search_log(query)` - Searches log text
- `clear_log()` - Clears log (with confirmation)
- `export_log()` - Saves log to file

**Dependencies:** base_widgets.py, styles.py, dialogs.py

**Estimated Complexity:** Low (mostly text display and filtering)

---

### Step 6.3: Category Manager
**File:** `ui_qt/category_manager.py`

**Replace:** CategoryManagerWindow from category_manager.py

**Components:**
- Title: "Category Manager"
- Main content (scrollable list):
  - For each category:
    - Checkbox (enabled/disabled)
    - Category label
    - Category name entry (QLineEdit, editable)
    - Extensions entry (QLineEdit, semicolon-separated)
    - "Save" button (saves individual category)
- Button frame:
  - "Restore Default Categories" button (red, warning color)
  - "Close" button

**Methods:**
- `_render()` - Rebuilds UI from profile categories
- `_toggle_enabled(category, enabled)` - Updates enable state
- `_save_category(category)` - Saves single category
- `_restore_defaults()` - Restores all categories to defaults
- `_commit_changes()` - Saves all changes back to profile

**State:**
- `self.working_profile: dict` - Deep copy of profile being edited
- `self.category_rows: dict` - Maps category name to UI row

**Signals:**
- `categories_changed` - Emitted when changes are saved
- `closed`

**Dependencies:** base_widgets.py, styles.py, dialogs.py

**Estimated Complexity:** Medium (category list, enable/disable state)

---

### Step 6.4: Profile Manager
**File:** `ui_qt/profile_manager.py`

**Replace:** ProfileManagerWindow from profile_manager.py

**Components:**

**Left Pane (Sidebar):**
- Button row:
  - "New" button → `create_new_profile()`
  - "Import" button → `import_profiles()`
  - "Export" button → `export_profile()`
- Profile list (scrollable):
  - Each profile item:
    - QFrame (selectable on click)
    - Profile name label (bold if active)
    - "(active)" indicator (if applicable)
    - Menu button "⋯" → `popup_menu(pid)`
- Context menu:
  - "Rename" → `_rename_action()`
  - "Duplicate" → `duplicate_profile()`
  - "Delete" → `delete_profile()` (not for builtin)
  - "Set Active" → `set_active_profile()`

**Right Pane (Editor):**
- Name section:
  - Label: "Profile Name"
  - Name entry (QLineEdit)
- Description section:
  - Label: "Description"
  - Description text edit (QPlainTextEdit, multiline)
- Basic settings:
  - "Include subfolders" checkbox
  - "Ignore hidden/system files" checkbox
  - "Safe Mode" checkbox
  - "Dry Run" checkbox
  - "Smart Sorting" checkbox
- Filters section:
  - "Ignore file extensions" entry (semicolon-separated)
  - "Minimum file age (days)" entry (numeric)
- Advanced patterns section:
  - "Ignore patterns" text edit (one per line)
  - "Don't move files matching" text edit (one per line)
- Buttons:
  - "Edit Categories…" button → `open_category_editor_for_profile()`
  - "Open Rule Manager" button → `open_rule_manager()`
  - "Save Changes" button → `save_editor()`

**Methods:**
- `refresh_list()` - Reloads profile list from storage
- `load_editor(pid)` - Populates right pane with profile data
- `save_editor()` - Saves all changes to storage
- `create_new_profile()` - Creates new profile based on current
- `duplicate_profile(pid)` - Creates copy of existing profile
- `delete_profile(pid)` - Removes profile (with confirmation)
- `rename_profile(pid)` - Renames profile (prompt dialog)
- `set_active_profile(pid)` - Sets as active
- `import_profiles()` - Loads profiles from JSON file
- `export_profile()` - Saves profile to JSON file
- `open_category_editor_for_profile()` - Opens CategoryManager for this profile
- `open_rule_manager()` - Opens RuleManager for this profile
- `popup_menu(pid)` - Shows context menu for profile

**State:**
- `self.selected_id: str` - Current profile ID
- `self.profiles: dict` - Profile objects
- `self.doc: dict` - Full profiles document

**Signals:**
- `profile_selected(profile_id: str)`
- `profile_saved`
- `profile_changed` (general change notification)

**Dependencies:** rule_manager.py, category_manager.py, base_widgets.py, styles.py, dialogs.py, profile_store module

**Estimated Complexity:** High (complex two-pane layout, profile CRUD operations, context menus)

---

## Phase 7: Tray Integration

### Step 7.1: Tray Icon & Menu
**File:** `ui_qt/tray.py`

**Replace:** tray.py (keeping pystray integration)

**Note:** pystray is Qt-agnostic, so the integration should be similar to CustomTkinter. The main difference is the parent window reference and callback signatures.

**Components:**
- Tray icon creation
- Dynamic menu building based on auto-tidy state:
  - "Open FolderFresh" → shows main window
  - "Turn Auto-tidy ON/OFF" → toggle auto-tidy
  - "Exit" → closes application

**Methods:**
- `build_tray_image(size=64)` - Creates tray icon (PIL Image)
- `build_tray_menu(app)` - Builds menu dynamically
- `show_tray_icon(app)` - Creates and runs tray icon in thread
- `hide_tray_icon(app)` - Stops and removes tray icon
- `update_tray_menu(app)` - Rebuilds menu (called on auto-tidy toggle)

**Signals:** (None, communicates via callbacks)

**Dependencies:** pystray, PIL, styles.py

**Estimated Complexity:** Low (minimal changes from CustomTkinter version)

---

## Phase 8: Main Application Wrapper

### Step 8.1: Application Launcher
**File:** `ui_qt/application.py`

**Purpose:** Main application class that ties everything together

**Components:**
- `FolderFreshApplication(QApplication)` class
- Initializes all backend systems
- Wires up signal/slot connections
- Manages window lifecycle
- Handles application-level events

**Methods:**
- `__init__()` - Initializes app, config, profiles, watchers
- `create_main_window()` - Creates main window instance
- `show_main_window()` - Shows and focuses main window
- `hide_to_tray()` - Hides window, shows tray icon
- `toggle_auto_tidy()` - Toggles auto-tidy state
- `shutdown()` - Cleanup on exit

**Dependencies:** main_window.py, profile_manager.py, rule_manager.py, config, profile_store, watcher_manager

**Estimated Complexity:** High (application orchestration)

---

### Step 8.2: Entry Point
**File:** `src/main_qt.py` (new, parallel to existing main.py)

**Purpose:** Entry point for PySide6 version

**Components:**
```python
def main():
    from folderfresh.ui_qt.application import FolderFreshApplication

    app = FolderFreshApplication(sys.argv)
    app.create_main_window()
    app.show_main_window()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**Use:** `python main_qt.py` to launch PySide6 version

**Note:** Keep existing `main.py` intact for CustomTkinter version

---

## Phase 9: Testing & Validation

### Step 9.1: Unit Tests
**File:** `tests/test_qt_widgets.py`

**Components to Test:**
- All custom widgets render without errors
- Signals are emitted correctly
- State management works
- Color schemes apply correctly

---

### Step 9.2: Integration Tests
**File:** `tests/test_qt_integration.py`

**Components to Test:**
- Main window creation
- Window interactions
- Dialog creation and closing
- Backend logic integration
- File operations (preview, organize, etc.)
- Profile management
- Rule execution

---

### Step 9.3: Manual Testing Checklist

#### Main Window:
- [ ] All buttons render correctly
- [ ] Folder selection works (Choose/Open)
- [ ] Checkboxes save state correctly
- [ ] Preview shows correct output
- [ ] Organise executes correctly
- [ ] Undo works
- [ ] Find Duplicates works
- [ ] Clean Desktop works
- [ ] Advanced options toggle works
- [ ] Help dialog opens
- [ ] Keyboard shortcuts work (Ctrl+O, Ctrl+P, Return)

#### Dialogs:
- [ ] Profile Manager opens and closes
- [ ] Rule Manager opens and closes
- [ ] Rule Editor opens and closes
- [ ] Condition Editor creates conditions correctly
- [ ] Action Editor creates actions correctly
- [ ] All dialogs are modal (block parent interaction)
- [ ] All dialogs can be cancelled without side effects

#### Watched Folders:
- [ ] Can add folders
- [ ] Can remove folders
- [ ] Profile dropdowns work
- [ ] Status indicator updates correctly

#### Tray:
- [ ] Tray icon appears
- [ ] Tray menu has correct options
- [ ] "Open FolderFresh" restores window
- [ ] "Turn Auto-tidy ON/OFF" toggles correctly
- [ ] "Exit" closes application

#### Cross-Platform:
- [ ] All fonts render correctly (Segoe UI Variable on Windows, fallback on macOS/Linux)
- [ ] Colors match CustomTkinter theme
- [ ] Dialogs position correctly on screen
- [ ] Window resizing works smoothly

---

## Migration Timeline & Sequencing

### Critical Path (Minimum to Functional):
1. Phase 1: Foundation (✓ Done)
2. Phase 2.1: Styling module → needed for all subsequent phases
3. Phase 3.1-3.3: Main window (highest complexity, but core functionality)
4. Phase 5.3-5.4: Condition/Rule editors (needed for rule editing)
5. Phase 6.1-6.4: Managers (needed for profile/rule management)
6. Phase 8.1-8.2: Application wrapper & entry point
7. Phase 9: Testing & validation

### Recommended Order:
1. Phase 1 (Foundation) ✓
2. Phase 2 (Infrastructure) - Order: 2.1 → 2.2 → 2.3
3. Phase 3 (Main Window) - Order: 3.1 → 3.2 → 3.3
4. Phase 4 (Secondary Windows) - Order: 4.1 → 4.2
5. Phase 5 (Modal Editors) - Order: 5.1 → 5.2 → 5.3 → 5.4 → 5.5
6. Phase 6 (Managers) - Order: 6.1 → 6.2 → 6.3 → 6.4
7. Phase 7 (Tray)
8. Phase 8 (Application Wrapper)
9. Phase 9 (Testing)

### Dependency Graph:
```
Phase 1 (Foundation)
    ↓
Phase 2.1 (Styling) ← required by all
    ↓
Phase 2.2 (Dialogs)
    ├→ Phase 2.3 (Base Widgets)
    ├→ Phase 3 (Main Window)
    ├→ Phase 4 (Secondary Windows)
    ├→ Phase 5 (Modal Editors)
    ├→ Phase 6 (Managers)
    └→ Phase 7 (Tray)
        ↓
Phase 8 (Application Wrapper)
    ↓
Phase 9 (Testing)
```

---

## Key Architectural Decisions

### 1. Parallel Implementation
- Keep `src/folderfresh/gui.py` and CustomTkinter code intact
- Build PySide6 code in `src/folderfresh/ui_qt/` directory
- Create new entry point `src/main_qt.py` for PySide6 version
- Switch by modifying `src/main.py` or launcher script

### 2. Backend Isolation
- **STRICT RULE:** Do not modify any backend code (rule_engine, watcher, actions, config, etc.)
- UI layer communicates with backend via existing APIs
- Backend modules remain CustomTkinter-agnostic

### 3. Signal/Slot Architecture
- Use PySide6 signals (pyqtSignal) for event communication
- No direct backend calls from UI event handlers
- Application wrapper orchestrates signal-to-logic connections

### 4. Styling Approach
- Centralized stylesheet in `ui_qt/styles.py`
- Consistent color palette across all windows
- Reusable button/label/input styles
- Hover/active/disabled states via CSS stylesheets

### 5. Window Management
- All dialogs use `QDialog` or `QMainWindow` (not custom)
- Modal dialogs use `exec()` for blocking behavior
- Parent-child relationships for Z-ordering
- Proper cleanup in `closeEvent()` methods

### 6. Threading
- Use `QThread` and `QThreadPool` for background operations
- Use `QTimer` for periodic updates
- Use signals to communicate between threads and UI

### 7. Data Binding
- No automatic data binding (keep simple)
- Explicit `refresh_*()` methods to update UI from backend
- Explicit `get_*()` methods to extract values from UI

---

## Risk Mitigation

### Risk 1: Breaking Backend Integration
**Mitigation:**
- Create `ui_qt/backend_adapter.py` to wrap all backend calls
- Version all backend APIs explicitly
- Add integration tests for each backend interaction
- Keep CustomTkinter version as fallback

### Risk 2: Performance Issues
**Mitigation:**
- Profile rendering performance frequently
- Use `setUpdatesEnabled(False)` during bulk updates
- Lazy-load large lists (pagination)
- Use `QTimer.singleShot()` for deferred updates

### Risk 3: Platform-Specific Issues
**Mitigation:**
- Test on Windows, macOS, and Linux
- Use platform-specific fonts (fallbacks defined)
- Handle file dialogs platform-safely (use QFileDialog)
- Test tray icon on all platforms

### Risk 4: Theme Inconsistency
**Mitigation:**
- Centralize all colors in `styles.py`
- Create visual style guide (document expected appearance)
- Regular side-by-side comparisons with CustomTkinter version
- Use consistent icon/emoji approach across windows

---

## Success Criteria

✓ **Completion Checklist:**
- [ ] All 14 windows migrated to PySide6
- [ ] All UI elements render identically to CustomTkinter version
- [ ] All signals/slots connected and functional
- [ ] All backend integrations work (preview, organize, undo, etc.)
- [ ] Tray mode functional
- [ ] All keyboard shortcuts work
- [ ] All dialogs modal and properly sized
- [ ] No CustomTkinter imports in `ui_qt/` directory
- [ ] Manual testing checklist complete
- [ ] Cross-platform testing on Windows/macOS/Linux
- [ ] Entry point `src/main_qt.py` works without errors
- [ ] Zero regressions in backend functionality

---

## Dependencies to Add

### New Python Packages:
```
PySide6>=6.0.0          # Qt for Python
```

### Updated requirements.txt:
```
# GUI Framework
customtkinter>=5.2.0    # Keep for fallback
PySide6>=6.0.0          # New: Qt for Python
Pillow>=10.0.0

# File Monitoring & System Tray
watchdog>=3.0.0
pystray>=0.19.0

# Testing & Code Quality
pytest>=7.4.0
pytest-cov>=4.1.0
coverage>=7.2.0
```

---

## Notes for Implementation

### Code Style:
- Follow PySide6 conventions (camelCase for methods, PascalCase for classes)
- Use type hints throughout (`from typing import ...`)
- Document complex UI logic with docstrings
- Keep methods small and focused

### Common PySide6 Patterns:
```python
# Signal definition
signal_name = Signal(str)  # Signal(int) for arguments

# Signal emission
self.signal_name.emit("value")

# Signal connection
button.clicked.connect(self.on_button_clicked)

# Thread-safe UI updates
self.worker_finished.connect(self.update_ui)  # Called in main thread

# Modal dialog
dialog = SomeDialog(self)
if dialog.exec() == QDialog.Accepted:
    result = dialog.get_result()
```

### File Structure After Migration:
```
src/folderfresh/
├── ui_qt/                      # NEW: PySide6 UI components
│   ├── __init__.py
│   ├── application.py          # Main application class
│   ├── main_window.py          # Main window
│   ├── sidebar.py              # Sidebar navigation
│   ├── status_bar.py           # Status bar component
│   ├── tooltip.py              # Tooltip helper
│   ├── styles.py               # Theme and colors
│   ├── base_widgets.py         # Reusable widgets
│   ├── dialogs.py              # Common dialog utilities
│   ├── action_editor.py        # Action editor dialog
│   ├── condition_editor.py     # Condition editor dialog
│   ├── condition_selector.py   # Condition selector popup
│   ├── rule_editor.py          # Rule editor dialog
│   ├── rule_simulator.py       # Rule simulator dialog
│   ├── rule_manager.py         # Rule manager window
│   ├── activity_log_window.py  # Activity log window
│   ├── category_manager.py     # Category manager window
│   ├── profile_manager.py      # Profile manager window
│   ├── watched_folders_window.py  # Watched folders window
│   ├── help_window.py          # Help dialog
│   └── tray.py                 # Tray integration
├── gui.py                      # KEEP: CustomTkinter version (fallback)
├── (all other modules unchanged)
└── main_qt.py                  # NEW: PySide6 entry point (at root level)
```

---

## Next Steps

1. **Start Phase 2.1:** Create `ui_qt/styles.py` with color palette and styling utilities
2. **Review with User:** Confirm timeline, dependencies, and any architectural changes
3. **Implement in Order:** Follow the Critical Path sequencing
4. **Test Continuously:** Build and test each phase before moving to the next
5. **Document as You Go:** Keep implementation notes for future reference

---

## Questions to Address

- [ ] Should we keep CustomTkinter version indefinitely (for fallback), or remove it after full migration?
- [ ] Should we support both versions running simultaneously, or switch completely?
- [ ] Are there specific PySide6 features you want to leverage (e.g., QML, animations)?
- [ ] Should we add dark/light theme toggle in PySide6 version?
- [ ] Any specific Windows/macOS/Linux compatibility requirements?
- [ ] Should packaging/installer script be updated during migration, or after?

---

**End of Plan**
