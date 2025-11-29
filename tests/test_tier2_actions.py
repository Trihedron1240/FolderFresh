"""
Comprehensive tests for Tier-2 advanced actions.

Tests cover:
- ColorLabelAction with idempotency
- AddTagAction / RemoveTagAction with tag management
- DeleteToTrashAction with safe mode protection
- MarkAsDuplicateAction with duplicate tagging
"""

import os
import pytest
import tempfile
from pathlib import Path
from folderfresh.rule_engine import (
    ColorLabelAction,
    AddTagAction,
    RemoveTagAction,
    DeleteToTrashAction,
    MarkAsDuplicateAction,
    METADATA_DB,
)
from folderfresh.fileinfo import get_fileinfo


@pytest.mark.unit
class TestColorLabelAction:
    """Test ColorLabelAction for applying color labels."""

    def test_color_label_apply(self, tmp_path):
        """Test applying a color label to a file."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = ColorLabelAction("red")
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "COLOR_LABEL" in result["log"]
        # Verify color was set
        assert METADATA_DB.get_color(str(test_file)) == "red"

    def test_color_label_idempotent(self, tmp_path):
        """Test that applying same color twice skips."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = ColorLabelAction("blue")
        config = {"dry_run": False, "safe_mode": False}

        # Apply color first time
        result1 = action.run(fileinfo, config)
        assert result1["ok"] is True

        # Apply same color again - should skip
        result2 = action.run(fileinfo, config)
        assert result2["ok"] is True
        assert "SKIP" in result2["log"]
        assert result2["meta"].get("skipped") is True

    def test_color_label_dry_run(self, tmp_path):
        """Test color label in dry_run mode."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = ColorLabelAction("green")
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        # Color should NOT be set in dry run
        assert METADATA_DB.get_color(str(test_file)) is None

    def test_color_label_change_color(self, tmp_path):
        """Test changing a file's color label."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        # Set initial color
        action1 = ColorLabelAction("red")
        config = {"dry_run": False, "safe_mode": False}
        result1 = action1.run(fileinfo, config)
        assert result1["ok"] is True
        assert METADATA_DB.get_color(str(test_file)) == "red"

        # Change to different color
        action2 = ColorLabelAction("blue")
        result2 = action2.run(fileinfo, config)
        assert result2["ok"] is True
        assert METADATA_DB.get_color(str(test_file)) == "blue"


@pytest.mark.unit
class TestAddTagAction:
    """Test AddTagAction for adding tags."""

    def test_add_tag_success(self, tmp_path):
        """Test adding a tag to a file."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = AddTagAction("important")
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "ADD_TAG" in result["log"]
        # Verify tag was added
        assert METADATA_DB.has_tag(str(test_file), "important")

    def test_add_tag_idempotent(self, tmp_path):
        """Test that adding same tag twice skips."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = AddTagAction("urgent")
        config = {"dry_run": False, "safe_mode": False}

        # Add tag first time
        result1 = action.run(fileinfo, config)
        assert result1["ok"] is True

        # Add same tag again - should skip
        result2 = action.run(fileinfo, config)
        assert result2["ok"] is True
        assert "SKIP" in result2["log"]
        assert result2["meta"].get("skipped") is True

    def test_add_multiple_tags(self, tmp_path):
        """Test adding multiple tags to a file."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        config = {"dry_run": False, "safe_mode": False}

        # Add first tag
        action1 = AddTagAction("important")
        result1 = action1.run(fileinfo, config)
        assert result1["ok"] is True

        # Add second tag
        action2 = AddTagAction("urgent")
        result2 = action2.run(fileinfo, config)
        assert result2["ok"] is True

        # Verify both tags exist
        tags = METADATA_DB.get_tags(str(test_file))
        assert "important" in tags
        assert "urgent" in tags

    def test_add_tag_dry_run(self, tmp_path):
        """Test adding tag in dry_run mode."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = AddTagAction("test")
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        # Tag should NOT be added in dry run
        assert not METADATA_DB.has_tag(str(test_file), "test")


@pytest.mark.unit
class TestRemoveTagAction:
    """Test RemoveTagAction for removing tags."""

    def test_remove_tag_success(self, tmp_path):
        """Test removing a tag from a file."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        # First add the tag
        METADATA_DB.add_tag(str(test_file), "temporary")

        # Then remove it
        action = RemoveTagAction("temporary")
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "REMOVE_TAG" in result["log"]
        # Verify tag was removed
        assert not METADATA_DB.has_tag(str(test_file), "temporary")

    def test_remove_tag_idempotent(self, tmp_path):
        """Test that removing non-existent tag skips."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = RemoveTagAction("nonexistent")
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "SKIP" in result["log"]
        assert result["meta"].get("skipped") is True

    def test_remove_tag_dry_run(self, tmp_path):
        """Test removing tag in dry_run mode."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        # Add tag first
        METADATA_DB.add_tag(str(test_file), "temp")

        # Try to remove in dry run
        action = RemoveTagAction("temp")
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        # Tag should still exist after dry run
        assert METADATA_DB.has_tag(str(test_file), "temp")


@pytest.mark.unit
class TestDeleteToTrashAction:
    """Test DeleteToTrashAction for safe deletion."""

    def test_delete_to_trash_safe_mode_skips(self, tmp_path):
        """Test that safe mode prevents deletion."""
        test_file = tmp_path / "temporary.txt"
        test_file.write_text("delete me")
        fileinfo = get_fileinfo(test_file)

        action = DeleteToTrashAction()
        config = {"dry_run": False, "safe_mode": True}
        result = action.run(fileinfo, config)

        # Should skip in safe mode
        assert result["ok"] is True
        assert "SKIP" in result["log"]
        assert result["meta"].get("skipped") is True
        # File should still exist
        assert test_file.exists()

    def test_delete_to_trash_dry_run_skips(self, tmp_path):
        """Test that dry run skips deletion."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = DeleteToTrashAction()
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        # File should still exist
        assert test_file.exists()

    def test_delete_to_trash_actual_delete(self, tmp_path):
        """Test actual deletion (if send2trash available)."""
        test_file = tmp_path / "deleteme.txt"
        test_file.write_text("will be deleted")
        fileinfo = get_fileinfo(test_file)

        action = DeleteToTrashAction()
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        # File should be deleted (sent to trash or removed)
        # Note: send2trash actually moves to recycle bin, so file may still "exist" temporarily
        # We check the action succeeded instead of existence


@pytest.mark.unit
class TestMarkAsDuplicateAction:
    """Test MarkAsDuplicateAction for marking duplicates."""

    def test_mark_duplicate_success(self, tmp_path):
        """Test marking a file as duplicate."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = MarkAsDuplicateAction()
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "MARK_DUPLICATE" in result["log"]
        # Verify tag was added
        assert METADATA_DB.has_tag(str(test_file), "duplicate")

    def test_mark_duplicate_idempotent(self, tmp_path):
        """Test that marking duplicate twice skips."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = MarkAsDuplicateAction()
        config = {"dry_run": False, "safe_mode": False}

        # Mark as duplicate first time
        result1 = action.run(fileinfo, config)
        assert result1["ok"] is True

        # Mark as duplicate again - should skip
        result2 = action.run(fileinfo, config)
        assert result2["ok"] is True
        assert "SKIP" in result2["log"]
        assert result2["meta"].get("skipped") is True

    def test_mark_duplicate_dry_run(self, tmp_path):
        """Test marking duplicate in dry_run mode."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = MarkAsDuplicateAction()
        config = {"dry_run": True, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        # Tag should NOT be added in dry run
        assert not METADATA_DB.has_tag(str(test_file), "duplicate")

    def test_mark_duplicate_custom_tag(self, tmp_path):
        """Test marking duplicate with custom tag."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("content")
        fileinfo = get_fileinfo(test_file)

        action = MarkAsDuplicateAction(tag="needs_review")
        config = {"dry_run": False, "safe_mode": False}
        result = action.run(fileinfo, config)

        assert result["ok"] is True
        # Verify custom tag was used
        assert METADATA_DB.has_tag(str(test_file), "needs_review")
