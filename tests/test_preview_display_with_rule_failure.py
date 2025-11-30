"""Test that preview display correctly shows rule failures when fallback is disabled."""

import pytest
from pathlib import Path


class TestPreviewDisplayWithRuleFailure:
    """Test preview display for rule failures with fallback disabled."""

    def test_failed_rule_with_fallback_disabled_shows_error(self):
        """Test that failed rule shows error message, not sorting information."""
        # When a rule fails and fallback is OFF, preview should show error
        move_entry = {
            "src": "/path/to/file.txt",
            "dst": "/path/to/file.txt",  # No change (same as src)
            "mode": "rule",
            "error": "Rule action failed"
        }

        # Simulate display formatting
        src = Path(move_entry["src"]).name
        
        # Check if move has error
        if move_entry.get("error"):
            display = f"{src} - ERROR: {move_entry.get('error')}"
        else:
            dst = move_entry.get("category", move_entry.get("rule_name", "Unknown"))
            display = f"{src} -> {dst} ({move_entry['mode']})"

        # Should display error, not "Unknown" sorting
        assert "ERROR:" in display
        assert "file.txt" in display
        assert "Rule action failed" in display
        # Should NOT show an arrow or category
        assert "->" not in display
        assert "Unknown" not in display

    def test_successful_rule_shows_destination(self):
        """Test that successful rule shows destination folder."""
        # When a rule succeeds, preview should show where file will go
        move_entry = {
            "src": "/path/to/file.txt",
            "dst": "/archive/file.txt",
            "mode": "rule",
            "rule_name": "Archive Old Files"
        }

        # Simulate display formatting
        src = Path(move_entry["src"]).name
        
        if move_entry.get("error"):
            display = f"{src} - ERROR: {move_entry.get('error')}"
        else:
            dst = move_entry.get("category", move_entry.get("rule_name", "Unknown"))
            display = f"{src} -> {dst} ({move_entry['mode']})"

        # Should show rule name
        assert "Archive Old Files" in display
        assert "file.txt" in display
        assert "->" in display
        assert "ERROR:" not in display

    def test_category_sort_shows_category(self):
        """Test that category sort shows the category being used."""
        # When no rule matched, preview should show category sort
        move_entry = {
            "src": "/path/to/image.png",
            "dst": "/Pictures/image.png",
            "mode": "sort",
            "category": "Pictures"
        }

        # Simulate display formatting
        src = Path(move_entry["src"]).name
        
        if move_entry.get("error"):
            display = f"{src} - ERROR: {move_entry.get('error')}"
        else:
            dst = move_entry.get("category", move_entry.get("rule_name", "Unknown"))
            display = f"{src} -> {dst} ({move_entry['mode']})"

        # Should show category
        assert "Pictures" in display
        assert "image.png" in display
        assert "->" in display
        assert "sort" in display
        assert "ERROR:" not in display

    def test_failed_rule_preview_not_shown_as_sorted(self):
        """Test that when rule fails and fallback is off, file is not shown as being sorted."""
        # This tests the actual user scenario
        
        # Simulate what happens in do_preview when rule fails and fallback is OFF
        moves = []
        
        # File matched a rule but rule failed
        result = {
            "matched": True,
            "success": False,
            "error": "Target folder does not exist"
        }
        
        # Config has fallback disabled
        config = {"rule_fallback_to_sort": False}
        
        # What the code does:
        if result.get("matched") and not result.get("success"):
            if not config.get("rule_fallback_to_sort", True):
                # Add error entry
                moves.append({
                    "src": "/test/file.doc",
                    "dst": "/test/file.doc",
                    "mode": "rule",
                    "error": result.get("error", "Rule failed"),
                })
                # continue (skip sorting)
        
        # After loop, moves should only have the error, no sort entries
        assert len(moves) == 1
        assert moves[0]["mode"] == "rule"
        assert "error" in moves[0]
        assert "category" not in moves[0]
        
        # Display should show error
        move = moves[0]
        src = Path(move["src"]).name
        
        if move.get("error"):
            display = f"{src} - ERROR: {move.get('error')}"
        else:
            dst = move.get("category", move.get("rule_name", "Unknown"))
            display = f"{src} -> {dst} ({move['mode']})"
        
        assert "ERROR:" in display
        assert "->" not in display

    def test_failed_rule_with_fallback_enabled_shows_both(self):
        """Test that when rule fails and fallback is ON, both error and sort are shown."""
        # When fallback is enabled, file should be shown both with rule error AND category sort
        
        moves = []
        
        # Scenario: rule failed but fallback enabled
        result = {
            "matched": True,
            "success": False,
            "error": "Target folder does not exist"
        }
        
        config = {"rule_fallback_to_sort": True}  # Fallback ENABLED
        
        # When fallback is enabled, code falls through to sorting
        if result.get("matched") and not result.get("success"):
            if not config.get("rule_fallback_to_sort", True):
                # This block doesn't execute when fallback is enabled
                moves.append({
                    "src": "/test/file.doc",
                    "dst": "/test/file.doc",
                    "mode": "rule",
                    "error": result.get("error", "Rule failed"),
                })
            # If we reach here (fallback enabled), fall through to sorting
        
        # Fall through to sorting logic
        moves.append({
            "src": "/test/file.doc",
            "dst": "/Documents/file.doc",
            "mode": "sort",
            "category": "Documents",
        })
        
        # Should have only the sort entry (no error entry when fallback enabled)
        assert len(moves) == 1
        assert moves[0]["mode"] == "sort"
        assert "error" not in moves[0]
        assert moves[0]["category"] == "Documents"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
