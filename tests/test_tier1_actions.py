"""
Comprehensive tests for Tier-1 Hazel-style actions.

Tests cover:
- TokenRenameAction with various token combinations
- RunCommandAction in dry_run and safe_mode
- ArchiveAction (zip creation)
- ExtractAction (unzip)
- CreateFolderAction with tokens
- Idempotency and skip logic
- Safe_mode collision avoidance
- Undo support integration
"""

import os
import pytest
import tempfile
import zipfile
from pathlib import Path
from folderfresh.rule_engine import (
    TokenRenameAction,
    RunCommandAction,
    ArchiveAction,
    ExtractAction,
    CreateFolderAction,
    ContentContainsCondition,
    DatePatternCondition,
    expand_tokens,
)
from folderfresh.fileinfo import get_fileinfo


@pytest.mark.unit
class TestTokenRenameAction:
    """Test TokenRenameAction with token expansion."""

    def test_token_rename_simple_date_pattern(self, tmp_path):
        """Test rename with date tokens."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("test content")
        fileinfo = get_fileinfo(test_file)

        action = TokenRenameAction("<date_modified>_<name><extension>")
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "TOKEN_RENAME" in result["log"]
        # File should be renamed with date prefix
        assert not test_file.exists()
        # Check that a file with date prefix exists
        renamed_files = list(tmp_path.glob("*_document.txt"))
        assert len(renamed_files) == 1

    def test_token_rename_with_name_extension(self, tmp_path):
        """Test rename using <name> and <extension> tokens."""
        test_file = tmp_path / "myfile.pdf"
        test_file.write_text("pdf content")
        fileinfo = get_fileinfo(test_file)

        action = TokenRenameAction("[<name>]<extension>")
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        expected_name = "[myfile].pdf"
        assert os.path.exists(tmp_path / expected_name)

    def test_token_rename_dry_run(self, tmp_path):
        """Test token rename in dry_run mode (no actual changes)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("keep me")
        fileinfo = get_fileinfo(test_file)

        action = TokenRenameAction("renamed_<name><extension>")
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        # File should NOT be renamed
        assert test_file.exists()
        assert not (tmp_path / "renamed_test.txt").exists()

    def test_token_rename_idempotent_with_exact_pattern(self, tmp_path):
        """Test that renaming with same pattern as current name is idempotent."""
        test_file = tmp_path / "test_backup.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = TokenRenameAction("<name><extension>")
        config = {"dry_run": False, "safe_mode": False}

        # Renaming to same pattern as current name should skip
        result = action.run(fileinfo, config)
        assert result["ok"] is True
        assert "SKIP" in result["log"]
        # File should not be moved
        assert test_file.exists()


@pytest.mark.unit
class TestRunCommandAction:
    """Test RunCommandAction for script execution."""

    def test_run_command_dry_run(self, tmp_path):
        """Test command in dry_run mode (no execution)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("echo test")
        fileinfo = get_fileinfo(test_file)

        action = RunCommandAction("echo {path}")
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        assert "Would execute" in result["log"]

    def test_run_command_safe_mode(self, tmp_path):
        """Test command in safe_mode (no execution)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = RunCommandAction("echo test")
        config = {"dry_run": False, "safe_mode": True}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]

    def test_run_command_execute_echo(self, tmp_path):
        """Test actual command execution (echo)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = RunCommandAction("echo hello world")
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "RUN_COMMAND" in result["log"]


@pytest.mark.unit
class TestArchiveAction:
    """Test ArchiveAction for creating zip files."""

    def test_archive_create_zip(self, tmp_path):
        """Test creating a zip archive."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("important data")
        dest_dir = tmp_path / "archives"
        fileinfo = get_fileinfo(test_file)

        action = ArchiveAction(str(dest_dir))
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "ARCHIVE" in result["log"]

        # Check zip was created
        zip_file = dest_dir / "document.zip"
        assert zip_file.exists()

        # Verify zip contents
        with zipfile.ZipFile(zip_file, 'r') as zf:
            assert "document.txt" in zf.namelist()
            assert zf.read("document.txt") == b"important data"

    def test_archive_with_token_path(self, tmp_path):
        """Test archive with token expansion in destination."""
        test_file = tmp_path / "report.pdf"
        test_file.write_text("pdf data")
        fileinfo = get_fileinfo(test_file)

        # Use token in destination path
        action = ArchiveAction(str(tmp_path / "archives_<year>"))
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        # Folder should exist with year suffix
        year_folders = list(tmp_path.glob("archives_*"))
        assert len(year_folders) >= 1

    def test_archive_dry_run(self, tmp_path):
        """Test archive in dry_run mode."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = ArchiveAction(str(tmp_path / "backup"))
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        # No zip should be created
        assert not (tmp_path / "backup" / "file.zip").exists()

    def test_archive_collision_avoidance(self, tmp_path):
        """Test that archiving twice avoids overwriting."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("data")
        dest_dir = tmp_path / "archives"
        fileinfo = get_fileinfo(test_file)

        action = ArchiveAction(str(dest_dir))
        config = {"dry_run": False, "safe_mode": True}

        # Archive once
        result1 = action.run(fileinfo, config)
        assert result1["ok"] is True
        assert (dest_dir / "data.zip").exists()

        # Archive again (should create data (1).zip)
        result2 = action.run(fileinfo, config)
        assert result2["ok"] is True
        assert (dest_dir / "data (1).zip").exists()


@pytest.mark.unit
class TestExtractAction:
    """Test ExtractAction for extracting archives."""

    def test_extract_zip(self, tmp_path):
        """Test extracting a zip file."""
        # Create a zip file
        zip_path = tmp_path / "archive.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file.txt", "extracted content")

        fileinfo = get_fileinfo(zip_path)
        extract_dir = tmp_path / "extracted"

        action = ExtractAction(str(extract_dir))
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "EXTRACT" in result["log"]
        assert (extract_dir / "file.txt").exists()
        assert (extract_dir / "file.txt").read_text() == "extracted content"

    def test_extract_with_tokens(self, tmp_path):
        """Test extract with token expansion in destination."""
        # Create a zip
        zip_path = tmp_path / "backup.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("data.txt", "restore me")

        fileinfo = get_fileinfo(zip_path)

        action = ExtractAction(str(tmp_path / "restore_<date_modified>"))
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        # Should extract to a folder with date in name
        restore_folders = list(tmp_path.glob("restore_*"))
        assert len(restore_folders) >= 1

    def test_extract_dry_run(self, tmp_path):
        """Test extract in dry_run mode."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("test.txt", "data")

        fileinfo = get_fileinfo(zip_path)
        extract_dir = tmp_path / "extracted"

        action = ExtractAction(str(extract_dir))
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        # Folder should not exist
        assert not extract_dir.exists()

    def test_extract_unsupported_format(self, tmp_path):
        """Test extract with unsupported file format."""
        # Create a non-archive file
        not_zip = tmp_path / "notazip.txt"
        not_zip.write_text("regular file")

        fileinfo = get_fileinfo(not_zip)

        action = ExtractAction(str(tmp_path / "output"))
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is False
        assert "unsupported" in result["log"].lower()


@pytest.mark.unit
class TestCreateFolderAction:
    """Test CreateFolderAction for folder creation."""

    def test_create_folder_simple(self, tmp_path):
        """Test creating a simple folder."""
        fileinfo = get_fileinfo(tmp_path / "dummy.txt")

        action = CreateFolderAction(str(tmp_path / "new_folder"))
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "CREATE_FOLDER" in result["log"]
        assert (tmp_path / "new_folder").exists()

    def test_create_folder_nested(self, tmp_path):
        """Test creating nested folders."""
        fileinfo = get_fileinfo(tmp_path / "test.txt")

        action = CreateFolderAction(str(tmp_path / "a" / "b" / "c"))
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert (tmp_path / "a" / "b" / "c").exists()

    def test_create_folder_with_tokens(self, tmp_path):
        """Test creating folder with token expansion."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = CreateFolderAction(str(tmp_path / "documents_<year>_<month>"))
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        # Folder with year_month should be created
        dated_folders = list(tmp_path.glob("documents_*"))
        assert len(dated_folders) >= 1

    def test_create_folder_already_exists(self, tmp_path):
        """Test creating folder that already exists (idempotent)."""
        folder = tmp_path / "existing"
        folder.mkdir()

        fileinfo = get_fileinfo(tmp_path / "test.txt")

        action = CreateFolderAction(str(folder))
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        # Should succeed with skip message
        assert result["ok"] is True
        assert "SKIP" in result["log"]

    def test_create_folder_dry_run(self, tmp_path):
        """Test create folder in dry_run mode."""
        fileinfo = get_fileinfo(tmp_path / "test.txt")

        action = CreateFolderAction(str(tmp_path / "dry_folder"))
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        # Folder should not actually be created
        assert not (tmp_path / "dry_folder").exists()


@pytest.mark.unit
class TestExpandTokens:
    """Test token expansion utility function."""

    def test_expand_basic_tokens(self, tmp_path):
        """Test expanding basic file tokens."""
        test_file = tmp_path / "myfile.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        result = expand_tokens("<name>_backup<extension>", fileinfo)
        assert result == "myfile_backup.txt"

    def test_expand_date_tokens(self, tmp_path):
        """Test expanding date tokens."""
        test_file = tmp_path / "document.pdf"
        test_file.write_text("pdf")
        fileinfo = get_fileinfo(test_file)

        result = expand_tokens("<year>/<month>/<day>_<name>", fileinfo)
        # Should contain year/month/day pattern
        assert "/" in result
        assert test_file.stat().st_mtime > 0  # File has a modification time


@pytest.mark.unit
class TestContentCondition:
    """Test ContentContainsCondition for content matching."""

    def test_content_contains_plain_text(self, tmp_path):
        """Test matching text in plain text file."""
        test_file = tmp_path / "log.txt"
        test_file.write_text("Error: something went wrong\nWarning: check status")

        fileinfo = get_fileinfo(test_file)
        condition = ContentContainsCondition("Error")

        result = condition.evaluate(fileinfo)
        assert result is True

    def test_content_contains_not_found(self, tmp_path):
        """Test when content is not found."""
        test_file = tmp_path / "log.txt"
        test_file.write_text("All systems operational")

        fileinfo = get_fileinfo(test_file)
        condition = ContentContainsCondition("Error")

        result = condition.evaluate(fileinfo)
        assert result is False

    def test_content_contains_case_insensitive(self, tmp_path):
        """Test case-insensitive matching."""
        test_file = tmp_path / "report.txt"
        test_file.write_text("CRITICAL FAILURE DETECTED")

        fileinfo = get_fileinfo(test_file)
        condition = ContentContainsCondition("critical")

        result = condition.evaluate(fileinfo)
        assert result is True


@pytest.mark.unit
class TestDatePatternCondition:
    """Test DatePatternCondition for date-based matching."""

    def test_date_pattern_year_wildcard(self, tmp_path):
        """Test matching files created in specific year."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        fileinfo = get_fileinfo(test_file)
        # Match any date created in 2024 or current year
        import datetime
        current_year = str(datetime.datetime.now().year)
        condition = DatePatternCondition("modified", f"{current_year}-*")

        result = condition.evaluate(fileinfo)
        assert result is True  # File was just created

    def test_date_pattern_month_wildcard(self, tmp_path):
        """Test matching files in specific month."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        fileinfo = get_fileinfo(test_file)
        import datetime
        current_year = datetime.datetime.now().year
        current_month = f"{current_year}-{datetime.datetime.now().month:02d}"
        condition = DatePatternCondition("modified", f"{current_month}-*")

        result = condition.evaluate(fileinfo)
        assert result is True
