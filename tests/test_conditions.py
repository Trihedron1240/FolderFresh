# test_conditions.py
"""
Test suite for rule conditions.
"""

import os
import pytest
from folderfresh.rule_engine.backbone import (
    NameContainsCondition,
    ExtensionIsCondition,
    FileSizeGreaterThanCondition
)


@pytest.mark.unit
class TestNameConditions:
    """Test name-based conditions."""

    def test_name_contains_match(self):
        """Test NameContainsCondition matching."""
        cond = NameContainsCondition("test")
        fileinfo = {"name": "test_file.txt", "path": "/path/test_file.txt"}
        assert cond.evaluate(fileinfo) is True

    def test_name_contains_no_match(self):
        """Test NameContainsCondition non-matching."""
        cond = NameContainsCondition("test")
        fileinfo = {"name": "document.txt", "path": "/path/document.txt"}
        assert cond.evaluate(fileinfo) is False

    def test_name_contains_case_insensitive(self):
        """Test NameContainsCondition is case-insensitive."""
        cond = NameContainsCondition("TEST")
        fileinfo = {"name": "test_file.txt", "path": "/path/test_file.txt"}
        assert cond.evaluate(fileinfo) is True

    def test_name_contains_partial_match(self):
        """Test NameContainsCondition with partial match."""
        cond = NameContainsCondition("report")
        fileinfo = {"name": "annual_report_2024.pdf", "path": "/path/annual_report_2024.pdf"}
        assert cond.evaluate(fileinfo) is True

    def test_name_contains_empty_string(self):
        """Test NameContainsCondition with empty string."""
        cond = NameContainsCondition("")
        fileinfo = {"name": "file.txt", "path": "/path/file.txt"}
        # Empty string is in all strings
        assert cond.evaluate(fileinfo) is True


@pytest.mark.unit
class TestExtensionConditions:
    """Test extension-based conditions."""

    def test_extension_is_match(self):
        """Test ExtensionIsCondition matching."""
        cond = ExtensionIsCondition(".pdf")
        fileinfo = {"name": "document.pdf", "ext": ".pdf", "path": "/path/document.pdf"}
        assert cond.evaluate(fileinfo) is True

    def test_extension_is_no_match(self):
        """Test ExtensionIsCondition non-matching."""
        cond = ExtensionIsCondition(".pdf")
        fileinfo = {"name": "document.txt", "ext": ".txt", "path": "/path/document.txt"}
        assert cond.evaluate(fileinfo) is False

    def test_extension_is_case_insensitive(self):
        """Test ExtensionIsCondition is case-insensitive."""
        cond = ExtensionIsCondition(".PDF")
        fileinfo = {"name": "document.pdf", "ext": ".pdf", "path": "/path/document.pdf"}
        assert cond.evaluate(fileinfo) is True

    def test_extension_is_with_different_types(self):
        """Test ExtensionIsCondition with various file types."""
        extensions = [".jpg", ".png", ".gif", ".zip", ".exe"]
        for ext in extensions:
            cond = ExtensionIsCondition(ext)
            fileinfo = {"name": f"file{ext}", "ext": ext, "path": f"/path/file{ext}"}
            assert cond.evaluate(fileinfo) is True

    def test_extension_is_no_extension(self):
        """Test ExtensionIsCondition with file without extension."""
        cond = ExtensionIsCondition(".txt")
        fileinfo = {"name": "README", "ext": "", "path": "/path/README"}
        assert cond.evaluate(fileinfo) is False


@pytest.mark.unit
class TestSizeConditions:
    """Test file size conditions."""

    def test_file_size_greater_than_match(self):
        """Test FileSizeGreaterThanCondition matching."""
        cond = FileSizeGreaterThanCondition(1024)  # 1 KB
        fileinfo = {"name": "large.txt", "size": 2048, "path": "/path/large.txt"}
        assert cond.evaluate(fileinfo) is True

    def test_file_size_greater_than_equal(self):
        """Test FileSizeGreaterThanCondition with equal size."""
        cond = FileSizeGreaterThanCondition(1024)
        fileinfo = {"name": "file.txt", "size": 1024, "path": "/path/file.txt"}
        # Greater than means strictly greater, so equal should be False
        assert cond.evaluate(fileinfo) is False

    def test_file_size_greater_than_no_match(self):
        """Test FileSizeGreaterThanCondition non-matching."""
        cond = FileSizeGreaterThanCondition(1024)
        fileinfo = {"name": "small.txt", "size": 512, "path": "/path/small.txt"}
        assert cond.evaluate(fileinfo) is False

    def test_size_conditions_with_large_files(self):
        """Test size conditions with larger file sizes."""
        # 1 MB = 1024 * 1024 bytes
        cond = FileSizeGreaterThanCondition(1024 * 1024)
        fileinfo = {"name": "file.bin", "size": 2048 * 1024, "path": "/path/file.bin"}
        assert cond.evaluate(fileinfo) is True

    def test_size_condition_zero_bytes(self):
        """Test size condition with zero-byte file."""
        cond = FileSizeGreaterThanCondition(1)
        fileinfo = {"name": "empty.txt", "size": 0, "path": "/path/empty.txt"}
        assert cond.evaluate(fileinfo) is False

    def test_size_condition_boundary(self):
        """Test size condition at exact boundary."""
        cond = FileSizeGreaterThanCondition(1000)
        # Just under
        fileinfo1 = {"name": "file.txt", "size": 999, "path": "/path/file.txt"}
        assert cond.evaluate(fileinfo1) is False

        # Just over
        fileinfo2 = {"name": "file.txt", "size": 1001, "path": "/path/file.txt"}
        assert cond.evaluate(fileinfo2) is True


@pytest.mark.unit
class TestConditionCombinations:
    """Test multiple conditions together."""

    def test_multiple_conditions_all_match(self):
        """Test multiple conditions all matching."""
        cond1 = NameContainsCondition("screenshot")
        cond2 = ExtensionIsCondition(".png")

        fileinfo = {"name": "screenshot_2024.png", "ext": ".png", "path": "/path/screenshot_2024.png"}

        assert cond1.evaluate(fileinfo) is True
        assert cond2.evaluate(fileinfo) is True

    def test_multiple_conditions_partial_match(self):
        """Test multiple conditions with partial match."""
        cond1 = NameContainsCondition("screenshot")
        cond2 = ExtensionIsCondition(".jpg")

        fileinfo = {"name": "screenshot_2024.png", "ext": ".png", "path": "/path/screenshot_2024.png"}

        assert cond1.evaluate(fileinfo) is True
        assert cond2.evaluate(fileinfo) is False

    def test_condition_with_missing_fileinfo_keys(self):
        """Test conditions handle missing fileinfo keys gracefully."""
        cond = ExtensionIsCondition(".pdf")
        fileinfo = {"name": "document"}  # Missing ext key

        # Should either return False or handle gracefully
        result = cond.evaluate(fileinfo)
        assert isinstance(result, bool)

    def test_name_and_size_conditions(self):
        """Test combining name and size conditions."""
        name_cond = NameContainsCondition("archive")
        size_cond = FileSizeGreaterThanCondition(5 * 1024 * 1024)  # 5 MB

        large_archive = {"name": "archive_2024.zip", "size": 10 * 1024 * 1024, "path": "/path/archive_2024.zip"}
        small_archive = {"name": "archive_2024.zip", "size": 1024, "path": "/path/archive_2024.zip"}
        large_document = {"name": "document.pdf", "size": 10 * 1024 * 1024, "path": "/path/document.pdf"}

        assert name_cond.evaluate(large_archive) is True
        assert size_cond.evaluate(large_archive) is True

        assert name_cond.evaluate(small_archive) is True
        assert size_cond.evaluate(small_archive) is False

        assert name_cond.evaluate(large_document) is False
        assert size_cond.evaluate(large_document) is True


@pytest.mark.unit
class TestConditionEdgeCases:
    """Test edge cases and special scenarios."""

    def test_condition_with_special_characters(self):
        """Test conditions with special characters in names."""
        cond = NameContainsCondition("(1)")
        fileinfo = {"name": "file (1).txt", "path": "/path/file (1).txt"}
        assert cond.evaluate(fileinfo) is True

    def test_extension_with_multiple_dots(self):
        """Test extension condition with multiple dots in filename."""
        cond = ExtensionIsCondition(".gz")
        # Note: get_fileinfo returns just .gz for files like archive.tar.gz
        fileinfo = {"name": "archive.tar.gz", "ext": ".gz", "path": "/path/archive.tar.gz"}
        assert cond.evaluate(fileinfo) is True

    def test_name_contains_unicode(self):
        """Test name condition with unicode characters."""
        cond = NameContainsCondition("文件")
        fileinfo = {"name": "文件_2024.txt", "path": "/path/文件_2024.txt"}
        assert cond.evaluate(fileinfo) is True

    def test_very_large_file_size(self):
        """Test size condition with very large file."""
        cond = FileSizeGreaterThanCondition(1024 * 1024 * 1024)  # 1 GB
        fileinfo = {"name": "huge.iso", "size": 4 * 1024 * 1024 * 1024, "path": "/path/huge.iso"}  # 4 GB
        assert cond.evaluate(fileinfo) is True
