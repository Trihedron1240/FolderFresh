# test_actions.py
"""
Test suite for rule actions (Move, Copy, Rename).
"""

import os
import pytest
from folderfresh.rule_engine.backbone import (
    MoveAction, CopyAction, RenameAction
)
from folderfresh.fileinfo import get_fileinfo


@pytest.mark.unit
class TestMoveAction:
    """Test MoveAction functionality."""

    def test_move_action_success(self, test_structure, test_file_factory, basic_config):
        """Test successful file move."""
        # Create test file
        src_file = test_file_factory(test_structure["source"], "document.txt", "content")
        fileinfo = get_fileinfo(src_file)

        # Execute move
        action = MoveAction(test_structure["dest"])
        result = action.run(fileinfo, basic_config)

        # Verify result structure
        assert isinstance(result, dict)
        assert "ok" in result
        assert "log" in result
        assert "meta" in result

        # Verify move succeeded
        assert result["ok"] is True
        assert "MOVE" in result["log"]

        # Verify metadata
        assert result["meta"]["type"] == "move"
        assert result["meta"]["src"] == src_file
        assert result["meta"]["was_dry_run"] is False

        # Verify file was moved
        assert not os.path.exists(src_file), "Source file should not exist"
        dest_file = os.path.join(test_structure["dest"], "document.txt")
        assert os.path.exists(dest_file), "Dest file should exist"

    def test_move_action_dry_run(self, test_structure, test_file_factory, dry_run_config):
        """Test move action in dry_run mode."""
        src_file = test_file_factory(test_structure["source"], "document.txt")
        fileinfo = get_fileinfo(src_file)

        action = MoveAction(test_structure["dest"])
        result = action.run(fileinfo, dry_run_config)

        # Verify dry run
        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        assert result["meta"]["was_dry_run"] is True

        # Verify file was NOT moved
        assert os.path.exists(src_file), "File should still exist in source (dry run)"
        dest_file = os.path.join(test_structure["dest"], "document.txt")
        assert not os.path.exists(dest_file), "File should not exist in dest (dry run)"

    def test_move_action_collision_safe_mode(self, test_structure, test_file_factory, basic_config):
        """Test move action with collision (safe_mode)."""
        # Create file in source
        src_file = test_file_factory(test_structure["source"], "document.txt", "source version")

        # Create file with same name in dest
        test_file_factory(test_structure["dest"], "document.txt", "dest version")

        fileinfo = get_fileinfo(src_file)

        action = MoveAction(test_structure["dest"])
        result = action.run(fileinfo, basic_config)

        # Verify move succeeded with collision handling
        assert result["ok"] is True
        assert result["meta"]["collision_handled"] is True

        # Verify file was moved with collision-safe name
        dest_file = os.path.join(test_structure["dest"], "document (1).txt")
        assert os.path.exists(dest_file), "File should be moved with collision-safe name"

        # Verify both files exist
        original_dest = os.path.join(test_structure["dest"], "document.txt")
        assert os.path.exists(original_dest), "Original dest file should still exist"

    def test_move_action_creates_target_dir(self, test_structure, test_file_factory, basic_config):
        """Test move action creates target directory if needed."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        # Target a non-existent subdirectory
        target_dir = os.path.join(test_structure["dest"], "subdir", "nested")
        action = MoveAction(target_dir)
        result = action.run(fileinfo, basic_config)

        assert result["ok"] is True
        dest_file = os.path.join(target_dir, "file.txt")
        assert os.path.exists(dest_file), "File should be moved to created directory"

    def test_move_action_missing_source(self, basic_config):
        """Test move action with missing source file."""
        fileinfo = {"path": "/nonexistent/file.txt", "name": "file.txt"}

        action = MoveAction("/some/dest")
        result = action.run(fileinfo, basic_config)

        assert result["ok"] is False
        assert "ERROR" in result["log"]


@pytest.mark.unit
class TestCopyAction:
    """Test CopyAction functionality."""

    def test_copy_action_success(self, test_structure, test_file_factory, basic_config):
        """Test successful file copy."""
        src_file = test_file_factory(test_structure["source"], "document.txt", "content")
        fileinfo = get_fileinfo(src_file)

        action = CopyAction(test_structure["copy"])
        result = action.run(fileinfo, basic_config)

        # Verify result structure
        assert result["ok"] is True
        assert "COPY" in result["log"]
        assert result["meta"]["type"] == "copy"
        assert result["meta"]["was_dry_run"] is False

        # Verify both files exist
        assert os.path.exists(src_file), "Source file should still exist"
        copy_file = os.path.join(test_structure["copy"], "document.txt")
        assert os.path.exists(copy_file), "Copy should exist"

        # Verify content is identical
        with open(src_file, "r") as f:
            src_content = f.read()
        with open(copy_file, "r") as f:
            copy_content = f.read()
        assert src_content == copy_content, "Copy should have identical content"

    def test_copy_action_dry_run(self, test_structure, test_file_factory, dry_run_config):
        """Test copy action in dry_run mode."""
        src_file = test_file_factory(test_structure["source"], "document.txt")
        fileinfo = get_fileinfo(src_file)

        action = CopyAction(test_structure["copy"])
        result = action.run(fileinfo, dry_run_config)

        # Verify dry run
        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        assert result["meta"]["was_dry_run"] is True

        # Verify file was NOT copied
        assert os.path.exists(src_file), "Source should exist"
        copy_file = os.path.join(test_structure["copy"], "document.txt")
        assert not os.path.exists(copy_file), "Copy should not exist (dry run)"

    def test_copy_action_collision_safe_mode(self, test_structure, test_file_factory, basic_config):
        """Test copy action with collision (safe_mode)."""
        src_file = test_file_factory(test_structure["source"], "document.txt")

        # Create file with same name in dest
        test_file_factory(test_structure["copy"], "document.txt", "existing")

        fileinfo = get_fileinfo(src_file)

        action = CopyAction(test_structure["copy"])
        result = action.run(fileinfo, basic_config)

        assert result["ok"] is True
        assert result["meta"]["collision_handled"] is True

        # Verify copy was created with collision-safe name
        copy_file = os.path.join(test_structure["copy"], "document (1).txt")
        assert os.path.exists(copy_file), "Copy should have collision-safe name"


@pytest.mark.unit
class TestRenameAction:
    """Test RenameAction functionality."""

    def test_rename_action_success(self, test_structure, test_file_factory, basic_config):
        """Test successful file rename."""
        src_file = test_file_factory(test_structure["source"], "oldname.txt", "content")
        fileinfo = get_fileinfo(src_file)

        action = RenameAction("newname.txt")
        result = action.run(fileinfo, basic_config)

        # Verify result
        assert result["ok"] is True
        assert "RENAME" in result["log"]
        assert result["meta"]["type"] == "rename"
        assert result["meta"]["old_name"] == "oldname.txt"
        assert result["meta"]["new_name"] == "newname.txt"
        assert result["meta"]["was_dry_run"] is False

        # Verify file was renamed
        assert not os.path.exists(src_file), "Old name should not exist"
        renamed_file = os.path.join(test_structure["source"], "newname.txt")
        assert os.path.exists(renamed_file), "New name should exist"

    def test_rename_action_dry_run(self, test_structure, test_file_factory, dry_run_config):
        """Test rename action in dry_run mode."""
        src_file = test_file_factory(test_structure["source"], "oldname.txt")
        fileinfo = get_fileinfo(src_file)

        action = RenameAction("newname.txt")
        result = action.run(fileinfo, dry_run_config)

        assert result["ok"] is True
        assert "DRY RUN" in result["log"]
        assert result["meta"]["was_dry_run"] is True

        # Verify file was NOT renamed
        assert os.path.exists(src_file), "File should keep old name (dry run)"
        renamed_file = os.path.join(test_structure["source"], "newname.txt")
        assert not os.path.exists(renamed_file), "New name should not exist (dry run)"

    def test_rename_action_collision_safe_mode(self, test_structure, test_file_factory, basic_config):
        """Test rename action with collision (safe_mode)."""
        src_file = test_file_factory(test_structure["source"], "oldname.txt")

        # Create file with target name
        test_file_factory(test_structure["source"], "newname.txt", "existing")

        fileinfo = get_fileinfo(src_file)

        action = RenameAction("newname.txt")
        result = action.run(fileinfo, basic_config)

        assert result["ok"] is True
        assert result["meta"]["collision_handled"] is True

        # Verify rename used collision-safe name
        renamed_file = os.path.join(test_structure["source"], "newname (1).txt")
        assert os.path.exists(renamed_file), "Rename should use collision-safe name"

        # Verify original target still exists
        original_target = os.path.join(test_structure["source"], "newname.txt")
        assert os.path.exists(original_target), "Original target should still exist"

    def test_rename_preserves_extension(self, test_structure, test_file_factory, basic_config):
        """Test rename preserves file extension."""
        src_file = test_file_factory(test_structure["source"], "document.pdf")
        fileinfo = get_fileinfo(src_file)

        action = RenameAction("annual_report.pdf")
        result = action.run(fileinfo, basic_config)

        assert result["ok"] is True
        renamed_file = os.path.join(test_structure["source"], "annual_report.pdf")
        assert os.path.exists(renamed_file), "File should be renamed with extension"


@pytest.mark.unit
class TestActionReturnFormat:
    """Test that all actions return correct dict format."""

    def test_action_returns_dict(self, test_structure, test_file_factory, basic_config):
        """Test action returns dict, not string."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        actions = [
            MoveAction(test_structure["dest"]),
            CopyAction(test_structure["copy"]),
            RenameAction("newname.txt")
        ]

        for action in actions:
            result = action.run(fileinfo, basic_config)
            assert isinstance(result, dict), f"{action.__class__.__name__} should return dict"
            assert "ok" in result
            assert "log" in result
            assert "meta" in result
            assert isinstance(result["ok"], bool)
            assert isinstance(result["log"], str)
            assert isinstance(result["meta"], dict)
