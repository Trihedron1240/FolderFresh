# tests/test_conditions_name_based.py
"""
Test suite for name-based conditions.

Tests NameStartsWithCondition, NameEndsWithCondition, and NameEqualsCondition.
"""

import pytest
from folderfresh.rule_engine.backbone import (
    NameStartsWithCondition,
    NameEndsWithCondition,
    NameEqualsCondition,
    Rule,
)


@pytest.mark.unit
class TestNameStartsWithCondition:
    """Test NameStartsWithCondition."""

    def test_name_starts_with_true(self):
        """Test NameStartsWithCondition matching true case."""
        fileinfo = {
            "name": "draft_report.txt",
            "path": "/path/draft_report.txt",
        }

        cond = NameStartsWithCondition("draft")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_name_starts_with_false(self):
        """Test NameStartsWithCondition matching false case."""
        fileinfo = {
            "name": "final_report.txt",
            "path": "/path/final_report.txt",
        }

        cond = NameStartsWithCondition("draft")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_name_starts_with_case_insensitive(self):
        """Test NameStartsWithCondition is case-insensitive."""
        fileinfo = {
            "name": "DRAFT_report.txt",
            "path": "/path/DRAFT_report.txt",
        }

        cond = NameStartsWithCondition("draft")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_name_starts_with_missing_name(self):
        """Test NameStartsWithCondition with missing name."""
        fileinfo = {
            "path": "/path/file.txt",
        }

        cond = NameStartsWithCondition("draft")
        result = cond.evaluate(fileinfo)

        # Should be False (empty string doesn't start with anything)
        assert result is False

    def test_name_starts_with_empty_prefix(self):
        """Test NameStartsWithCondition with empty prefix."""
        fileinfo = {
            "name": "report.txt",
            "path": "/path/report.txt",
        }

        cond = NameStartsWithCondition("")
        result = cond.evaluate(fileinfo)

        # Empty prefix matches any filename
        assert result is True


@pytest.mark.unit
class TestNameEndsWithCondition:
    """Test NameEndsWithCondition."""

    def test_name_ends_with_true(self):
        """Test NameEndsWithCondition matching true case."""
        fileinfo = {
            "name": "data.backup",
            "path": "/path/data.backup",
        }

        cond = NameEndsWithCondition("backup")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_name_ends_with_false(self):
        """Test NameEndsWithCondition matching false case."""
        fileinfo = {
            "name": "data_archive.zip",
            "path": "/path/data_archive.zip",
        }

        cond = NameEndsWithCondition("backup")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_name_ends_with_case_insensitive(self):
        """Test NameEndsWithCondition is case-insensitive."""
        fileinfo = {
            "name": "data.BACKUP",
            "path": "/path/data.BACKUP",
        }

        cond = NameEndsWithCondition("backup")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_name_ends_with_missing_name(self):
        """Test NameEndsWithCondition with missing name."""
        fileinfo = {
            "path": "/path/file.txt",
        }

        cond = NameEndsWithCondition("backup")
        result = cond.evaluate(fileinfo)

        # Should be False (empty string doesn't end with anything)
        assert result is False

    def test_name_ends_with_empty_suffix(self):
        """Test NameEndsWithCondition with empty suffix."""
        fileinfo = {
            "name": "report.txt",
            "path": "/path/report.txt",
        }

        cond = NameEndsWithCondition("")
        result = cond.evaluate(fileinfo)

        # Empty suffix matches any filename
        assert result is True


@pytest.mark.unit
class TestNameEqualsCondition:
    """Test NameEqualsCondition."""

    def test_name_equals_case_insensitive_true(self):
        """Test NameEqualsCondition case-insensitive match."""
        fileinfo = {
            "name": "README.md",
            "path": "/path/README.md",
        }

        cond = NameEqualsCondition("readme.md", case_sensitive=False)
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_name_equals_case_insensitive_false(self):
        """Test NameEqualsCondition case-insensitive non-match."""
        fileinfo = {
            "name": "notes.md",
            "path": "/path/notes.md",
        }

        cond = NameEqualsCondition("readme.md", case_sensitive=False)
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_name_equals_case_sensitive_true(self):
        """Test NameEqualsCondition case-sensitive match."""
        fileinfo = {
            "name": "README.md",
            "path": "/path/README.md",
        }

        cond = NameEqualsCondition("README.md", case_sensitive=True)
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_name_equals_case_sensitive_false_exact_case(self):
        """Test NameEqualsCondition case-sensitive non-match due to case."""
        fileinfo = {
            "name": "readme.md",
            "path": "/path/readme.md",
        }

        cond = NameEqualsCondition("README.md", case_sensitive=True)
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_name_equals_default_case_insensitive(self):
        """Test NameEqualsCondition defaults to case-insensitive."""
        fileinfo = {
            "name": "TestFile.txt",
            "path": "/path/TestFile.txt",
        }

        cond = NameEqualsCondition("testfile.txt")
        result = cond.evaluate(fileinfo)

        # Should be True (defaults to case_sensitive=False)
        assert result is True

    def test_name_equals_missing_name(self):
        """Test NameEqualsCondition with missing name."""
        fileinfo = {
            "path": "/path/file.txt",
        }

        cond = NameEqualsCondition("readme.md")
        result = cond.evaluate(fileinfo)

        # Empty string doesn't equal "readme.md"
        assert result is False

    def test_name_equals_empty_value(self):
        """Test NameEqualsCondition with empty value."""
        fileinfo = {
            "name": "report.txt",
            "path": "/path/report.txt",
        }

        cond = NameEqualsCondition("")
        result = cond.evaluate(fileinfo)

        # Empty value doesn't match non-empty filename
        assert result is False


@pytest.mark.unit
class TestConditionSerialization:
    """Test serialization/deserialization of name-based conditions."""

    def test_name_starts_with_serialization_roundtrip(self):
        """Test NameStartsWithCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = NameStartsWithCondition("draft")
        rule = Rule(
            name="Draft Files",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "NameStartsWith"
        assert rule_dict["conditions"][0]["args"]["prefix"] == "draft"

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, NameStartsWithCondition)
        assert restored_cond.prefix == "draft"

    def test_name_ends_with_serialization_roundtrip(self):
        """Test NameEndsWithCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = NameEndsWithCondition("backup")
        rule = Rule(
            name="Backup Files",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "NameEndsWith"
        assert rule_dict["conditions"][0]["args"]["suffix"] == "backup"

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, NameEndsWithCondition)
        assert restored_cond.suffix == "backup"

    def test_name_equals_serialization_roundtrip(self):
        """Test NameEqualsCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = NameEqualsCondition("README.md", case_sensitive=True)
        rule = Rule(
            name="Exact Match",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "NameEquals"
        assert rule_dict["conditions"][0]["args"]["value"] == "README.md"
        assert rule_dict["conditions"][0]["args"]["case_sensitive"] is True

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, NameEqualsCondition)
        assert restored_cond.value == "README.md"
        assert restored_cond.case_sensitive is True


@pytest.mark.integration
class TestRuleIntegration:
    """Test name-based conditions within rules."""

    def test_rule_match_with_name_starts_with(self):
        """Test Rule.matches() with NameStartsWithCondition."""
        fileinfo = {
            "path": "/path/draft_proposal.docx",
            "name": "draft_proposal.docx",
            "ext": ".docx",
            "size": 100,
        }

        rule = Rule(
            name="Draft Documents",
            conditions=[NameStartsWithCondition("draft")],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_rule_match_with_name_ends_with(self):
        """Test Rule.matches() with NameEndsWithCondition."""
        fileinfo = {
            "path": "/path/project.backup",
            "name": "project.backup",
            "ext": ".backup",
            "size": 5000000,
        }

        rule = Rule(
            name="Backup Archives",
            conditions=[NameEndsWithCondition("backup")],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_rule_match_with_name_equals(self):
        """Test Rule.matches() with NameEqualsCondition."""
        fileinfo = {
            "path": "/path/README.md",
            "name": "README.md",
            "ext": ".md",
            "size": 1000,
        }

        rule = Rule(
            name="Main Readme",
            conditions=[NameEqualsCondition("README.md", case_sensitive=True)],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_rule_match_combined_name_conditions(self):
        """Test Rule with multiple name conditions."""
        fileinfo = {
            "path": "/path/draft_data.backup",
            "name": "draft_data.backup",
            "ext": ".backup",
            "size": 500,
        }

        rule = Rule(
            name="Draft Backups",
            conditions=[
                NameStartsWithCondition("draft"),
                NameEndsWithCondition("backup"),
            ],
            actions=[],
            match_mode="all"
        )

        # Should match both conditions
        assert rule.matches(fileinfo) is True

    def test_rule_no_match_combined_conditions(self):
        """Test Rule with combined conditions that don't all match."""
        fileinfo = {
            "path": "/path/final_report.txt",
            "name": "final_report.txt",
            "ext": ".txt",
            "size": 500,
        }

        rule = Rule(
            name="Draft Backups",
            conditions=[
                NameStartsWithCondition("draft"),
                NameEndsWithCondition("backup"),
            ],
            actions=[],
            match_mode="all"
        )

        # Should not match (neither condition is true)
        assert rule.matches(fileinfo) is False


@pytest.mark.integration
class TestPreviewMode:
    """Test name-based conditions in preview mode."""

    def test_name_starts_with_preview(self):
        """Test NameStartsWithCondition works in preview context."""
        fileinfo = {
            "name": "draft_memo.txt",
            "path": "/path/draft_memo.txt",
        }

        config = {"dry_run": True, "preview": True}

        cond = NameStartsWithCondition("draft")
        result = cond.evaluate(fileinfo)

        # Should still work correctly in preview mode
        assert result is True

    def test_name_equals_preview(self):
        """Test NameEqualsCondition works in preview context."""
        fileinfo = {
            "name": "config.json",
            "path": "/path/config.json",
        }

        config = {"dry_run": True}

        cond = NameEqualsCondition("config.json", case_sensitive=True)
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_conditions_no_side_effects(self):
        """Test that conditions have no side effects in preview."""
        fileinfo = {
            "name": "test_file.txt",
            "path": "/path/test_file.txt",
        }

        # Evaluate conditions multiple times
        cond = NameStartsWithCondition("test")
        result1 = cond.evaluate(fileinfo)
        result2 = cond.evaluate(fileinfo)

        # Results should be consistent
        assert result1 == result2
        assert result1 is True


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_name_starts_with_special_characters(self):
        """Test NameStartsWithCondition with special characters."""
        fileinfo = {
            "name": "[IMPORTANT]_report.txt",
            "path": "/path/[IMPORTANT]_report.txt",
        }

        cond = NameStartsWithCondition("[important]")
        result = cond.evaluate(fileinfo)

        # Should work with special characters (case-insensitive)
        assert result is True

    def test_name_ends_with_unicode(self):
        """Test NameEndsWithCondition with unicode characters in filename."""
        fileinfo = {
            "name": "résumé_2024",
            "path": "/path/résumé_2024",
        }

        cond = NameEndsWithCondition("2024")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_name_equals_whitespace(self):
        """Test NameEqualsCondition with whitespace in filenames."""
        fileinfo = {
            "name": "My Documents.txt",
            "path": "/path/My Documents.txt",
        }

        cond = NameEqualsCondition("my documents.txt")
        result = cond.evaluate(fileinfo)

        # Case-insensitive by default
        assert result is True

    def test_name_starts_with_entire_name(self):
        """Test NameStartsWithCondition matching entire filename."""
        fileinfo = {
            "name": "archive.zip",
            "path": "/path/archive.zip",
        }

        cond = NameStartsWithCondition("archive.zip")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_name_ends_with_entire_name(self):
        """Test NameEndsWithCondition matching entire filename."""
        fileinfo = {
            "name": "archive.zip",
            "path": "/path/archive.zip",
        }

        cond = NameEndsWithCondition("archive.zip")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_name_starts_with_partial_word(self):
        """Test NameStartsWithCondition with partial word match."""
        fileinfo = {
            "name": "backup_data_v1.tar.gz",
            "path": "/path/backup_data_v1.tar.gz",
        }

        cond = NameStartsWithCondition("back")
        result = cond.evaluate(fileinfo)

        # Should match "back" even though it's only part of "backup"
        assert result is True


@pytest.mark.unit
class TestConditionLogging:
    """Test that conditions produce correct log output."""

    def test_name_starts_with_logging_true(self, capsys):
        """Test NameStartsWithCondition logs correctly."""
        fileinfo = {
            "name": "draft_report.txt",
            "path": "/path/draft_report.txt",
        }

        cond = NameStartsWithCondition("draft")
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "NameStartsWith" in captured.out
        assert "draft" in captured.out
        assert "True" in captured.out

    def test_name_ends_with_logging_false(self, capsys):
        """Test NameEndsWithCondition logs correctly on non-match."""
        fileinfo = {
            "name": "report.txt",
            "path": "/path/report.txt",
        }

        cond = NameEndsWithCondition("backup")
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "NameEndsWith" in captured.out
        assert "backup" in captured.out
        assert "False" in captured.out

    def test_name_equals_logging(self, capsys):
        """Test NameEqualsCondition logs correctly."""
        fileinfo = {
            "name": "README.md",
            "path": "/path/README.md",
        }

        cond = NameEqualsCondition("README.md", case_sensitive=True)
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "NameEquals" in captured.out
        assert "README.md" in captured.out
        assert "case-sensitive" in captured.out
