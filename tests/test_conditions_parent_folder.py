# tests/test_conditions_parent_folder.py
"""
Test suite for path-based conditions.

Tests ParentFolderContainsCondition with:
- Case-insensitive substring matching in parent folder names
- Graceful handling of missing or invalid paths
- Empty substring handling
- Serialization/deserialization support
"""

import pytest
from pathlib import Path
from folderfresh.rule_engine.backbone import (
    ParentFolderContainsCondition,
    Rule,
)


@pytest.mark.unit
class TestParentFolderContainsBasic:
    """Test basic parent folder matching functionality."""

    def test_parent_folder_contains_true(self):
        """Test ParentFolderContainsCondition matching true case."""
        fileinfo = {
            "name": "document.txt",
            "path": "/home/user/Downloads/document.txt",
        }

        cond = ParentFolderContainsCondition("Downloads")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_parent_folder_contains_false(self):
        """Test ParentFolderContainsCondition matching false case."""
        fileinfo = {
            "name": "file.txt",
            "path": "/home/user/Documents/file.txt",
        }

        cond = ParentFolderContainsCondition("Downloads")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_parent_folder_contains_case_insensitive(self):
        """Test ParentFolderContainsCondition with case-insensitive matching."""
        fileinfo = {
            "name": "file.txt",
            "path": "/home/user/MyDownloads/file.txt",
        }

        cond = ParentFolderContainsCondition("downloads")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_parent_folder_contains_case_insensitive_uppercase(self):
        """Test ParentFolderContainsCondition matching uppercase substring."""
        fileinfo = {
            "name": "file.txt",
            "path": "/home/user/mydocuments/file.txt",
        }

        cond = ParentFolderContainsCondition("DOCUMENTS")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_parent_folder_contains_partial_match(self):
        """Test ParentFolderContainsCondition with partial folder name match."""
        fileinfo = {
            "name": "image.png",
            "path": "/home/user/Backup_old_files/image.png",
        }

        cond = ParentFolderContainsCondition("backup")
        result = cond.evaluate(fileinfo)

        assert result is True


@pytest.mark.unit
class TestParentFolderContainsEdgeCases:
    """Test edge cases and error handling."""

    def test_parent_folder_missing_path_returns_false(self):
        """Test that missing path returns False."""
        fileinfo = {
            "name": "file.txt",
        }

        cond = ParentFolderContainsCondition("Downloads")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_parent_folder_empty_path_returns_false(self):
        """Test that empty path returns False."""
        fileinfo = {
            "name": "file.txt",
            "path": "",
        }

        cond = ParentFolderContainsCondition("Downloads")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_parent_folder_invalid_path_returns_false(self):
        """Test that invalid path is handled gracefully."""
        fileinfo = {
            "name": "file.txt",
            "path": None,
        }

        cond = ParentFolderContainsCondition("Downloads")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_parent_folder_empty_substring_matches_all(self):
        """Test that empty substring matches all parent folders."""
        fileinfo = {
            "name": "file.txt",
            "path": "/home/user/Documents/file.txt",
        }

        cond = ParentFolderContainsCondition("")
        result = cond.evaluate(fileinfo)

        # Empty substring should match any folder name
        assert result is True

    def test_parent_folder_root_path_returns_false(self):
        """Test that root path (no parent) returns False."""
        fileinfo = {
            "name": "file.txt",
            "path": "/file.txt",
        }

        cond = ParentFolderContainsCondition("anything")
        result = cond.evaluate(fileinfo)

        # Root path has empty parent name
        assert result is False

    def test_parent_folder_relative_path(self):
        """Test ParentFolderContainsCondition with relative path."""
        fileinfo = {
            "name": "file.txt",
            "path": "Documents/file.txt",
        }

        cond = ParentFolderContainsCondition("Documents")
        result = cond.evaluate(fileinfo)

        assert result is True


@pytest.mark.unit
class TestParentFolderContainsSerialization:
    """Test serialization/deserialization."""

    def test_serialization_roundtrip(self):
        """Test ParentFolderContainsCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = ParentFolderContainsCondition("Downloads")
        rule = Rule(
            name="Downloads Folder",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "ParentFolderContains"
        assert rule_dict["conditions"][0]["args"]["substring"] == "Downloads"

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, ParentFolderContainsCondition)
        assert restored_cond.substring == "Downloads"

    def test_serialization_case_sensitive_substring(self):
        """Test serialization preserves substring exactly."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = ParentFolderContainsCondition("MyFolder")
        rule = Rule(
            name="My Folder",
            conditions=[cond],
            actions=[]
        )

        rule_dict = rule_to_dict(rule)
        assert rule_dict["conditions"][0]["args"]["substring"] == "MyFolder"

        restored_rule = dict_to_rule(rule_dict)
        assert restored_rule.conditions[0].substring == "MyFolder"


@pytest.mark.integration
class TestParentFolderRuleIntegration:
    """Test ParentFolderContainsCondition within rules."""

    def test_rule_match_with_parent_folder_condition(self):
        """Test Rule.matches() with ParentFolderContainsCondition."""
        fileinfo = {
            "path": "/home/user/Downloads/document.pdf",
            "name": "document.pdf",
            "ext": ".pdf",
            "size": 1000,
        }

        rule = Rule(
            name="Downloads Files",
            conditions=[ParentFolderContainsCondition("Downloads")],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_rule_no_match_with_parent_folder_condition(self):
        """Test Rule.matches() when parent folder doesn't match."""
        fileinfo = {
            "path": "/home/user/Documents/document.pdf",
            "name": "document.pdf",
            "ext": ".pdf",
            "size": 1000,
        }

        rule = Rule(
            name="Downloads Files",
            conditions=[ParentFolderContainsCondition("Downloads")],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is False

    def test_rule_with_multiple_conditions_including_parent_folder(self):
        """Test Rule with parent folder and other conditions."""
        from folderfresh.rule_engine import NameContainsCondition

        fileinfo = {
            "path": "/home/user/Backup/report_2024.txt",
            "name": "report_2024.txt",
            "ext": ".txt",
            "size": 2000,
        }

        rule = Rule(
            name="Backup Reports",
            conditions=[
                NameContainsCondition("report"),
                ParentFolderContainsCondition("Backup"),
            ],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_rule_with_multiple_conditions_partial_match(self):
        """Test Rule with parent folder condition when only one matches."""
        from folderfresh.rule_engine import NameContainsCondition

        fileinfo = {
            "path": "/home/user/Backup/image.png",
            "name": "image.png",
            "ext": ".png",
            "size": 5000,
        }

        rule = Rule(
            name="Backup Reports",
            conditions=[
                NameContainsCondition("report"),
                ParentFolderContainsCondition("Backup"),
            ],
            actions=[],
            match_mode="all"
        )

        # Only parent folder matches, not name
        assert rule.matches(fileinfo) is False


@pytest.mark.integration
class TestParentFolderPreviewMode:
    """Test ParentFolderContainsCondition in preview mode."""

    def test_parent_folder_preview_mode(self):
        """Test ParentFolderContainsCondition works in preview context."""
        fileinfo = {
            "name": "file.txt",
            "path": "/home/user/Downloads/file.txt",
        }

        config = {"dry_run": True, "preview": True}

        cond = ParentFolderContainsCondition("Downloads")
        result = cond.evaluate(fileinfo)

        # Should work correctly in preview mode
        assert result is True

    def test_parent_folder_no_side_effects(self):
        """Test that parent folder evaluation has no side effects."""
        fileinfo = {
            "name": "document.pdf",
            "path": "/home/user/Archive/document.pdf",
        }

        cond = ParentFolderContainsCondition("Archive")

        # Evaluate multiple times
        result1 = cond.evaluate(fileinfo)
        result2 = cond.evaluate(fileinfo)

        # Results should be consistent
        assert result1 == result2
        assert result1 is True


@pytest.mark.unit
class TestParentFolderContainsLogging:
    """Test parent folder condition logging."""

    def test_parent_folder_match_logging_true(self, capsys):
        """Test ParentFolderContainsCondition logs correctly on match."""
        fileinfo = {
            "name": "file.txt",
            "path": "/home/user/Downloads/file.txt",
        }

        cond = ParentFolderContainsCondition("Downloads")
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "ParentFolderContains" in captured.out
        assert "Downloads" in captured.out
        assert "True" in captured.out

    def test_parent_folder_match_logging_false(self, capsys):
        """Test ParentFolderContainsCondition logs correctly on non-match."""
        fileinfo = {
            "name": "file.txt",
            "path": "/home/user/Documents/file.txt",
        }

        cond = ParentFolderContainsCondition("Downloads")
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "ParentFolderContains" in captured.out
        assert "False" in captured.out

    def test_parent_folder_error_logging(self, capsys):
        """Test that errors are logged gracefully."""
        fileinfo = {
            "name": "file.txt",
        }

        cond = ParentFolderContainsCondition("Downloads")
        result = cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "ParentFolderContains" in captured.out
        assert result is False
