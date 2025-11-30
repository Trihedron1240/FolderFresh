import json
from pathlib import Path
from typing import Dict, Any
from .backbone import (
    Rule,
    NameContainsCondition,
    NameStartsWithCondition,
    NameEndsWithCondition,
    NameEqualsCondition,
    RegexMatchCondition,
    ParentFolderContainsCondition,
    FileInFolderCondition,
    ExtensionIsCondition,
    FileSizeGreaterThanCondition,
    FileAgeGreaterThanCondition,
    LastModifiedBeforeCondition,
    IsHiddenCondition,
    IsReadOnlyCondition,
    IsDirectoryCondition,
    RenameAction,
    MoveAction,
    CopyAction,
    DeleteFileAction,
)


# Mapping to reconstruct classes from saved JSON (camelCase keys)
CONDITION_MAP = {
    "NameContains": NameContainsCondition,
    "NameStartsWith": NameStartsWithCondition,
    "NameEndsWith": NameEndsWithCondition,
    "NameEquals": NameEqualsCondition,
    "RegexMatch": RegexMatchCondition,
    "ParentFolderContains": ParentFolderContainsCondition,
    "FileInFolder": FileInFolderCondition,
    "ExtensionIs": ExtensionIsCondition,
    "FileSizeGreaterThan": FileSizeGreaterThanCondition,
    "FileAgeGreaterThan": FileAgeGreaterThanCondition,
    "LastModifiedBefore": LastModifiedBeforeCondition,
    "IsHidden": IsHiddenCondition,
    "IsReadOnly": IsReadOnlyCondition,
    "IsDirectory": IsDirectoryCondition,
}

# Mapping from display names (with spaces) to camelCase names (for PyQt UI compatibility)
# The PyQt condition editor uses display names like "Name Contains" but the backend uses "NameContains"
DISPLAY_NAME_TO_INTERNAL = {
    "Name Contains": "NameContains",
    "Name Starts With": "NameStartsWith",
    "Name Ends With": "NameEndsWith",
    "Name Equals": "NameEquals",
    "Regex Match": "RegexMatch",
    "Parent Folder Contains": "ParentFolderContains",
    "File is in folder containing": "FileInFolder",
    "Extension Is": "ExtensionIs",
    "File Size > X bytes": "FileSizeGreaterThan",
    "File Age > X days": "FileAgeGreaterThan",
    "Last Modified Before": "LastModifiedBefore",
    "Is Hidden": "IsHidden",
    "Is Read-Only": "IsReadOnly",
    "Is Directory": "IsDirectory",
}

# Reverse mapping for converting back to display names
INTERNAL_NAME_TO_DISPLAY = {v: k for k, v in DISPLAY_NAME_TO_INTERNAL.items()}

# Mapping from action display names (with spaces) to action class names (for PyQt UI compatibility)
# The PyQt action editor uses display names like "Rename File" but the backend uses "Rename"
ACTION_DISPLAY_NAME_TO_INTERNAL = {
    "Rename File": "Rename",
    "Move to Folder": "Move",
    "Copy to Folder": "Copy",
    "Delete File": "Delete",
}

ACTION_MAP = {
    "Rename": RenameAction,
    "Move": MoveAction,
    "Copy": CopyAction,
    "Delete": DeleteFileAction,
}


def rule_to_dict(rule: Rule):
    """Convert a Rule object into a JSON-serializable dict."""
    def get_args_for_condition(cond):
        """Get serializable args for a condition, excluding compiled regex."""
        args = cond.__dict__.copy()
        # Exclude _compiled for RegexMatchCondition (it will be recompiled on deserialization)
        args.pop("_compiled", None)
        return args

    return {
        "name": rule.name,
        "match_mode": rule.match_mode,
        "stop_on_match": rule.stop_on_match,
        "conditions": [
            {
                "type": cond.__class__.__name__.replace("Condition", ""),
                "args": get_args_for_condition(cond),
            }
            for cond in rule.conditions
        ],
        "actions": [
            {
                "type": act.__class__.__name__.replace("Action", ""),
                "args": act.__dict__,
            }
            for act in rule.actions
        ],
    }


def _normalize_condition_args(condition_class_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize condition arguments to use correct parameter names.
    Handles cases where old rules used label text as parameter keys.
    """
    # Map class names to expected parameters
    expected_params = {
        "NameContains": ["substring"],
        "NameStartsWith": ["prefix"],
        "NameEndsWith": ["suffix"],
        "NameEquals": ["value", "case_sensitive"],
        "RegexMatch": ["pattern", "ignore_case"],
        "ExtensionIs": ["extension"],
        "FileSizeGreaterThan": ["min_bytes"],
        "FileAgeGreaterThan": ["days"],
        "LastModifiedBefore": ["timestamp"],
        "IsHidden": [],
        "IsReadOnly": [],
        "IsDirectory": [],
        "ParentFolderContains": ["substring"],
        "FileInFolder": ["folder_pattern"],
    }

    expected = expected_params.get(condition_class_name, list(args.keys()))

    # If args already has correct keys, return as-is
    if all(key in expected or key == "" for key in args.keys()):
        return args

    # If args keys don't match expected, need to normalize
    # Try to map values by position/type
    normalized = {}
    args_list = list(args.values())

    for i, param_name in enumerate(expected):
        if i < len(args_list):
            normalized[param_name] = args_list[i]
        elif param_name in args:
            normalized[param_name] = args[param_name]

    return normalized if normalized else args


def dict_to_rule(data: dict) -> Rule:
    """Convert a saved dict into a Rule object."""
    conditions = []
    for c in data["conditions"]:
        condition_type = c["type"]
        # Handle both camelCase (from backend) and display names (from PyQt UI)
        if condition_type in DISPLAY_NAME_TO_INTERNAL:
            condition_type = DISPLAY_NAME_TO_INTERNAL[condition_type]

        if condition_type not in CONDITION_MAP:
            raise ValueError(f"Unknown condition type: {c['type']}")

        # Handle both "args" (from rule_to_dict) and "parameters" (from UI editors) keys
        condition_args = c.get("args") or c.get("parameters", {})

        # Normalize parameter names in case old data used label text as keys
        normalized_args = _normalize_condition_args(condition_type, condition_args)

        conditions.append(CONDITION_MAP[condition_type](**normalized_args))

    actions = []
    for a in data["actions"]:
        action_type = a["type"]
        # Handle both display names (from PyQt UI) and internal names (from backend)
        if action_type in ACTION_DISPLAY_NAME_TO_INTERNAL:
            action_type = ACTION_DISPLAY_NAME_TO_INTERNAL[action_type]

        if action_type not in ACTION_MAP:
            raise ValueError(f"Unknown action type: {a['type']}")

        # Handle both "args" (from rule_to_dict) and "parameters" (from UI editors) keys
        action_args = a.get("args") or a.get("parameters", {})
        actions.append(ACTION_MAP[action_type](**action_args))

    return Rule(
        name=data["name"],
        match_mode=data.get("match_mode", "all"),
        stop_on_match=data.get("stop_on_match", False),
        conditions=conditions,
        actions=actions,
    )


def save_rules(path: Path, rules: list[Rule]):
    """Save list of rules to a JSON file."""
    data = [rule_to_dict(r) for r in rules]
    path.write_text(json.dumps(data, indent=4))


def load_rules(path: Path) -> list[Rule]:
    """Load rules from disk. Return empty list if file doesn’t exist."""
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [dict_to_rule(entry) for entry in data]
