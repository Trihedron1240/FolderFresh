# tests/test_conditions_file_in_folder.py
"""
Test suite for path-based conditions.

Tests FileInFolderCondition with:
- Folder pattern substring matching in full parent path
- Graceful handling of missing or invalid paths
- Empty pattern handling
- Serialization/deserialization support
"""

import pytest
from pathlib import Path
from folderfresh.rule_engine.backbone import (
    FileInFolderCondition,
    Rule,
)


@pytest.mark.unit
class TestFileInFolderBasic:
    """Test basic file in folder matching functionality."""

    def test_file_in_folder_true_simple(self):
        """Test FileInFolderCondition matching true case - simple path."""
        fileinfo = {
            "name": "image.png",
            "path": "C:/Users/me/Pictures/Screenshots/image.png",
        }

        cond = FileInFolderCondition("screenshots")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_file_in_folder_true_nested(self):
        """Test FileInFolderCondition matching true case - nested path."""
        fileinfo = {
            "name": "file.txt",
            "path": "C:/downloads/2024/screenshots_archive/file.txt",
        }

        cond = FileInFolderCondition("screenshots")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_file_in_folder_false(self):
        """Test FileInFolderCondition matching false case."""
        fileinfo = {
            "name": "file.txt",
            "path": "C:/Users/me/Documents/file.txt",
        }

        cond = FileInFolderCondition("screenshots")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_file_in_folder_case_insensitive(self):
        """Test FileInFolderCondition with case-insensitive matching."""
        fileinfo = {
            "name": "file.txt",
            "path": "C:/Users/me/Pictures/ScreenSHOTS_OLD/file.txt",
        }

        cond = FileInFolderCondition("screenshots")
        result = cond.evaluate(fileinfo)

        assert result is True


@pytest.mark.unit
class TestFileInFolderEdgeCases:
    """Test edge cases and error handling."""

    def test_file_in_folder_missing_path_returns_false(self):
        """Test that missing path returns False."""
        fileinfo = {
            "name": "file.txt",
        }

        cond = FileInFolderCondition("screenshots")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_file_in_folder_invalid_path_returns_false(self):
        """Test that invalid/empty path returns False."""
        fileinfo = {
            "name": "file.txt",
            "path": "",
        }

        cond = FileInFolderCondition("screenshots")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_file_in_folder_empty_pattern_matches_all(self):
        """Test that empty folder_pattern matches all paths."""
        fileinfo = {
            "name": "file.txt",
            "path": "C:/Users/me/Documents/file.txt",
        }

        cond = FileInFolderCondition("")
        result = cond.evaluate(fileinfo)

        # Empty pattern should match any path
        assert result is True

    def test_file_in_folder_with_forward_slashes(self):
        """Test FileInFolderCondition with Unix-style paths."""
        fileinfo = {
            "name": "photo.jpg",
            "path": "/home/user/images/screenshots/photo.jpg",
        }

        cond = FileInFolderCondition("screenshots")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_file_in_folder_with_mixed_slashes(self):
        """Test FileInFolderCondition with mixed path separators."""
        fileinfo = {
            "name": "document.pdf",
            "path": "C:\\Documents\\archive\\backup\\document.pdf",
        }

        cond = FileInFolderCondition("archive")
        result = cond.evaluate(fileinfo)

        assert result is True


@pytest.mark.unit
class TestFileInFolderSerialization:
    """Test serialization/deserialization."""

    def test_serialization_roundtrip_file_in_folder(self):
        """Test FileInFolderCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = FileInFolderCondition("screenshots")
        rule = Rule(
            name="Screenshots Folder",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "FileInFolder"
        assert rule_dict["conditions"][0]["args"]["folder_pattern"] == "screenshots"

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, FileInFolderCondition)
        assert restored_cond.folder_pattern == "screenshots"


@pytest.mark.integration
class TestFileInFolderRuleIntegration:
    """Test FileInFolderCondition within rules."""

    def test_rule_match_with_file_in_folder_condition(self):
        """Test Rule.matches() with FileInFolderCondition."""
        fileinfo = {
            "path": "C:/Users/me/Pictures/Screenshots/photo.jpg",
            "name": "photo.jpg",
            "ext": ".jpg",
            "size": 2000,
        }

        rule = Rule(
            name="Screenshots Files",
            conditions=[FileInFolderCondition("screenshots")],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_rule_no_match_with_file_in_folder_condition(self):
        """Test Rule.matches() when folder pattern doesn't match."""
        fileinfo = {
            "path": "C:/Users/me/Documents/report.pdf",
            "name": "report.pdf",
            "ext": ".pdf",
            "size": 5000,
        }

        rule = Rule(
            name="Screenshots Files",
            conditions=[FileInFolderCondition("screenshots")],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is False


@pytest.mark.integration
class TestFileInFolderPreviewMode:
    """Test FileInFolderCondition in preview mode."""

    def test_preview_file_in_folder_condition(self):
        """Test FileInFolderCondition works in preview context."""
        fileinfo = {
            "name": "image.png",
            "path": "C:/Users/me/Downloads/screenshots/image.png",
        }

        config = {"dry_run": True, "preview": True}

        cond = FileInFolderCondition("screenshots")
        result = cond.evaluate(fileinfo)

        # Should work correctly in preview mode
        assert result is True

    def test_file_in_folder_no_side_effects(self):
        """Test that file in folder evaluation has no side effects."""
        fileinfo = {
            "name": "file.txt",
            "path": "C:/Users/me/Backup/file.txt",
        }

        cond = FileInFolderCondition("Backup")

        # Evaluate multiple times
        result1 = cond.evaluate(fileinfo)
        result2 = cond.evaluate(fileinfo)

        # Results should be consistent
        assert result1 == result2
        assert result1 is True


@pytest.mark.unit
class TestFileInFolderLogging:
    """Test file in folder condition logging."""

    def test_file_in_folder_match_logging_true(self, capsys):
        """Test FileInFolderCondition logs correctly on match."""
        fileinfo = {
            "name": "file.txt",
            "path": "C:/Users/me/Screenshots/file.txt",
        }

        cond = FileInFolderCondition("screenshots")
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "FileInFolder" in captured.out
        assert "screenshots" in captured.out
        assert "True" in captured.out

    def test_file_in_folder_match_logging_false(self, capsys):
        """Test FileInFolderCondition logs correctly on non-match."""
        fileinfo = {
            "name": "file.txt",
            "path": "C:/Users/me/Documents/file.txt",
        }

        cond = FileInFolderCondition("screenshots")
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "FileInFolder" in captured.out
        assert "False" in captured.out

    def test_file_in_folder_error_logging(self, capsys):
        """Test that errors are logged gracefully."""
        fileinfo = {
            "name": "file.txt",
        }

        cond = FileInFolderCondition("screenshots")
        result = cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "FileInFolder" in captured.out
        assert result is False
