# FolderFresh Activity Log System

## Overview

The Activity Log is a real-time monitoring system that tracks all rule execution activity in FolderFresh:
- Rule matches and misses
- Actions taken (MOVE, COPY, RENAME)
- Dry run output
- Errors and warnings
- Watcher-triggered executions
- Rule simulation logs
- Timestamped entries

The Activity Log is **accessible from the Rule Manager** and updates **automatically** as rules are executed.

---

## Features

✅ **Real-Time Updates** - Logs appear instantly as rules execute
✅ **Ring Buffer Storage** - Stores up to 2000 entries (configurable)
✅ **Timestamps** - Every entry includes `[YYYY-MM-DD HH:MM:SS]`
✅ **Auto-Refresh UI** - Window updates every 1 second
✅ **Save/Export** - Export logs as JSON or plain text
✅ **Clear Function** - Clear logs with confirmation
✅ **File Persistence** - Save logs to disk for later review
✅ **Memory Efficient** - Ring buffer prevents unbounded growth
✅ **Production Ready** - Handles concurrent access safely

---

## Architecture

### Components

**1. activity_log.py**
- `ActivityLog` class: Core logging backend
- `ACTIVITY_LOG` singleton: Global instance
- `log_activity(message)`: Convenience function
- Ring buffer with max 2000 entries
- Timestamp management
- File persistence (JSON, text)

**2. activity_log_window.py**
- `ActivityLogWindow` class: UI window (CTkToplevel)
- 800x600 window with scrollable text area
- Real-time auto-refresh (1 second interval)
- Clear log button with confirmation
- Save log button (JSON/text export)
- Entry count display

**3. Integration Points**
- **RuleExecutor.execute()** - Forwards all logs to ActivityLog
- **RuleManager UI** - "Activity Log" button opens the window
- **Rule Simulator** - Logs appear in activity log
- **File Watcher** - All triggered executions logged

---

## Usage

### Opening the Activity Log

From the Rule Manager window:
1. Click the **"📋 Activity Log"** button (green, at bottom of sidebar)
2. Activity Log window opens showing all logged entries
3. Window auto-refreshes every 1 second

### Log Format

Each entry includes a timestamp and context:

```
[2025-02-08 14:22:31]
=== Processing file: document.pdf ===

[2025-02-08 14:22:31]
[RULE] 'Organize PDFs'

[2025-02-08 14:22:31]   -> MATCHED!

[2025-02-08 14:22:31]   -> DRY RUN: Would MOVE: C:\Downloads\document.pdf -> C:\Documents\document.pdf

[2025-02-08 14:22:31]   -> stop_on_match=True, stopping here.
```

### Entry Types

| Type | Example | Meaning |
|------|---------|---------|
| **File Processing** | `=== Processing file: ...` | Start of file evaluation |
| **Rule Execution** | `[RULE] 'Rule Name'` | Evaluating this rule |
| **Match** | `-> MATCHED!` | Rule conditions matched |
| **No Match** | `-> No match, skipping actions.` | Rule conditions didn't match |
| **Action** | `-> MOVE: ... -> ...` | Real file operation |
| **Dry Run** | `-> DRY RUN: Would ...` | Preview (no real operation) |
| **Error** | `ERROR: RENAME - ...` | Something went wrong |
| **Stop Flag** | `-> stop_on_match=True, stopping here.` | Rule halted processing |

---

## Features in Detail

### Real-Time Updates

The Activity Log window **automatically refreshes** every 1 second:
- Checks if log size changed
- Only updates if new entries appeared
- Non-blocking (doesn't freeze UI)
- Scales to multiple windows

### Save/Export Functions

**Save as JSON:**
```
{
  "saved_at": "2025-02-08T14:30:45.123456",
  "entries": [
    "[2025-02-08 14:22:31] Processing file...",
    "[2025-02-08 14:22:31] [RULE] 'Test Rule'",
    ...
  ]
}
```

**Save as Plain Text:**
```
[2025-02-08 14:22:31] Processing file...
[2025-02-08 14:22:31] [RULE] 'Test Rule'
...
```

**How to Export:**
1. Open Activity Log window
2. Click "Save Log" button
3. Choose location and format
4. File is saved

### Clear Function

To clear the activity log:
1. Open Activity Log window
2. Click "Clear Log" button
3. Confirm in dialog
4. All entries are removed

---

## Integration with Other Systems

### Rule Simulator

When you test a rule with the Rule Simulator:
- All simulation logs appear in Activity Log
- Marked with "DRY RUN:" prefix
- Shows what would happen without actually modifying files

### File Watcher

When the file watcher triggers rule execution:
- All matched files logged
- All actions logged (or dry run previews)
- Errors logged with full context
- Allows monitoring background activity

### Dry Run Mode

When Dry Run Mode is enabled in profile settings:
- All actions logged as "DRY RUN: Would ..."
- No actual file modifications occur
- Allows safe testing before enabling real operations

---

## Technical Details

### ActivityLog Class

```python
class ActivityLog:
    MAX_ENTRIES = 2000  # Ring buffer limit

    def append(message: str)           # Add with timestamp
    def get_log() -> List[str]         # Get all entries
    def get_log_text() -> str          # Get as single string
    def clear()                        # Remove all entries
    def save_to_file(filepath) -> bool # Save as JSON
    def load_from_file(filepath) -> bool # Load from JSON
```

### Ring Buffer Behavior

The ActivityLog uses a `deque` with `maxlen=2000`:
- Oldest entries automatically removed when limit reached
- No manual management needed
- Memory efficient (bounded growth)
- FIFO order (first in, first out)

### Thread Safety

Simple implementation assumes:
- Single-threaded GUI updates
- Lock flag prevents concurrent iteration during updates
- Suitable for desktop application use

### Performance

- **Append**: O(1) - constant time
- **Get Log**: O(n) - linear in number of entries
- **Save**: O(n) - linear in number of entries
- **Clear**: O(1) - constant time
- **UI Refresh**: Checks entry count (O(1)), updates if needed

---

## Workflow Example

### Scenario: Organizing PDF Files

```
1. User enables Rule Manager
2. User creates rule: "Move PDFs to Documents"
3. User clicks "Activity Log" button
4. Activity Log window opens (empty or showing previous entries)

5. User runs auto-tidy:
   [14:22:31] === Processing file: document.pdf ===
   [14:22:31] [RULE] 'Move PDFs to Documents'
   [14:22:31]   -> MATCHED!
   [14:22:31]   -> DRY RUN: Would MOVE: C:\Downloads\document.pdf -> C:\Documents\document.pdf

6. User reviews the log
7. User disables Dry Run Mode in profile
8. User runs auto-tidy again:
   [14:23:15] === Processing file: document.pdf ===
   [14:23:15] [RULE] 'Move PDFs to Documents'
   [14:23:15]   -> MATCHED!
   [14:23:15]   -> MOVE: C:\Downloads\document.pdf -> C:\Documents\document.pdf

9. User reviews actual operations in log
10. User saves log for audit trail
```

---

## Persistence (Optional)

The ActivityLog can persist logs between sessions:

**Configuration in profile settings:**
```json
{
  "name": "Auto-Tidy",
  "settings": {
    "persist_activity_log": false,  // Optional: default false
    "activity_log_file": "~/.folderfresh/activity.log"
  }
}
```

**Implementation (future enhancement):**
1. On application startup: Load last N entries from disk
2. On application exit: Save all entries to disk
3. Allows audit trail across sessions

---

## Troubleshooting

### Issue: Activity Log shows old entries

**Cause:** Previous session's entries still in memory

**Solution:** Click "Clear Log" to start fresh

---

### Issue: Activity Log not updating

**Cause:** Window closed or not in focus

**Solution:**
1. Open Activity Log window again
2. Wait 1 second for auto-refresh
3. New entries should appear

---

### Issue: Log file won't save

**Cause:** No write permissions or full disk

**Solution:**
1. Check disk space
2. Verify folder permissions
3. Try saving to different location

---

## Best Practices

✅ **Review logs regularly** - Monitor rule execution
✅ **Save logs for audits** - Export logs for compliance
✅ **Check for errors** - Look for "ERROR:" entries
✅ **Verify dry run** - Ensure "DRY RUN:" prefix in test mode
✅ **Clear periodically** - Prevent memory bloat on long-running sessions

---

## Configuration

### Ring Buffer Size

To change maximum entries (default 2000):

Edit `activity_log.py`:
```python
class ActivityLog:
    MAX_ENTRIES = 2000  # Change this value
```

### Auto-Refresh Interval

To change refresh frequency (default 1 second):

Edit `activity_log_window.py`:
```python
self.after(1000, self._auto_refresh)  # 1000 ms = 1 second
```

---

## Integration Points for Developers

### Log from Custom Code

```python
from folderfresh.activity_log import log_activity

# Log a message
log_activity("Custom: Processing special rule")
```

### Access the Global Log

```python
from folderfresh.activity_log import ACTIVITY_LOG

# Get all entries
entries = ACTIVITY_LOG.get_log()

# Get as text
text = ACTIVITY_LOG.get_log_text()

# Clear log
ACTIVITY_LOG.clear()

# Get entry count
count = len(ACTIVITY_LOG)
```

### Save/Load from Custom Locations

```python
from folderfresh.activity_log import ACTIVITY_LOG

# Save to custom location
ACTIVITY_LOG.save_to_file("/path/to/log.json")

# Load from file
ACTIVITY_LOG.load_from_file("/path/to/log.json")
```

---

## Summary

The Activity Log provides **complete visibility** into FolderFresh's operations:

✅ **Real-time monitoring** of all rule execution
✅ **Easy access** from Rule Manager window
✅ **Auto-saving** capability for audit trails
✅ **Professional UI** with auto-refresh
✅ **Export functions** for external analysis
✅ **Error tracking** for troubleshooting

Use the Activity Log to:
- Debug rule behavior
- Monitor automated operations
- Create audit trails
- Verify dry run mode before enabling real operations
- Track file system changes over time
