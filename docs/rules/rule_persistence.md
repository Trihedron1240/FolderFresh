# FolderFresh Rule Persistence Implementation Guide

## Overview

This document explains how rules are saved and persisted in FolderFresh. All changes made to rules through the Rule Manager are automatically saved to the active profile and persisted to `~/.folderfresh_profiles.json`.

---

## Complete Save Flow

### 1. Rule Addition
```
User clicks "Add Rule" in Rule Manager
↓
RuleManager.add_rule()
  - Creates new Rule object
  - Appends to self.rules
  - Calls save_rules()
↓
RuleManager.save_rules()
  - Calls store.set_rules(self.profile, self.rules)
↓
ProfileStore.set_rules()
  - Converts rules to JSON via rule_to_dict()
  - Finds active profile in document
  - Updates profile["rules"]
  - Updates profile["updated_at"]
  - Calls store.save(doc)
↓
ProfileStore.save()
  - Atomic write to ~/.folderfresh_profiles.json
  - Persisted to disk ✓
```

### 2. Rule Name/Settings Change
```
User edits rule name, match_mode, or stop_on_match
↓
RuleEditor._on_field_change() triggered
  - Calls _apply_changes()
  - Calls save_callback() (which is RuleManager.save_rules())
↓
RuleManager.save_rules()
  - Calls store.set_rules(self.profile, self.rules)
↓
ProfileStore.set_rules()
  - Updates profile["rules"] with current rule objects
  - Saves to disk ✓
```

### 3. Condition Addition
```
User clicks "Add Condition" in RuleEditor
↓
ConditionEditor popup opens
↓
User enters values and clicks "Add Condition"
↓
ConditionEditor.add_condition()
  - Converts user input to bytes (for file size)
  - Creates Condition object
  - Calls callback (RuleEditor.on_condition_added)
↓
RuleEditor.on_condition_added()
  - Appends condition to self.rule.conditions
  - Calls save_callback() (RuleManager.save_rules())
  - Refreshes conditions list display
↓
RuleManager.save_rules()
  - Calls store.set_rules(self.profile, self.rules)
  - Persists to disk ✓
```

### 4. Condition Deletion
```
User selects condition and clicks "Delete Condition"
↓
RuleEditor.delete_condition()
  - Removes condition from self.rule.conditions
  - Calls save_callback() (RuleManager.save_rules())
  - Refreshes conditions list display
↓
RuleManager.save_rules()
  - Persists to disk ✓
```

### 5. Action Addition
```
User clicks "Add Action" in RuleEditor
↓
ActionEditor popup opens
↓
User enters values and clicks "Add Action"
↓
ActionEditor._create_action()
  - Creates Action object
  - Calls callback (RuleEditor.on_action_added)
↓
RuleEditor.on_action_added()
  - Appends action to self.rule.actions
  - Calls save_callback() (RuleManager.save_rules())
  - Refreshes actions list display
↓
RuleManager.save_rules()
  - Persists to disk ✓
```

### 6. Action Deletion
```
User selects action and clicks "Delete Action"
↓
RuleEditor.delete_action()
  - Removes action from self.rule.actions
  - Calls save_callback() (RuleManager.save_rules())
  - Refreshes actions list display
↓
RuleManager.save_rules()
  - Persists to disk ✓
```

### 7. Rule Deletion
```
User selects rule and clicks "Delete Rule"
↓
RuleManager.delete_rule()
  - Removes rule from self.rules
  - Calls save_rules()
↓
RuleManager.save_rules()
  - Persists to disk ✓
```

### 8. Rule Reordering (Up/Down)
```
User clicks "Move Up" or "Move Down"
↓
RuleManager.move_rule_up() or move_rule_down()
  - Swaps rules in self.rules
  - Calls save_rules()
↓
RuleManager.save_rules()
  - Persists to disk ✓
```

---

## Key Components

### ProfileStore.set_rules()
Located in: `src/folderfresh/profile_store.py`

**Responsibility**: Converts Rule objects to JSON and saves to disk.

**Implementation**:
```python
def set_rules(self, profile: Dict[str, Any], rules: list[Rule]):
    # Update the profile's rules field
    profile["rules"] = [rule_to_dict(r) for r in rules]

    # Update modified timestamp
    profile["updated_at"] = now_iso()

    # Load the full document to ensure correct state
    doc = self.load()

    # Find the active profile and update it
    active_id = doc.get("active_profile_id")
    for p in doc["profiles"]:
        if p["id"] == active_id:
            p["rules"] = [rule_to_dict(r) for r in rules]
            p["updated_at"] = now_iso()
            break

    # Save the updated document
    self.save(doc)
```

**Key Points**:
- Uses `rule_to_dict()` to convert Rule objects to JSON
- Updates the active profile in the full document
- Updates the `updated_at` timestamp
- Uses atomic write for safety

### RuleManager.save_rules()
Located in: `src/folderfresh/rule_manager.py`

**Responsibility**: Orchestrates rule saving from the UI.

**Implementation**:
```python
def save_rules(self):
    """Save all rules to the active profile and persist to disk."""
    self.store.set_rules(self.profile, self.rules)
```

**Call Points**:
- `add_rule()` - after creating a new rule
- `delete_rule()` - after removing a rule
- `move_rule_up()` - after reordering
- `move_rule_down()` - after reordering
- Callbacks from RuleEditor - after any field change

### RuleEditor._on_field_change()
Located in: `src/folderfresh/rule_editor.py`

**Responsibility**: Auto-save when rule properties are edited.

**Implementation**:
```python
def _on_field_change(self):
    """Called when any field changes. Saves immediately via callback."""
    self._apply_changes()
    if self.save_callback:
        self.save_callback()
```

**Triggered By**:
- Editing rule name (KeyRelease event)
- Changing match mode (dropdown selection)
- Toggling stop_on_match (checkbox)

---

## Data Flow Architecture

```
RuleManager (UI)
  │
  ├─ self.rules (list[Rule])
  ├─ self.profile (dict)
  └─ self.store (ProfileStore)
      │
      ├─ get_rules(profile) → list[Rule]
      └─ set_rules(profile, list[Rule]) → saves to disk
          │
          └─ Converts Rule → JSON dict
              │
              ├─ rule_to_dict()
              ├─ Updates profile["rules"]
              ├─ Saves to profiles.json
              └─ Atomic write for safety
```

---

## JSON Storage Format

Rules are stored in the profile under the `rules` key:

```json
{
  "profiles": [
    {
      "id": "profile_default",
      "name": "Default",
      "rules": [
        {
          "name": "Organize PDFs",
          "match_mode": "all",
          "stop_on_match": true,
          "conditions": [
            {
              "type": "ExtensionIs",
              "args": {"extension": "pdf"}
            },
            {
              "type": "FileSizeGreaterThan",
              "args": {"min_bytes": 5242880}
            }
          ],
          "actions": [
            {
              "type": "Move",
              "args": {"target_dir": "C:\\Documents"}
            }
          ]
        }
      ]
    }
  ]
}
```

---

## Callback Chain

The callback system ensures changes propagate correctly:

```
ConditionEditor/ActionEditor
  │
  └─ callback = RuleEditor.on_condition_added
       │
       └─ Appends to self.rule.conditions/actions
            │
            └─ save_callback = RuleManager.save_rules()
                 │
                 └─ Calls store.set_rules()
                      │
                      └─ Persists to disk
```

---

## Error Handling

All save operations go through `ProfileStore.save()`, which:
1. Creates a backup of the existing file
2. Atomically writes to a temporary file
3. Replaces the original file
4. Handles file system errors gracefully

If a save fails, previous backups can be restored.

---

## Testing the Implementation

### Test 1: Add and Reload Rule
```python
# In Rule Manager:
1. Click "Add Rule"
2. Enter name "Test Rule"
3. Close Rule Manager
4. Re-open Rule Manager
# Expected: "Test Rule" appears in the list
```

### Test 2: Edit and Reload Rule
```python
# In Rule Manager:
1. Select a rule
2. Change name in RuleEditor
3. Change match mode
4. Close Rule Manager
5. Re-open Rule Manager
# Expected: Changes persist
```

### Test 3: Add Condition and Reload
```python
# In Rule Manager:
1. Select a rule
2. Click "Add Condition"
3. Add a "Name Contains" condition
4. Close Rule Manager
5. Re-open Rule Manager
# Expected: Condition appears in the list
```

### Test 4: Check profiles.json
```bash
# On disk:
cat ~/.folderfresh_profiles.json
# Expected: Rules appear in profile["rules"] as JSON
```

---

## Important Notes

1. **Atomicity**: All saves use atomic writes (write to temp, then replace)
2. **Timestamps**: `profile["updated_at"]` is updated on every save
3. **Backwards Compatibility**: Uses existing `rule_to_dict()` and `dict_to_rule()`
4. **Profile Isolation**: Only saves to the active profile, leaves others untouched
5. **Live Updates**: Changes appear in the UI immediately via refresh() calls

---

## Files Modified

1. **profile_store.py**
   - Fixed `set_rules()` to properly update active profile and save

2. **rule_manager.py**
   - Updated `save_rules()` to use `store.set_rules()`
   - Removed unused `rule_to_dict` import

3. **rule_editor.py**
   - Updated `_on_field_change()` to save in both embedded and popup modes
   - Modified name entry binding to always trigger auto-save

4. **condition_editor.py**
   - No changes needed (already calls callback correctly)

5. **action_editor.py**
   - No changes needed (already calls callback correctly)

---

## Summary

The rule persistence system now ensures that:
- ✅ Rules are saved immediately after any change
- ✅ Rules persist across application restarts
- ✅ Only the active profile is modified
- ✅ All changes are atomic (safe from corruption)
- ✅ Timestamps are updated for audit trails
- ✅ Callbacks ensure proper save sequencing
- ✅ Backwards compatible with existing rule format
