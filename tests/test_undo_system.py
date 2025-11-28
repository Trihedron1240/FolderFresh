#!/usr/bin/env python3
"""
Comprehensive test suite for the FolderFresh Undo/Rollback system.

Tests:
- Basic undo manager operations
- Move action and undo
- Rename action and undo
- Copy action and undo
- Collision handling (safe_mode)
- Dry run behavior (no undo recording)
- Activity Log integration
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from folderfresh.undo_manager import UNDO_MANAGER, UndoManager
from folderfresh.rule_engine.backbone import (
    RenameAction, MoveAction, CopyAction
)
from folderfresh.fileinfo import get_fileinfo
from folderfresh.activity_log import ACTIVITY_LOG


def setup_test_environment():
    """Create temporary test directory structure."""
    test_dir = tempfile.mkdtemp(prefix="folderfresh_test_")
    source_dir = os.path.join(test_dir, "source")
    move_dir = os.path.join(test_dir, "moved")
    copy_dir = os.path.join(test_dir, "copied")

    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(move_dir, exist_ok=True)
    os.makedirs(copy_dir, exist_ok=True)

    return test_dir, source_dir, move_dir, copy_dir


def create_test_file(directory, filename, content="test content"):
    """Create a test file with content."""
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        f.write(content)
    return filepath


def cleanup_test_environment(test_dir):
    """Clean up temporary test directory."""
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


def test_undo_manager_basic():
    """Test basic UndoManager operations."""
    print("\n[TEST] Basic UndoManager Operations")
    print("-" * 50)

    manager = UndoManager()

    # Test record and get_history
    entry1 = {
        "type": "move",
        "src": "/path/to/file.txt",
        "dst": "/new/path/file.txt",
        "was_dry_run": False
    }
    manager.record_action(entry1)
    assert len(manager) == 1, "Entry should be recorded"
    print("[OK] record_action works")

    # Test get_history
    history = manager.get_history()
    assert len(history) == 1, "History should have 1 entry"
    assert history[0]["type"] == "move", "Entry type should be move"
    print("[OK] get_history returns entries in correct order")

    # Test pop_last
    popped = manager.pop_last()
    assert popped is not None, "Pop should return entry"
    assert len(manager) == 0, "History should be empty after pop"
    print("[OK] pop_last removes and returns entry")

    # Test clear_history
    manager.record_action(entry1)
    manager.record_action(entry1)
    manager.clear_history()
    assert len(manager) == 0, "History should be empty after clear"
    print("[OK] clear_history removes all entries")

    print("[OK] All basic UndoManager tests passed!")


def _test_move_action_undo_old():
    """Test move action and undo."""
    print("\n[TEST] Move Action and Undo")
    print("-" * 50)

    test_dir, source_dir, move_dir, copy_dir = setup_test_environment()

    try:
        # Create test file
        test_file = create_test_file(source_dir, "document.txt", "document content")
        print(f"[SETUP] Created test file: {test_file}")

        # Clear undo manager
        UNDO_MANAGER.clear_history()
        ACTIVITY_LOG.clear()

        # Get file info
        fileinfo = get_fileinfo(test_file)
        print(f"[INFO] File info: {fileinfo}")

        # Execute move action
        config = {"dry_run": False, "safe_mode": True}
        action = MoveAction(move_dir)
        result = action.run(fileinfo, config)

        assert result["ok"], "Move action should succeed"
        print(f"[OK] Move action succeeded: {result['log']}")

        # Verify file was moved
        moved_file = os.path.join(move_dir, "document.txt")
        assert os.path.exists(moved_file), "File should be at destination"
        assert not os.path.exists(test_file), "File should not exist at source"
        print("[OK] File moved to destination")

        # Verify undo was recorded
        assert len(UNDO_MANAGER) == 1, "Undo entry should be recorded"
        print("[OK] Undo entry recorded")

        # Execute undo
        undo_result = UNDO_MANAGER.undo_last()
        assert undo_result["success"], "Undo should succeed"
        print(f"[OK] Undo succeeded: {undo_result['message']}")

        # Verify file was restored
        assert os.path.exists(test_file), "File should be restored at source"
        assert not os.path.exists(moved_file), "File should not exist at destination"
        print("[OK] File restored to original location")

        print("[OK] All move action tests passed!")

    finally:
        cleanup_test_environment(test_dir)


def _test_rename_action_undo_old():
    """Test rename action and undo."""
    print("\n[TEST] Rename Action and Undo")
    print("-" * 50)

    test_dir, source_dir, move_dir, copy_dir = setup_test_environment()

    try:
        # Create test file
        test_file = create_test_file(source_dir, "oldname.txt", "file content")
        print(f"[SETUP] Created test file: {test_file}")

        # Clear undo manager
        UNDO_MANAGER.clear_history()
        ACTIVITY_LOG.clear()

        # Get file info
        fileinfo = get_fileinfo(test_file)

        # Execute rename action
        config = {"dry_run": False, "safe_mode": True}
        action = RenameAction("newname.txt")
        result = action.run(fileinfo, config)

        assert result["ok"], "Rename action should succeed"
        print(f"[OK] Rename action succeeded: {result['log']}")

        # Verify file was renamed
        renamed_file = os.path.join(source_dir, "newname.txt")
        assert os.path.exists(renamed_file), "File should exist with new name"
        assert not os.path.exists(test_file), "File should not exist with old name"
        print("[OK] File renamed")

        # Verify undo was recorded
        assert len(UNDO_MANAGER) == 1, "Undo entry should be recorded"
        print("[OK] Undo entry recorded")

        # Execute undo
        undo_result = UNDO_MANAGER.undo_last()
        assert undo_result["success"], "Undo should succeed"
        print(f"[OK] Undo succeeded: {undo_result['message']}")

        # Verify file was restored
        assert os.path.exists(test_file), "File should be restored with old name"
        assert not os.path.exists(renamed_file), "File should not exist with new name"
        print("[OK] File restored to original name")

        print("[OK] All rename action tests passed!")

    finally:
        cleanup_test_environment(test_dir)


def _test_copy_action_undo_old():
    """Test copy action and undo."""
    print("\n[TEST] Copy Action and Undo")
    print("-" * 50)

    test_dir, source_dir, move_dir, copy_dir = setup_test_environment()

    try:
        # Create test file
        test_file = create_test_file(source_dir, "original.txt", "original content")
        print(f"[SETUP] Created test file: {test_file}")

        # Clear undo manager
        UNDO_MANAGER.clear_history()
        ACTIVITY_LOG.clear()

        # Get file info
        fileinfo = get_fileinfo(test_file)

        # Execute copy action
        config = {"dry_run": False, "safe_mode": True}
        action = CopyAction(copy_dir)
        result = action.run(fileinfo, config)

        assert result["ok"], "Copy action should succeed"
        print(f"[OK] Copy action succeeded: {result['log']}")

        # Verify file was copied
        copied_file = os.path.join(copy_dir, "original.txt")
        assert os.path.exists(test_file), "Original should still exist"
        assert os.path.exists(copied_file), "Copy should exist at destination"
        print("[OK] File copied to destination")

        # Verify undo was recorded
        assert len(UNDO_MANAGER) == 1, "Undo entry should be recorded"
        print("[OK] Undo entry recorded")

        # Execute undo
        undo_result = UNDO_MANAGER.undo_last()
        assert undo_result["success"], "Undo should succeed"
        print(f"[OK] Undo succeeded: {undo_result['message']}")

        # Verify copy was deleted
        assert os.path.exists(test_file), "Original should still exist"
        assert not os.path.exists(copied_file), "Copy should be deleted"
        print("[OK] Copy deleted during undo")

        print("[OK] All copy action tests passed!")

    finally:
        cleanup_test_environment(test_dir)


def test_dry_run_no_undo():
    """Test that dry_run actions don't record undo entries."""
    print("\n[TEST] Dry Run - No Undo Recording")
    print("-" * 50)

    test_dir, source_dir, move_dir, copy_dir = setup_test_environment()

    try:
        # Create test file
        test_file = create_test_file(source_dir, "dryrun.txt", "content")
        print(f"[SETUP] Created test file: {test_file}")

        # Clear undo manager
        UNDO_MANAGER.clear_history()
        ACTIVITY_LOG.clear()

        # Get file info
        fileinfo = get_fileinfo(test_file)

        # Execute move action in dry_run mode
        config = {"dry_run": True, "safe_mode": True}
        action = MoveAction(move_dir)
        result = action.run(fileinfo, config)

        assert result["ok"], "Dry run should not fail"
        assert "DRY RUN" in result["log"], "Log should indicate dry run"
        print(f"[OK] Dry run executed: {result['log']}")

        # Verify file was NOT moved
        assert os.path.exists(test_file), "File should NOT be moved in dry run"
        moved_file = os.path.join(move_dir, "dryrun.txt")
        assert not os.path.exists(moved_file), "File should not exist at destination"
        print("[OK] File not modified in dry run")

        # Verify undo was NOT recorded (because was_dry_run=True)
        assert len(UNDO_MANAGER) == 0, "Dry run should NOT record undo entry"
        print("[OK] No undo entry recorded for dry run")

        print("[OK] All dry run tests passed!")

    finally:
        cleanup_test_environment(test_dir)


def test_collision_handling():
    """Test collision handling with safe_mode."""
    print("\n[TEST] Collision Handling (safe_mode)")
    print("-" * 50)

    test_dir, source_dir, move_dir, copy_dir = setup_test_environment()

    try:
        # Create two files with same name
        test_file1 = create_test_file(source_dir, "document.txt", "first version")
        test_file2 = create_test_file(move_dir, "document.txt", "existing file")
        print(f"[SETUP] Created test file: {test_file1}")
        print(f"[SETUP] Created existing file: {test_file2}")

        # Clear undo manager
        UNDO_MANAGER.clear_history()

        # Get file info
        fileinfo = get_fileinfo(test_file1)

        # Execute move action with safe_mode
        config = {"dry_run": False, "safe_mode": True}
        action = MoveAction(move_dir)
        result = action.run(fileinfo, config)

        assert result["ok"], "Move with collision should succeed"
        assert result["meta"]["collision_handled"], "Collision should be detected"
        print(f"[OK] Collision handled: {result['log']}")

        # Verify file was moved with new name
        moved_file = os.path.join(move_dir, "document (1).txt")
        assert os.path.exists(moved_file), "File should be moved with collision-safe name"
        assert os.path.exists(test_file2), "Original file should still exist"
        print("[OK] File moved to collision-safe path")

        # Verify both files exist with different names
        files_in_dest = os.listdir(move_dir)
        assert len(files_in_dest) == 2, "Both files should exist in destination"
        print("[OK] Both files coexist with different names")

        print("[OK] All collision handling tests passed!")

    finally:
        cleanup_test_environment(test_dir)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FOLDERFRESH UNDO SYSTEM TEST SUITE")
    print("=" * 60)

    try:
        test_undo_manager_basic()
        test_move_action_undo()
        test_rename_action_undo()
        test_copy_action_undo()
        test_dry_run_no_undo()
        test_collision_handling()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n[FAILED] {str(e)}")
        return 1

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
