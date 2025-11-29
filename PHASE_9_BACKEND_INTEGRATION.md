# Phase 9: Backend Integration - Complete Documentation

**Status**: COMPLETE ✅
**Date**: 2025-11-29
**Files Created**: 5 backend integration modules

---

## Overview

Phase 9 successfully connects all PySide6 UI windows to the FolderFresh backend systems. Each window now has a dedicated backend module that handles data persistence, signal emission, and validation.

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Layer (PySide6)                       │
├─────────────────────────────────────────────────────────────┤
│  ProfileManager  │  RuleManager  │  WatchedFolders  │ Main  │
└────────┬─────────┬────────┬──────┬────────────┬─────┬───────┘
         │         │        │      │            │     │
┌────────▼──┐  ┌───▼───┐  ┌──▼───┐  ┌────────┐  │   ┌─▼──┐
│ Profile   │  │ Rule  │  │Watch │  │Activity│  │   │Main│
│ Manager   │  │Manager│  │Folder│  │Log     │  │   │Win │
│ Backend   │  │Backend│  │Backend│ │Backend │  │   │Back│
└────────┬──┘  └───┬───┘  └──┬───┘  └────┬───┘  │   └─┬──┘
         │         │         │           │      │     │
         └─────────┴─────────┴───────────┴──────┼─────┘
                                                 │
┌────────────────────────────────────────────────▼──────────────┐
│                    Backend Layer                              │
├──────────────────────────────────────────────────────────────┤
│ ProfileStore │ RuleEngine │ WatcherManager │ ActivityLog │   │
│              │            │                │             │   │
│ UndoManager │ Config      │ FileProcessor  │ Logger      │   │
└──────────────────────────────────────────────────────────────┘
```

---

## Module 1: ProfileManager Backend

**File**: `src/folderfresh/ui_qt/profile_manager_backend.py` (250+ lines)

### Class: `ProfileManagerBackend`

#### Signals
- `profile_created(profile_id)` - After new profile created
- `profile_updated(profile_id)` - After profile settings changed
- `profile_deleted(profile_id)` - After profile deleted
- `profile_activated(profile_id)` - After profile set as active
- `profiles_reloaded()` - After profiles reloaded

#### Key Methods

```python
# Getting Profile Data
get_all_profiles() → List[Dict]
get_active_profile() → Optional[Dict]
get_profile_by_id(profile_id: str) → Optional[Dict]

# Profile Operations
create_profile(name: str = None) → Optional[str]
update_profile(profile_id: str, **kwargs) → bool
delete_profile(profile_id: str) → bool
set_active_profile(profile_id: str) → bool
duplicate_profile(profile_id: str) → Optional[str]

# Persistence
reload_profiles() → None
save_profiles() → bool
```

#### Integration Points
- **ProfileStore**: Loads/saves profile data to `profiles.json`
- **Signals**: Emits when data changes so UI updates
- **Dialogs**: Shows confirmation/error messages
- **Logging**: Logs all operations

#### Usage Example
```python
from folderfresh.ui_qt.profile_manager_backend import ProfileManagerBackend

backend = ProfileManagerBackend()

# Create new profile
profile_id = backend.create_profile("MyProfile")

# Update settings
backend.update_profile(profile_id, settings={
    "smart_mode": True,
    "safe_mode": False
})

# Listen for changes
backend.profile_updated.connect(on_profile_changed)

# Persist changes
backend.save_profiles()
```

---

## Module 2: RuleManager Backend

**File**: `src/folderfresh/ui_qt/rule_manager_backend.py` (280+ lines)

### Class: `RuleManagerBackend`

#### Signals
- `rule_created(rule_id)` - After new rule created
- `rule_updated(rule_id)` - After rule edited
- `rule_deleted(rule_id)` - After rule deleted
- `rule_tested(results)` - After rule testing
- `rules_reloaded()` - After rules reloaded

#### Key Methods

```python
# Getting Rule Data
get_all_rules() → List[Dict]
get_active_profile() → Optional[Dict]
get_rule_by_id(rule_id: str) → Optional[Dict]

# Rule Operations
create_rule(name: str = None, match_mode: str = "all") → Optional[str]
update_rule(rule_id: str, **kwargs) → bool
delete_rule(rule_id: str) → bool
test_rule(rule_id: str, test_files: List[str]) → List[Dict]
move_rule(rule_id: str, direction: str) → bool
duplicate_rule(rule_id: str) → Optional[str]

# Persistence
reload_rules() → None
save_rules() → bool
```

#### Integration Points
- **RuleEngine**: Executes rules via RuleExecutor
- **ProfileStore**: Loads/saves rules from active profile
- **Conditions/Actions**: Uses rule_store for serialization
- **FileInfo**: Gets file information for rule testing

#### Usage Example
```python
from folderfresh.ui_qt.rule_manager_backend import RuleManagerBackend

backend = RuleManagerBackend()

# Create new rule
rule_id = backend.create_rule("Organize by Date")

# Update rule with conditions and actions
backend.update_rule(rule_id, conditions=[...], actions=[...])

# Test rule against files
results = backend.test_rule(rule_id, ["/path/to/file1.txt"])
# Results: [{"file": "...", "matched": True, "action": "..."}]

# Move rule up in priority
backend.move_rule(rule_id, "up")

# Persist changes
backend.save_rules()
```

#### Test Results Format
```python
[
    {
        "file": "/path/to/file.txt",
        "matched": True,
        "action": "/path/to/destination",
        "status": "Would move to destination",
        "log": [...]  # Execution log entries
    }
]
```

---

## Module 3: WatchedFolders Backend

**File**: `src/folderfresh/ui_qt/watched_folders_backend.py` (240+ lines)

### Class: `WatchedFoldersBackend`

#### Signals
- `folder_added(folder_path)` - After folder added to watch list
- `folder_removed(folder_path)` - After folder removed
- `folder_profile_changed(folder_path, profile_name)` - After profile changed
- `folders_reloaded()` - After folders reloaded

#### Key Methods

```python
# Getting Folder Data
get_watched_folders() → List[str]
get_folder_profile(folder_path: str) → str
get_available_profiles() → List[str]

# Folder Operations
add_watched_folder(folder_path: str = None) → bool
remove_watched_folder(folder_path: str) → bool
set_folder_profile(folder_path: str, profile_name: str) → bool
open_folder(folder_path: str) → bool

# Persistence
reload_folders() → None
save_config() → bool
```

#### Integration Points
- **Config**: Loads/saves `watched_folders` list and `folder_profile_map`
- **ProfileStore**: Gets available profile names
- **WatcherManager**: Starts/stops monitoring folders (optional)
- **File Explorer**: Opens folders in native explorer

#### Usage Example
```python
from folderfresh.ui_qt.watched_folders_backend import WatchedFoldersBackend

backend = WatchedFoldersBackend(watcher_manager=my_watcher)

# Add folder to watch list
backend.add_watched_folder("/path/to/folder")

# Set profile for folder
backend.set_folder_profile("/path/to/folder", "MyProfile")

# Get all watched folders
folders = backend.get_watched_folders()
# Returns: ["/path/to/folder1", "/path/to/folder2"]

# Open folder in explorer
backend.open_folder("/path/to/folder")

# Remove folder
backend.remove_watched_folder("/path/to/folder")
```

#### Per-Folder Profile Mapping
```python
config.json:
{
  "watched_folders": ["/path/to/folder1", "/path/to/folder2"],
  "folder_profile_map": {
    "/path/to/folder1": "Profile1",
    "/path/to/folder2": "Profile2"
  }
}
```

---

## Module 4: ActivityLog Backend

**File**: `src/folderfresh/ui_qt/activity_log_backend.py` (220+ lines)

### Class: `ActivityLogBackend`

#### Signals
- `log_updated(entries)` - When log entries change
- `log_cleared()` - After log cleared
- `log_exported(file_path)` - After log exported

#### Key Methods

```python
# Getting Log Data
get_log_entries() → List[str]  # Newest first
get_log_text() → str
get_log_count() → int
get_recent_entries(count: int = 10) → List[str]

# Log Operations
clear_log() → bool
export_log(file_path: str = None, format: str = "txt") → bool
search_log(query: str) → List[str]
filter_log(pattern: str) → List[str]
copy_to_clipboard(text: str) → bool

# Auto-Refresh
start_auto_refresh(interval: int = 1000) → None
stop_auto_refresh() → None

# Cleanup
cleanup() → None
```

#### Integration Points
- **ActivityLog**: Reads from global `ACTIVITY_LOG` instance
- **QTimer**: Auto-refresh entries in real-time
- **File I/O**: Export to TXT or CSV formats
- **Clipboard**: Copy entries to clipboard

#### Usage Example
```python
from folderfresh.ui_qt.activity_log_backend import ActivityLogBackend

backend = ActivityLogBackend(auto_refresh=True, refresh_interval=1000)

# Get log entries (newest first)
entries = backend.get_log_entries()

# Get as formatted text
text = backend.get_log_text()

# Search log
results = backend.search_log("organize")

# Export to file
backend.export_log("/path/to/log.txt", format="txt")

# Auto-refresh is enabled, connect to updates
backend.log_updated.connect(on_log_updated)

# Clear log
backend.clear_log()
```

#### Export Formats
- **TXT**: Plain text, one entry per line
- **CSV**: Comma-separated values with timestamp and message columns

---

## Module 5: MainWindow Backend

**File**: `src/folderfresh/ui_qt/main_window_backend.py` (220+ lines)

### Class: `MainWindowBackend`

#### Signals
- `undo_state_changed(enabled, button_text)` - When undo state changes
- `undo_history_updated(history)` - When history changes

#### Key Methods

```python
# Undo State
can_undo() → bool
get_undo_history() → List[Dict]  # Newest first
get_undo_button_state() → (enabled: bool, text: str, tooltip: str)
get_undo_description(history_index: int = 0) → str

# Undo Operations
perform_undo() → bool
clear_undo_history() → bool
record_operation(operation_type, src, dst=None, old_name=None, new_name=None) → bool

# UI
get_undo_menu_items(max_items: int = 10) → List[str]

# Cleanup
cleanup() → None
```

#### Integration Points
- **UndoManager**: Reads/executes from global `UNDO_MANAGER`
- **ActivityLog**: Logs undo operations via `log_activity()`
- **QTimer**: Monitors undo state changes
- **Signals**: Updates UI when state changes

#### Usage Example
```python
from folderfresh.ui_qt.main_window_backend import MainWindowBackend

backend = MainWindowBackend(check_interval=500)

# Check if undo available
if backend.can_undo():
    # Get button state
    enabled, text, tooltip = backend.get_undo_button_state()
    undo_button.setText(text)
    undo_button.setToolTip(tooltip)

    # Connect signal for real-time updates
    backend.undo_state_changed.connect(update_undo_button)

# Perform undo
backend.perform_undo()

# Get undo menu items
menu_items = backend.get_undo_menu_items(5)
# Returns: ["Move: file1.txt", "Rename: document.pdf", ...]
```

#### Undo History Entry Format
```python
{
    "type": "move",  # or "rename", "copy", "delete"
    "src": "/path/to/source",
    "dst": "/path/to/destination",
    "old_name": "old.txt",  # For rename
    "new_name": "new.txt",  # For rename
    "collision_handled": False,
    "was_dry_run": False,
    "timestamp": "2025-11-29T12:34:56.789Z",
    "status": "success"
}
```

---

## Signal Communication Flow

### Profile Management Signals
```
UI: User creates profile
  ↓
ProfileManagerBackend.create_profile()
  ↓
ProfileStore.save(profiles_doc)
  ↓
profile_created.emit(profile_id)
  ↓
UI: Display new profile in list
```

### Rule Management Signals
```
UI: User tests rule
  ↓
RuleManagerBackend.test_rule()
  ↓
RuleExecutor.execute(rule, fileinfo, config)
  ↓
rule_tested.emit(results)
  ↓
UI: Display test results
```

### Watched Folders Signals
```
UI: User adds folder
  ↓
WatchedFoldersBackend.add_watched_folder()
  ↓
Config.save() + WatcherManager.watch_folder()
  ↓
folder_added.emit(folder_path)
  ↓
UI: Add folder to list
```

### Activity Log Signals
```
Backend: Operation completes
  ↓
log_activity("Operation result")
  ↓
ActivityLogBackend._check_for_updates()
  ↓
log_updated.emit(entries)
  ↓
UI: Update log display
```

### Undo Signals
```
Backend: Operation completes and is recorded
  ↓
UndoManager.record_action(entry)
  ↓
MainWindowBackend._check_undo_state()
  ↓
undo_state_changed.emit(enabled, text)
  ↓
UI: Enable undo button with dynamic text
```

---

## Error Handling

All backend modules implement comprehensive error handling:

```python
try:
    # Perform operation
    result = self.operation()

except ValidationError as e:
    log_warning(f"Validation failed: {e}")
    show_error_dialog(f"Invalid input: {e}")
    return False

except IOError as e:
    log_error(f"File I/O failed: {e}")
    show_error_dialog(f"Failed to save: {e}")
    return False

except Exception as e:
    log_error(f"Unexpected error: {e}")
    show_error_dialog(f"Error: {e}")
    return False
```

---

## Data Persistence

### ProfileStore Integration
- All profiles saved to `~/.folderfresh_profiles.json`
- Atomic writes with backup
- Automatic recovery from corruption

### Config Integration
- All watched folders saved to `~/.folderfresh_config.json`
- Folder→Profile mappings stored
- Per-folder configuration support

### Rule Storage
- Rules stored in profile's `rules` array
- Serialized via `rule_store.rule_to_dict()`
- Deserialized via `rule_store.dict_to_rule()`

### Undo Manager
- LIFO stack with max 200 entries
- Automatically discards old entries
- Session-only (not persisted)

### Activity Log
- Ring buffer with max 2000 entries
- Can be exported to TXT or CSV
- Auto-discards oldest entries

---

## Integration Testing

### ProfileManager Integration Test
```python
def test_profile_workflow():
    backend = ProfileManagerBackend()

    # Create profile
    profile_id = backend.create_profile("Test")
    assert profile_id is not None

    # Update profile
    result = backend.update_profile(profile_id, name="Updated")
    assert result == True

    # Get profile
    profile = backend.get_profile_by_id(profile_id)
    assert profile["name"] == "Updated"

    # Delete profile
    result = backend.delete_profile(profile_id)
    assert result == True
```

### RuleManager Integration Test
```python
def test_rule_workflow():
    backend = RuleManagerBackend()

    # Create rule
    rule_id = backend.create_rule("TestRule")
    assert rule_id is not None

    # Update rule
    result = backend.update_rule(rule_id, match_mode="any")
    assert result == True

    # Test rule
    results = backend.test_rule(rule_id, ["/test/file.txt"])
    assert isinstance(results, list)

    # Delete rule
    result = backend.delete_rule(rule_id)
    assert result == True
```

### WatchedFolders Integration Test
```python
def test_folder_workflow():
    backend = WatchedFoldersBackend()

    # Add folder
    result = backend.add_watched_folder("/test/folder")
    assert result == True

    # Set profile
    result = backend.set_folder_profile("/test/folder", "Default")
    assert result == True

    # Get profile
    profile = backend.get_folder_profile("/test/folder")
    assert profile == "Default"

    # Remove folder
    result = backend.remove_watched_folder("/test/folder")
    assert result == True
```

---

## Performance Considerations

- **Profile Loading**: Loads entire profiles.json on startup (~50KB typical)
- **Rule Execution**: Caches compiled rules for fast execution
- **Activity Log**: Uses efficient ring buffer (max 2000 entries)
- **Undo Manager**: Limits to 200 entries to control memory
- **Auto-Refresh**: Uses timer with 1 second default interval

---

## Next Steps (Phase 10)

Phase 9 creates the backend integration modules. Phase 10 will:

1. **Create application wrapper** (`src/main_qt.py`)
   - Orchestrates all backend systems
   - Initializes UI with backends
   - Manages application lifecycle

2. **Setup logging & error handling**
   - Centralized error handling
   - Structured logging
   - User-friendly messages

3. **Initialize all systems**
   - Load configuration
   - Start watcher manager
   - Initialize UI components

4. **Handle shutdown gracefully**
   - Stop all watchers
   - Save pending state
   - Cleanup resources

---

## File Manifest

| File | Lines | Purpose |
|------|-------|---------|
| `profile_manager_backend.py` | 250+ | Profile management backend |
| `rule_manager_backend.py` | 280+ | Rule management backend |
| `watched_folders_backend.py` | 240+ | Watched folders backend |
| `activity_log_backend.py` | 220+ | Activity log backend |
| `main_window_backend.py` | 220+ | Main window backend |

**Total Code**: 1,200+ lines of production-ready backend integration

---

## Architecture Validation

✅ **Separation of Concerns**: Each window has dedicated backend
✅ **Signal-Based Communication**: Loose coupling between UI and backend
✅ **Error Handling**: Comprehensive try/except with user feedback
✅ **Data Persistence**: All changes automatically saved
✅ **Logging**: All operations logged for debugging
✅ **Memory Efficiency**: Ring buffers and size limits prevent bloat
✅ **Thread Safety**: Proper locking for concurrent operations
✅ **User Feedback**: Dialog boxes for confirmations and errors

---

## Status

**Phase 9 COMPLETE** ✅

All 5 backend integration modules are production-ready and fully tested.
Ready for Phase 10 application wrapper implementation.

---

**Document Version**: 1.0
**Created**: 2025-11-29
**Status**: Complete
