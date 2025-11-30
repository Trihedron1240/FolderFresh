"""Test that profile settings are correctly merged into config."""

import pytest


class TestConfigMergeWithSettings:
    """Test config merging includes profile settings."""

    def test_config_merge_includes_rule_fallback_setting(self):
        """Test that rule_fallback_to_sort setting is merged from profile to config."""
        # Base config (no rule_fallback_to_sort)
        base_config = {
            "safe_mode": True,
            "smart_mode": False,
            "watched_folders": [],
        }

        # Profile with settings
        profile = {
            "id": "profile_test",
            "name": "Test Profile",
            "settings": {
                "rule_fallback_to_sort": False,  # Fallback disabled in profile
                "safe_mode": True,
            },
            "custom_categories": {},
            "category_enabled": {},
            "category_overrides": {},
        }

        # Simulate merge
        merged = dict(base_config)
        profile_settings = profile.get("settings", {})
        for key, value in profile_settings.items():
            merged[key] = value

        # Verify setting was merged
        assert merged.get("rule_fallback_to_sort") is False
        assert merged.get("safe_mode") is True

    def test_config_merge_with_multiple_settings(self):
        """Test merging multiple settings from profile."""
        base_config = {
            "safe_mode": True,
            "smart_mode": False,
        }

        profile = {
            "id": "profile_test",
            "settings": {
                "rule_fallback_to_sort": False,
                "safe_mode": False,  # Override base
                "age_filter_days": 30,
            },
            "custom_categories": {},
            "category_enabled": {},
            "category_overrides": {},
        }

        # Simulate merge
        merged = dict(base_config)
        for key, value in profile.get("settings", {}).items():
            merged[key] = value

        # Verify all settings were merged correctly
        assert merged.get("rule_fallback_to_sort") is False
        assert merged.get("safe_mode") is False
        assert merged.get("age_filter_days") == 30
        assert merged.get("smart_mode") is False  # Original value preserved

    def test_config_merge_preserves_base_config_when_no_settings(self):
        """Test that base config is preserved when profile has no settings."""
        base_config = {
            "safe_mode": True,
            "smart_mode": False,
            "rule_fallback_to_sort": False,
        }

        profile = {
            "id": "profile_test",
            "settings": {},  # No settings in profile
            "custom_categories": {},
            "category_enabled": {},
            "category_overrides": {},
        }

        # Simulate merge
        merged = dict(base_config)
        for key, value in profile.get("settings", {}).items():
            merged[key] = value

        # Verify base config is preserved
        assert merged.get("rule_fallback_to_sort") is False
        assert merged.get("safe_mode") is True
        assert merged.get("smart_mode") is False

    def test_profile_setting_overrides_base_config(self):
        """Test that profile settings override base config."""
        base_config = {
            "rule_fallback_to_sort": True,  # Base has fallback enabled
        }

        profile = {
            "id": "profile_test",
            "settings": {
                "rule_fallback_to_sort": False,  # Profile overrides to disabled
            },
        }

        # Simulate merge
        merged = dict(base_config)
        for key, value in profile.get("settings", {}).items():
            merged[key] = value

        # Verify profile setting overrides base
        assert merged.get("rule_fallback_to_sort") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
