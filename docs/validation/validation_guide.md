# FolderFresh Rule Validation Guide

## Overview

FolderFresh implements a strict validation system to ensure only complete, valid rules are persisted to disk. This guide explains the validation rules, when they're applied, and how users interact with them.

---

## Validation Rules

A rule is **valid** only if ALL of the following conditions are met:

### 1. Rule Name is Not Empty
- `rule.name` must be a non-empty string (whitespace doesn't count)
- Example: `"Organize PDFs"` ✓, `""` ✗, `"  "` ✗

### 2. Match Mode is Valid
- `rule.match_mode` must be either `"all"` or `"any"`
- `"all"` means ALL conditions must be true (AND logic)
- `"any"` means ANY condition can be true (OR logic)
- Example: `"all"` ✓, `"any"` ✓, `"both"` ✗

### 3. At Least One Condition or Action
- `rule.conditions` must not be empty OR `rule.actions` must not be empty
- A rule cannot be empty (doing nothing would be pointless)
- Example: Rule with 1 condition ✓, Rule with 1 action ✓, Rule with both ✓, Rule with neither ✗

### 4. All Conditions are Fully Formed
- Every condition in `rule.conditions` must have all required parameters filled in

#### Condition Types and Requirements:

**NameContainsCondition**
- Requires: `substring` (non-empty string)
- Example: `substring="backup"` ✓, `substring=""` ✗

**ExtensionIsCondition**
- Requires: `extension` (non-empty string, no dot)
- Example: `extension="pdf"` ✓, `extension=""` ✗, `extension=".pdf"` ✗

**FileSizeGreaterThanCondition**
- Requires: `min_bytes` (non-negative integer)
- Example: `min_bytes=1048576` (1MB) ✓, `min_bytes=-100` ✗, `min_bytes=None` ✗

### 5. All Actions are Fully Formed
- Every action in `rule.actions` must have all required parameters filled in

#### Action Types and Requirements:

**RenameAction**
- Requires: `new_name` (non-empty string)
- Example: `new_name="archive_{datetime}.zip"` ✓, `new_name=""` ✗

**MoveAction**
- Requires: `target_dir` (non-empty string, valid path)
- Example: `target_dir="C:\\Documents"` ✓, `target_dir=""` ✗

**CopyAction**
- Requires: `target_dir` (non-empty string, valid path)
- Example: `target_dir="D:\\Backup"` ✓, `target_dir=""` ✗

---

## When Validation Occurs

### 1. On Field Changes (Auto-Save)
**Location**: `RuleEditor._on_field_change()` (embedded and popup modes)

When the user edits a rule property (name, match_mode, stop_on_match):
- Changes are applied to the rule object in memory
- Rule is validated
- If valid: `save_callback()` is called → rule is persisted to disk
- If invalid: Changes stay in memory, rule is NOT persisted to disk

**Example**: User changes rule name from "Old Name" to "" (empty)
- Memory: Rule now has empty name
- Disk: Rule still has "Old Name" (old version)
- User must fix the name to trigger save

### 2. When Adding Conditions (Manual)
**Location**: `RuleEditor.on_condition_added()`

When the user adds a new condition via the ConditionEditor popup:
- Condition is appended to `rule.conditions`
- UI is refreshed to show the new condition
- Rule is validated (now has name + condition)
- If valid: `save_callback()` is called → rule is persisted to disk
- If invalid: Rule stays in memory unsaved (should not happen if rule had name)

**Example**: User creates rule "My Rule" (invalid), then adds "Name Contains PDF" condition
- Memory: Rule now has name + 1 condition
- Validation passes (has name + has conditions)
- `save_callback()` is called
- Disk: Rule is saved with condition ✓

### 3. When Deleting Conditions (Manual)
**Location**: `RuleEditor.delete_condition()`

When the user deletes a condition:
- Condition is removed from `rule.conditions`
- UI is refreshed to show the deletion
- Rule is validated
- If valid: `save_callback()` is called → rule is persisted to disk
- If invalid: Deletion stays in memory unsaved

**Example**: User has rule with only 1 condition and deletes it
- Memory: Rule now has name but no conditions/actions
- Validation fails (no conditions or actions)
- `save_callback()` is NOT called
- Disk: Rule still has the condition (old version) - user must add action to save changes
- Next reload: Rule loads from disk with the original condition

### 4. When Adding Actions (Manual)
**Location**: `RuleEditor.on_action_added()`

When the user adds a new action via the ActionEditor popup:
- Action is appended to `rule.actions`
- UI is refreshed to show the new action
- Rule is validated
- If valid: `save_callback()` is called → rule is persisted to disk
- If invalid: Rule stays in memory unsaved

### 5. When Deleting Actions (Manual)
**Location**: `RuleEditor.delete_action()`

When the user deletes an action:
- Action is removed from `rule.actions`
- UI is refreshed to show the deletion
- Rule is validated
- If valid: `save_callback()` is called → rule is persisted to disk
- If invalid: Deletion stays in memory unsaved

### 6. When Saving Popup Editor
**Location**: `RuleEditor.save_and_close()`

In popup mode (standalone RuleEditor window), when user clicks "Save Changes":
- Changes are applied to the rule
- Rule is validated
- If valid: `save_callback()` is called, popup closes
- If invalid: Popup stays open, user sees warning message

**Warning Message**:
```
"Cannot save an incomplete rule. Please:
1. Enter a rule name
2. Add at least one condition or action
3. Ensure all conditions and actions are fully configured"
```

---

## Workflow Examples

### Example 1: Creating a New Rule (Happy Path)

```
1. User clicks "Add Rule" in RuleManager
   → Rule created in memory: name="New Rule", conditions=[], actions=[]
   → Rule is INVALID (no conditions or actions)
   → Rule NOT saved to disk

2. RuleManager auto-selects the new rule
   → RuleEditor opens (embedded mode)
   → Shows empty conditions/actions lists

3. User clicks "Add Condition"
   → ConditionEditor popup opens

4. User selects "Name Contains", enters "backup", clicks "Add Condition"
   → Condition appended to rule
   → Rule validated: has name + has conditions = VALID ✓
   → save_callback() called
   → Rule persisted to disk

5. Rule now appears in both memory and disk ✓
```

### Example 2: Editing Existing Rule - Invalid Deletion

```
1. User has rule: name="Organize PDFs", conditions=[ExtensionIs("pdf")], actions=[Move("D:\\PDFs")]
   → Rule is VALID, stored on disk

2. User opens RuleManager, selects the rule
   → RuleEditor shows the rule

3. User deletes the condition
   → Condition removed from memory
   → Rule validated: has name + has action = VALID ✓
   → save_callback() called
   → Disk updated: Rule now has no condition, just action

4. User then deletes the action
   → Action removed from memory
   → Rule validated: has name but no conditions/actions = INVALID ✗
   → save_callback() NOT called
   → Disk remains: Rule still has no condition, just action

5. User closes editor
   → On disk: Rule has only the action (from previous save in step 3)
   → In memory: Rule has nothing (deleted action not saved)

6. User reopens rule
   → Loads from disk: Rule has the action ✓
```

### Example 3: Creating Invalid Rule and Abandoning It

```
1. User clicks "Add Rule", names it "Incomplete"
   → Rule in memory: name="Incomplete", conditions=[], actions=[]
   → INVALID, NOT saved to disk

2. RuleEditor opens, user changes name to "Still Incomplete"
   → Changes in memory, rule still INVALID
   → NOT saved to disk

3. User closes RuleManager without adding conditions/actions
   → Rule discarded from memory
   → Nothing saved to disk ✓

4. User reopens RuleManager
   → Rule is gone (never persisted)
```

---

## Implementation Details

### Validation Logic

```python
@staticmethod
def rule_is_valid(rule) -> bool:
    # Check name
    if not rule.name or not str(rule.name).strip():
        return False

    # Check match mode
    if rule.match_mode not in ("all", "any"):
        return False

    # Check that rule has at least one condition or action
    if not rule.conditions and not rule.actions:
        return False

    # Validate all conditions
    for cond in rule.conditions:
        if not RuleEditor._condition_is_valid(cond):
            return False

    # Validate all actions
    for action in rule.actions:
        if not RuleEditor._action_is_valid(action):
            return False

    return True
```

### Key Points

1. **Validation is checked BEFORE saving**, not during normal edits
2. **Changes stay in memory** if invalid - user can fix them
3. **Disk version persists** - only updated when rule becomes valid
4. **New rules** are NOT saved until they become valid (have conditions or actions)
5. **Existing rules** can be edited but only valid changes are persisted

---

## User Experience

### What Users See

**Valid Rule**:
- Changes are saved automatically
- No warnings or errors
- Rule appears in list with proper display

**Invalid Rule Being Edited**:
- Changes appear in UI immediately
- Changes are NOT saved to disk
- If trying to close popup editor: warning message appears
- Can continue editing to make rule valid

**Example Feedback**:
```
[User changes rule name to empty]
→ In editor: name field is empty
→ Rule is INVALID
→ If they click "Save Changes" (popup): warning appears
→ Changes not saved to disk
→ They must re-enter name to save
```

---

## Testing Validation

### Test Case 1: Add Valid Rule
```python
1. Click "Add Rule", name it "Test"
2. Add condition "Name Contains test"
3. Close RuleManager
4. Reopen and verify rule persisted ✓
```

### Test Case 2: Add Invalid Rule and Abandon
```python
1. Click "Add Rule", name it "Incomplete"
2. Close RuleManager without adding conditions/actions
3. Reopen - rule should be gone ✓
```

### Test Case 3: Delete Last Condition
```python
1. Open rule with only 1 condition and 0 actions
2. Delete the condition
3. Close and reopen RuleManager
4. Rule should still have the condition (deletion not saved) ✓
```

### Test Case 4: Invalid Name Change
```python
1. Open rule and change name to empty string
2. Close editor (popup mode)
3. Warning should appear, editor stays open ✓
```

### Test Case 5: Add Condition to New Rule
```python
1. Create new rule "My Rule"
2. Add condition "Extension is pdf"
3. Close RuleManager
4. Reopen - rule should be persisted with condition ✓
```

---

## Summary

The validation system ensures:
- ✅ Only complete, valid rules are persisted to disk
- ✅ New rules must be made valid before saving
- ✅ Existing rules cannot be corrupted by deletion of all conditions/actions
- ✅ Users get feedback when rules are invalid (popup mode only)
- ✅ Changes are always available in memory, even if not persisted
- ✅ Validation is automatic and transparent in most cases
