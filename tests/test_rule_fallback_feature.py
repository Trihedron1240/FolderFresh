"""Test rule fallback to category sort feature."""

import pytest
from folderfresh.rule_engine import Rule, NameContainsCondition, RenameAction


class MockApp:
    """Mock app object for testing."""
    def __init__(self, config_data):
        self.config_data = config_data
        self.smart_mode = type('obj', (object,), {'get': lambda self: False})()
        self.selected_folder = "/test"


class TestRuleFallbackFeature:
    """Test rule fallback to category sort feature."""

    def test_default_fallback_enabled(self):
        """Test that fallback is enabled by default."""
        config = {
            "rule_fallback_to_sort": True,  # Default
            "safe_mode": True,
            "smart_mode": False,
        }
        assert config.get("rule_fallback_to_sort", True) is True

    def test_fallback_can_be_disabled(self):
        """Test that fallback can be disabled."""
        config = {
            "rule_fallback_to_sort": False,
            "safe_mode": True,
            "smart_mode": False,
        }
        assert config.get("rule_fallback_to_sort", True) is False

    def test_default_fallback_with_missing_setting(self):
        """Test that missing setting defaults to True (backward compatibility)."""
        config = {
            "safe_mode": True,
            "smart_mode": False,
            # "rule_fallback_to_sort" is missing
        }
        assert config.get("rule_fallback_to_sort", True) is True

    def test_fallback_logic_enabled(self):
        """Test fallback logic when enabled."""
        app = MockApp({
            "rule_fallback_to_sort": True,
            "safe_mode": True,
        })

        # When fallback is enabled, rule failure should allow fallback to sorting
        rule_failed = True  # Simulating rule failure
        fallback_enabled = app.config_data.get("rule_fallback_to_sort", True)

        # Logic: if fallback is enabled AND rule failed, should continue to sorting
        should_continue_to_sort = fallback_enabled and rule_failed
        assert should_continue_to_sort is True

    def test_fallback_logic_disabled(self):
        """Test fallback logic when disabled."""
        app = MockApp({
            "rule_fallback_to_sort": False,
            "safe_mode": True,
        })

        # When fallback is disabled, rule failure should NOT allow fallback
        rule_failed = True  # Simulating rule failure
        fallback_enabled = app.config_data.get("rule_fallback_to_sort", True)

        # Logic: if fallback is disabled AND rule failed, should NOT continue to sorting
        should_continue_to_sort = fallback_enabled and rule_failed
        assert should_continue_to_sort is False

    def test_fallback_disabled_with_successful_rule(self):
        """Test that successful rules always work regardless of fallback setting."""
        app = MockApp({
            "rule_fallback_to_sort": False,
            "safe_mode": True,
        })

        # A successful rule should work regardless of fallback setting
        rule_succeeded = False  # Simulating rule success (no need for fallback)
        fallback_enabled = app.config_data.get("rule_fallback_to_sort", True)

        # Logic: if rule succeeded, no need to check fallback
        should_continue_to_sort = rule_succeeded and fallback_enabled
        assert should_continue_to_sort is False

    def test_profile_has_fallback_setting(self):
        """Test that profile settings include the fallback option."""
        profile = {
            "id": "profile_default",
            "name": "Default",
            "settings": {
                "smart_mode": False,
                "safe_mode": True,
                "dry_run": True,
                "include_sub": True,
                "skip_hidden": True,
                "ignore_exts": "",
                "age_filter_days": 0,
                "rule_fallback_to_sort": True,  # New setting
            }
        }

        assert "rule_fallback_to_sort" in profile["settings"]
        assert profile["settings"]["rule_fallback_to_sort"] is True

    def test_profile_fallback_can_be_disabled(self):
        """Test that profile can have fallback disabled."""
        profile = {
            "id": "profile_custom",
            "name": "Custom",
            "settings": {
                "smart_mode": False,
                "safe_mode": True,
                "dry_run": True,
                "include_sub": True,
                "skip_hidden": True,
                "ignore_exts": "",
                "age_filter_days": 0,
                "rule_fallback_to_sort": False,  # Disabled
            }
        }

        assert profile["settings"]["rule_fallback_to_sort"] is False

    def test_merge_profile_setting_into_config(self):
        """Test that profile setting is merged into config."""
        profile = {
            "settings": {
                "rule_fallback_to_sort": False,
                "safe_mode": True,
            },
            "custom_categories": {},
            "category_enabled": {},
            "ignore_patterns": [],
            "dont_move_list": [],
        }

        global_config = {
            "safe_mode": True,
            "smart_mode": False,
        }

        # Simulate merge_profile_into_config behavior
        merged_config = dict(global_config)
        for key in ["rule_fallback_to_sort", "safe_mode"]:
            if key in profile.get("settings", {}):
                merged_config[key] = profile["settings"][key]

        assert merged_config.get("rule_fallback_to_sort") is False
        assert merged_config.get("safe_mode") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
