# FolderFresh PySide6 - Quick Reference Guide

## 🚀 Getting Started

### Launch Application
```bash
python src/main_qt_app.py
```

### Check Logs
```bash
# Linux/macOS
tail -f ~/.folderfresh/logs/folderfresh.log

# Windows
%APPDATA%\Local\FolderFresh\logs\folderfresh.log
```

### Run Tests
```bash
pytest tests/ -v
```

---

## 📁 Project Structure

```
FolderFresh/
├── src/
│   ├── main_qt_app.py              # Main entry point
│   └── folderfresh/
│       ├── logger_qt.py            # Logging system
│       ├── error_handler_qt.py      # Error handling
│       └── ui_qt/
│           ├── *_backend.py        # 5 backend modules
│           ├── main_window.py       # Main UI
│           ├── application.py       # App wrapper
│           └── styles.py            # Design tokens
├── tests/
│   ├── test_ui_qt_windows.py       # Window tests
│   ├── test_ui_qt_base_widgets.py  # Widget tests
│   └── test_ui_qt_integration.py    # Integration tests
└── docs/
    ├── PHASES_8_10_COMPLETION_SUMMARY.md
    ├── PHASE_9_BACKEND_INTEGRATION.md
    ├── PHASE_10_APPLICATION_WRAPPER.md
    └── MANUAL_TESTING_CHECKLIST.md
```

---

## 🔧 Backend Integration Modules

### ProfileManager Backend
```python
from folderfresh.ui_qt.profile_manager_backend import ProfileManagerBackend

backend = ProfileManagerBackend()
profile_id = backend.create_profile("MyProfile")
backend.update_profile(profile_id, name="Updated")
backend.delete_profile(profile_id)
```

### RuleManager Backend
```python
from folderfresh.ui_qt.rule_manager_backend import RuleManagerBackend

backend = RuleManagerBackend()
rule_id = backend.create_rule("TestRule")
results = backend.test_rule(rule_id, ["/test/file.txt"])
backend.delete_rule(rule_id)
```

### WatchedFolders Backend
```python
from folderfresh.ui_qt.watched_folders_backend import WatchedFoldersBackend

backend = WatchedFoldersBackend(watcher_manager)
backend.add_watched_folder("/test/folder")
backend.set_folder_profile("/test/folder", "Default")
backend.remove_watched_folder("/test/folder")
```

### ActivityLog Backend
```python
from folderfresh.ui_qt.activity_log_backend import ActivityLogBackend

backend = ActivityLogBackend(auto_refresh=True)
entries = backend.get_log_entries()
backend.export_log("/path/to/log.txt", format="txt")
backend.clear_log()
```

### MainWindow Backend
```python
from folderfresh.ui_qt.main_window_backend import MainWindowBackend

backend = MainWindowBackend()
if backend.can_undo():
    backend.perform_undo()
history = backend.get_undo_history()
```

---

## 📝 Logging

### Basic Logging
```python
from folderfresh.logger_qt import log_info, log_error

log_info("Operation started")
try:
    # operation
except Exception as e:
    log_error("Operation failed", exc_info=True)
```

### Logger Configuration
```python
from folderfresh.logger_qt import QtLogger

logger = QtLogger("folderfresh")
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message", exc_info=False)
```

---

## ⚠️ Error Handling

### Basic Error Handling
```python
from folderfresh.error_handler_qt import QtErrorHandler

try:
    # operation
except Exception as e:
    QtErrorHandler.handle_file_operation_error(
        e, "organize", "/path/to/file", parent=window
    )
```

### Error Types
```python
# File operations
QtErrorHandler.handle_file_operation_error(error, "move", path)

# Rule execution
QtErrorHandler.handle_rule_execution_error(error, "MyRule")

# Configuration
QtErrorHandler.handle_config_error(error)

# Folder watching
QtErrorHandler.handle_folder_watch_error(error, path)

# Fatal errors
QtErrorHandler.handle_fatal_error(error)
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_ui_qt_windows.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src/folderfresh/ui_qt --cov-report=html
```

### Run Specific Test
```bash
pytest tests/test_ui_qt_windows.py::TestMainWindowInitialization::test_main_window_creates_without_error -v
```

---

## 📊 Test Coverage

| Component | Tests | File |
|-----------|-------|------|
| MainWindow | 20+ | test_ui_qt_windows.py |
| Windows (All) | 40+ | test_ui_qt_windows.py |
| Base Widgets | 50+ | test_ui_qt_base_widgets.py |
| Integration | 20+ | test_ui_qt_integration.py |
| Manual | 180+ | MANUAL_TESTING_CHECKLIST.md |

---

## 📋 Manual Testing

### Quick Test Checklist
```
[ ] Application launches without errors
[ ] All buttons are visible and clickable
[ ] All checkboxes are functional
[ ] Folder selection works
[ ] Preview shows results
[ ] Dark theme applied consistently
[ ] No white space visible
[ ] Text is readable
[ ] Window can be resized
[ ] Application can be closed gracefully
```

### Full Checklist
See `MANUAL_TESTING_CHECKLIST.md` (180+ test cases)

---

## 🔗 Signal Examples

### Connect Signals
```python
from folderfresh.ui_qt.profile_manager_backend import ProfileManagerBackend

backend = ProfileManagerBackend()

# Connect to signals
backend.profile_created.connect(lambda pid: print(f"Profile created: {pid}"))
backend.profile_updated.connect(lambda pid: print(f"Profile updated: {pid}"))
backend.profile_deleted.connect(lambda pid: print(f"Profile deleted: {pid}"))
```

### Signal List
```python
# ProfileManager
profile_created(profile_id)
profile_updated(profile_id)
profile_deleted(profile_id)
profile_activated(profile_id)
profiles_reloaded()

# RuleManager
rule_created(rule_id)
rule_updated(rule_id)
rule_deleted(rule_id)
rule_tested(results)
rules_reloaded()

# WatchedFolders
folder_added(folder_path)
folder_removed(folder_path)
folder_profile_changed(folder_path, profile_name)
folders_reloaded()

# ActivityLog
log_updated(entries)
log_cleared()
log_exported(file_path)

# MainWindow
undo_state_changed(enabled, button_text)
undo_history_updated(history)
```

---

## 🐛 Debugging

### Check Log File
```bash
# Show last 100 lines
tail -100 ~/.folderfresh/logs/folderfresh.log

# Search for errors
grep ERROR ~/.folderfresh/logs/folderfresh.log

# Follow log in real-time
tail -f ~/.folderfresh/logs/folderfresh.log
```

### Debug Mode
```python
import logging
from folderfresh.logger_qt import get_logger

logger = get_logger()
logger.setLevel(logging.DEBUG)  # Show all messages including DEBUG
```

### Test a Single Component
```python
from folderfresh.ui_qt.profile_manager_backend import ProfileManagerBackend

backend = ProfileManagerBackend()
print(backend.get_all_profiles())  # Check what profiles exist
```

---

## 📦 Dependencies

### Required
- PySide6 >= 6.0
- Python >= 3.9

### Development
- pytest >= 7.0
- pytest-cov >= 4.0

### Optional
- black (code formatting)
- mypy (type checking)
- flake8 (linting)

---

## 🎯 Common Tasks

### Add New Profile
```python
backend = ProfileManagerBackend()
profile_id = backend.create_profile("NewProfile")
```

### Test a Rule
```python
backend = RuleManagerBackend()
results = backend.test_rule(rule_id, ["/test/file.txt"])
for result in results:
    print(f"{result['file']}: {result['action']}")
```

### Watch a Folder
```python
backend = WatchedFoldersBackend(watcher_manager)
backend.add_watched_folder("/home/user/Downloads")
```

### Export Activity Log
```python
backend = ActivityLogBackend()
backend.export_log("/home/user/activity.csv", format="csv")
```

### Check Undo History
```python
backend = MainWindowBackend()
history = backend.get_undo_history()
for i, action in enumerate(history):
    print(f"{i}: {action['type']} - {action['src']}")
```

---

## 📚 Documentation Files

| File | Purpose | Size |
|------|---------|------|
| PHASES_8_10_COMPLETION_SUMMARY.md | Overall summary | 600+ lines |
| PHASE_9_BACKEND_INTEGRATION.md | Backend guide | 600+ lines |
| PHASE_10_APPLICATION_WRAPPER.md | App wrapper guide | 600+ lines |
| MANUAL_TESTING_CHECKLIST.md | QA checklist | 600+ lines |
| QUICK_REFERENCE.md | This file | 400+ lines |

---

## ❓ FAQ

**Q: How do I launch the application?**
A: `python src/main_qt_app.py`

**Q: Where are logs stored?**
A: Linux/macOS: `~/.folderfresh/logs/folderfresh.log`
   Windows: `%APPDATA%\Local\FolderFresh\logs\folderfresh.log`

**Q: How do I run tests?**
A: `pytest tests/ -v`

**Q: How do I add a new backend module?**
A: See `PHASE_9_BACKEND_INTEGRATION.md` for patterns and examples

**Q: How do I handle errors?**
A: Use `QtErrorHandler` class or `error_handler_qt` module functions

**Q: What's the main entry point?**
A: `src/main_qt_app.py` - FolderFreshQtApplication class

**Q: How does logging work?**
A: Uses `QtLogger` singleton with file + console output

**Q: Can I run tests in parallel?**
A: Yes: `pytest tests/ -v -n auto`

---

## 🔐 Security Notes

- All file operations validated before execution
- Configuration files stored in user home directory
- Logs don't contain sensitive information
- Error messages shown to user are sanitized
- Exception details logged only to file (not console)

---

## 📈 Performance

- **Startup**: ~2-3 seconds
- **Memory**: ~50-100MB typical
- **Watcher**: ~1MB per folder
- **Logs**: Auto-rotated at 10MB
- **Activity Log**: Max 2000 entries (~1MB)
- **Undo History**: Max 200 entries (~500KB)

---

## 🎓 Learning Resources

1. **For PySide6**: Read Phase 8 implementation plan
2. **For Backend**: Read Phase 9 integration guide
3. **For Architecture**: Read Phase 10 application guide
4. **For Testing**: Run tests with `-v` flag and read output
5. **For Debugging**: Check log files using tail/grep

---

**Quick Reference Version**: 1.0
**Last Updated**: 2025-11-29
**Status**: Current ✅
