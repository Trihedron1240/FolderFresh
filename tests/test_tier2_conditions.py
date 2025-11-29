"""
Comprehensive tests for Tier-2 advanced conditions.

Tests cover:
- ColorIsCondition for matching color labels
- HasTagCondition for matching tags
- MetadataContainsCondition for content matching
- MetadataFieldEqualsCondition for exact matching
- IsDuplicateCondition for duplicate detection
"""

import os
import pytest
import tempfile
from pathlib import Path
from folderfresh.rule_engine import (
    ColorIsCondition,
    HasTagCondition,
    MetadataContainsCondition,
    MetadataFieldEqualsCondition,
    IsDuplicateCondition,
    METADATA_DB,
)
from folderfresh.fileinfo import get_fileinfo


@pytest.mark.unit
class TestColorIsCondition:
    """Test ColorIsCondition for color matching."""

    def test_color_is_match(self, tmp_path):
        """Test matching a file with specific color."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        # Set color label
        METADATA_DB.set_color(str(test_file), "red")

        fileinfo = get_fileinfo(test_file)
        condition = ColorIsCondition("red")

        result = condition.evaluate(fileinfo)
        assert result is True

    def test_color_is_no_match(self, tmp_path):
        """Test when color doesn't match."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        # Set different color
        METADATA_DB.set_color(str(test_file), "blue")

        fileinfo = get_fileinfo(test_file)
        condition = ColorIsCondition("red")

        result = condition.evaluate(fileinfo)
        assert result is False

    def test_color_is_no_label(self, tmp_path):
        """Test when file has no color label."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        fileinfo = get_fileinfo(test_file)
        condition = ColorIsCondition("red")

        result = condition.evaluate(fileinfo)
        assert result is False

    def test_color_is_case_insensitive(self, tmp_path):
        """Test case-insensitive color matching."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        METADATA_DB.set_color(str(test_file), "RED")

        fileinfo = get_fileinfo(test_file)
        condition = ColorIsCondition("red")

        result = condition.evaluate(fileinfo)
        assert result is True


@pytest.mark.unit
class TestHasTagCondition:
    """Test HasTagCondition for tag matching."""

    def test_has_tag_match(self, tmp_path):
        """Test matching a file with specific tag."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        # Add tag
        METADATA_DB.add_tag(str(test_file), "important")

        fileinfo = get_fileinfo(test_file)
        condition = HasTagCondition("important")

        result = condition.evaluate(fileinfo)
        assert result is True

    def test_has_tag_no_match(self, tmp_path):
        """Test when tag doesn't exist."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        # Add different tag
        METADATA_DB.add_tag(str(test_file), "urgent")

        fileinfo = get_fileinfo(test_file)
        condition = HasTagCondition("important")

        result = condition.evaluate(fileinfo)
        assert result is False

    def test_has_tag_multiple_tags(self, tmp_path):
        """Test matching when file has multiple tags."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        # Add multiple tags
        METADATA_DB.add_tag(str(test_file), "important")
        METADATA_DB.add_tag(str(test_file), "urgent")
        METADATA_DB.add_tag(str(test_file), "confidential")

        fileinfo = get_fileinfo(test_file)

        # All should match
        assert HasTagCondition("important").evaluate(fileinfo) is True
        assert HasTagCondition("urgent").evaluate(fileinfo) is True
        assert HasTagCondition("confidential").evaluate(fileinfo) is True

        # Non-existent should not match
        assert HasTagCondition("archived").evaluate(fileinfo) is False


@pytest.mark.unit
class TestMetadataContainsCondition:
    """Test MetadataContainsCondition for content matching."""

    def test_metadata_contains_match(self, tmp_path):
        """Test matching metadata content."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        # Set metadata
        metadata = {
            "author": "John Smith",
            "title": "Project Proposal"
        }
        METADATA_DB.set_metadata(str(test_file), metadata)

        fileinfo = get_fileinfo(test_file)
        condition = MetadataContainsCondition("author", "John")

        result = condition.evaluate(fileinfo)
        assert result is True

    def test_metadata_contains_no_match(self, tmp_path):
        """Test when content doesn't match."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        metadata = {"author": "Jane Doe"}
        METADATA_DB.set_metadata(str(test_file), metadata)

        fileinfo = get_fileinfo(test_file)
        condition = MetadataContainsCondition("author", "John")

        result = condition.evaluate(fileinfo)
        assert result is False

    def test_metadata_contains_nested_field(self, tmp_path):
        """Test matching nested metadata fields."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        metadata = {
            "exif": {
                "CameraModel": "Canon EOS R5"
            }
        }
        METADATA_DB.set_metadata(str(test_file), metadata)

        fileinfo = get_fileinfo(test_file)
        condition = MetadataContainsCondition("exif.CameraModel", "Canon")

        result = condition.evaluate(fileinfo)
        assert result is True

    def test_metadata_contains_case_insensitive(self, tmp_path):
        """Test case-insensitive matching."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        metadata = {"author": "John Smith"}
        METADATA_DB.set_metadata(str(test_file), metadata)

        fileinfo = get_fileinfo(test_file)
        condition = MetadataContainsCondition("author", "JOHN")

        result = condition.evaluate(fileinfo)
        assert result is True


@pytest.mark.unit
class TestMetadataFieldEqualsCondition:
    """Test MetadataFieldEqualsCondition for exact matching."""

    def test_metadata_field_equals_match(self, tmp_path):
        """Test exact metadata matching."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        metadata = {"status": "completed"}
        METADATA_DB.set_metadata(str(test_file), metadata)

        fileinfo = get_fileinfo(test_file)
        condition = MetadataFieldEqualsCondition("status", "completed")

        result = condition.evaluate(fileinfo)
        assert result is True

    def test_metadata_field_equals_no_match(self, tmp_path):
        """Test when exact value doesn't match."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        metadata = {"status": "pending"}
        METADATA_DB.set_metadata(str(test_file), metadata)

        fileinfo = get_fileinfo(test_file)
        condition = MetadataFieldEqualsCondition("status", "completed")

        result = condition.evaluate(fileinfo)
        assert result is False

    def test_metadata_field_equals_case_insensitive(self, tmp_path):
        """Test case-insensitive exact matching."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")

        metadata = {"Status": "COMPLETED"}
        METADATA_DB.set_metadata(str(test_file), metadata)

        fileinfo = get_fileinfo(test_file)
        condition = MetadataFieldEqualsCondition("Status", "completed")

        result = condition.evaluate(fileinfo)
        assert result is True


@pytest.mark.unit
class TestIsDuplicateCondition:
    """Test IsDuplicateCondition for duplicate detection."""

    def test_is_duplicate_match(self, tmp_path):
        """Test detecting duplicate files."""
        # Create two files with same content
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("identical content")
        file2.write_text("identical content")

        # Store hashes for both
        from folderfresh.rule_engine import calculate_quick_hash
        hash1 = calculate_quick_hash(str(file1))
        hash2 = calculate_quick_hash(str(file2))

        METADATA_DB.set_hash(str(file1), file1.stat().st_size, hash1)
        METADATA_DB.set_hash(str(file2), file2.stat().st_size, hash2)

        # Check if file2 is detected as duplicate
        fileinfo2 = get_fileinfo(file2)
        condition = IsDuplicateCondition("quick")

        result = condition.evaluate(fileinfo2)
        assert result is True

    def test_is_duplicate_no_match(self, tmp_path):
        """Test when no duplicates exist."""
        file1 = tmp_path / "unique.txt"
        file1.write_text("unique content that doesn't match anything")

        fileinfo = get_fileinfo(file1)
        condition = IsDuplicateCondition("quick")

        result = condition.evaluate(fileinfo)
        assert result is False

    def test_is_duplicate_match_type_quick(self, tmp_path):
        """Test quick hash duplicate detection."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content")
        file2.write_text("content")

        from folderfresh.rule_engine import calculate_quick_hash
        hash_val = calculate_quick_hash(str(file1))

        METADATA_DB.set_hash(str(file1), file1.stat().st_size, hash_val)
        METADATA_DB.set_hash(str(file2), file2.stat().st_size, hash_val)

        fileinfo = get_fileinfo(file2)
        condition = IsDuplicateCondition(match_type="quick")

        result = condition.evaluate(fileinfo)
        assert result is True
