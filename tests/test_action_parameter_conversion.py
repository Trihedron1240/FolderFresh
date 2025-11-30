"""Test action parameter conversion in rule_editor."""

import pytest
import json
from pathlib import Path
from folderfresh.rule_engine.rule_store import dict_to_rule, rule_to_dict, ACTION_DISPLAY_NAME_TO_INTERNAL


class TestActionParameterConversion:
    """Test that action parameters are converted correctly from UI format to backend format."""

    def test_rename_action_conversion(self):
        """Test Rename action converts from display name to internal with correct parameter name."""
        rule_data = {
            "name": "Test Rename",
            "match_mode": "all",
            "stop_on_match": False,
            "conditions": [],
            "actions": [
                {
                    "type": "Rename File",  # Display name from ActionEditor
                    "args": {
                        "new_name": "new_file_name"
                    }
                }
            ]
        }

        rule = dict_to_rule(rule_data)
        assert len(rule.actions) == 1
        action = rule.actions[0]
        assert action.__class__.__name__ == "RenameAction"
        assert action.new_name == "new_file_name"

    def test_move_action_conversion(self):
        """Test Move action converts from display name to internal with correct parameter name."""
        rule_data = {
            "name": "Test Move",
            "match_mode": "all",
            "stop_on_match": False,
            "conditions": [],
            "actions": [
                {
                    "type": "Move to Folder",  # Display name from ActionEditor
                    "args": {
                        "target_dir": "/path/to/destination"
                    }
                }
            ]
        }

        rule = dict_to_rule(rule_data)
        assert len(rule.actions) == 1
        action = rule.actions[0]
        assert action.__class__.__name__ == "MoveAction"
        assert action.target_dir == "/path/to/destination"

    def test_copy_action_conversion(self):
        """Test Copy action converts from display name to internal with correct parameter name."""
        rule_data = {
            "name": "Test Copy",
            "match_mode": "all",
            "stop_on_match": False,
            "conditions": [],
            "actions": [
                {
                    "type": "Copy to Folder",  # Display name from ActionEditor
                    "args": {
                        "target_dir": "/path/to/backup"
                    }
                }
            ]
        }

        rule = dict_to_rule(rule_data)
        assert len(rule.actions) == 1
        action = rule.actions[0]
        assert action.__class__.__name__ == "CopyAction"
        assert action.target_dir == "/path/to/backup"

    def test_delete_action_conversion(self):
        """Test Delete action converts from display name to internal with no parameters."""
        rule_data = {
            "name": "Test Delete",
            "match_mode": "all",
            "stop_on_match": False,
            "conditions": [],
            "actions": [
                {
                    "type": "Delete File",  # Display name from ActionEditor
                    "args": {}
                }
            ]
        }

        rule = dict_to_rule(rule_data)
        assert len(rule.actions) == 1
        action = rule.actions[0]
        assert action.__class__.__name__ == "DeleteFileAction"

    def test_action_display_name_to_internal_mapping(self):
        """Test that all action display names map to internal names."""
        assert ACTION_DISPLAY_NAME_TO_INTERNAL["Rename File"] == "Rename"
        assert ACTION_DISPLAY_NAME_TO_INTERNAL["Move to Folder"] == "Move"
        assert ACTION_DISPLAY_NAME_TO_INTERNAL["Copy to Folder"] == "Copy"
        assert ACTION_DISPLAY_NAME_TO_INTERNAL["Delete File"] == "Delete"

    def test_multiple_actions_conversion(self):
        """Test that multiple actions are converted correctly."""
        rule_data = {
            "name": "Test Multiple Actions",
            "match_mode": "all",
            "stop_on_match": False,
            "conditions": [],
            "actions": [
                {
                    "type": "Rename File",
                    "args": {"new_name": "renamed.txt"}
                },
                {
                    "type": "Move to Folder",
                    "args": {"target_dir": "/archive"}
                },
                {
                    "type": "Copy to Folder",
                    "args": {"target_dir": "/backup"}
                }
            ]
        }

        rule = dict_to_rule(rule_data)
        assert len(rule.actions) == 3
        assert rule.actions[0].__class__.__name__ == "RenameAction"
        assert rule.actions[1].__class__.__name__ == "MoveAction"
        assert rule.actions[2].__class__.__name__ == "CopyAction"

    def test_internal_action_names_still_work(self):
        """Test that internal action names (not display names) still work for backward compatibility."""
        rule_data = {
            "name": "Test Internal Names",
            "match_mode": "all",
            "stop_on_match": False,
            "conditions": [],
            "actions": [
                {
                    "type": "Rename",  # Internal name (not display name)
                    "args": {"new_name": "renamed.txt"}
                },
                {
                    "type": "Move",  # Internal name
                    "args": {"target_dir": "/archive"}
                }
            ]
        }

        rule = dict_to_rule(rule_data)
        assert len(rule.actions) == 2
        assert rule.actions[0].__class__.__name__ == "RenameAction"
        assert rule.actions[1].__class__.__name__ == "MoveAction"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
