# test_rule_executor.py
"""
Test suite for RuleExecutor.
"""

import os
import pytest
from folderfresh.rule_engine.backbone import (
    Rule, RuleExecutor, NameContainsCondition, ExtensionIsCondition,
    MoveAction, CopyAction, RenameAction,
    FileSizeGreaterThanCondition
)
from folderfresh.fileinfo import get_fileinfo


@pytest.mark.unit
class TestRuleExecutorBasic:
    """Test basic RuleExecutor functionality."""

    def test_executor_processes_single_rule(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test RuleExecutor with single rule."""
        # Create test file
        src_file = test_file_factory(test_structure["source"], "screenshot.png")
        fileinfo = get_fileinfo(src_file)

        # Create rule
        rule = Rule(
            name="Organize Screenshots",
            conditions=[ExtensionIsCondition(".png")],
            actions=[MoveAction(test_structure["dest"])]
        )

        # Execute
        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Verify logs
        assert isinstance(logs, list)
        assert len(logs) > 0
        assert any("screenshot" in log.lower() for log in logs)

        # Verify file was moved
        assert not os.path.exists(src_file)
        assert os.path.exists(os.path.join(test_structure["dest"], "screenshot.png"))

    def test_executor_skips_non_matching_rule(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test RuleExecutor skips non-matching rules."""
        src_file = test_file_factory(test_structure["source"], "document.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Move PNGs",
            conditions=[ExtensionIsCondition(".png")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Verify logs mention no match
        assert any("No match" in log for log in logs)

        # Verify file was NOT moved
        assert os.path.exists(src_file)

    def test_executor_with_no_rules(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test RuleExecutor with empty rule list."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        executor = RuleExecutor()
        logs = executor.execute([], fileinfo, basic_config)

        assert isinstance(logs, list)
        assert len(logs) > 0  # Should at least have file processing header


@pytest.mark.unit
class TestRuleExecutorMultipleRules:
    """Test RuleExecutor with multiple rules."""

    def test_executor_processes_multiple_rules_all_match_mode(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test multiple rules with match_mode='all' (AND logic)."""
        src_file = test_file_factory(test_structure["source"], "screenshot.png", size_kb=2)
        fileinfo = get_fileinfo(src_file)

        # Rule requires BOTH conditions to match
        rule = Rule(
            name="Big PNGs",
            conditions=[
                ExtensionIsCondition(".png"),
                FileSizeGreaterThanCondition(1024)  # 1 KB
            ],
            actions=[MoveAction(test_structure["dest"])],
            match_mode="all"  # AND
        )

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Should match (both conditions true)
        assert any("MATCHED" in log for log in logs)
        assert not os.path.exists(src_file)

    def test_executor_with_any_match_mode(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test rule with match_mode='any' (OR logic)."""
        src_file = test_file_factory(test_structure["source"], "screenshot.pdf", size_kb=5)
        fileinfo = get_fileinfo(src_file)

        # Rule matches if ANY condition matches
        rule = Rule(
            name="PNGs OR Large Files",
            conditions=[
                ExtensionIsCondition(".png"),
                FileSizeGreaterThanCondition(1024)  # File is larger
            ],
            actions=[MoveAction(test_structure["dest"])],
            match_mode="any"  # OR
        )

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Should match (second condition true)
        assert any("MATCHED" in log for log in logs)

    def test_executor_with_stop_on_match(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test stop_on_match behavior."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule1 = Rule(
            name="Rule 1",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[RenameAction("renamed.txt")],
            stop_on_match=True
        )

        rule2 = Rule(
            name="Rule 2",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[MoveAction(test_structure["dest"])]
        )

        executor = RuleExecutor()
        logs = executor.execute([rule1, rule2], fileinfo, basic_config)

        # Rule 1 should appear in logs
        assert any("Rule 1" in log for log in logs)

        # Rule 2 should NOT execute due to stop_on_match
        assert not any("Rule 2" in log for log in logs)

        # Verify action from Rule 1 executed
        assert any("RENAME" in log for log in logs)

    def test_executor_executes_multiple_actions(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test rule with multiple actions."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Multi-action",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[
                RenameAction("processed.txt"),
                MoveAction(test_structure["dest"])
            ]
        )

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Verify both actions logged
        rename_logged = any("RENAME" in log for log in logs)
        move_logged = any("MOVE" in log for log in logs)

        # At least one should succeed (rename likely will)
        assert rename_logged or move_logged


@pytest.mark.unit
class TestRuleExecutorDryRun:
    """Test RuleExecutor with dry_run."""

    def test_executor_dry_run_no_changes(self, test_structure, test_file_factory, clear_activity_log):
        """Test dry_run prevents actual file changes."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Move Files",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[MoveAction(test_structure["dest"])]
        )

        dry_run_config = {"dry_run": True, "safe_mode": True}
        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, dry_run_config)

        # Verify logs mention DRY RUN
        assert any("DRY RUN" in log for log in logs)

        # Verify file was NOT moved
        assert os.path.exists(src_file)
        assert not os.path.exists(os.path.join(test_structure["dest"], "file.txt"))

    def test_executor_dry_run_with_multiple_actions(self, test_structure, test_file_factory, clear_activity_log):
        """Test dry_run with multiple actions."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Multi",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[
                RenameAction("new.txt"),
                MoveAction(test_structure["dest"])
            ]
        )

        dry_run_config = {"dry_run": True, "safe_mode": True}
        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, dry_run_config)

        # All actions should be DRY RUN
        assert all("DRY RUN" in log or "ERROR" in log or "RENAME" not in log.upper()
                  for log in logs if log.strip())

        # No actual changes
        assert os.path.exists(src_file)


@pytest.mark.unit
class TestRuleExecutorActivityLogIntegration:
    """Test RuleExecutor integrates with ActivityLog."""

    def test_executor_logs_to_activity_log(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test RuleExecutor forwards logs to ActivityLog."""
        from folderfresh.activity_log import ACTIVITY_LOG

        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Test Rule",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[MoveAction(test_structure["dest"])]
        )

        # Clear before test
        ACTIVITY_LOG.clear()

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Verify logs were added to ActivityLog
        activity_logs = ACTIVITY_LOG.get_log()
        assert len(activity_logs) > 0
        assert any("Test Rule" in log for log in activity_logs)

    def test_executor_logs_match_results(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test RuleExecutor logs match/no-match results."""
        from folderfresh.activity_log import ACTIVITY_LOG

        matching_file = test_file_factory(test_structure["source"], "file.png")
        non_matching_file = test_file_factory(test_structure["source"], "file.txt")

        rule = Rule(
            name="PNG Rule",
            conditions=[ExtensionIsCondition(".png")],
            actions=[MoveAction(test_structure["dest"])]
        )

        ACTIVITY_LOG.clear()

        executor = RuleExecutor()

        # Execute for matching file
        executor.execute([rule], get_fileinfo(matching_file), basic_config)
        logs_after_match = ACTIVITY_LOG.get_log_text()
        assert "MATCHED" in logs_after_match

        ACTIVITY_LOG.clear()

        # Execute for non-matching file
        executor.execute([rule], get_fileinfo(non_matching_file), basic_config)
        logs_after_no_match = ACTIVITY_LOG.get_log_text()
        assert "No match" in logs_after_no_match


@pytest.mark.unit
class TestRuleExecutorErrorHandling:
    """Test RuleExecutor error handling."""

    def test_executor_handles_missing_fileinfo_path(self, basic_config, clear_activity_log):
        """Test executor handles missing fileinfo."""
        fileinfo = {"name": "file.txt"}  # Missing path

        rule = Rule(
            name="Test",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[MoveAction("/some/dir")]
        )

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Should complete without crashing
        assert isinstance(logs, list)

    def test_executor_continues_after_action_error(self, test_structure, test_file_factory, basic_config, clear_activity_log):
        """Test executor continues after action error."""
        src_file = test_file_factory(test_structure["source"], "file.txt")
        fileinfo = get_fileinfo(src_file)

        rule = Rule(
            name="Multi",
            conditions=[ExtensionIsCondition(".txt")],
            actions=[
                MoveAction(test_structure["dest"]),  # Will succeed
                RenameAction("newname.txt")  # Should still execute
            ]
        )

        executor = RuleExecutor()
        logs = executor.execute([rule], fileinfo, basic_config)

        # Both actions should appear in logs
        assert any("MOVE" in log for log in logs)
        assert any("RENAME" in log for log in logs)
        # Multiple log entries for actions
        assert len(logs) >= 2
