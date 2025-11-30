"""
RuleManager Backend Integration
Connects RuleManager to RuleEngine and ProfileStore
"""

import uuid
from typing import Dict, List, Optional

from PySide6.QtCore import Signal, QObject

from folderfresh.profile_store import ProfileStore
from folderfresh.rule_engine.backbone import Rule, RuleExecutor
from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule
from folderfresh.fileinfo import get_fileinfo
from folderfresh.ui_qt.dialogs import (
    show_confirmation_dialog,
    show_error_dialog,
    show_info_dialog,
    ask_text_dialog
)
from folderfresh.logger_qt import log_info, log_error, log_warning


class RuleManagerBackend(QObject):
    """
    Backend integration for RuleManager window.
    Handles all rule operations with RuleEngine and ProfileStore.
    """

    # Signals
    rule_created = Signal(str)  # rule_id
    rule_updated = Signal(str)  # rule_id
    rule_deleted = Signal(str)  # rule_id
    rule_tested = Signal(list)  # test_results
    rules_reloaded = Signal()

    def __init__(self):
        """Initialize RuleManager backend"""
        super().__init__()
        self.profile_store = ProfileStore()
        self.profiles_doc = None
        self.active_profile = None
        self.executor = RuleExecutor()

        # Load initial data
        self._load_data()

    def _load_data(self) -> None:
        """Load profiles and active profile"""
        try:
            self.profiles_doc = self.profile_store.load()
            active_id = self.profiles_doc.get("active_profile_id")

            for profile in self.profiles_doc.get("profiles", []):
                if profile["id"] == active_id:
                    self.active_profile = profile
                    break

            if not self.active_profile:
                log_warning("No active profile found")

            log_info("Rules loaded for active profile")
            self.rules_reloaded.emit()

        except Exception as e:
            log_error(f"Failed to load rules: {e}")
            show_error_dialog(f"Failed to load rules:\n{e}")

    def get_active_profile(self) -> Optional[Dict]:
        """Get currently active profile"""
        return self.active_profile

    def get_all_rules(self) -> List[Dict]:
        """Get all rules from active profile"""
        if not self.active_profile:
            return []
        return self.active_profile.get("rules", [])

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """Get rule by ID"""
        for rule_dict in self.get_all_rules():
            if rule_dict.get("id") == rule_id:
                return rule_dict
        return None

    def create_rule(self, name: str = None, match_mode: str = "all") -> Optional[str]:
        """
        Create new rule

        Args:
            name: Rule name
            match_mode: "all" or "any"

        Returns:
            Rule ID or None if failed
        """
        try:
            if not self.active_profile:
                show_error_dialog("No active profile")
                return None

            if name is None:
                name = ask_text_dialog(None, "New Rule", "Enter rule name:")
                if not name:
                    return None

            # Check for duplicate names
            for rule_dict in self.get_all_rules():
                if rule_dict["name"].lower() == name.lower():
                    show_error_dialog(f"Rule '{name}' already exists")
                    return None

            # Create new rule
            new_rule = {
                "id": f"rule_{uuid.uuid4().hex[:8]}",
                "name": name,
                "conditions": [],
                "actions": [],
                "match_mode": match_mode,
                "stop_on_match": True
            }

            self.active_profile["rules"].append(new_rule)
            self.profile_store.save(self.profiles_doc)

            log_info(f"Rule created: {name}")
            self.rule_created.emit(new_rule["id"])
            show_info_dialog(f"Rule '{name}' created")

            return new_rule["id"]

        except Exception as e:
            log_error(f"Failed to create rule: {e}")
            show_error_dialog(f"Failed to create rule:\n{e}")
            return None

    def update_rule(self, rule_id: str, **kwargs) -> bool:
        """
        Update rule

        Args:
            rule_id: Rule to update
            **kwargs: Fields to update (name, conditions, actions, match_mode, stop_on_match)

        Returns:
            True if successful
        """
        try:
            rule_dict = self.get_rule_by_id(rule_id)
            if not rule_dict:
                show_error_dialog(f"Rule not found: {rule_id}")
                return False

            # Update fields
            for key, value in kwargs.items():
                if key in ["name", "conditions", "actions", "match_mode", "stop_on_match"]:
                    rule_dict[key] = value

            self.profile_store.save(self.profiles_doc)

            log_info(f"Rule updated: {rule_dict['name']}")
            self.rule_updated.emit(rule_id)

            return True

        except Exception as e:
            log_error(f"Failed to update rule: {e}")
            show_error_dialog(f"Failed to update rule:\n{e}")
            return False

    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete rule

        Args:
            rule_id: Rule to delete

        Returns:
            True if successful
        """
        try:
            rule_dict = self.get_rule_by_id(rule_id)
            if not rule_dict:
                show_error_dialog(f"Rule not found: {rule_id}")
                return False

            if not show_confirmation_dialog(
                None,
                "Delete Rule",
                f"Delete rule '{rule_dict['name']}'?\nThis cannot be undone."
            ):
                return False

            # Verify active_profile is in profiles_doc
            if not self.active_profile or "rules" not in self.active_profile:
                show_error_dialog("Active profile is invalid")
                return False

            # Count before deletion
            rules_before = len(self.active_profile["rules"])
            log_info(f"[delete_rule] Rules before deletion: {rules_before}")

            # Remove rule from profile
            self.active_profile["rules"] = [
                r for r in self.active_profile["rules"]
                if r["id"] != rule_id
            ]

            rules_after = len(self.active_profile["rules"])
            log_info(f"[delete_rule] Rules after deletion: {rules_after}")

            if rules_before == rules_after:
                log_error(f"[delete_rule] ERROR: Rule was not removed!")
                show_error_dialog("Failed to delete rule: Rule was not found in profile")
                return False

            # Save to disk
            log_info(f"[delete_rule] Saving profile to disk...")
            self.profile_store.save(self.profiles_doc)
            log_info(f"[delete_rule] Profile saved successfully")

            log_info(f"Rule deleted: {rule_dict['name']}")
            self.rule_deleted.emit(rule_id)
            show_info_dialog(f"Rule '{rule_dict['name']}' deleted")

            return True

        except Exception as e:
            log_error(f"Failed to delete rule: {e}")
            import traceback
            log_error(f"Traceback: {traceback.format_exc()}")
            show_error_dialog(f"Failed to delete rule:\n{e}")
            return False

    def test_rule(self, rule_id: str, test_files: List[str]) -> List[Dict]:
        """
        Test rule against files

        Args:
            rule_id: Rule to test
            test_files: List of file paths to test

        Returns:
            List of test results
        """
        try:
            rule_dict = self.get_rule_by_id(rule_id)
            if not rule_dict:
                show_error_dialog(f"Rule not found: {rule_id}")
                return []

            # Convert dict to Rule object
            rule = dict_to_rule(rule_dict)

            # Test against each file
            results = []
            config = {
                "safe_mode": False,
                "dry_run": True,
                "skip_hidden": True,
                "include_sub": True
            }

            for file_path in test_files:
                try:
                    fileinfo = get_fileinfo(file_path)
                    result = self.executor.execute([rule], fileinfo, config)

                    results.append({
                        "file": file_path,
                        "matched": result.get("matched_rule") is not None,
                        "action": result.get("final_dst"),
                        "status": result.get("status", "Unknown"),
                        "log": result.get("log", [])
                    })
                except Exception as e:
                    log_warning(f"Failed to test file {file_path}: {e}")
                    results.append({
                        "file": file_path,
                        "matched": False,
                        "action": None,
                        "status": f"Error: {str(e)}",
                        "log": []
                    })

            log_info(f"Rule tested: {rule_dict['name']} ({len(test_files)} files)")
            self.rule_tested.emit(results)

            return results

        except Exception as e:
            log_error(f"Failed to test rule: {e}")
            show_error_dialog(f"Failed to test rule:\n{e}")
            return []

    def move_rule(self, rule_id: str, direction: str) -> bool:
        """
        Move rule up or down in list

        Args:
            rule_id: Rule to move
            direction: "up" or "down"

        Returns:
            True if successful
        """
        try:
            rules = self.active_profile["rules"]
            current_index = next(
                (i for i, r in enumerate(rules) if r["id"] == rule_id),
                -1
            )

            if current_index == -1:
                return False

            if direction == "up" and current_index > 0:
                rules[current_index], rules[current_index - 1] = \
                    rules[current_index - 1], rules[current_index]
                self.profile_store.save(self.profiles_doc)
                self.rules_reloaded.emit()
                return True

            elif direction == "down" and current_index < len(rules) - 1:
                rules[current_index], rules[current_index + 1] = \
                    rules[current_index + 1], rules[current_index]
                self.profile_store.save(self.profiles_doc)
                self.rules_reloaded.emit()
                return True

            return False

        except Exception as e:
            log_error(f"Failed to move rule: {e}")
            return False

    def duplicate_rule(self, rule_id: str) -> Optional[str]:
        """
        Duplicate rule

        Args:
            rule_id: Rule to duplicate

        Returns:
            New rule ID or None if failed
        """
        try:
            rule_dict = self.get_rule_by_id(rule_id)
            if not rule_dict:
                show_error_dialog(f"Rule not found: {rule_id}")
                return None

            new_rule = {
                "id": f"rule_{uuid.uuid4().hex[:8]}",
                "name": f"{rule_dict['name']} (Copy)",
                "conditions": [c.copy() for c in rule_dict.get("conditions", [])],
                "actions": [a.copy() for a in rule_dict.get("actions", [])],
                "match_mode": rule_dict.get("match_mode", "all"),
                "stop_on_match": rule_dict.get("stop_on_match", True)
            }

            self.active_profile["rules"].append(new_rule)
            self.profile_store.save(self.profiles_doc)

            log_info(f"Rule duplicated: {rule_dict['name']}")
            self.rule_created.emit(new_rule["id"])

            return new_rule["id"]

        except Exception as e:
            log_error(f"Failed to duplicate rule: {e}")
            show_error_dialog(f"Failed to duplicate rule:\n{e}")
            return None

    def reload_rules(self) -> None:
        """Reload rules from disk"""
        self._load_data()

    def save_rules(self) -> bool:
        """Save rules to disk"""
        try:
            self.profile_store.save(self.profiles_doc)
            log_info("Rules saved")
            return True
        except Exception as e:
            log_error(f"Failed to save rules: {e}")
            show_error_dialog(f"Failed to save rules:\n{e}")
            return False
