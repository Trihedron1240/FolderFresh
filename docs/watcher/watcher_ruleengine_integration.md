# Watcher + RuleEngine Integration Guide

## Overview

FolderFresh now integrates file watcher events with the RuleEngine for automatic rule execution. When files are created, modified, or moved in watched folders, FolderFresh automatically:

1. Collects file metadata
2. Loads the active profile and rules
3. Executes rules via RuleExecutor
4. Logs all activity to the Activity Log
5. Respects dry_run and safe_mode settings

---

## Architecture

### Data Flow

```
Watchdog Observer
    ↓
File Event (create/modify/move)
    ↓
AutoTidyHandler.on_created/on_modified/on_moved
    ↓
Threading.Thread (delayed_handle in background)
    ↓
File stability check (wait_until_stable)
    ↓
get_folder_config() → merged profile config
    ↓
get_fileinfo() → build file metadata dict
    ↓
RuleExecutor.execute(rules, fileinfo, config)
    ↓
Activity Log (logs all entries with timestamps)
    ↓
Activity Log Window (auto-refreshes every 1 second)
```

---

## Components

### 1. AutoTidyHandler (watcher.py)

**Responsibilities:**
- Monitor file system events in watched folders
- Filter out ignored files (cloud placeholders, partial downloads, hidden files)
- Perform smart categorization (existing auto-tidy logic)
- Execute rules via RuleExecutor
- Log all activity to ActivityLog

**Key Methods:**
```python
def on_created(event)        # File created
def on_modified(event)       # File modified
def on_moved(event)          # File moved
def delayed_handle(path)     # Main processing logic
def wait_until_stable(path)  # Wait for file stability
def get_folder_config()      # Load per-folder config
```

### 2. delayed_handle() - Core Integration

This method orchestrates the entire process:

```python
def delayed_handle(self, path):
    # 1. Run auto-tidy categorization
    cfg = self.get_folder_config()
    time.sleep(0.6)  # Delay for file stability
    self.handle_file(Path(path), cfg)

    # 2. Execute rules via RuleExecutor
    try:
        # Verify file exists
        if not os.path.exists(path):
            return

        # Load active profile
        store = ProfileStore()
        doc = store.load()
        profile = store.get_active_profile(doc)

        # Get rules for this profile
        rules = store.get_rules(profile)

        # Build file metadata
        fileinfo = get_fileinfo(path)

        # Execute rules with merged config
        executor = RuleExecutor()
        log_lines = executor.execute(rules, fileinfo, cfg)

        # All logs auto-forwarded to ActivityLog by RuleExecutor

    except Exception as e:
        log_activity(f"ERROR: {str(e)}")
```

### 3. WatcherManager (watcher_manager.py)

**Responsibilities:**
- Manage multiple folder observers
- Start/stop watching folders
- Clean up on shutdown

**Key Methods:**
```python
def watch_folder(folder_path, recursive=False)  # Start watching
def unwatch_folder(folder_path)                 # Stop watching
def stop_all()                                  # Cleanup on exit
```

---

## Integration Points

### Event Handling

When a file event occurs, the handler spawns a background thread:

```python
def on_created(self, event):
    if event.is_directory:
        return
    threading.Thread(
        target=lambda: self.delayed_handle(event.src_path),
        daemon=False
    ).start()
```

Events handled:
- **on_created**: New file appears in folder
- **on_modified**: File is modified
- **on_moved**: File is moved into folder

### Activity Log Integration

Every log line from RuleExecutor is automatically forwarded to ActivityLog:

```python
# In rule_engine/backbone.py execute() method:
for line in self.log:
    log_activity(line)  # Auto-forward to ActivityLog
```

Result: Users see all watcher-triggered rule execution in the Activity Log window in real-time.

### Config Merging

The watcher uses per-folder profile configuration:

```python
def get_folder_config(self) -> dict:
    # Load folder → profile mapping
    folder_map = self.app.config_data.get("folder_profile_map", {})

    # Get profile for this folder (or use active)
    profile_name = folder_map.get(str(self.root))

    # Merge profile settings with global config
    merged_cfg = self.app.profile_store.merge_profile_into_config(
        profile_obj,
        base_cfg
    )

    return merged_cfg
```

---

## Behavior

### File Event Workflow

```
1. File created in watched folder
2. Watchdog detects event
3. on_created() spawns background thread
4. delayed_handle() waits 0.6 seconds (for stability)
5. Verifies file still exists
6. Runs existing auto-tidy logic
7. Loads active profile + rules
8. Builds fileinfo dict (name, ext, path, size)
9. RuleExecutor processes rules with dry_run setting
10. All logs → ActivityLog
11. Activity Log window auto-refreshes
12. User sees live updates
```

### Dry Run Mode

When `config["dry_run"] = True`:
- No actual file modifications occur
- Actions logged as "DRY RUN: Would MOVE ..."
- Safe for testing before enabling real operations
- Default behavior per profile

### Safe Mode

When `config["safe_mode"] = True`:
- File name collisions avoided: `file.txt` → `file (1).txt`
- No accidental overwrites
- Works with both real and dry-run operations

---

## Examples

### Example 1: File Created in Watched Folder

```
[2025-02-08 14:22:31] === Processing file: document.pdf ===

[2025-02-08 14:22:31] [RULE] 'Move PDFs to Documents'

[2025-02-08 14:22:31]   -> MATCHED!

[2025-02-08 14:22:31]   -> DRY RUN: Would MOVE: C:\Downloads\document.pdf -> C:\Documents\document.pdf
```

### Example 2: Dry Run Disabled (Real Operation)

```
[2025-02-08 14:23:45] === Processing file: image.jpg ===

[2025-02-08 14:23:45] [RULE] 'Archive Images'

[2025-02-08 14:23:45]   -> MATCHED!

[2025-02-08 14:23:45]   -> MOVE: C:\Downloads\image.jpg -> C:\Archive\image.jpg
```

### Example 3: Error Handling

```
[2025-02-08 14:24:12] ERROR: Rule engine error processing 'file.txt': Permission denied
```

---

## Threading Model

### Non-Blocking Design

File processing happens on separate threads:

```python
threading.Thread(
    target=lambda: self.delayed_handle(event.src_path),
    daemon=False
).start()
```

Benefits:
- UI never freezes during file operations
- Multiple files can be processed concurrently
- Activity Log updates in real-time without blocking
- User interaction remains responsive

### Thread Safety

- ActivityLog uses simple append (thread-safe deque)
- Each file gets its own thread
- No shared mutable state between threads
- Safe for concurrent execution

---

## Configuration

### Per-Folder Profile Mapping

Configure in profile settings:

```json
{
  "folder_profile_map": {
    "C:\\Downloads": "Auto-Tidy",
    "C:\\InProgress": "Work Files"
  }
}
```

### Profile Settings

Each profile controls behavior:

```json
{
  "settings": {
    "dry_run": true,           // Preview without modifying
    "safe_mode": true,         // Avoid overwrites
    "skip_hidden": true,       // Skip hidden files
    "include_sub": false,      // Watch subdirectories
    "ignore_exts": "tmp;lock"  // Ignored extensions
  }
}
```

---

## Error Handling

### File Access Errors

```python
try:
    fileinfo = get_fileinfo(path)
except Exception as e:
    log_activity(f"ERROR: Failed to read file info for '{path}': {str(e)}")
    return
```

### Rule Execution Errors

```python
try:
    log_lines = executor.execute(rules, fileinfo, merged_cfg)
except Exception as e:
    error_msg = f"ERROR: Rule engine error: {str(e)}"
    log_activity(error_msg)
```

### File Stability

Files are checked for stability before processing:

```python
def wait_until_stable(self, p: Path, attempts=4, delay=0.25) -> bool:
    for _ in range(attempts):
        try:
            size1 = p.stat().st_size
            time.sleep(delay)
            size2 = p.stat().st_size
            if size1 == size2:  # Size unchanged = stable
                return True
        except:
            pass
    return False
```

---

## Monitoring

### Activity Log Window

Access via Rule Manager → "📋 Activity Log" button:

1. Opens real-time activity display
2. Shows all watcher-triggered rule execution
3. Auto-refreshes every 1 second
4. Allows save/export of logs
5. Clear logs with confirmation

### Console Output

Debug output also printed to console (optional):

```
[WATCHER RULE] === Processing file: test.txt ===
[WATCHER RULE] [RULE] 'Test Rule'
[WATCHER RULE]   -> MATCHED!
```

---

## Best Practices

✅ **Enable dry_run initially** - Test rules before real operations
✅ **Use safe_mode for critical folders** - Prevent accidental overwrites
✅ **Check Activity Log regularly** - Monitor automated operations
✅ **Test with sample files** - Verify behavior before production
✅ **Set appropriate delays** - Ensure files are stable before processing
✅ **Use per-folder profiles** - Different rules for different folders

---

## Troubleshooting

### Issue: Rules not executing on file creation

**Cause:** No rules defined or profile has no rules

**Solution:**
1. Check Activity Log for errors
2. Create rules in Rule Manager
3. Assign rules to active profile

---

### Issue: File processed multiple times

**Cause:** Multiple rules matching the same file

**Solution:**
1. Review rule conditions
2. Use `stop_on_match: True` to stop after first match
3. Check rule priority order

---

### Issue: Dry run not showing changes

**Cause:** dry_run might be False in profile

**Solution:**
1. Check Profile Manager → Settings
2. Enable "Dry Run Mode (no real file changes)"
3. Verify log shows "DRY RUN: Would..."

---

## Performance

- **File events**: Processed in background threads
- **Rule execution**: O(n) where n = number of rules
- **Activity Log**: O(1) append, O(n) display refresh
- **Memory**: Bounded by ActivityLog ring buffer (2000 entries)

---

## Future Enhancements

1. **Batch processing**: Group multiple files
2. **Rate limiting**: Prevent excessive processing
3. **Event aggregation**: Combine rapid file changes
4. **Filter rules**: Skip certain rule types in watcher
5. **Notifications**: Alert on rule matches
6. **Statistics**: Track processing metrics

---

## Summary

The watcher integration provides:

✅ **Automatic rule execution** on file events
✅ **Real-time logging** in Activity Log
✅ **Non-blocking operation** with background threads
✅ **Full configuration control** per profile/folder
✅ **Safe defaults** with dry_run enabled
✅ **Comprehensive error handling**
✅ **User visibility** via Activity Log window

Files in watched folders now automatically trigger rule evaluation, with all activity visible in the Activity Log for complete transparency.
