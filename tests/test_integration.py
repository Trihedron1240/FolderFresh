# test_integration.py
"""
Integration tests for complex scenarios and watcher simulation.
"""

import os
import pytest
from folderfresh.rule_engine.backbone import (
    Rule, RuleExecutor, NameContainsCondition, ExtensionIsCondition,
    FileSizeGreaterThanCondition, MoveAction, CopyAction, RenameAction
)
from folderfresh.fileinfo import get_fileinfo
from folderfresh.undo_manager import UNDO_MANAGER
from folderfresh.activity_log import ACTIVITY_LOG


@pytest.mark.integration
class TestWatcherSimulation:
    """Simulate file watcher events with rule execution."""

    def test_watcher_create_event_simulation(self, test_structure, test_file_factory, basic_config, clear_activity_log, clear_undo_manager):
        """Simulate a file creation event in watcher."""
        # Simulate watcher detecting new file
        pdf_file = test_file_factory(test_structure["source"], "document.pdf")

        # Rule: Move PDFs to archive
        rule = Rule(
            name="Archive PDFs",
            conditions=[ExtensionIsCondition(".pdf")],
            actions=[MoveAction(test_structure["dest"])]
        )

        # Execute rules (as watcher would)
        fileinfo = get_fileinfo(pdf_file)
        executor = RuleExecutor()
        result = executor.execute([rule], fileinfo, basic_config)
        logs = result.get("log", []) if isinstance(result, dict) else result

        # Verify file was moved
        assert not os.path.exists(pdf_file)
        assert os.path.exists(os.path.join(test_structure["dest"], "document.pdf"))

        # Verify logs
        assert len(logs) > 0
        assert any("Archive PDFs" in log for log in logs)

    def test_watcher_multiple_files_sequence(self, test_structure, test_file_factory, basic_config, clear_activity_log, clear_undo_manager):
        """Simulate watcher processing multiple files sequentially."""
        # Create multiple files
        pdf_file = test_file_factory(test_structure["source"], "doc.pdf")
        png_file = test_file_factory(test_structure["source"], "image.png")
        txt_file = test_file_factory(test_structure["source"], "note.txt")

        # Setup rules for different file types
        pdf_rule = Rule(
            name="Archive PDFs",
            conditions=[ExtensionIsCondition(".pdf")],
            actions=[MoveAction(test_structure["dest"])]
        )

        png_rule = Rule(
            name="Copy Images",
            conditions=[ExtensionIsCondition(".png")],
            actions=[CopyAction(test_structure["copy"])]
        )

        rules = [pdf_rule, png_rule]

        # Process each file
        executor = RuleExecutor()

        # Process PDF
        executor.execute(rules, get_fileinfo(pdf_file), basic_config)
        assert not os.path.exists(pdf_file)
        assert os.path.exists(os.path.join(test_structure["dest"], "doc.pdf"))

        # Process PNG
        executor.execute(rules, get_fileinfo(png_file), basic_config)
        assert os.path.exists(png_file)  # Still exists (copied, not moved)
        assert os.path.exists(os.path.join(test_structure["copy"], "image.png"))

        # Process TXT (no rules match)
        executor.execute(rules, get_fileinfo(txt_file), basic_config)
        assert os.path.exists(txt_file)  # Unchanged

    def test_watcher_with_dry_run_then_real(self, test_structure, test_file_factory, basic_config, clear_activity_log, clear_undo_manager):
        """Simulate watcher in dry_run mode, then real mode."""
        file1 = test_file_factory(test_structure["source"], "file1.pdf")
        file2 = test_file_factory(test_structure["source"], "file2.pdf")

        rule = Rule(
            name="Move PDFs",
            conditions=[ExtensionIsCondition(".pdf")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()
        dry_run_config = {"dry_run": True, "safe_mode": True}

        # Test with dry_run
        executor.execute([rule], get_fileinfo(file1), dry_run_config)
        assert os.path.exists(file1), "File should not move in dry_run"

        # Test with real
        executor.execute([rule], get_fileinfo(file2), basic_config)
        assert not os.path.exists(file2), "File should move in real mode"
        assert os.path.exists(os.path.join(test_structure["dest"], "file2.pdf"))


@pytest.mark.integration
class TestComplexRuleScenarios:
    """Test complex rule configurations and interactions."""

    def test_rule_with_all_conditions(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test rule matching multiple condition types."""
        # Create a large PNG file
        png_file = test_file_factory(test_structure["source"], "large_screenshot.png", size_kb=1500)

        rule = Rule(
            name="Archive Large Screenshots",
            conditions=[
                NameContainsCondition("screenshot"),
                ExtensionIsCondition(".png"),
                FileSizeGreaterThanCondition(1024 * 1024)  # > 1 MB
            ],
            actions=[MoveAction(test_structure["dest"])],
            match_mode="all"
        )

        executor = RuleExecutor()
        fileinfo = get_fileinfo(png_file)
        result = executor.execute([rule], fileinfo, basic_config)
        logs = result.get("log", []) if isinstance(result, dict) else result

        # Should match all conditions
        assert any("MATCHED" in log for log in logs)

    def test_rule_with_any_conditions(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test rule with OR logic (any condition)."""
        # File matches first condition but not second
        old_small_file = test_file_factory(test_structure["source"], "archive.zip", size_kb=100)

        rule = Rule(
            name="Important Files",
            conditions=[
                ExtensionIsCondition(".zip"),  # Matches
                FileSizeGreaterThanCondition(5 * 1024 * 1024)  # Doesn't match (file is 100KB)
            ],
            actions=[CopyAction(test_structure["copy"])],
            match_mode="any"
        )

        executor = RuleExecutor()
        fileinfo = get_fileinfo(old_small_file)
        result = executor.execute([rule], fileinfo, basic_config)
        logs = result.get("log", []) if isinstance(result, dict) else result

        # Should match (at least one condition true)
        assert any("MATCHED" in log for log in logs)

    def test_sequential_rules_chaining(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test sequential rules where one rule's output affects the next."""
        txt_file = test_file_factory(test_structure["source"], "report.txt")

        # Rule 1: Rename
        rule1 = Rule(
            name="Rename Reports",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[RenameAction("report_processed.txt")],
            stop_on_match=False  # Continue to next rule
        )

        # Rule 2: Move renamed file
        rule2 = Rule(
            name="Archive Reports",
            conditions=[NameContainsCondition("processed")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()
        fileinfo = get_fileinfo(txt_file)
        result = executor.execute([rule1, rule2], fileinfo, basic_config)
        logs = result.get("log", []) if isinstance(result, dict) else result

        # Rule 1 should execute and rename
        assert any("RENAME" in log for log in logs)

        # Rule 2 should execute (if rename completed and file matches)
        assert any("Archive Reports" in log for log in logs)


@pytest.mark.integration
class TestSafetyAndCollisions:
    """Test safety features and collision handling."""

    def test_safe_mode_collision_prevention(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test safe_mode prevents collisions."""
        # Create source file
        src = test_file_factory(test_structure["source"], "file.txt", "source")

        # Create collision target
        test_file_factory(test_structure["dest"], "file.txt", "existing")
        test_file_factory(test_structure["dest"], "file (1).txt", "collision1")

        fileinfo = get_fileinfo(src)

        rule = Rule(
            name="Move",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()
        result = executor.execute([rule], fileinfo, basic_config)
        logs = result.get("log", []) if isinstance(result, dict) else result

        # Should successfully move with collision avoidance
        assert any("MATCHED" in log for log in logs)

        # File should exist at collision-safe path
        files = os.listdir(test_structure["dest"])
        assert "file (2).txt" in files  # Next available name

    def test_multiple_actions_partial_failure(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test rule continues after one action fails."""
        txt_file = test_file_factory(test_structure["source"], "file.txt")

        rule = Rule(
            name="Multi-action",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[
                RenameAction("newname.txt"),
                # Second action could fail, but first succeeded
                CopyAction(test_structure["copy"])
            ]
        )

        executor = RuleExecutor()
        fileinfo = get_fileinfo(txt_file)
        result = executor.execute([rule], fileinfo, basic_config)
        logs = result.get("log", []) if isinstance(result, dict) else result

        # At least first action should succeed
        assert any("RENAME" in log for log in logs)


@pytest.mark.integration
class TestActivityLogWithRealOperations:
    """Test Activity Log captures real operations correctly."""

    def test_activity_log_captures_complete_workflow(self, test_structure, test_file_factory, basic_config, clear_activity_log, clear_undo_manager):
        """Test Activity Log captures complete rule execution workflow."""
        ACTIVITY_LOG.clear()
        pdf_file = test_file_factory(test_structure["source"], "document.pdf")

        rule = Rule(
            name="Archive PDFs",
            conditions=[ExtensionIsCondition(".pdf")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()
        fileinfo = get_fileinfo(pdf_file)
        result = executor.execute([rule], fileinfo, basic_config)
        logs = result.get("log", []) if isinstance(result, dict) else result

        # Check Activity Log
        activity_logs = ACTIVITY_LOG.get_log()
        assert len(activity_logs) > 0

        activity_text = ACTIVITY_LOG.get_log_text()
        assert "document.pdf" in activity_text
        assert "Archive PDFs" in activity_text
        assert "MATCHED" in activity_text

    def test_activity_log_dry_run_vs_real(self, test_structure, test_file_factory, clear_activity_log):
        """Test Activity Log clearly distinguishes dry_run vs real operations."""
        ACTIVITY_LOG.clear()

        # Dry run operation
        file1 = test_file_factory(test_structure["source"], "dry_run.txt")
        rule = Rule(
            name="Test",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()
        dry_run_config = {"dry_run": True, "safe_mode": True}
        executor.execute([rule], get_fileinfo(file1), dry_run_config)

        dry_run_logs = ACTIVITY_LOG.get_log_text()
        assert "DRY RUN" in dry_run_logs

        ACTIVITY_LOG.clear()

        # Real operation
        file2 = test_file_factory(test_structure["source"], "real.txt")
        executor = RuleExecutor()
        basic_config = {"dry_run": False, "safe_mode": True}
        executor.execute([rule], get_fileinfo(file2), basic_config)

        real_logs = ACTIVITY_LOG.get_log_text()
        assert "DRY RUN" not in real_logs
        assert "MOVE" in real_logs


@pytest.mark.integration
class TestUndoWithComplexOperations:
    """Test undo system with complex rule operations."""

    def test_undo_after_multi_file_batch(self, test_structure, test_file_factory, basic_config, clear_activity_log, clear_undo_manager):
        """Test undoing operations from a batch of files."""
        UNDO_MANAGER.clear_history()

        # Simulate processing batch of files
        files = [
            test_file_factory(test_structure["source"], "file1.pdf"),
            test_file_factory(test_structure["source"], "file2.pdf"),
            test_file_factory(test_structure["source"], "file3.pdf")
        ]

        rule = Rule(
            name="Archive",
            conditions=[ExtensionIsCondition(".pdf")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()

        # Process each file
        for f in files:
            executor.execute([rule], get_fileinfo(f), basic_config)

        # Should have 3 undo entries
        assert len(UNDO_MANAGER) == 3

        # Undo all operations
        while len(UNDO_MANAGER) > 0:
            result = UNDO_MANAGER.undo_last()
            assert result["success"]

        # All files should be back in source
        for f in files:
            assert os.path.exists(f)

        # Dest should be empty
        assert len(os.listdir(test_structure["dest"])) == 0


@pytest.mark.integration
class TestIdempotentOrganization:
    """Test that organizing is idempotent (second run = no changes)."""

    def test_organizing_twice_is_idempotent(self, test_structure, test_file_factory, basic_config, clear_activity_log, clear_undo_manager):
        """Test that running Organise twice produces zero changes on second run."""
        UNDO_MANAGER.clear_history()

        # Create files in source
        file1 = test_file_factory(test_structure["source"], "doc1.pdf")
        file2 = test_file_factory(test_structure["source"], "doc2.pdf")

        rule = Rule(
            name="Move PDFs",
            conditions=[ExtensionIsCondition(".pdf")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()

        # FIRST RUN: Move files
        result1 = executor.execute([rule], get_fileinfo(file1), basic_config)
        result2 = executor.execute([rule], get_fileinfo(file2), basic_config)

        # Files should be in dest now
        assert not os.path.exists(file1)
        assert not os.path.exists(file2)
        assert os.path.exists(os.path.join(test_structure["dest"], "doc1.pdf"))
        assert os.path.exists(os.path.join(test_structure["dest"], "doc2.pdf"))

        # SECOND RUN: Try to organize again
        file1_moved = os.path.join(test_structure["dest"], "doc1.pdf")
        file2_moved = os.path.join(test_structure["dest"], "doc2.pdf")

        ACTIVITY_LOG.clear()
        result1_again = executor.execute([rule], get_fileinfo(file1_moved), basic_config)
        result2_again = executor.execute([rule], get_fileinfo(file2_moved), basic_config)
        logs = ACTIVITY_LOG.get_log_text()

        # Second run should skip (SKIP: MOVE logged)
        assert "SKIP: MOVE" in logs
        # Files should still be in same location
        assert os.path.exists(os.path.join(test_structure["dest"], "doc1.pdf"))
        assert os.path.exists(os.path.join(test_structure["dest"], "doc2.pdf"))

    def test_rename_then_move_is_idempotent(self, test_structure, test_file_factory, basic_config, clear_activity_log, clear_undo_manager):
        """Test rename+move sequence is idempotent."""
        UNDO_MANAGER.clear_history()

        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Rename and Move",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[
                RenameAction("processed.txt"),
                MoveAction(test_structure["dest"])
            ]
        )

        executor = RuleExecutor()

        # FIRST RUN
        result1 = executor.execute([rule], fileinfo, basic_config)
        moved_file = os.path.join(test_structure["dest"], "processed.txt")
        assert os.path.exists(moved_file)
        assert not os.path.exists(src_file)

        # SECOND RUN: Process the already-processed file
        fileinfo_again = get_fileinfo(moved_file)
        ACTIVITY_LOG.clear()
        result2 = executor.execute([rule], fileinfo_again, basic_config)
        logs = ACTIVITY_LOG.get_log_text()

        # Should skip both operations (already processed and already in destination)
        assert "SKIP" in logs  # Either rename or move or both
        assert os.path.exists(moved_file)

    def test_multiple_organise_runs_zero_changes(self, test_structure, test_file_factory, basic_config, clear_activity_log, clear_undo_manager):
        """Test that multiple Organise runs after first have zero changes."""
        UNDO_MANAGER.clear_history()

        # Create test files
        files = [
            test_file_factory(test_structure["source"], f"file{i}.pdf")
            for i in range(3)
        ]

        rule = Rule(
            name="Archive All",
            conditions=[ExtensionIsCondition(".pdf")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()

        # FIRST RUN: Organize
        for f in files:
            executor.execute([rule], get_fileinfo(f), basic_config)

        # Verify all moved
        for i in range(3):
            assert os.path.exists(os.path.join(test_structure["dest"], f"file{i}.pdf"))

        # SECOND AND THIRD RUNS: No changes expected
        for run_num in range(2, 4):
            ACTIVITY_LOG.clear()
            moved_files = [
                os.path.join(test_structure["dest"], f"file{i}.pdf")
                for i in range(3)
            ]
            for f in moved_files:
                executor.execute([rule], get_fileinfo(f), basic_config)

            logs = ACTIVITY_LOG.get_log_text()
            # All should be SKIPped
            assert "SKIP: MOVE" in logs
            # Files still in dest
            for i in range(3):
                assert os.path.exists(os.path.join(test_structure["dest"], f"file{i}.pdf"))
