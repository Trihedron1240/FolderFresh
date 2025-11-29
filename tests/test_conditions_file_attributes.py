# tests/test_conditions_file_attributes.py
"""
Test suite for file attribute conditions.

Tests IsHiddenCondition, IsReadOnlyCondition, and IsDirectoryCondition.
"""

import os
import stat
import pytest
from pathlib import Path
from folderfresh.rule_engine.backbone import (
    IsHiddenCondition,
    IsReadOnlyCondition,
    IsDirectoryCondition,
    Rule,
)


@pytest.mark.unit
class TestIsHiddenCondition:
    """Test IsHiddenCondition."""

    def test_is_hidden_starts_with_dot(self):
        """Test IsHiddenCondition matching Unix-style hidden files."""
        fileinfo = {
            "name": ".hidden.txt",
            "path": "/path/.hidden.txt",
        }

        cond = IsHiddenCondition()
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_is_hidden_dot_prefix_true(self):
        """Test IsHiddenCondition with dot prefix."""
        fileinfo = {
            "name": ".gitignore",
            "path": "/path/.gitignore",
        }

        cond = IsHiddenCondition()
        assert cond.evaluate(fileinfo) is True

    def test_is_hidden_normal_file(self):
        """Test IsHiddenCondition with normal file."""
        fileinfo = {
            "name": "normal.txt",
            "path": "/path/normal.txt",
        }

        cond = IsHiddenCondition()
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_is_hidden_no_name(self):
        """Test IsHiddenCondition with missing name."""
        fileinfo = {
            "path": "/path/file.txt",
        }

        cond = IsHiddenCondition()
        result = cond.evaluate(fileinfo)

        # Should be False (no "." prefix in empty string)
        assert result is False

    def test_is_hidden_windows_attribute(self):
        """Test IsHiddenCondition with Windows hidden attribute."""
        # Create a mock stat object with Windows hidden attribute
        class MockStat:
            st_file_attributes = 0x2  # FILE_ATTRIBUTE_HIDDEN

        fileinfo = {
            "name": "file.txt",
            "path": "/path/file.txt",
            "stat": MockStat(),
        }

        cond = IsHiddenCondition()
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_is_hidden_windows_not_hidden(self):
        """Test IsHiddenCondition with Windows attribute not hidden."""
        # Create a mock stat object without hidden attribute
        class MockStat:
            st_file_attributes = 0x0  # No hidden attribute

        fileinfo = {
            "name": "file.txt",
            "path": "/path/file.txt",
            "stat": MockStat(),
        }

        cond = IsHiddenCondition()
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_is_hidden_dot_prefix_takes_precedence(self):
        """Test that dot prefix is checked first."""
        class MockStat:
            st_file_attributes = 0x0  # No hidden attribute

        fileinfo = {
            "name": ".hidden",
            "path": "/path/.hidden",
            "stat": MockStat(),
        }

        cond = IsHiddenCondition()
        # Should be True because of dot prefix, even though stat says not hidden
        assert cond.evaluate(fileinfo) is True


@pytest.mark.unit
class TestIsReadOnlyCondition:
    """Test IsReadOnlyCondition."""

    def test_is_read_only_true(self, tmp_path):
        """Test IsReadOnlyCondition with read-only file."""
        test_file = tmp_path / "readonly.txt"
        test_file.write_text("content")

        # Make file read-only
        os.chmod(test_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
        }

        cond = IsReadOnlyCondition()
        result = cond.evaluate(fileinfo)

        # Restore permissions for cleanup
        os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR)

        assert result is True

    def test_is_read_only_false(self, tmp_path):
        """Test IsReadOnlyCondition with writable file."""
        test_file = tmp_path / "writable.txt"
        test_file.write_text("content")

        # File is writable by default
        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
        }

        cond = IsReadOnlyCondition()
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_is_read_only_missing_path(self):
        """Test IsReadOnlyCondition with missing path."""
        fileinfo = {
            "name": "file.txt",
        }

        cond = IsReadOnlyCondition()
        result = cond.evaluate(fileinfo)

        # Should be False when path is missing
        assert result is False

    def test_is_read_only_nonexistent_file(self):
        """Test IsReadOnlyCondition with non-existent file."""
        fileinfo = {
            "path": "/nonexistent/file.txt",
            "name": "file.txt",
        }

        cond = IsReadOnlyCondition()
        result = cond.evaluate(fileinfo)

        # Non-existent files cannot be written to, so they are read-only
        assert result is True


@pytest.mark.unit
class TestIsDirectoryCondition:
    """Test IsDirectoryCondition."""

    def test_is_directory_true(self, tmp_path):
        """Test IsDirectoryCondition with directory."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        fileinfo = {
            "path": str(test_dir),
            "name": test_dir.name,
        }

        cond = IsDirectoryCondition()
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_is_directory_false(self, tmp_path):
        """Test IsDirectoryCondition with file."""
        test_file = tmp_path / "testfile.txt"
        test_file.write_text("content")

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
        }

        cond = IsDirectoryCondition()
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_is_directory_missing_path(self):
        """Test IsDirectoryCondition with missing path."""
        fileinfo = {
            "name": "something",
        }

        cond = IsDirectoryCondition()
        result = cond.evaluate(fileinfo)

        # Should be False when path is missing
        assert result is False

    def test_is_directory_nonexistent(self):
        """Test IsDirectoryCondition with non-existent path."""
        fileinfo = {
            "path": "/nonexistent/path",
            "name": "path",
        }

        cond = IsDirectoryCondition()
        result = cond.evaluate(fileinfo)

        # Should be False for non-existent paths
        assert result is False


@pytest.mark.unit
class TestConditionSerialization:
    """Test serialization/deserialization of file attribute conditions."""

    def test_is_hidden_serialization_roundtrip(self):
        """Test IsHiddenCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = IsHiddenCondition()
        rule = Rule(
            name="Find Hidden",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "IsHidden"

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, IsHiddenCondition)

    def test_is_read_only_serialization_roundtrip(self):
        """Test IsReadOnlyCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = IsReadOnlyCondition()
        rule = Rule(
            name="Protected Files",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "IsReadOnly"

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, IsReadOnlyCondition)

    def test_is_directory_serialization_roundtrip(self):
        """Test IsDirectoryCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        cond = IsDirectoryCondition()
        rule = Rule(
            name="Find Directories",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "IsDirectory"

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, IsDirectoryCondition)


@pytest.mark.integration
class TestRuleIntegration:
    """Test file attribute conditions within rules."""

    def test_rule_match_with_is_hidden(self):
        """Test Rule.matches() with IsHiddenCondition."""
        fileinfo = {
            "path": "/path/.hidden.txt",
            "name": ".hidden.txt",
            "ext": ".txt",
            "size": 100,
        }

        rule = Rule(
            name="Hidden Files",
            conditions=[IsHiddenCondition()],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_rule_match_with_is_read_only(self, tmp_path):
        """Test Rule.matches() with IsReadOnlyCondition."""
        test_file = tmp_path / "readonly.txt"
        test_file.write_text("content")
        os.chmod(test_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "ext": ".txt",
            "size": 100,
        }

        rule = Rule(
            name="Protected Files",
            conditions=[IsReadOnlyCondition()],
            actions=[],
            match_mode="all"
        )

        result = rule.matches(fileinfo)

        # Restore permissions for cleanup
        os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR)

        assert result is True

    def test_rule_match_with_is_directory(self, tmp_path):
        """Test Rule.matches() with IsDirectoryCondition."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        fileinfo = {
            "path": str(test_dir),
            "name": test_dir.name,
        }

        rule = Rule(
            name="Find Folders",
            conditions=[IsDirectoryCondition()],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_rule_match_combined_conditions(self):
        """Test Rule with multiple file attribute conditions."""
        from folderfresh.rule_engine.backbone import NameContainsCondition

        fileinfo = {
            "path": "/path/.backup.txt",
            "name": ".backup.txt",
            "ext": ".txt",
            "size": 100,
        }

        rule = Rule(
            name="Hidden Backups",
            conditions=[
                NameContainsCondition("backup"),
                IsHiddenCondition(),
            ],
            actions=[],
            match_mode="all"
        )

        # Should match both conditions
        assert rule.matches(fileinfo) is True


@pytest.mark.integration
class TestPreviewMode:
    """Test file attribute conditions in preview mode."""

    def test_is_hidden_preview(self):
        """Test IsHiddenCondition works in preview context."""
        fileinfo = {
            "name": ".secret.txt",
            "path": "/path/.secret.txt",
        }

        config = {"dry_run": True, "preview": True}

        cond = IsHiddenCondition()
        result = cond.evaluate(fileinfo)

        # Should still work correctly
        assert result is True

    def test_is_directory_preview(self, tmp_path):
        """Test IsDirectoryCondition works in preview context."""
        test_dir = tmp_path / "dir"
        test_dir.mkdir()

        fileinfo = {
            "path": str(test_dir),
            "name": test_dir.name,
        }

        config = {"dry_run": True}

        cond = IsDirectoryCondition()
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_conditions_no_side_effects(self, tmp_path):
        """Test that conditions have no side effects in preview."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
        }

        # Evaluate conditions multiple times
        cond = IsReadOnlyCondition()
        result1 = cond.evaluate(fileinfo)
        result2 = cond.evaluate(fileinfo)

        # Results should be consistent
        assert result1 == result2

        # File should still be intact
        assert test_file.exists()
        assert test_file.read_text() == "content"


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_is_hidden_empty_filename(self):
        """Test IsHiddenCondition with empty filename."""
        fileinfo = {
            "name": "",
            "path": "/path/",
        }

        cond = IsHiddenCondition()
        result = cond.evaluate(fileinfo)

        # Empty string doesn't start with "."
        assert result is False

    def test_is_hidden_dot_only(self):
        """Test IsHiddenCondition with just a dot."""
        fileinfo = {
            "name": ".",
            "path": "/path/.",
        }

        cond = IsHiddenCondition()
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_is_directory_symlink(self, tmp_path):
        """Test IsDirectoryCondition with symlink to directory."""
        actual_dir = tmp_path / "actual"
        actual_dir.mkdir()

        link_dir = tmp_path / "link"
        try:
            link_dir.symlink_to(actual_dir)

            fileinfo = {
                "path": str(link_dir),
                "name": link_dir.name,
            }

            cond = IsDirectoryCondition()
            # os.path.isdir follows symlinks
            result = cond.evaluate(fileinfo)

            assert result is True
        except OSError:
            # Skip if symlinks not supported
            pytest.skip("Symlinks not supported on this system")

    def test_multiple_conditions_no_crash(self, tmp_path):
        """Test multiple conditions don't crash with edge case inputs."""
        fileinfo = {
            "path": str(tmp_path),
            "name": tmp_path.name,
        }

        conds = [
            IsHiddenCondition(),
            IsReadOnlyCondition(),
            IsDirectoryCondition(),
        ]

        for cond in conds:
            # Should not raise exceptions
            result = cond.evaluate(fileinfo)
            assert isinstance(result, bool)


@pytest.mark.unit
class TestConditionLogging:
    """Test that conditions produce correct log output."""

    def test_is_hidden_logging_true(self, capsys):
        """Test IsHiddenCondition logs correctly."""
        fileinfo = {
            "name": ".secret.txt",
            "path": "/path/.secret.txt",
        }

        cond = IsHiddenCondition()
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "IsHidden" in captured.out
        assert "True" in captured.out

    def test_is_read_only_logging(self, capsys, tmp_path):
        """Test IsReadOnlyCondition logs correctly."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
        }

        cond = IsReadOnlyCondition()
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "IsReadOnly" in captured.out

    def test_is_directory_logging(self, capsys, tmp_path):
        """Test IsDirectoryCondition logs correctly."""
        test_dir = tmp_path / "dir"
        test_dir.mkdir()

        fileinfo = {
            "path": str(test_dir),
            "name": test_dir.name,
        }

        cond = IsDirectoryCondition()
        cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "IsDirectory" in captured.out
        assert "True" in captured.out
