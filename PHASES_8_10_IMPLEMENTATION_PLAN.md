# FolderFresh PySide6 UI - Phases 8-10 Implementation Plan

## Overview
Complete the PySide6 UI overhaul with comprehensive testing, backend integration, and full application wrapper. This brings the modern PySide6 interface into full parity with the existing CustomTkinter backend.

**Status**: Planning Phase
**Target Phases**: 8, 9, 10
**Estimated Work**: 40-60 hours
**Timeline**: Sequential implementation of testing → integration → wrapper

---

## Phase 8: Testing & Validation

### 8.1 Unit Tests for UI Windows

**Objective**: Test each PySide6 window component in isolation

**Files to Create**:
- `tests/test_ui_qt_windows.py` - Unit tests for all window classes
- `tests/test_ui_qt_dialogs.py` - Unit tests for all dialog classes
- `tests/test_ui_qt_base_widgets.py` - Unit tests for base widget classes

**Test Coverage**:

#### MainWindow Tests
```python
def test_main_window_initialization():
    """Test MainWindow creates all components"""
    window = MainWindow()
    assert window.isVisible() == False  # Not shown until launched
    assert hasattr(window, 'preview_btn')
    assert hasattr(window, 'organise_btn')
    assert hasattr(window, 'undo_btn')
    # ... all buttons and checkboxes

def test_main_window_signals_exist():
    """Test all required signals are defined"""
    window = MainWindow()
    signals = [
        'folder_chosen', 'preview_requested', 'organise_requested',
        'undo_requested', 'duplicates_requested', 'desktop_clean_requested',
        'profiles_requested', 'watched_folders_requested', 'help_requested',
        'options_changed'
    ]
    for sig_name in signals:
        assert hasattr(window, sig_name)

def test_main_window_signal_connections():
    """Test button clicks emit correct signals"""
    window = MainWindow()
    signal_received = []
    window.preview_requested.connect(lambda: signal_received.append('preview'))
    # Simulate button click
    window.preview_btn.clicked.emit()
    assert 'preview' in signal_received

def test_main_window_checkbox_states():
    """Test checkbox initialization and state changes"""
    window = MainWindow()
    assert window.include_sub_check.isChecked() == True
    window.include_sub_check.setChecked(False)
    assert window.include_sub_check.isChecked() == False

def test_main_window_advanced_section_toggle():
    """Test advanced section collapse/expand"""
    window = MainWindow()
    initial_visible = window.advanced_content.isVisible()
    window.advanced_btn.clicked.emit()
    assert window.advanced_content.isVisible() != initial_visible
```

#### ProfileManagerWindow Tests
```python
def test_profile_manager_initialization():
    """Test ProfileManagerWindow creates all components"""
    window = ProfileManagerWindow()
    assert hasattr(window, 'profiles_scroll')
    assert hasattr(window, 'editor_scroll')
    assert hasattr(window, 'new_profile_btn')

def test_profile_manager_profile_list():
    """Test profile list populates correctly"""
    window = ProfileManagerWindow()
    # Mock profiles (will be filled from backend in Phase 9)
    assert window.profiles_scroll is not None

def test_profile_manager_profile_selection():
    """Test selecting a profile updates editor"""
    window = ProfileManagerWindow()
    # Test that clicking a profile updates editor fields
```

#### RuleManagerWindow Tests
```python
def test_rule_manager_initialization():
    """Test RuleManager creates all components"""
    window = RuleManager()
    assert hasattr(window, 'rules_list')
    assert hasattr(window, 'new_rule_btn')
    assert hasattr(window, 'edit_rule_btn')

def test_rule_manager_rule_list():
    """Test rule list displays correctly"""
    window = RuleManager()
    # Test rule list population (will be filled from backend in Phase 9)
    assert window.rules_list is not None
```

#### ActivityLogWindow Tests
```python
def test_activity_log_window_initialization():
    """Test ActivityLogWindow creates all components"""
    window = ActivityLogWindow()
    assert hasattr(window, 'log_display')
    assert hasattr(window, 'clear_btn')

def test_activity_log_window_display():
    """Test log entries display correctly"""
    window = ActivityLogWindow()
    # Test that log entries are displayed
    assert window.log_display is not None
```

#### WatchedFoldersWindow Tests
```python
def test_watched_folders_initialization():
    """Test WatchedFoldersWindow creates all components"""
    window = WatchedFoldersWindow()
    assert hasattr(window, 'folders_list')
    assert hasattr(window, 'add_folder_btn')

def test_watched_folders_add_remove():
    """Test adding/removing watched folders"""
    window = WatchedFoldersWindow()
    # Test folder addition and removal (backend in Phase 9)
    assert window.folders_list is not None
```

#### Base Widget Tests
```python
def test_styled_button_creation():
    """Test StyledButton initializes correctly"""
    btn = StyledButton("Test", Colors.ACCENT)
    assert btn.text() == "Test"
    assert btn.minimumHeight() >= 40

def test_styled_line_edit_creation():
    """Test StyledLineEdit initializes correctly"""
    edit = StyledLineEdit()
    assert edit.isEnabled() == True

def test_card_frame_creation():
    """Test CardFrame creates correctly"""
    frame = CardFrame()
    assert frame.layout() is not None

def test_scrollable_frame_with_spacing():
    """Test ScrollableFrame accepts spacing parameter"""
    frame = ScrollableFrame(spacing=8)
    assert frame.content_layout.spacing() == 8
```

**Test Execution**:
```bash
pytest tests/test_ui_qt_windows.py -v
pytest tests/test_ui_qt_dialogs.py -v
pytest tests/test_ui_qt_base_widgets.py -v
```

---

### 8.2 Integration Tests

**Objective**: Test UI components working together with each other

**Files to Create**:
- `tests/test_ui_qt_integration.py` - Integration tests between UI components

**Test Coverage**:

#### Cross-Window Signal Communication
```python
def test_main_window_to_profile_manager():
    """Test MainWindow → ProfileManager integration"""
    main = MainWindow()
    manager = ProfileManagerWindow()

    # When profile changes in manager, main window should update
    # (Signal connection tested in Phase 9)

def test_profile_changes_update_ui():
    """Test that changing profile updates all relevant UI"""
    window = MainWindow()
    # When active profile changes:
    # - Main window options should update
    # - Rule list should update
    # - Watched folders should update
```

#### Rule Editor Integration
```python
def test_rule_creation_workflow():
    """Test complete rule creation flow"""
    manager = RuleManager()
    # 1. Click new_rule_btn
    # 2. Opens RuleEditor dialog
    # 3. Fill in rule details
    # 4. Click save
    # 5. Rule appears in list

def test_action_editor_integration():
    """Test ActionEditor opens from RuleEditor"""
    editor = RuleEditor()
    # Click add action button
    # ActionEditor dialog opens
    # Select action type
    # Configure action parameters
    # Action added to rule
```

#### Folder Selection Integration
```python
def test_main_window_folder_selection():
    """Test folder selection flow"""
    window = MainWindow()
    # 1. Click browse button
    # 2. Folder dialog opens
    # 3. Select folder
    # 4. Path appears in path_entry
    # 5. Preview button becomes enabled
```

#### Preview Integration
```python
def test_preview_shows_results():
    """Test preview displays results correctly"""
    window = MainWindow()
    # 1. Set folder
    # 2. Click preview
    # 3. Results appear in preview_box
    # 4. Shows what will happen (dry run)
```

**Test Execution**:
```bash
pytest tests/test_ui_qt_integration.py -v
```

---

### 8.3 Manual Testing Checklist

**File to Create**: `MANUAL_TESTING_CHECKLIST.md`

**Checklist Structure**:

#### Main Window
- [ ] Window opens and displays all components
- [ ] All buttons are visible and clickable
- [ ] All checkboxes are functional
- [ ] Folder selection works (browse button)
- [ ] Path entry shows selected folder
- [ ] Options panel can be toggled (Advanced)
- [ ] All signals fire correctly when buttons clicked

#### Buttons Functionality
- [ ] Preview button opens folder browser
- [ ] Preview shows file list without changes
- [ ] Organise button applies rules
- [ ] Undo button reverses last action
- [ ] Find Duplicates button opens duplicates dialog
- [ ] Clean Desktop button works
- [ ] All buttons disable/enable appropriately

#### Checkboxes
- [ ] Include Subfolders checkbox state persists
- [ ] Skip Hidden/System Files checkbox works
- [ ] Safe Mode checkbox prevents actual changes
- [ ] Smart Sorting checkbox affects organization
- [ ] Auto-tidy checkbox enables watch mode

#### Windows Management
- [ ] Manage Profiles window opens
- [ ] Manage Rules window opens
- [ ] Manage Watched Folders window opens
- [ ] Activity Log window opens
- [ ] Help window opens
- [ ] All windows can be closed

#### Profile Manager
- [ ] Profile list displays
- [ ] Can create new profile
- [ ] Can edit existing profile
- [ ] Can delete profile
- [ ] Active profile highlighted
- [ ] Settings save correctly

#### Rule Manager
- [ ] Rule list displays
- [ ] Can create new rule
- [ ] Can edit rule
- [ ] Can delete rule
- [ ] Can test rule
- [ ] Rules save to active profile

#### Styling & Appearance
- [ ] Dark theme applied consistently
- [ ] No white space visible
- [ ] Buttons have proper hover state
- [ ] Input fields have proper focus state
- [ ] Text is readable (high contrast)
- [ ] Icons display correctly
- [ ] Spacing is cohesive throughout

#### Keyboard Navigation
- [ ] Tab navigates through controls
- [ ] Enter activates buttons
- [ ] Escape closes dialogs
- [ ] All buttons have keyboard shortcuts

#### Error Handling
- [ ] Invalid folder paths show error message
- [ ] Duplicate profile names prevented
- [ ] Invalid rules show error
- [ ] File operations show appropriate messages

---

### 8.4 Keyboard Shortcuts

**File to Create/Update**: `src/folderfresh/ui_qt/shortcuts.py`

**Standard Shortcuts**:
```python
class ApplicationShortcuts:
    PREVIEW = "Ctrl+E"
    ORGANISE = "Ctrl+O"
    UNDO = "Ctrl+Z"
    REDO = "Ctrl+Y"
    HELP = "F1"
    SETTINGS = "Ctrl+,"
    QUIT = "Ctrl+Q"
    NEW_PROFILE = "Ctrl+N"
    NEW_RULE = "Ctrl+Shift+N"
    OPEN_PROFILES = "Ctrl+P"
    OPEN_RULES = "Ctrl+R"
    OPEN_FOLDERS = "Ctrl+W"
```

**Implementation**:
```python
# In MainWindow.__init__
self.preview_btn.setShortcut(ApplicationShortcuts.PREVIEW)
self.organise_btn.setShortcut(ApplicationShortcuts.ORGANISE)
self.undo_btn.setShortcut(ApplicationShortcuts.UNDO)

# Create QActions for menu/tray
profile_action = QAction(self.tr("Manage Profiles"), self)
profile_action.setShortcut(ApplicationShortcuts.OPEN_PROFILES)
profile_action.triggered.connect(self.on_manage_profiles)
```

---

### 8.5 Context Menus

**File to Create/Update**: `src/folderfresh/ui_qt/context_menus.py`

**Context Menus Needed**:

1. **Profile List Context Menu**
   - Edit Profile
   - Duplicate Profile
   - Set as Active
   - Delete Profile

2. **Rule List Context Menu**
   - Edit Rule
   - Duplicate Rule
   - Test Rule
   - Move Up/Down (reorder)
   - Delete Rule

3. **Activity Log Context Menu**
   - Copy Entry
   - Clear Log
   - Export Log

4. **Folder List Context Menu**
   - Edit Profile for Folder
   - Remove Folder
   - Open Folder

**Implementation Pattern**:
```python
def setup_context_menu(self):
    """Setup right-click context menus"""
    self.profile_list.setContextMenuPolicy(Qt.CustomContextMenu)
    self.profile_list.customContextMenuRequested.connect(self.show_profile_context_menu)

def show_profile_context_menu(self, position):
    """Show context menu at cursor"""
    menu = QMenu(self)
    menu.addAction("Edit Profile", self.on_edit_profile)
    menu.addAction("Duplicate Profile", self.on_duplicate_profile)
    menu.addSeparator()
    menu.addAction("Delete Profile", self.on_delete_profile)
    menu.exec(QCursor.pos())
```

---

## Phase 9: Backend Integration

### 9.1 ProfileManager ↔ ProfileStore

**Objective**: ProfileManagerWindow reads/writes real profile data

**Current State**: ProfileStore is fully implemented
**Task**: Connect UI to ProfileStore

**Implementation**:

```python
# In ProfileManagerWindow.__init__
from folderfresh.profile_store import ProfileStore

def __init__(self):
    super().__init__()
    self.profile_store = ProfileStore()
    self.profiles_doc = self.profile_store.load()
    self._populate_profile_list()

def _populate_profile_list(self):
    """Load profiles from ProfileStore"""
    profiles = self.profiles_doc.get("profiles", [])
    for profile in profiles:
        # Add to profiles_scroll
        item = self._create_profile_item(profile)
        self.profiles_scroll.add_widget(item)

def on_save_profile(self):
    """Save profile changes to ProfileStore"""
    # Gather edited profile data
    profile = {
        "id": self.profile_id,
        "name": self.profile_name_input.text(),
        "settings": {
            "smart_mode": self.smart_mode_check.isChecked(),
            "safe_mode": self.safe_mode_check.isChecked(),
            # ... other settings
        }
    }
    # Update in profiles_doc
    for p in self.profiles_doc["profiles"]:
        if p["id"] == self.profile_id:
            p.update(profile)
            break
    # Persist
    self.profile_store.save(self.profiles_doc)
    self.profile_saved.emit()

def on_create_profile(self):
    """Create new profile"""
    new_profile = {
        "id": f"profile_{uuid.uuid4().hex[:8]}",
        "name": "New Profile",
        "settings": {...default settings...},
        "rules": []
    }
    self.profiles_doc["profiles"].append(new_profile)
    self.profile_store.save(self.profiles_doc)
    self._populate_profile_list()
    self.profile_created.emit(new_profile["id"])

def on_delete_profile(self, profile_id):
    """Delete profile"""
    if profile_id == self.profiles_doc.get("active_profile_id"):
        # Cannot delete active profile
        show_error_dialog("Cannot delete active profile")
        return

    self.profiles_doc["profiles"] = [
        p for p in self.profiles_doc["profiles"]
        if p["id"] != profile_id
    ]
    self.profile_store.save(self.profiles_doc)
    self._populate_profile_list()
    self.profile_deleted.emit(profile_id)
```

**Signal Emissions**:
- `profile_created(profile_id)` - After profile created
- `profile_updated(profile_id)` - After profile edited
- `profile_deleted(profile_id)` - After profile deleted
- `profile_activated(profile_id)` - After profile activated

**Data Binding**:
- Read from `self.profiles_doc["profiles"]`
- Write changes back to ProfileStore via `save()`
- Emit signals so MainWindow can update

---

### 9.2 RuleManager ↔ RuleEngine

**Objective**: RuleManager reads/writes rules to active profile

**Current State**: RuleEngine fully implemented, rules stored in ProfileStore
**Task**: Connect UI to rule engine

**Implementation**:

```python
# In RuleManager.__init__
from folderfresh.profile_store import ProfileStore
from folderfresh.rule_engine import Rule, RuleExecutor

def __init__(self):
    super().__init__()
    self.profile_store = ProfileStore()
    self.profiles_doc = self.profile_store.load()
    self.active_profile = self._get_active_profile()
    self._populate_rule_list()

def _get_active_profile(self):
    """Get currently active profile"""
    active_id = self.profiles_doc.get("active_profile_id")
    for p in self.profiles_doc["profiles"]:
        if p["id"] == active_id:
            return p
    return None

def _populate_rule_list(self):
    """Load rules from active profile"""
    if not self.active_profile:
        return

    rules = self.active_profile.get("rules", [])
    for rule_data in rules:
        # Deserialize from dict to Rule object
        from folderfresh.rule_engine import rule_store
        rule = rule_store.dict_to_rule(rule_data)

        # Add to rules_list
        item = self._create_rule_item(rule, rule_data)
        self.rules_list.add_widget(item)

def on_save_rule(self, rule: Rule):
    """Save rule to active profile"""
    from folderfresh.rule_engine import rule_store

    if not self.active_profile:
        show_error_dialog("No active profile")
        return

    # Convert Rule object to dict
    rule_dict = rule_store.rule_to_dict(rule)

    # Update or append to rules
    rules = self.active_profile.get("rules", [])
    updated = False
    for i, r in enumerate(rules):
        if r.get("id") == rule.id:
            rules[i] = rule_dict
            updated = True
            break

    if not updated:
        rules.append(rule_dict)

    self.active_profile["rules"] = rules
    self.profile_store.save(self.profiles_doc)
    self._populate_rule_list()
    self.rule_saved.emit(rule.id)

def on_test_rule(self, rule: Rule):
    """Test rule against selected files"""
    # Get files from file browser
    files = self._get_selected_files()

    # Create RuleExecutor
    executor = RuleExecutor()

    # Test each file
    results = []
    config = {
        "safe_mode": False,
        "dry_run": True,
        "skip_hidden": True
    }

    for file_path in files:
        from folderfresh.fileinfo import get_fileinfo
        fileinfo = get_fileinfo(file_path)

        result = executor.execute([rule], fileinfo, config)
        results.append({
            "file": file_path,
            "matched": result.get("matched_rule") is not None,
            "action": result.get("final_dst"),
            "log": result.get("log", [])
        })

    # Show results in dialog
    self._show_test_results(results)
```

**Signal Emissions**:
- `rule_created(rule_id)` - After rule created
- `rule_updated(rule_id)` - After rule edited
- `rule_deleted(rule_id)` - After rule deleted
- `rule_tested(results)` - After rule test completes

**Integration Points**:
- Read rules from active profile
- Serialize/deserialize via rule_store
- Test via RuleExecutor
- Write back to ProfileStore

---

### 9.3 WatchedFoldersWindow ↔ WatcherManager

**Objective**: Manage watched folders and their profiles

**Current State**: WatcherManager implemented with per-folder profiles
**Task**: Connect UI to WatcherManager

**Implementation**:

```python
# In WatchedFoldersWindow.__init__
from folderfresh.watcher_manager import WatcherManager
from folderfresh.config import Config

def __init__(self):
    super().__init__()
    self.config = Config()
    self.config_data = self.config.load()
    self.watcher_manager = None  # Will be passed from main app
    self._populate_folder_list()

def set_watcher_manager(self, watcher_manager):
    """Set reference to WatcherManager"""
    self.watcher_manager = watcher_manager

def _populate_folder_list(self):
    """Load watched folders from config"""
    folders = self.config_data.get("watched_folders", [])
    for folder_path in folders:
        # Get profile for this folder
        folder_profile_map = self.config_data.get("folder_profile_map", {})
        profile_name = folder_profile_map.get(folder_path, "Default")

        item = self._create_folder_item(folder_path, profile_name)
        self.folders_scroll.add_widget(item)

def on_add_folder(self):
    """Add new watched folder"""
    folder_path = browse_folder_dialog(self, "Select folder to watch")
    if not folder_path:
        return

    # Check if already watching
    if folder_path in self.config_data.get("watched_folders", []):
        show_warning_dialog("Already watching this folder")
        return

    # Add to config
    if "watched_folders" not in self.config_data:
        self.config_data["watched_folders"] = []
    self.config_data["watched_folders"].append(folder_path)

    # Start watching
    if self.watcher_manager:
        self.watcher_manager.watch_folder(folder_path)

    # Save config
    self.config.save(self.config_data)

    # Update UI
    self._populate_folder_list()
    self.folder_added.emit(folder_path)

def on_remove_folder(self, folder_path):
    """Remove watched folder"""
    # Stop watching
    if self.watcher_manager:
        self.watcher_manager.unwatch_folder(folder_path)

    # Remove from config
    if folder_path in self.config_data.get("watched_folders", []):
        self.config_data["watched_folders"].remove(folder_path)

    # Remove folder profile mapping
    folder_profile_map = self.config_data.get("folder_profile_map", {})
    if folder_path in folder_profile_map:
        del folder_profile_map[folder_path]

    # Save config
    self.config.save(self.config_data)

    # Update UI
    self._populate_folder_list()
    self.folder_removed.emit(folder_path)

def on_set_folder_profile(self, folder_path, profile_name):
    """Set profile for specific folder"""
    folder_profile_map = self.config_data.get("folder_profile_map", {})
    folder_profile_map[folder_path] = profile_name
    self.config_data["folder_profile_map"] = folder_profile_map

    # Save config
    self.config.save(self.config_data)

    # Update UI
    self._populate_folder_list()
    self.folder_profile_changed.emit(folder_path, profile_name)
```

**Signal Emissions**:
- `folder_added(folder_path)` - After folder added
- `folder_removed(folder_path)` - After folder removed
- `folder_profile_changed(folder_path, profile_name)` - After profile changed

**Data Binding**:
- Read watched folders from Config
- Read folder→profile mapping from Config
- Update WatcherManager when folders added/removed
- Persist via Config.save()

---

### 9.4 ActivityLogWindow ↔ ActivityLog Backend

**Objective**: Display real activity log entries

**Current State**: ActivityLog is in-memory ring buffer
**Task**: Connect UI to ActivityLog

**Implementation**:

```python
# In ActivityLogWindow.__init__
from folderfresh.activity_log import ACTIVITY_LOG

def __init__(self):
    super().__init__()
    self.activity_log = ACTIVITY_LOG
    self._populate_log_display()
    self._setup_auto_refresh()

def _populate_log_display(self):
    """Load activity log entries"""
    log_entries = self.activity_log.get_log()

    # Clear current display
    self.log_display.setPlainText("")

    # Add entries (newest first)
    for entry in reversed(log_entries):
        self.log_display.appendPlainText(entry)

def _setup_auto_refresh(self):
    """Refresh log display periodically"""
    self.refresh_timer = QTimer()
    self.refresh_timer.timeout.connect(self._populate_log_display)
    self.refresh_timer.start(1000)  # Refresh every second

def on_clear_log(self):
    """Clear activity log"""
    if ask_confirmation_dialog(self, "Clear all activity log entries?"):
        self.activity_log.clear()
        self.log_display.setPlainText("")
        self.log_cleared.emit()

def on_export_log(self):
    """Export log to file"""
    file_path = save_file_dialog(
        self,
        "Export Activity Log",
        filter="Text Files (*.txt);;CSV Files (*.csv)"
    )
    if not file_path:
        return

    try:
        self.activity_log.save_to_file(file_path)
        show_info_dialog(f"Log exported to {file_path}")
        self.log_exported.emit(file_path)
    except Exception as e:
        show_error_dialog(f"Failed to export log: {e}")

def on_copy_entry(self):
    """Copy selected entry to clipboard"""
    text = self.log_display.textCursor().selectedText()
    if text:
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        show_info_dialog("Entry copied to clipboard")
```

**Signal Emissions**:
- `log_cleared()` - After log cleared
- `log_exported(file_path)` - After log exported

**Auto-Refresh**:
- Use QTimer to refresh display every 1 second
- Only update if new entries added (optimization)
- Show most recent entries at top

---

### 9.5 MainWindow ↔ UndoManager

**Objective**: Undo button reverses actual file operations

**Current State**: UndoManager is LIFO stack
**Task**: Connect undo button to UndoManager

**Implementation**:

```python
# In MainWindow.__init__
from folderfresh.undo_manager import UNDO_MANAGER

def __init__(self):
    super().__init__()
    self.undo_manager = UNDO_MANAGER

    # Connect undo button
    self.undo_btn.clicked.connect(self.on_undo)

    # Update undo button state
    self._update_undo_state()

    # Periodically check if undo available
    self.undo_check_timer = QTimer()
    self.undo_check_timer.timeout.connect(self._update_undo_state)
    self.undo_check_timer.start(500)

def on_undo(self):
    """Undo last action"""
    try:
        result = self.undo_manager.undo_last()

        if result["success"]:
            show_info_dialog(
                f"Undid: {result['status']}\n"
                f"From: {result.get('dst', result.get('new_name'))}\n"
                f"To: {result.get('src', result.get('old_name'))}"
            )
        else:
            show_error_dialog(f"Undo failed: {result.get('error', 'Unknown error')}")

        # Refresh display
        self._update_undo_state()
        self.undo_requested.emit()

    except Exception as e:
        show_error_dialog(f"Error during undo: {e}")

def _update_undo_state(self):
    """Update undo button enabled state"""
    history = self.undo_manager.get_history()

    if history:
        last_action = history[0]
        action_type = last_action.get("type", "").capitalize()
        src = last_action.get("src", "")
        self.undo_btn.setText(f"Undo {action_type}")
        self.undo_btn.setEnabled(True)
        self.undo_btn.setToolTip(f"Undo: {src}")
    else:
        self.undo_btn.setText("Undo Last")
        self.undo_btn.setEnabled(False)
        self.undo_btn.setToolTip("No actions to undo")
```

**Features**:
- Dynamic button text: "Undo Move", "Undo Rename", etc.
- Disabled when no undo history
- Tooltip shows what will be undone
- Refresh undo state every 500ms
- Show confirmation dialog on success/failure

---

## Phase 10: Full Application Wrapper

### 10.1 PySide6 Application Entry Point

**File to Create**: `src/main_qt.py` (New main entry point for PySide6)

**Purpose**: Complete application wrapper orchestrating all backend systems and UI

**Implementation**:

```python
"""
FolderFresh PySide6 Application Wrapper
Main entry point for the modern PySide6 UI with full backend integration
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer

# Backend systems
from folderfresh.profile_store import ProfileStore
from folderfresh.config import Config
from folderfresh.watcher_manager import WatcherManager
from folderfresh.undo_manager import UNDO_MANAGER
from folderfresh.activity_log import ACTIVITY_LOG, log_activity

# UI components
from folderfresh.ui_qt.main_qt import setup_qt_app, setup_stylesheet
from folderfresh.ui_qt.application import FolderFreshApplication
from folderfresh.ui_qt.main_window import MainWindow


class FolderFreshQtApp:
    """
    Complete FolderFresh application wrapper.
    Initializes all backend systems and manages application lifecycle.
    """

    def __init__(self):
        """Initialize application"""
        self.logger = self._setup_logging()
        self.logger.info("=" * 60)
        self.logger.info("FolderFresh PySide6 Application Starting")
        self.logger.info("=" * 60)

        # Initialize backend systems
        self.config = Config()
        self.profile_store = ProfileStore()
        self.watcher_manager = None

        # Load persistent data
        self._load_configuration()

        # Initialize UI
        self.qt_app = None
        self.main_window = None

    def _setup_logging(self) -> logging.Logger:
        """Setup application logging"""
        logger = logging.getLogger("folderfresh")
        logger.setLevel(logging.DEBUG)

        # File handler
        log_dir = Path.home() / ".folderfresh_logs"
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / "folderfresh.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        return logger

    def _load_configuration(self) -> None:
        """Load all configuration and profiles"""
        try:
            self.logger.info("Loading configuration...")
            self.config_data = self.config.load()
            self.logger.info("Configuration loaded successfully")

            self.logger.info("Loading profiles...")
            self.profiles_doc = self.profile_store.load()
            self.logger.info("Profiles loaded successfully")

            # Get active profile
            active_id = self.profiles_doc.get("active_profile_id")
            self.active_profile = next(
                (p for p in self.profiles_doc.get("profiles", [])
                 if p["id"] == active_id),
                None
            )

            if self.active_profile:
                self.logger.info(f"Active profile: {self.active_profile.get('name')}")
            else:
                self.logger.warning("No active profile found")

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def _initialize_ui(self) -> None:
        """Initialize PySide6 UI components"""
        try:
            self.logger.info("Initializing PySide6 UI...")

            # Create QApplication
            self.qt_app = setup_qt_app()
            setup_stylesheet(self.qt_app)

            self.logger.info("PySide6 application created")

            # Create main window
            self.main_window = FolderFreshApplication()
            self._connect_ui_to_backend()

            self.logger.info("Main window created")

        except Exception as e:
            self.logger.error(f"Failed to initialize UI: {e}")
            raise

    def _connect_ui_to_backend(self) -> None:
        """Connect UI signals to backend operations"""
        self.logger.info("Connecting UI to backend...")

        # Get main window from FolderFreshApplication
        main_window = self.main_window.main_window

        # Connect main window signals
        main_window.folder_chosen.connect(self._on_folder_chosen)
        main_window.preview_requested.connect(self._on_preview_requested)
        main_window.organise_requested.connect(self._on_organise_requested)
        main_window.undo_requested.connect(self._on_undo_requested)
        main_window.profiles_requested.connect(self._on_profiles_requested)
        main_window.watched_folders_requested.connect(self._on_watched_folders_requested)
        main_window.help_requested.connect(self._on_help_requested)

        self.logger.info("UI connected to backend")

    def _initialize_watcher(self) -> None:
        """Initialize file watcher for auto-tidy"""
        try:
            self.logger.info("Initializing file watcher...")

            self.watcher_manager = WatcherManager(self.main_window)

            # Watch configured folders
            watched_folders = self.config_data.get("watched_folders", [])
            for folder_path in watched_folders:
                self.watcher_manager.watch_folder(folder_path)
                self.logger.info(f"Watching folder: {folder_path}")

            self.logger.info(f"File watcher initialized ({len(watched_folders)} folders)")

        except Exception as e:
            self.logger.error(f"Failed to initialize file watcher: {e}")
            # Don't raise - watcher is optional

    def _on_folder_chosen(self, folder_path: str) -> None:
        """Handle folder selection"""
        self.logger.info(f"Folder chosen: {folder_path}")
        log_activity(f"Selected folder: {folder_path}")

    def _on_preview_requested(self) -> None:
        """Handle preview request"""
        self.logger.info("Preview requested")
        log_activity("Preview started")

    def _on_organise_requested(self) -> None:
        """Handle organize request"""
        self.logger.info("Organize requested")
        log_activity("Organization started")

    def _on_undo_requested(self) -> None:
        """Handle undo request"""
        self.logger.info("Undo requested")
        history = UNDO_MANAGER.get_history()
        if history:
            last = history[0]
            log_activity(f"Undo: {last.get('type')} - {last.get('src')}")

    def _on_profiles_requested(self) -> None:
        """Handle profiles window request"""
        self.logger.info("Profiles window requested")

    def _on_watched_folders_requested(self) -> None:
        """Handle watched folders window request"""
        self.logger.info("Watched folders window requested")

    def _on_help_requested(self) -> None:
        """Handle help request"""
        self.logger.info("Help requested")

    def run(self) -> int:
        """Run the application"""
        try:
            # Initialize UI
            self._initialize_ui()

            # Initialize watcher
            self._initialize_watcher()

            # Show main window
            self.main_window.showNormal()
            self.logger.info("Application started successfully")
            log_activity("FolderFresh started")

            # Run event loop
            return self.qt_app.exec()

        except Exception as e:
            self.logger.critical(f"Fatal error: {e}")
            return 1

    def shutdown(self) -> None:
        """Shutdown application gracefully"""
        try:
            self.logger.info("Shutting down...")

            # Stop file watcher
            if self.watcher_manager:
                self.watcher_manager.stop_all()
                self.logger.info("File watcher stopped")

            # Save any pending state
            self.config.save(self.config_data)
            self.logger.info("Configuration saved")

            log_activity("FolderFresh closed")

            self.logger.info("=" * 60)
            self.logger.info("FolderFresh Application Closed")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def main() -> int:
    """Application entry point"""
    app = FolderFreshQtApp()

    try:
        return app.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        app.shutdown()
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        app.shutdown()
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

**Usage**:
```bash
python src/main_qt.py
```

---

### 10.2 Logging & Error Handling

**File to Create**: `src/folderfresh/logger.py`

**Features**:
- Structured logging to file and console
- Separate log levels for file (DEBUG) and console (INFO)
- Log rotation (7 days)
- Exception context logging
- Activity logging integration

**Implementation**:

```python
"""
FolderFresh Logging System
Comprehensive logging for debugging and audit trails
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


class FolderFreshLogger:
    """Central logging system for FolderFresh"""

    _instance: Optional['FolderFreshLogger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize logger singleton"""
        if self._logger is None:
            self._setup()

    def _setup(self) -> None:
        """Setup logging configuration"""
        # Create logger
        self._logger = logging.getLogger("folderfresh")
        self._logger.setLevel(logging.DEBUG)

        # Create log directory
        log_dir = Path.home() / ".folderfresh_logs"
        log_dir.mkdir(exist_ok=True, parents=True)

        # File handler with rotation
        log_file = log_dir / "folderfresh.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        """Get the logger instance"""
        return self._logger

    @classmethod
    def debug(cls, msg: str, *args, **kwargs):
        """Log debug message"""
        cls()._logger.debug(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg: str, *args, **kwargs):
        """Log info message"""
        cls()._logger.info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg: str, *args, **kwargs):
        """Log warning message"""
        cls()._logger.warning(msg, *args, **kwargs)

    @classmethod
    def error(cls, msg: str, *args, exc_info=False, **kwargs):
        """Log error message"""
        cls()._logger.error(msg, *args, exc_info=exc_info, **kwargs)

    @classmethod
    def critical(cls, msg: str, *args, exc_info=False, **kwargs):
        """Log critical error"""
        cls()._logger.critical(msg, *args, exc_info=exc_info, **kwargs)


# Convenience functions
def log_debug(msg: str, *args, **kwargs):
    FolderFreshLogger.debug(msg, *args, **kwargs)

def log_info(msg: str, *args, **kwargs):
    FolderFreshLogger.info(msg, *args, **kwargs)

def log_warning(msg: str, *args, **kwargs):
    FolderFreshLogger.warning(msg, *args, **kwargs)

def log_error(msg: str, *args, exc_info=False, **kwargs):
    FolderFreshLogger.error(msg, *args, exc_info=exc_info, **kwargs)

def log_critical(msg: str, *args, exc_info=False, **kwargs):
    FolderFreshLogger.critical(msg, *args, exc_info=exc_info, **kwargs)
```

**Usage**:
```python
from folderfresh.logger import log_info, log_error

log_info("Application started")
try:
    # code
except Exception as e:
    log_error("Operation failed", exc_info=True)
```

---

### 10.3 Application Lifecycle Management

**File Update**: `src/main_qt.py` (already included above)

**Shutdown Sequence**:
1. Stop file watcher (stop observing folders)
2. Save pending configuration
3. Flush activity log
4. Log shutdown event
5. Close database connections (if any)
6. Exit event loop

**Signal Handling**:
```python
import signal

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    app.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

---

### 10.4 Error Recovery

**File to Create**: `src/folderfresh/error_handler.py`

```python
"""
FolderFresh Error Handling & Recovery
Graceful error recovery and user-friendly error reporting
"""

from typing import Callable, Optional
from PySide6.QtWidgets import QMessageBox


class ErrorHandler:
    """Centralized error handling and recovery"""

    @staticmethod
    def handle_file_operation_error(
        error: Exception,
        operation: str,
        file_path: str,
        recovery_fn: Optional[Callable] = None
    ) -> bool:
        """
        Handle file operation errors with user feedback

        Returns:
            True if user chose to retry, False otherwise
        """
        error_msg = f"Error during {operation}:\n{str(error)}"

        reply = QMessageBox.critical(
            None,
            f"{operation.capitalize()} Failed",
            error_msg,
            QMessageBox.Retry | QMessageBox.Cancel
        )

        if reply == QMessageBox.Retry and recovery_fn:
            return recovery_fn()

        return False

    @staticmethod
    def handle_rule_execution_error(
        error: Exception,
        rule_name: str
    ) -> None:
        """Handle rule execution errors"""
        QMessageBox.warning(
            None,
            "Rule Execution Failed",
            f"Rule '{rule_name}' failed:\n{str(error)}"
        )

    @staticmethod
    def handle_config_error(
        error: Exception,
        recovery_fn: Optional[Callable] = None
    ) -> bool:
        """Handle configuration loading errors"""
        reply = QMessageBox.critical(
            None,
            "Configuration Error",
            f"Failed to load configuration:\n{str(error)}\n\nTry to recover?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes and recovery_fn:
            return recovery_fn()

        return False
```

---

## Implementation Sequence

### Phase 8 Timeline
1. **Unit Tests** (8 hours)
   - MainWindow tests
   - Manager window tests
   - Widget tests

2. **Integration Tests** (6 hours)
   - Cross-window communication
   - Signal flow
   - Data binding

3. **Testing Checklist & Docs** (4 hours)
   - Manual testing checklist
   - Keyboard shortcuts
   - Context menus

### Phase 9 Timeline
1. **Backend Connections** (16 hours)
   - ProfileManager ↔ ProfileStore
   - RuleManager ↔ RuleEngine
   - WatchedFoldersWindow ↔ WatcherManager
   - ActivityLogWindow ↔ ActivityLog
   - MainWindow ↔ UndoManager

### Phase 10 Timeline
1. **Application Wrapper** (10 hours)
   - Main entry point
   - Logging system
   - Error handling
   - Lifecycle management

---

## Testing Strategy

### Automated Tests
- Unit tests for each component
- Integration tests for component interactions
- Backend integration tests

### Manual Testing
- Check all buttons and controls
- Verify all windows open correctly
- Test profile creation/deletion
- Test rule creation and execution
- Test file organization
- Test undo functionality
- Verify dark theme consistency
- Check keyboard shortcuts

### Integration Testing
- Profile changes update all related UI
- Rules execute correctly
- Files get organized as expected
- Undo reverses operations
- Activity log records events
- Auto-tidy works in watch mode

---

## Success Criteria

✅ **Phase 8**: All unit and integration tests pass, testing checklist completed
✅ **Phase 9**: All UI windows connected to backend, data flows correctly
✅ **Phase 10**: Full application launches, all features work end-to-end

---

## Next Steps

1. Create comprehensive test files (Phase 8a)
2. Implement backend connections (Phase 9a-9e)
3. Create main application wrapper (Phase 10a)
4. Add logging and error handling (Phase 10b-10d)
5. Full integration testing and manual testing

---

**Document Status**: Ready for implementation
**Last Updated**: 2025-11-29
**Total Estimated Hours**: 40-60 hours
