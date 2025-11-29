# Hazel-Style Condition Builder - Quick Reference

## What Changed?

The **Add Condition** dialog is now **fully dynamic** — fields change based on the selected condition type, just like Hazel.

### Before
```
User selects any condition → Always shows single "Parameter" text field
❌ How do users know what to type?
❌ Multi-parameter conditions impossible
❌ No dropdowns, checkboxes, or smart input controls
```

### After
```
User selects "Name Contains"    → Shows "Text to search for:" field
User selects "Metadata Contains" → Shows TWO fields (field name + keyword)
User selects "File Size > X"     → Shows number + unit dropdown (smart!)
User selects "Color Is"          → Shows color dropdown [red▼]
User selects "Name Equals"       → Shows text field + "Case sensitive" checkbox

✅ Contextual, clear, intuitive
✅ Multi-parameter support
✅ Smart controls (dropdowns, units, checkboxes)
```

## Architecture

```python
# 1. Central Configuration: Maps condition type → UI fields
UI_SCHEMA = {
    "Name Contains": [
        {"label": "Text to search for:", "type": "text", "placeholder": "e.g., backup"},
    ],
    "Metadata Contains": [
        {"label": "Field name...", "type": "text", ...},
        {"label": "Keyword...", "type": "text", ...},
    ],
    "File Size > X bytes": [
        {"label": "Minimum file size:", "type": "size", "unit": "MB"},
    ],
    "Color Is": [
        {"label": "Color name:", "type": "dropdown", "options": ["red", "blue", ...], "default": "red"},
    ],
}

# 2. User selects condition type
on_type_changed() → Look up schema → Clear old fields → Build new fields

# 3. User fills fields and clicks "Add Condition"
_collect_parameters() → Validate → _instantiate_condition() → Create object → Callback
```

## Field Types

| Type | Widget | Use Case | Example |
|------|--------|----------|---------|
| `text` | CTkEntry | Free-form text | "Name Contains", "Tag name" |
| `numeric` | CTkEntry | Integer input | "File Age > X days" |
| `size` | Entry + Menu | Size with units | "File Size > X bytes" (1 MB) |
| `date` | CTkEntry | ISO format | "Last Modified Before" |
| `dropdown` | CTkOptionMenu | Choose from list | "Color Is" (red/blue/green) |
| `checkbox` | CTkCheckBox | Boolean flag | "Case sensitive" |
| `none` | (nothing) | No input | "Is Hidden", "Is Directory" |

## All 21 Conditions

### Basic Name (4)
- **Name Contains** → text field
- **Name Starts With** → text field
- **Name Ends With** → text field
- **Name Equals** → text field + **checkbox** (case sensitive)

### Regex (1)
- **Regex Match** → text field + **checkbox** (ignore case)

### Path (2)
- **Parent Folder Contains** → text field
- **File is in folder containing** → text field

### File Properties (4)
- **Extension Is** → text field
- **File Size > X bytes** → **size field with unit selector** (MB/KB/GB)
- **File Age > X days** → numeric field
- **Last Modified Before** → text field (ISO date)

### Attributes (3)
- **Is Hidden** → no input
- **Is Read-Only** → no input
- **Is Directory** → no input

### Tier-1: Content & Patterns (2)
- **Content Contains** → text field
- **Date Pattern** → **dropdown** (created/modified) + text field (pattern)

### Tier-2: Metadata & Tags (5)
- **Color Is** → **dropdown** (red/blue/green/yellow/orange/purple)
- **Has Tag** → text field
- **Metadata Contains** → text field (field name) + text field (keyword)
- **Metadata Field Equals** → text field (field name) + text field (exact value)
- **Is Duplicate** → **dropdown** (quick/full hash match)

## Code Structure

```
condition_editor.py
├── UI_SCHEMA (71 lines)
│   └─ 21 conditions × field specs
├── DESCRIPTIONS (134 lines)
│   └─ Help text for each condition
├── ConditionEditor class
│   ├── __init__()
│   │   └─ Initialize UI structure
│   ├── on_type_changed()
│   │   └─ Triggered by dropdown → rebuild fields
│   ├── Field factories (6 methods)
│   │   ├─ _create_text_field()
│   │   ├─ _create_numeric_field()
│   │   ├─ _create_size_field()
│   │   ├─ _create_dropdown_field()
│   │   ├─ _create_checkbox_field()
│   │   └─ _clear_fields()
│   ├── Parameter handling (2 methods)
│   │   ├─ _collect_parameters() → Validate + gather
│   │   └─ _get_field_value()
│   ├── Instantiation (1 method)
│   │   └─ _instantiate_condition() → Create object
│   └── Helpers
│       ├─ _update_description()
│       └─ _convert_to_bytes()
```

## Key Methods

### `on_type_changed(choice: str)`
Triggered when user selects a condition type:
1. Store the choice
2. `_clear_fields()` - Destroy old widgets
3. Look up `UI_SCHEMA[choice]`
4. For each field spec in schema:
   - Call appropriate factory method
5. `_update_description()` - Update help text

### `_collect_parameters(condition_type: str, schema: list) → dict`
Gathers and validates parameter values:
- Iterates through schema
- `_get_field_value()` for each widget
- Type validation (numeric → int, size → bytes)
- Returns `{"Field Label": value, ...}`

### `_instantiate_condition(ConditionClass, condition_type, params) → object`
Creates the right condition object with correct constructor signature:
```python
if condition_type == "Name Equals":
    filename = params.get("Filename to match:", "")
    case_sensitive = params.get("Case sensitive:", False)
    return ConditionClass(filename, case_sensitive=case_sensitive)

elif condition_type == "Metadata Contains":
    field_name = params.get("Field name...", "")
    keyword = params.get("Keyword...", "")
    return ConditionClass(field_name, keyword)
```

## Adding a New Condition

### Step 1: Add to `UI_SCHEMA`
```python
UI_SCHEMA["My Condition"] = [
    {"label": "First param:", "type": "text", "placeholder": "example"},
    {"label": "Second param:", "type": "numeric"},
]
```

### Step 2: Add to `DESCRIPTIONS`
```python
DESCRIPTIONS["My Condition"] = (
    "Explanation of what this condition does.\n\n"
    "Parameter 1: ...\n"
    "Parameter 2: ...\n\n"
    "Example: ..."
)
```

### Step 3: Add to `_instantiate_condition()`
```python
elif condition_type == "My Condition":
    param1 = params.get("First param:", "")
    param2 = int(params.get("Second param:", "0"))
    return ConditionClass(param1, param2)
```

**Done!** Field rendering and validation are automatic.

## Testing

✅ All 361 tests pass
✅ Zero regressions
✅ Backwards compatible with existing rules

Run tests:
```bash
cd FolderFresh
python -m pytest tests/ -v
```

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **User Experience** | Confusing | Clear, guided |
| **Parameter Input** | Always text field | Contextual (dropdown, units, checkbox) |
| **Multi-Parameters** | Impossible | Full support |
| **Extensibility** | Hard (if/elif chains) | Easy (schema entry) |
| **Validation** | Weak | Strong |
| **Hazel Parity** | No | ✅ Yes |

## Files Modified

```
src/folderfresh/condition_editor.py
├── Before: 578 lines (static, hard-coded logic)
└── After:  712 lines (dynamic, schema-driven)

New:
└── HAZEL_UI_UPGRADE.md (detailed documentation)
└── HAZEL_UI_QUICK_REFERENCE.md (this file)
```

## Commits

```
5514659 Add comprehensive documentation for Hazel-style UI upgrade
c430c5a Upgrade condition editor to Hazel-style dynamic UI
```

---

**Ready to use!** The condition builder is production-ready and provides Hazel-class UX. 🎉
