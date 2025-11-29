# tests/test_conditions_regex.py
"""
Test suite for regex-based conditions.

Tests RegexMatchCondition with safety features:
- Invalid regex patterns handled gracefully
- Catastrophic backtracking protection via timeout
- Case sensitivity control
"""

import pytest
import re
from folderfresh.rule_engine.backbone import (
    RegexMatchCondition,
    Rule,
)


@pytest.mark.unit
class TestRegexMatchBasic:
    """Test basic regex matching functionality."""

    def test_regex_match_simple_true(self):
        """Test RegexMatchCondition matching true case."""
        fileinfo = {
            "name": "report_2024.txt",
            "path": "/path/report_2024.txt",
        }

        cond = RegexMatchCondition(r"report_\d{4}")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_regex_match_simple_false(self):
        """Test RegexMatchCondition matching false case."""
        fileinfo = {
            "name": "image.png",
            "path": "/path/image.png",
        }

        cond = RegexMatchCondition(r"report_\d+")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_regex_match_ignore_case_true(self):
        """Test RegexMatchCondition with case-insensitive flag."""
        fileinfo = {
            "name": "Report.TXT",
            "path": "/path/Report.TXT",
        }

        cond = RegexMatchCondition("report", ignore_case=True)
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_regex_match_ignore_case_false(self):
        """Test RegexMatchCondition with case-sensitive matching."""
        fileinfo = {
            "name": "Report.TXT",
            "path": "/path/Report.TXT",
        }

        cond = RegexMatchCondition("report", ignore_case=False)
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_regex_match_anchor_pattern(self):
        """Test RegexMatchCondition with anchor patterns."""
        fileinfo = {
            "name": "test_file.txt",
            "path": "/path/test_file.txt",
        }

        cond = RegexMatchCondition(r"^test_.*\.txt$")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_regex_match_wildcard_pattern(self):
        """Test RegexMatchCondition with wildcard patterns."""
        fileinfo = {
            "name": "backup_2024_v2.zip",
            "path": "/path/backup_2024_v2.zip",
        }

        cond = RegexMatchCondition(r".*backup.*")
        result = cond.evaluate(fileinfo)

        assert result is True


@pytest.mark.unit
class TestRegexMatchInvalid:
    """Test invalid regex handling."""

    def test_regex_invalid_pattern_does_not_crash(self):
        """Test that invalid regex pattern doesn't crash."""
        # Invalid pattern: unclosed bracket
        cond = RegexMatchCondition("*[")

        fileinfo = {
            "name": "test.txt",
            "path": "/path/test.txt",
        }

        # Should return False and not crash
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_regex_invalid_pattern_logged(self, capsys):
        """Test that invalid pattern is logged."""
        # Invalid pattern
        cond = RegexMatchCondition("(unclosed")

        fileinfo = {
            "name": "test.txt",
            "path": "/path/test.txt",
        }

        cond.evaluate(fileinfo)
        captured = capsys.readouterr()

        # Should log invalid pattern message
        assert "Invalid pattern" in captured.out or cond.compiled is None

    def test_regex_empty_pattern(self):
        """Test that empty pattern is handled."""
        cond = RegexMatchCondition("")

        fileinfo = {
            "name": "test.txt",
            "path": "/path/test.txt",
        }

        # Empty pattern should match (empty string matches anywhere)
        result = cond.evaluate(fileinfo)

        # Empty pattern is valid and matches
        assert result is True


@pytest.mark.unit
class TestRegexMatchCatastrophic:
    """Test catastrophic backtracking protection."""

    def test_regex_catastrophic_pattern_times_out(self):
        """Test that catastrophic backtracking pattern times out safely."""
        # Classic ReDoS pattern: (a+)+b
        # This will cause exponential backtracking when 'b' is missing (no match)
        # Use 20+ 'a's to trigger exponential backtracking
        cond = RegexMatchCondition("(a+)+b")

        fileinfo = {
            "name": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # No 'b' at end - triggers backtracking
            "path": "/path/aaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        }

        # Should timeout and return False, not hang the test
        result = cond.evaluate(fileinfo)

        # Catastrophic backtracking should be caught by timeout or return False
        assert result is False

    def test_regex_catastrophic_pattern_no_hang(self):
        """Test that catastrophic patterns don't cause infinite loops."""
        # Another ReDoS pattern
        cond = RegexMatchCondition("(x+x+)+y")

        fileinfo = {
            "name": "xxxxxxxxxxxxxxxxxxz",
            "path": "/path/xxxxxxxxxxxxxxxxxxz",
        }

        # Should complete quickly despite pattern
        result = cond.evaluate(fileinfo)

        # Should return False (no match or timeout)
        assert result is False


@pytest.mark.unit
class TestRegexMatchSerialization:
    """Test serialization/deserialization."""

    def test_serialization_roundtrip(self):
        """Test RegexMatchCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = RegexMatchCondition(r"^test.*\.txt$", ignore_case=False)
        rule = Rule(
            name="Test Files",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "RegexMatch"
        assert rule_dict["conditions"][0]["args"]["pattern"] == r"^test.*\.txt$"
        assert rule_dict["conditions"][0]["args"]["ignore_case"] is False

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, RegexMatchCondition)
        assert restored_cond.pattern == r"^test.*\.txt$"
        assert restored_cond.ignore_case is False

    def test_serialization_with_ignore_case(self):
        """Test serialization preserves ignore_case flag."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = RegexMatchCondition("backup", ignore_case=True)
        rule = Rule(
            name="Backups",
            conditions=[cond],
            actions=[]
        )

        rule_dict = rule_to_dict(rule)
        assert rule_dict["conditions"][0]["args"]["ignore_case"] is True

        restored_rule = dict_to_rule(rule_dict)
        assert restored_rule.conditions[0].ignore_case is True


@pytest.mark.integration
class TestRegexRuleIntegration:
    """Test RegexMatchCondition within rules."""

    def test_rule_match_with_regex(self):
        """Test Rule.matches() with RegexMatchCondition."""
        fileinfo = {
            "path": "/path/report_2024.txt",
            "name": "report_2024.txt",
            "ext": ".txt",
            "size": 1000,
        }

        rule = Rule(
            name="Year Reports",
            conditions=[RegexMatchCondition(r"report_\d{4}")],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_rule_no_match_with_regex(self):
        """Test Rule.matches() when regex doesn't match."""
        fileinfo = {
            "path": "/path/image.png",
            "name": "image.png",
            "ext": ".png",
            "size": 5000,
        }

        rule = Rule(
            name="Reports",
            conditions=[RegexMatchCondition(r"report_.*")],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is False

    def test_rule_with_multiple_conditions_including_regex(self):
        """Test Rule with regex and other conditions."""
        from folderfresh.rule_engine import NameContainsCondition

        fileinfo = {
            "path": "/path/backup_report_2024.txt",
            "name": "backup_report_2024.txt",
            "ext": ".txt",
            "size": 2000,
        }

        rule = Rule(
            name="Backup Reports",
            conditions=[
                NameContainsCondition("backup"),
                RegexMatchCondition(r".*_\d{4}\.txt"),
            ],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True


@pytest.mark.integration
class TestRegexPreviewMode:
    """Test RegexMatchCondition in preview mode."""

    def test_regex_preview_mode(self):
        """Test RegexMatchCondition works in preview context."""
        fileinfo = {
            "name": "test_file.txt",
            "path": "/path/test_file.txt",
        }

        config = {"dry_run": True, "preview": True}

        cond = RegexMatchCondition(r"test_.*\.txt")
        result = cond.evaluate(fileinfo)

        # Should work correctly in preview mode
        assert result is True

    def test_regex_no_side_effects(self):
        """Test that regex evaluation has no side effects."""
        fileinfo = {
            "name": "document.pdf",
            "path": "/path/document.pdf",
        }

        cond = RegexMatchCondition(r".*\.pdf$")

        # Evaluate multiple times
        result1 = cond.evaluate(fileinfo)
        result2 = cond.evaluate(fileinfo)

        # Results should be consistent
        assert result1 == result2
        assert result1 is True


@pytest.mark.unit
class TestRegexEdgeCases:
    """Test edge cases and special scenarios."""

    def test_regex_match_empty_filename(self):
        """Test RegexMatchCondition with empty filename."""
        fileinfo = {
            "name": "",
            "path": "/path/",
        }

        cond = RegexMatchCondition(".*")
        result = cond.evaluate(fileinfo)

        # Empty filename returns False (implementation choice for safety)
        assert result is False

    def test_regex_match_missing_filename(self):
        """Test RegexMatchCondition with missing name field."""
        fileinfo = {
            "path": "/path/file.txt",
        }

        cond = RegexMatchCondition("test")
        result = cond.evaluate(fileinfo)

        # Missing filename defaults to empty, which doesn't match
        assert result is False

    def test_regex_match_special_characters(self):
        """Test regex with special filename characters."""
        fileinfo = {
            "name": "[IMPORTANT]_file-2024.txt",
            "path": "/path/[IMPORTANT]_file-2024.txt",
        }

        cond = RegexMatchCondition(r"\[IMPORTANT\].*")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_regex_match_unicode(self):
        """Test regex with unicode characters in filename."""
        fileinfo = {
            "name": "café_résumé.txt",
            "path": "/path/café_résumé.txt",
        }

        cond = RegexMatchCondition(r".*résumé.*")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_regex_alternation_pattern(self):
        """Test regex with alternation (|) operator."""
        fileinfo = {
            "name": "backup.zip",
            "path": "/path/backup.zip",
        }

        cond = RegexMatchCondition(r"(backup|archive)\.(zip|tar)")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_regex_character_class(self):
        """Test regex with character classes."""
        fileinfo = {
            "name": "file123.txt",
            "path": "/path/file123.txt",
        }

        cond = RegexMatchCondition(r"file[0-9]+\.txt")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_regex_lookahead_pattern(self):
        """Test regex with lookahead."""
        fileinfo = {
            "name": "document.pdf",
            "path": "/path/document.pdf",
        }

        cond = RegexMatchCondition(r".*(?=\.pdf$)")
        result = cond.evaluate(fileinfo)

        assert result is True


@pytest.mark.unit
class TestRegexLogging:
    """Test regex condition logging."""

    def test_regex_match_logging_true(self, capsys):
        """Test RegexMatchCondition logs correctly on match."""
        fileinfo = {
            "name": "report_2024.txt",
            "path": "/path/report_2024.txt",
        }

        cond = RegexMatchCondition(r"report_\d{4}")
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "RegexMatch" in captured.out
        assert "True" in captured.out

    def test_regex_match_logging_false(self, capsys):
        """Test RegexMatchCondition logs correctly on non-match."""
        fileinfo = {
            "name": "image.png",
            "path": "/path/image.png",
        }

        cond = RegexMatchCondition(r"report_.*")
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "RegexMatch" in captured.out
        assert "False" in captured.out

    def test_regex_invalid_logging(self, capsys):
        """Test invalid regex is logged."""
        cond = RegexMatchCondition("(invalid")

        fileinfo = {
            "name": "test.txt",
            "path": "/path/test.txt",
        }

        cond.evaluate(fileinfo)
        captured = capsys.readouterr()

        # Should show invalid pattern message
        assert "invalid pattern" in captured.out.lower() or "Invalid" in captured.out

    def test_regex_timeout_logging(self, capsys):
        """Test that catastrophic patterns are logged."""
        cond = RegexMatchCondition("(a+)+b")

        fileinfo = {
            "name": "aaaaaaaaaaaaaaaaaaaaaaaaa",  # No 'b' - triggers backtracking
            "path": "/path/aaaaaaaaaaaaaaaaaaaaaaaaa",
        }

        cond.evaluate(fileinfo)
        captured = capsys.readouterr()

        # Should log False result (either matched=False or timeout)
        assert "False" in captured.out or "timeout" in captured.out.lower()
