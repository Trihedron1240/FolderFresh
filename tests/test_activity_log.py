# test_activity_log.py
"""
Test suite for Activity Log system.
"""

import pytest
from folderfresh.activity_log import ACTIVITY_LOG, log_activity


@pytest.mark.unit
class TestActivityLogBasic:
    """Test basic ActivityLog functionality."""

    def test_activity_log_append(self, clear_activity_log):
        """Test appending to activity log."""
        ACTIVITY_LOG.clear()

        log_activity("Test message")

        logs = ACTIVITY_LOG.get_log()
        assert len(logs) == 1
        assert "Test message" in logs[0]
        assert "[" in logs[0]  # Contains timestamp

    def test_activity_log_timestamp(self, clear_activity_log):
        """Test activity log adds timestamp."""
        ACTIVITY_LOG.clear()

        log_activity("Message")

        logs = ACTIVITY_LOG.get_log()
        assert "[" in logs[0]
        assert "]" in logs[0]
        # Format: [YYYY-MM-DD HH:MM:SS] Message

    def test_activity_log_get_log_text(self, clear_activity_log):
        """Test getting all logs as text."""
        ACTIVITY_LOG.clear()

        log_activity("First")
        log_activity("Second")
        log_activity("Third")

        text = ACTIVITY_LOG.get_log_text()
        assert "First" in text
        assert "Second" in text
        assert "Third" in text
        assert "\n" in text  # Should be multiline

    def test_activity_log_clear(self, clear_activity_log):
        """Test clearing activity log."""
        ACTIVITY_LOG.clear()

        log_activity("Message 1")
        log_activity("Message 2")
        assert len(ACTIVITY_LOG) == 2

        ACTIVITY_LOG.clear()
        assert len(ACTIVITY_LOG) == 0

    def test_activity_log_len(self, clear_activity_log):
        """Test getting activity log count."""
        ACTIVITY_LOG.clear()

        assert len(ACTIVITY_LOG) == 0

        log_activity("Msg 1")
        assert len(ACTIVITY_LOG) == 1

        log_activity("Msg 2")
        assert len(ACTIVITY_LOG) == 2

    def test_activity_log_multiple_messages(self, clear_activity_log):
        """Test adding multiple messages."""
        ACTIVITY_LOG.clear()

        messages = ["Message 1", "Message 2", "Message 3", "Message 4"]
        for msg in messages:
            log_activity(msg)

        logs = ACTIVITY_LOG.get_log()
        assert len(logs) == 4

        for msg in messages:
            assert any(msg in log for log in logs)


@pytest.mark.unit
class TestActivityLogBoundedSize:
    """Test activity log bounded size (max entries)."""

    def test_activity_log_respects_max_size(self, clear_activity_log):
        """Test activity log doesn't exceed max entries."""
        ACTIVITY_LOG.clear()

        # Add more than max (ActivityLog.MAX_ENTRIES = 2000)
        for i in range(2100):  # More than default 2000
            log_activity(f"Message {i}")

        # Should only have max entries
        assert len(ACTIVITY_LOG) <= 2000

    def test_activity_log_fifo_when_full(self, clear_activity_log):
        """Test FIFO behavior when log is full."""
        ACTIVITY_LOG.clear()

        # Fill beyond capacity (ActivityLog.MAX_ENTRIES = 2000)
        for i in range(2100):
            log_activity(f"Message {i}")

        logs = ACTIVITY_LOG.get_log()

        # Should have exactly max entries when full
        assert len(logs) == 2000, f"Expected 2000 entries, got {len(logs)}"

        # Newest messages should exist
        text = ACTIVITY_LOG.get_log_text()
        assert "Message 2099" in text or "Message 2098" in text


@pytest.mark.unit
class TestActivityLogIntegration:
    """Test ActivityLog integration with other systems."""

    def test_activity_log_persists_across_calls(self, clear_activity_log):
        """Test activity log persists across multiple calls."""
        ACTIVITY_LOG.clear()

        # Simulate watcher operation 1
        log_activity("File: document.pdf")
        log_activity("Rule: Organize PDFs")
        log_activity("Action: MOVE")

        assert len(ACTIVITY_LOG) == 3

        # Simulate watcher operation 2
        log_activity("File: image.jpg")
        log_activity("Rule: Organize Images")
        log_activity("Action: MOVE")

        assert len(ACTIVITY_LOG) == 6

        text = ACTIVITY_LOG.get_log_text()
        assert "document.pdf" in text
        assert "image.jpg" in text

    def test_activity_log_handles_multiline_messages(self, clear_activity_log):
        """Test activity log with multiline content."""
        ACTIVITY_LOG.clear()

        # This might happen with error messages
        msg = "ERROR: Something went wrong\nDetails: File locked"
        log_activity(msg)

        logs = ACTIVITY_LOG.get_log()
        assert len(logs) == 1
        assert "ERROR" in logs[0]

    def test_activity_log_empty_message(self, clear_activity_log):
        """Test activity log with empty message."""
        ACTIVITY_LOG.clear()

        log_activity("")

        assert len(ACTIVITY_LOG) == 1  # Still recorded with timestamp

    def test_activity_log_special_characters(self, clear_activity_log):
        """Test activity log with special characters."""
        ACTIVITY_LOG.clear()

        special_msg = "Path: C:\\Users\\test\\file (1).txt → C:\\Archive\\file.pdf"
        log_activity(special_msg)

        text = ACTIVITY_LOG.get_log_text()
        assert "→" in text
        assert "file (1).txt" in text


@pytest.mark.unit
class TestActivityLogSaveLoad:
    """Test activity log persistence."""

    def test_activity_log_save_to_file(self, temp_dir, clear_activity_log):
        """Test saving activity log to file."""
        ACTIVITY_LOG.clear()

        log_activity("Message 1")
        log_activity("Message 2")

        filepath = os.path.join(temp_dir, "activity_log.json")
        success = ACTIVITY_LOG.save_to_file(filepath)

        assert success is True
        assert os.path.exists(filepath)

        # Verify file has content
        with open(filepath, "r") as f:
            content = f.read()
            assert "Message 1" in content
            assert "Message 2" in content

    def test_activity_log_load_from_file(self, temp_dir, clear_activity_log):
        """Test loading activity log from file."""
        import json

        ACTIVITY_LOG.clear()

        # Create a test file
        filepath = os.path.join(temp_dir, "test_log.json")
        data = {
            "saved_at": "2025-02-08T12:00:00",
            "entries": [
                "[2025-02-08 12:00:00] Loaded message 1",
                "[2025-02-08 12:00:01] Loaded message 2"
            ]
        }

        with open(filepath, "w") as f:
            json.dump(data, f)

        # Load it
        success = ACTIVITY_LOG.load_from_file(filepath)

        assert success is True
        assert len(ACTIVITY_LOG) == 2
        assert "Loaded message 1" in ACTIVITY_LOG.get_log_text()


@pytest.mark.unit
class TestActivityLogFormat:
    """Test activity log format and structure."""

    def test_log_entries_are_strings(self, clear_activity_log):
        """Test log entries are strings."""
        ACTIVITY_LOG.clear()

        log_activity("Test")

        logs = ACTIVITY_LOG.get_log()
        assert all(isinstance(log, str) for log in logs)

    def test_log_text_is_string(self, clear_activity_log):
        """Test get_log_text returns string."""
        ACTIVITY_LOG.clear()

        log_activity("Test")

        text = ACTIVITY_LOG.get_log_text()
        assert isinstance(text, str)

    def test_empty_log_returns_empty_text(self, clear_activity_log):
        """Test empty log returns empty string."""
        ACTIVITY_LOG.clear()

        text = ACTIVITY_LOG.get_log_text()
        assert text == ""


# Need to import os for save/load tests
import os
