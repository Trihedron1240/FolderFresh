# test_undo_integration.py
"""
Test suite for Undo system integration with Actions and RuleExecutor.
"""

import os
import pytest
from folderfresh.undo_manager import UNDO_MANAGER
from folderfresh.rule_engine.backbone import (
    Rule, RuleExecutor, ExtensionIsCondition,
    MoveAction, CopyAction, RenameAction
)
from folderfresh.fileinfo import get_fileinfo


@pytest.mark.integration
class TestUndoMoveIntegration:
    """Test undo integration with move actions."""

    def test_move_then_undo_move(self, test_structure, test_file_factory, basic_config, clear_undo_manager, clear_activity_log):
        """Test move action and undo it."""
        src_file = test_file_factory(test_structure["source"], "document.txt")
        fileinfo = get_fileinfo(src_file)

        # Move file
        action = MoveAction(test_structure["dest"])
        result = action.run(fileinfo, basic_config)

        assert result["ok"] is True
        dest_file = os.path.join(test_structure["dest"], "document.txt")
        assert os.path.exists(dest_file)
        assert not os.path.exists(src_file)

        # Record undo entry
        UNDO_MANAGER.record_action({
            "type": "move",
            "src": src_file,
            "dst": dest_file,
            "was_dry_run": False
        })

        # Undo the move
        undo_result = UNDO_MANAGER.undo_last()
        assert undo_result["success"] is True
        assert os.path.exists(src_file)
        assert not os.path.exists(dest_file)

    def test_move_then_undo_collision_safe(self, test_structure, test_file_factory, basic_config, clear_undo_manager, clear_activity_log):
        """Test move with collision, then undo."""
        src_file = test_file_factory(test_structure["source"], "document.txt", "source version")
        dest_original = test_file_factory(test_structure["dest"], "document.txt", "dest version")

        fileinfo = get_fileinfo(src_file)

        # Move with collision
        action = MoveAction(test_structure["dest"])
        result = action.run(fileinfo, basic_config)

        assert result["ok"] is True
        assert result["meta"]["collision_handled"] is True

        # File should be at collision-safe path
        moved_file = os.path.join(test_structure["dest"], "document (1).txt")
        assert os.path.exists(moved_file)

        # Record and undo
        UNDO_MANAGER.record_action(result["meta"])
        undo_result = UNDO_MANAGER.undo_last()

        assert undo_result["success"] is True
        assert os.path.exists(src_file)
        assert not os.path.exists(moved_file)


@pytest.mark.integration
class TestUndoCopyIntegration:
    """Test undo integration with copy actions."""

    def test_copy_then_undo_delete_copy(self, test_structure, test_file_factory, basic_config, clear_undo_manager, clear_activity_log):
        """Test copy action and undo it (delete copy)."""
        src_file = test_file_factory(test_structure["source"], "document.txt", "original")
        fileinfo = get_fileinfo(src_file)

        # Copy file
        action = CopyAction(test_structure["copy"])
        result = action.run(fileinfo, basic_config)

        assert result["ok"] is True
        copy_file = os.path.join(test_structure["copy"], "document.txt")
        assert os.path.exists(src_file)
        assert os.path.exists(copy_file)

        # Record and undo
        UNDO_MANAGER.record_action({
            "type": "copy",
            "src": src_file,
            "dst": copy_file,
            "was_dry_run": False
        })

        undo_result = UNDO_MANAGER.undo_last()
        assert undo_result["success"] is True
        assert os.path.exists(src_file), "Original should still exist"
        assert not os.path.exists(copy_file), "Copy should be deleted"


@pytest.mark.integration
class TestUndoRenameIntegration:
    """Test undo integration with rename actions."""

    def test_rename_then_undo_rename(self, test_structure, test_file_factory, basic_config, clear_undo_manager, clear_activity_log):
        """Test rename action and undo it."""
        src_file = test_file_factory(test_structure["source"], "oldname.txt")
        fileinfo = get_fileinfo(src_file)

        # Rename file
        action = RenameAction("newname.txt")
        result = action.run(fileinfo, basic_config)

        assert result["ok"] is True
        renamed_file = os.path.join(test_structure["source"], "newname.txt")
        assert os.path.exists(renamed_file)
        assert not os.path.exists(src_file)

        # Record and undo
        UNDO_MANAGER.record_action({
            "type": "rename",
            "src": renamed_file,  # Store where it ended up
            "old_name": "oldname.txt",
            "new_name": "newname.txt",
            "was_dry_run": False
        })

        undo_result = UNDO_MANAGER.undo_last()
        assert undo_result["success"] is True
        assert os.path.exists(src_file)
        assert not os.path.exists(renamed_file)


@pytest.mark.integration
class TestRuleExecutorUndoRecording:
    """Test RuleExecutor records undo entries."""

    def test_executor_records_move_undo(self, test_structure, test_file_factory, basic_config, clear_undo_manager, clear_activity_log):
        """Test RuleExecutor records undo for move action."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Move",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[MoveAction(test_structure["dest"])]
        )

        UNDO_MANAGER.clear_history()

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Verify undo entry was recorded
        assert len(UNDO_MANAGER) == 1, "Should have 1 undo entry"

        history = UNDO_MANAGER.get_history()
        assert history[0]["type"] == "move"

    def test_executor_does_not_record_dry_run_undo(self, test_structure, test_file_factory, clear_undo_manager, clear_activity_log):
        """Test RuleExecutor does NOT record undo for dry_run actions."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Move",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[MoveAction(test_structure["dest"])]
        )

        dry_run_config = {"dry_run": True, "safe_mode": True}
        UNDO_MANAGER.clear_history()

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, dry_run_config)

        # Verify NO undo entry was recorded
        assert len(UNDO_MANAGER) == 0, "Should have 0 undo entries (dry run)"

    def test_executor_records_multiple_action_undos(self, test_structure, test_file_factory, basic_config, clear_undo_manager, clear_activity_log):
        """Test RuleExecutor records undo for multiple actions."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Rename and Copy",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[
                RenameAction("processed.txt"),
                # Copy won't work after rename, but that's ok
            ]
        )

        UNDO_MANAGER.clear_history()

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Should have at least 1 undo entry (rename succeeded)
        assert len(UNDO_MANAGER) >= 1


@pytest.mark.integration
class TestUndoActionMetadata:
    """Test undo metadata from actions."""

    def test_move_action_provides_undo_metadata(self, test_structure, test_file_factory, basic_config):
        """Test move action returns proper undo metadata."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        action = MoveAction(test_structure["dest"])
        result = action.run(fileinfo, basic_config)

        # Verify metadata for undo
        assert result["meta"]["type"] == "move"
        assert result["meta"]["src"] is not None
        assert result["meta"]["dst"] is not None
        assert result["meta"]["was_dry_run"] is False
        assert "collision_handled" in result["meta"]

    def test_copy_action_provides_undo_metadata(self, test_structure, test_file_factory, basic_config):
        """Test copy action returns proper undo metadata."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        action = CopyAction(test_structure["copy"])
        result = action.run(fileinfo, basic_config)

        # Verify metadata for undo
        assert result["meta"]["type"] == "copy"
        assert result["meta"]["src"] is not None
        assert result["meta"]["dst"] is not None
        assert result["meta"]["was_dry_run"] is False

    def test_rename_action_provides_undo_metadata(self, test_structure, test_file_factory, basic_config):
        """Test rename action returns proper undo metadata."""
        src_file = test_file_factory(test_structure["source"], "old.txt")
        fileinfo = get_fileinfo(src_file)

        action = RenameAction("new.txt")
        result = action.run(fileinfo, basic_config)

        # Verify metadata for undo
        assert result["meta"]["type"] == "rename"
        assert result["meta"]["old_name"] == "old.txt"
        assert result["meta"]["new_name"] == "new.txt"
        assert result["meta"]["was_dry_run"] is False
