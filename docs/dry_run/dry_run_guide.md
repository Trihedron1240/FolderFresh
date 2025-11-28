# FolderFresh Dry Run Mode Guide

## Overview

Dry Run Mode is a safety feature that allows users to preview what FolderFresh will do without actually modifying any files. When enabled, rules are executed but no real file operations occur.

---

## How Dry Run Mode Works

### Default Behavior
- **Dry Run Mode is ENABLED by default** for maximum safety
- Users must explicitly disable it to perform real file operations
- This prevents accidental file modifications

### What Happens in Dry Run Mode

1. **Rules are evaluated normally**
   - Conditions are checked against files
   - Matching rules are identified
   - Rule priority order is respected

2. **Actions are NOT executed**
   - No files are moved, copied, or renamed
   - Directory creation is skipped
   - File collisions are not checked on disk

3. **Logs show what WOULD happen**
   - Each action returns a preview message
   - Format: `"DRY RUN: Would ACTION: source -> destination"`
   - Users can see exactly what would be executed

---

## Configuration

### Where to Find the Setting

**Profile Manager → Basic Settings**

Look for the checkbox:
```
☑ Dry Run Mode (no real file changes)
```

### Setting Values

| Value | Behavior |
|-------|----------|
| **Checked (✓)** | Dry run enabled - no real operations |
| **Unchecked (☐)** | Real operations enabled - files modified |

### Profile-Specific Setting

Dry Run Mode is a **per-profile setting**:
- Each profile can have its own dry_run setting
- Default: Enabled (checked) for new profiles
- Persisted in `~/.folderfresh_profiles.json` under `settings.dry_run`

---

## Log Messages in Dry Run Mode

### Action Logs

All action logs are prefixed with `"DRY RUN: Would"`:

**MOVE Action:**
```
DRY RUN: Would MOVE: C:\Downloads\document.pdf -> C:\Documents
```

**COPY Action:**
```
DRY RUN: Would COPY: C:\Downloads\photo.jpg -> C:\Pictures
```

**RENAME Action:**
```
DRY RUN: Would RENAME: old_filename.txt -> new_filename.txt
```

### Error Logs

Errors still occur normally (file not found, invalid path, etc.):
```
ERROR: MOVE - source file not found or not accessible: C:\nonexistent\file.txt
```

---

## Interaction with Other Features

### Safe Mode + Dry Run

Safe Mode and Dry Run Mode work together:

| Setting | Behavior |
|---------|----------|
| Safe Mode: ON, Dry Run: ON | Preview with collision avoidance |
| Safe Mode: ON, Dry Run: OFF | Real operations with collision avoidance |
| Safe Mode: OFF, Dry Run: ON | Preview allowing overwrites |
| Safe Mode: OFF, Dry Run: OFF | Real operations allowing overwrites |

**Example with collision avoidance in dry run:**
```
DRY RUN: Would MOVE: C:\Downloads\document.pdf -> C:\Documents\document (1).pdf
```
(Collision detected and name would be adjusted)

### Rule Validation

- Dry Run Mode does NOT bypass rule validation
- Invalid rules still cannot be saved
- Validation works the same way regardless of dry_run setting

### Rule Simulator

Rule Simulator **always uses Dry Run Mode** for safety:
- Users can test rules without risk
- Simulations never modify files
- Perfect for testing before enabling real operations

---

## Workflow Examples

### Example 1: Testing Before Enabling Real Operations

```
1. Create a rule: "Organize PDFs"
2. Profile Settings: Leave Dry Run Mode CHECKED
3. Run auto-tidy or watcher
4. Review logs: "DRY RUN: Would MOVE: ..."
5. Verify the behavior looks correct
6. Profile Settings: UNCHECK Dry Run Mode
7. Run auto-tidy again
8. Rules now execute in real mode
```

### Example 2: Different Profiles with Different Settings

```
Profile A (Testing):
  - Dry Run: ON
  - Safe Mode: ON
  - Used for testing new rules

Profile B (Production):
  - Dry Run: OFF
  - Safe Mode: ON
  - Used for automated file organization
```

### Example 3: Disabling Dry Run for Specific Profile

```
1. Profile Manager → Select "Daily Cleanup" profile
2. Find "Dry Run Mode (no real file changes)"
3. UNCHECK the checkbox
4. Click "Save Changes"
5. Now rules execute with real file operations
```

---

## Technical Implementation

### Code Changes

**Configuration Structure:**
```python
settings = {
    "safe_mode": True,
    "dry_run": True,  # NEW: Dry Run Mode
    "smart_mode": False,
    "include_sub": True,
    # ... other settings
}
```

**Merged Profile Config:**
```python
merged_config = {
    "safe_mode": True,
    "dry_run": True,
    # ... includes all settings from profile
}
```

**Action Execution:**
```python
# Each action checks dry_run flag
if config.get("dry_run", False):
    return f"DRY RUN: Would {ACTION_NAME}: ..."
else:
    # Perform real operation
    perform_file_operation()
    return f"{ACTION_NAME}: ..."
```

### Default Values

- **New profiles**: `dry_run: True` (dry run enabled)
- **Merged config**: `dry_run: True` if setting not specified
- **Safe Mode**: Both features default to safe (True)

---

## Frequently Asked Questions

### Q: Why is Dry Run Mode enabled by default?
A: For maximum safety. Users must explicitly enable real operations, preventing accidental file modifications.

### Q: Can I test rules without using Dry Run Mode?
A: Yes! Use the Rule Simulator (built into RuleEditor) which always uses Dry Run Mode.

### Q: What happens to files in dry run mode?
A: Nothing. No files are moved, copied, renamed, or deleted. The filesystem remains untouched.

### Q: Are logs still accurate in dry run mode?
A: Yes. Logs show exactly what WOULD happen, including collision avoidance names.

### Q: Can I have one profile in dry run and another in real mode?
A: Yes! Each profile has its own dry_run setting. Set them independently.

### Q: How do I switch from testing to production?
A: After testing with Dry Run ON, uncheck the checkbox in Profile Settings and click Save Changes.

### Q: What if I accidentally enable real operations?
A: Look for logs like `"MOVE: source -> dest"` (without "DRY RUN:" prefix) to confirm real operations are happening.

---

## Safety Recommendations

### Best Practices

1. **Always test first**
   - Keep Dry Run Mode ON by default
   - Run rules and review logs
   - Only disable after confirming behavior

2. **Use per-profile settings**
   - Testing profile: Dry Run ON
   - Production profile: Dry Run OFF
   - Prevents accidental operations on production data

3. **Enable Safe Mode**
   - Always keep Safe Mode ON for critical data
   - Prevents file overwrites
   - Combines with Dry Run for maximum protection

4. **Review logs carefully**
   - "DRY RUN: Would..." = preview (safe)
   - "MOVE:", "COPY:", "RENAME:" = real operations
   - Check file paths are correct before enabling real mode

5. **Test with sample files**
   - Create test directories with dummy files
   - Test rules in dry run mode first
   - Only enable real operations after verification

---

## Troubleshooting

### Issue: Logs show "DRY RUN" but I expected real operations

**Cause:** Dry Run Mode is still enabled

**Solution:**
1. Profile Manager → Profile Settings
2. Uncheck "Dry Run Mode (no real file changes)"
3. Click "Save Changes"
4. Run rules again

### Issue: I want to disable Dry Run Mode for one profile

**Solution:**
1. Go to Profile Manager
2. Select the profile
3. Uncheck the Dry Run Mode checkbox
4. Click "Save Changes"
5. Other profiles retain their settings

### Issue: I accidentally enabled real operations on the wrong profile

**Solution:**
1. Check the logs to see what operations ran
2. Manually fix any affected files (if needed)
3. Re-enable Dry Run Mode for that profile
4. Profile Manager → uncheck Dry Run Mode → Save Changes

---

## Summary

Dry Run Mode is FolderFresh's primary safety feature:

✅ **Enabled by default** - prevents accidental operations
✅ **Per-profile setting** - test and production profiles separate
✅ **Accurate logs** - shows exactly what would happen
✅ **Works with all features** - rules, simulator, watcher
✅ **Easy to control** - one checkbox to toggle real operations

**Remember:** Start with Dry Run Mode ON, test thoroughly, then enable real operations only when confident.
