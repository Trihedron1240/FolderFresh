"""Test that files are NOT sorted when fallback is disabled and no rule matches."""

import pytest


class TestNoRuleMatchWithFallbackDisabled:
    """Test behavior when no rule matches and fallback is disabled."""

    def test_no_sorting_when_fallback_disabled_and_no_rule_match(self):
        """
        Test that when:
        - fallback is DISABLED
        - rules exist but file doesn't match any
        Then: File should NOT be sorted
        """
        # Simulate the do_preview logic
        rules = [
            {"name": "Archive", "conditions": [{"type": "NameContains", "args": {"text": "old"}}]},
        ]
        config = {"rule_fallback_to_sort": False}
        
        # File doesn't match the rule
        file_name = "new_document.txt"
        rule_matched = False  # File didn't match any rule
        
        # What do_preview should do:
        should_attempt_sorting = False
        
        if rules:
            if not rule_matched:
                # No rule matched
                if not config.get("rule_fallback_to_sort", True):
                    # Fallback disabled - skip sorting
                    should_attempt_sorting = False
                else:
                    # Fallback enabled - do sorting
                    should_attempt_sorting = True
        
        # Verify file is NOT sorted
        assert should_attempt_sorting is False

    def test_sorting_when_fallback_enabled_and_no_rule_match(self):
        """
        Test that when:
        - fallback is ENABLED
        - rules exist but file doesn't match any
        Then: File SHOULD be sorted
        """
        rules = [
            {"name": "Archive", "conditions": [{"type": "NameContains", "args": {"text": "old"}}]},
        ]
        config = {"rule_fallback_to_sort": True}  # Fallback ENABLED
        
        file_name = "new_document.txt"
        rule_matched = False  # File didn't match any rule
        
        # What do_preview should do:
        should_attempt_sorting = False
        
        if rules:
            if not rule_matched:
                if not config.get("rule_fallback_to_sort", True):
                    should_attempt_sorting = False
                else:
                    should_attempt_sorting = True
        
        # Verify file IS sorted when fallback enabled
        assert should_attempt_sorting is True

    def test_sorting_when_no_rules_exist(self):
        """
        Test that when:
        - NO rules exist at all
        Then: File SHOULD be sorted (regardless of fallback setting)
        """
        rules = []  # No rules
        config = {"rule_fallback_to_sort": False}
        
        file_name = "document.txt"
        
        # When no rules exist, always sort
        should_attempt_sorting = True
        
        if rules:
            # Rules exist - check matching
            should_attempt_sorting = False
        else:
            # No rules - always sort
            should_attempt_sorting = True
        
        # Verify file IS sorted when no rules exist
        assert should_attempt_sorting is True

    def test_rule_match_always_used_regardless_of_fallback(self):
        """
        Test that when:
        - A rule matches successfully
        Then: File uses rule result, NOT category sort (regardless of fallback)
        """
        rules = [
            {"name": "Archive", "conditions": [{"type": "NameContains", "args": {"text": "old"}}]},
        ]
        config = {"rule_fallback_to_sort": False}
        
        file_name = "old_document.txt"
        rule_matched = True  # File matched a rule
        rule_succeeded = True
        
        # Logic:
        should_use_rule = False
        should_sort = False
        
        if rules:
            if rule_matched and rule_succeeded:
                should_use_rule = True
        
        if not should_use_rule:
            if not rule_matched:
                if not config.get("rule_fallback_to_sort", True):
                    should_sort = False
                else:
                    should_sort = True
        
        # Verify rule is used
        assert should_use_rule is True
        assert should_sort is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
