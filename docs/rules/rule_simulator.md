# FolderFresh Rule Simulator Guide

## Overview

The Rule Simulator is a built-in testing tool that allows you to preview exactly what a rule will do to a specific file **without actually modifying it**. This is essential for safely testing rules before enabling real file operations.

---

## Features

✅ **Zero Risk Testing** - Never modifies files (always uses Dry Run Mode)
✅ **Detailed Logs** - Shows exactly what the rule would do
✅ **Easy Access** - One-click from the Rule Editor
✅ **Test Any File** - Pick any file from your computer
✅ **Complete Visibility** - Shows conditions, actions, and execution path

---

## How to Access

### In Popup Rule Editor (Editing Individual Rules)

1. **Profile Manager** → Select a profile
2. Click **"Open Rule Manager"**
3. Select a rule from the list
4. Click the **"Simulate Rule"** button at the bottom
5. Rule Simulator window opens

### In Embedded Rule Editor (Within Rule Manager)

**Note:** The simulator is only available in popup mode, not in the embedded editor within Rule Manager.

---

## Using the Rule Simulator

### Step 1: Select a Test File

1. In the **Rule Simulator** window, click **"Browse for a file..."**
2. A file browser opens
3. Navigate to any file on your computer
4. Select the file and click "Open"
5. The selected filename appears in the display

**Supported Files:** Any type of file can be tested

### Step 2: Review Rule Configuration

The **"Rule Configuration"** section shows:
- **Conditions:** How many conditions the rule has and the match mode (ALL/ANY)
- **Actions:** How many actions the rule will perform
- **Stop on Match:** Whether the rule stops processing after matching

**Example:**
```
Rule Configuration:
Conditions: 2 (Match Mode: all)
Actions: 1
Stop on Match: False
```

### Step 3: Run Simulation

1. Click **"Run Simulation"** button
2. The log appears immediately in the textbox below
3. Review the output to see what would happen

### Step 4: Analyze the Log

The **"Simulation Log"** shows the complete execution:

#### Log Format

```
=== Processing file: document.pdf ===

[RULE] 'Organize PDFs'
  -> MATCHED!
  -> DRY RUN: Would MOVE: C:\Downloads\document.pdf -> C:\Documents\document.pdf
  -> stop_on_match=True, stopping here.
```

#### Understanding the Log

- **`=== Processing file: ... ===`** - Which file is being evaluated
- **`[RULE] 'Rule Name'`** - The rule being tested
- **`-> MATCHED!`** - Rule conditions matched the file
- **`-> DRY RUN: Would ...`** - Action preview (NOT executed)
- **`-> No match, skipping actions.`** - Rule didn't match the file
- **`ERROR: ...`** - Something went wrong (file not found, invalid path, etc.)

---

## Example Scenarios

### Scenario 1: Rule Matches and Executes

**Test:** Moving PDF files larger than 5MB to Documents folder

**Test File:** `backup_large.pdf` (10MB)

**Log Output:**
```
=== Processing file: backup_large.pdf ===

[RULE] 'Move Large PDFs'
  -> MATCHED!
  -> DRY RUN: Would MOVE: C:\Downloads\backup_large.pdf -> C:\Documents\backup_large.pdf
```

**Interpretation:** ✅ Rule would move this file to Documents

---

### Scenario 2: Rule Doesn't Match

**Test:** Moving image files to Pictures folder

**Test File:** `document.docx` (Not an image)

**Log Output:**
```
=== Processing file: document.docx ===

[RULE] 'Organize Images'
  -> No match, skipping actions.
```

**Interpretation:** ✅ Rule would NOT affect this file (as expected)

---

### Scenario 3: File Name Collision

**Test:** Rename file but target name already exists

**Test File:** `report.txt` (trying to rename to `summary.txt` which exists)

**Log Output:**
```
=== Processing file: report.txt ===

[RULE] 'Rename Reports'
  -> MATCHED!
  -> DRY RUN: Would RENAME: C:\Reports\report.txt -> C:\Reports\summary (1).txt
```

**Interpretation:** ✅ Safe Mode prevents overwriting; file would be renamed with `(1)` suffix

---

### Scenario 4: Multiple Conditions

**Test:** File must be PNG AND larger than 2MB

**Test File:** `photo.png` (3MB)

**Log Output:**
```
=== Processing file: photo.png ===

[RULE] 'Archive Large Images'
  -> MATCHED!
  -> DRY RUN: Would MOVE: C:\Pictures\photo.png -> C:\Archive\photo.png
```

**Interpretation:** ✅ All conditions met; rule would execute

---

## Log Interpretation Guide

### Key Terms

| Term | Meaning |
|------|---------|
| **MATCHED!** | Rule conditions matched the file |
| **No match** | Rule conditions didn't match; actions skipped |
| **DRY RUN: Would** | Action preview (never executes in simulator) |
| **ERROR:** | Operation failed (file not found, invalid path, etc.) |

### Action Prefixes

All simulated actions show what **would** happen:

```
DRY RUN: Would MOVE:   C:\source -> C:\dest
DRY RUN: Would COPY:   C:\source -> C:\dest
DRY RUN: Would RENAME: C:\old.txt -> C:\new.txt
```

### Safe Mode Behavior

When **Safe Mode** is enabled (default):
- Collision-avoided names are calculated: `file.txt` → `file (1).txt`
- The log shows the actual destination path that would be used

---

## Workflow: Test Before Enabling

### Recommended Testing Process

```
1. Create a rule in Rule Manager
   ↓
2. Open the rule (or the popup editor)
   ↓
3. Click "Simulate Rule"
   ↓
4. Select a test file from the category you want to organize
   ↓
5. Click "Run Simulation"
   ↓
6. Review the log carefully
   ↓
7. If satisfied:
   - Close the simulator
   - Enable real operations (disable Dry Run Mode in profile)
   - Run the rule on real data
   ↓
8. If NOT satisfied:
   - Adjust rule conditions/actions
   - Test again
   - Repeat until correct
```

---

## Tips and Best Practices

### Testing Smart

1. **Test with multiple file types**
   - Test a PDF, JPG, and TXT file separately
   - Verify each behaves correctly

2. **Test edge cases**
   - Large files (5GB+) vs small files
   - Files with special characters in names
   - Old files vs recent files

3. **Test collision scenarios**
   - Create a duplicate filename in target directory
   - Verify Safe Mode handles it correctly

4. **Test across rules**
   - Multiple rules can match the same file
   - Simulator only tests ONE rule at a time
   - Review each rule individually

### Safety Checklist

- ✅ Rule name is clear and descriptive
- ✅ Conditions are specific (not too broad)
- ✅ Test with at least 3 different files
- ✅ Verify target directories are correct
- ✅ Check Safe Mode is enabled (if needed)
- ✅ Review logs carefully before enabling real operations

---

## Troubleshooting

### Issue: "Please select a test file first"

**Cause:** No file selected

**Solution:**
1. Click "Browse for a file..."
2. Select a test file
3. Try again

---

### Issue: File shows "No match"

**Cause:** File doesn't meet rule conditions

**Solution:**
1. Check rule conditions (name, extension, size)
2. Select a file that matches those conditions
3. Or adjust rule conditions to be less restrictive
4. Test again

---

### Issue: Error message appears

**Cause:** File access problem or invalid configuration

**Common Errors:**
- `ERROR: MOVE - source file not found` - File was deleted or moved
- `ERROR: MOVE - target directory invalid` - Path doesn't exist
- `ERROR: RENAME - new name is empty` - Action configured incorrectly

**Solution:** Fix the file path or rule configuration and test again

---

### Issue: Path shows as "(No file selected)"

**Cause:** File was deleted after selection or browser was cancelled

**Solution:** Click "Browse for a file..." again and select a valid file

---

## Simulator vs. Real Mode

| Aspect | Simulator | Real Mode |
|--------|-----------|-----------|
| **Modifications** | None | Actual file operations |
| **Log Format** | `DRY RUN: Would...` | `MOVE:`, `COPY:`, etc. |
| **Safety** | 100% safe | Depends on settings |
| **Speed** | Fast | May be slower (large files) |
| **Use Case** | Testing/preview | Production |

---

## Integration with Other Features

### Rule Simulator + Dry Run Mode

- **Rule Simulator:** Always uses dry_run=True (enforced)
- **Dry Run Mode:** Uses your profile setting

**Result:** Simulator is independent of Dry Run Mode setting

---

### Rule Simulator + Safe Mode

- When **Safe Mode ON:** Simulator shows collision-avoided names
- When **Safe Mode OFF:** Simulator shows direct overwrites

**Result:** Simulator respects Safe Mode settings

---

### Rule Simulator + Rule Validation

- **Invalid rules:** Cannot be simulated
  - Must have a name
  - Must have at least one condition or action
  - Must have fully configured conditions/actions

- **Valid rules:** Can always be simulated

---

## Advanced Usage

### Testing Multiple Rules

To test how multiple rules interact:

1. Create/edit Rule 1
2. Simulate it against Test File A
3. Review the log
4. Switch to Rule 2
5. Simulate it against the same Test File A
6. Compare behavior

**Note:** The simulator only tests ONE rule at a time. To see how all rules work together, you'll need to run with real operations or check the actual activity logs.

---

### Creating Test Files

For safe testing, create a test directory with sample files:

```
C:\TestFolder\
  ├── document.pdf (large)
  ├── photo.jpg (medium)
  ├── script.exe (executable)
  ├── readme.txt (text)
  └── archive.zip (compressed)
```

Use these files for all rule simulations. They won't be modified.

---

## Summary

The Rule Simulator is your safety net for testing rules:

✅ **Always Safe** - Uses Dry Run Mode internally
✅ **Detailed Feedback** - Full execution logs
✅ **Easy to Use** - One button from Rule Editor
✅ **Test Before Enabling** - Verify behavior first
✅ **Zero Risk** - No files are ever modified

**Best Practice:** Always simulate a rule with at least 3 test files before enabling real operations.
