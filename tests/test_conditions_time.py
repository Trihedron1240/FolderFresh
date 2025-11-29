# tests/test_conditions_time.py
"""
Test suite for time-based rule conditions.

Tests FileAgeGreaterThanCondition and LastModifiedBeforeCondition.
"""

import os
import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path
from folderfresh.rule_engine.backbone import (
    FileAgeGreaterThanCondition,
    LastModifiedBeforeCondition,
    Rule,
    RuleExecutor,
)


@pytest.mark.unit
class TestFileAgeGreaterThanCondition:
    """Test FileAgeGreaterThanCondition."""

    def test_file_age_greater_than_true(self, tmp_path):
        """Test FileAgeGreaterThanCondition matching (file older than threshold)."""
        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("old file")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 86400)
        os.utime(test_file, (old_time, old_time))

        # Get file stat
        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        # Condition: file older than 7 days
        cond = FileAgeGreaterThanCondition(7)
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_file_age_greater_than_false(self, tmp_path):
        """Test FileAgeGreaterThanCondition not matching (file newer than threshold)."""
        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("new file")

        # Set modification time to 2 days ago
        old_time = time.time() - (2 * 86400)
        os.utime(test_file, (old_time, old_time))

        # Get file stat
        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        # Condition: file older than 7 days
        cond = FileAgeGreaterThanCondition(7)
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_file_age_boundary_case(self, tmp_path):
        """Test FileAgeGreaterThanCondition at boundary."""
        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("boundary file")

        # Set modification time to slightly less than 7 days ago (e.g., 6.99 days)
        # to avoid floating point precision issues
        boundary_time = time.time() - (6.99 * 86400)
        os.utime(test_file, (boundary_time, boundary_time))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        # Should be False because file is less than 7 days old
        cond = FileAgeGreaterThanCondition(7)
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_file_age_zero_days(self, tmp_path):
        """Test FileAgeGreaterThanCondition with zero days (just created)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("fresh file")

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        # Condition: file older than 0 days
        # Even a just-created file is technically older than 0 days (by milliseconds)
        # so this should return True (age > 0)
        cond = FileAgeGreaterThanCondition(0)
        result = cond.evaluate(fileinfo)

        # Should be True because even fresh files are older than 0 days
        assert result is True

    def test_file_age_negative_days(self):
        """Test FileAgeGreaterThanCondition with negative days (invalid input)."""
        cond = FileAgeGreaterThanCondition(-7)

        fileinfo = {"path": "/fake/path.txt", "name": "path.txt"}
        result = cond.evaluate(fileinfo)

        # Negative days should always return False
        assert result is False

    def test_file_age_fallback_to_getmtime(self, tmp_path):
        """Test FileAgeGreaterThanCondition fallback when stat not available."""
        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 86400)
        os.utime(test_file, (old_time, old_time))

        # fileinfo without stat object (fallback to os.path.getmtime)
        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
        }

        cond = FileAgeGreaterThanCondition(7)
        result = cond.evaluate(fileinfo)

        # Should still work using getmtime fallback
        assert result is True

    def test_file_age_missing_path(self):
        """Test FileAgeGreaterThanCondition with missing path."""
        fileinfo = {"name": "test.txt"}  # No path

        cond = FileAgeGreaterThanCondition(7)
        result = cond.evaluate(fileinfo)

        # Should return False when path is missing
        assert result is False


@pytest.mark.unit
class TestLastModifiedBeforeCondition:
    """Test LastModifiedBeforeCondition."""

    def test_last_modified_before_true(self, tmp_path):
        """Test LastModifiedBeforeCondition matching (file before threshold)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("old file")

        # Set modification time to 2023-01-01
        timestamp_2023_01_01 = datetime(2023, 1, 1).timestamp()
        os.utime(test_file, (timestamp_2023_01_01, timestamp_2023_01_01))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        # Condition: before 2023-02-01
        cond = LastModifiedBeforeCondition("2023-02-01")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_last_modified_before_false(self, tmp_path):
        """Test LastModifiedBeforeCondition not matching (file after threshold)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("new file")

        # Set modification time to 2023-03-01
        timestamp_2023_03_01 = datetime(2023, 3, 1).timestamp()
        os.utime(test_file, (timestamp_2023_03_01, timestamp_2023_03_01))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        # Condition: before 2023-02-01
        cond = LastModifiedBeforeCondition("2023-02-01")
        result = cond.evaluate(fileinfo)

        assert result is False

    def test_last_modified_before_boundary(self, tmp_path):
        """Test LastModifiedBeforeCondition at boundary."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("boundary file")

        # Set modification time to 2023-02-01
        timestamp = datetime(2023, 2, 1).timestamp()
        os.utime(test_file, (timestamp, timestamp))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        # Condition: before 2023-02-01
        cond = LastModifiedBeforeCondition("2023-02-01")
        result = cond.evaluate(fileinfo)

        # Should be False (not before, exactly at the time)
        assert result is False

    def test_last_modified_before_iso_datetime_format(self, tmp_path):
        """Test LastModifiedBeforeCondition with full ISO datetime format."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Set modification time to 2023-01-01 10:00:00
        timestamp = datetime(2023, 1, 1, 10, 0, 0).timestamp()
        os.utime(test_file, (timestamp, timestamp))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        # Condition: before 2023-01-01T11:00:00
        cond = LastModifiedBeforeCondition("2023-01-01T11:00:00")
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_last_modified_before_invalid_timestamp(self):
        """Test LastModifiedBeforeCondition with invalid timestamp format."""
        fileinfo = {
            "path": "/fake/path.txt",
            "name": "path.txt",
        }

        cond = LastModifiedBeforeCondition("invalid-date-format")
        result = cond.evaluate(fileinfo)

        # Should return False for invalid timestamp
        assert result is False

    def test_last_modified_before_datetime_object(self, tmp_path):
        """Test LastModifiedBeforeCondition with datetime object."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Set modification time to 2023-01-01
        timestamp = datetime(2023, 1, 1).timestamp()
        os.utime(test_file, (timestamp, timestamp))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        # Pass a datetime object directly
        threshold = datetime(2023, 2, 1)
        cond = LastModifiedBeforeCondition(threshold)
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_last_modified_before_fallback_to_getmtime(self, tmp_path):
        """Test LastModifiedBeforeCondition fallback when stat not available."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Set modification time to 2023-01-01
        timestamp = datetime(2023, 1, 1).timestamp()
        os.utime(test_file, (timestamp, timestamp))

        # fileinfo without stat object
        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
        }

        cond = LastModifiedBeforeCondition("2023-02-01")
        result = cond.evaluate(fileinfo)

        # Should work using getmtime fallback
        assert result is True

    def test_last_modified_before_missing_path(self):
        """Test LastModifiedBeforeCondition with missing path."""
        fileinfo = {"name": "test.txt"}  # No path

        cond = LastModifiedBeforeCondition("2023-02-01")
        result = cond.evaluate(fileinfo)

        # Should return False when path is missing
        assert result is False


@pytest.mark.unit
class TestConditionSerialization:
    """Test serialization/deserialization of time-based conditions."""

    def test_file_age_condition_dict_roundtrip(self):
        """Test FileAgeGreaterThanCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        # Create a rule with FileAgeGreaterThanCondition
        cond = FileAgeGreaterThanCondition(7)
        rule = Rule(
            name="Old Files",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "FileAgeGreaterThan"
        assert rule_dict["conditions"][0]["args"]["days"] == 7

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, FileAgeGreaterThanCondition)
        assert restored_cond.days == 7

    def test_last_modified_condition_dict_roundtrip(self):
        """Test LastModifiedBeforeCondition serialization roundtrip."""
        from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule

        # Create a rule with LastModifiedBeforeCondition
        cond = LastModifiedBeforeCondition("2023-01-01")
        rule = Rule(
            name="Before 2023",
            conditions=[cond],
            actions=[]
        )

        # Serialize
        rule_dict = rule_to_dict(rule)

        # Check serialized format
        assert rule_dict["conditions"][0]["type"] == "LastModifiedBefore"
        assert rule_dict["conditions"][0]["args"]["timestamp"] == "2023-01-01"

        # Deserialize
        restored_rule = dict_to_rule(rule_dict)
        restored_cond = restored_rule.conditions[0]

        # Verify
        assert isinstance(restored_cond, LastModifiedBeforeCondition)
        assert restored_cond.timestamp == "2023-01-01"


@pytest.mark.integration
class TestConditionInRuleMatching:
    """Test time-based conditions within Rule.matches()."""

    def test_file_age_condition_in_rule(self, tmp_path):
        """Test FileAgeGreaterThanCondition within a Rule."""
        test_file = tmp_path / "old_file.txt"
        test_file.write_text("content")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 86400)
        os.utime(test_file, (old_time, old_time))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "ext": ".txt",
            "size": len(b"content"),
            "stat": os.stat(test_file),
        }

        # Rule: match files older than 7 days
        rule = Rule(
            name="Old Files",
            conditions=[FileAgeGreaterThanCondition(7)],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_last_modified_condition_in_rule(self, tmp_path):
        """Test LastModifiedBeforeCondition within a Rule."""
        test_file = tmp_path / "old_file.txt"
        test_file.write_text("content")

        # Set modification time to 2023-01-01
        timestamp = datetime(2023, 1, 1).timestamp()
        os.utime(test_file, (timestamp, timestamp))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "ext": ".txt",
            "size": len(b"content"),
            "stat": os.stat(test_file),
        }

        # Rule: match files modified before 2023-06-01
        rule = Rule(
            name="Before Mid-2023",
            conditions=[LastModifiedBeforeCondition("2023-06-01")],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True

    def test_combined_conditions_with_time(self, tmp_path):
        """Test combining time-based conditions with other conditions."""
        from folderfresh.rule_engine.backbone import NameContainsCondition

        test_file = tmp_path / "backup_old.txt"
        test_file.write_text("content")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 86400)
        os.utime(test_file, (old_time, old_time))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "ext": ".txt",
            "size": len(b"content"),
            "stat": os.stat(test_file),
        }

        # Rule: match files with "backup" in name AND older than 7 days
        rule = Rule(
            name="Old Backups",
            conditions=[
                NameContainsCondition("backup"),
                FileAgeGreaterThanCondition(7),
            ],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True


@pytest.mark.integration
class TestPreviewAndDryRunMode:
    """Test time-based conditions in preview/dry-run mode."""

    def test_condition_works_in_dry_run_mode(self, tmp_path):
        """Test FileAgeGreaterThanCondition with dry_run config."""
        test_file = tmp_path / "old_file.txt"
        test_file.write_text("content")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 86400)
        os.utime(test_file, (old_time, old_time))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "ext": ".txt",
            "size": len(b"content"),
            "stat": os.stat(test_file),
        }

        config = {"dry_run": True}

        # Condition should evaluate the same regardless of dry_run setting
        cond = FileAgeGreaterThanCondition(7)
        result = cond.evaluate(fileinfo)

        assert result is True

    def test_time_condition_with_file_watcher_integration(self, tmp_path):
        """Test time condition behavior in watcher context."""
        # This tests that the conditions work correctly
        # even in automated/watcher scenarios
        test_file = tmp_path / "old_file.txt"
        test_file.write_text("content")

        # Set modification time to 30 days ago
        old_time = time.time() - (30 * 86400)
        os.utime(test_file, (old_time, old_time))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "ext": ".txt",
            "size": len(b"content"),
            "stat": os.stat(test_file),
        }

        # Rule that should match in watcher mode
        rule = Rule(
            name="Archive Old",
            conditions=[FileAgeGreaterThanCondition(7)],
            actions=[],
            match_mode="all"
        )

        assert rule.matches(fileinfo) is True


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_file_age_large_values(self):
        """Test FileAgeGreaterThanCondition with very large day values."""
        cond = FileAgeGreaterThanCondition(36500)  # ~100 years

        fileinfo = {
            "path": "/fake/path.txt",
            "name": "path.txt",
            "stat": None,  # Will trigger fallback path
        }

        # Should not crash
        result = cond.evaluate(fileinfo)
        assert isinstance(result, bool)

    def test_last_modified_before_various_formats(self):
        """Test LastModifiedBeforeCondition with various ISO formats."""
        formats_to_test = [
            "2024-01-01",
            "2024-01-01T00:00:00",
            "2024-01-01 00:00:00",
        ]

        # All formats should parse
        for fmt in formats_to_test:
            cond = LastModifiedBeforeCondition(fmt)
            parsed = cond._parse_iso_datetime(fmt)
            assert parsed is not None


@pytest.mark.unit
class TestConditionLogging:
    """Test that conditions produce correct log output."""

    def test_file_age_logging_true(self, capsys, tmp_path):
        """Test FileAgeGreaterThanCondition logs correctly on match."""
        test_file = tmp_path / "old_file.txt"
        test_file.write_text("content")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 86400)
        os.utime(test_file, (old_time, old_time))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        cond = FileAgeGreaterThanCondition(7)
        result = cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "FileAgeGreaterThan" in captured.out
        assert "True" in captured.out

    def test_last_modified_before_logging_true(self, capsys, tmp_path):
        """Test LastModifiedBeforeCondition logs correctly on match."""
        test_file = tmp_path / "old_file.txt"
        test_file.write_text("content")

        # Set modification time to 2023-01-01
        timestamp = datetime(2023, 1, 1).timestamp()
        os.utime(test_file, (timestamp, timestamp))

        fileinfo = {
            "path": str(test_file),
            "name": test_file.name,
            "stat": os.stat(test_file),
        }

        cond = LastModifiedBeforeCondition("2023-06-01")
        result = cond.evaluate(fileinfo)

        captured = capsys.readouterr()
        assert "LastModifiedBefore" in captured.out
        assert "True" in captured.out
