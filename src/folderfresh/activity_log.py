# activity_log.py

from datetime import datetime
from collections import deque
from typing import List
import json
import os


class ActivityLog:
    """
    In-memory ring buffer for activity logging.

    Stores up to MAX_ENTRIES log entries with timestamps.
    Provides append, get_log, clear, and persistence methods.
    """

    MAX_ENTRIES = 2000

    def __init__(self):
        """Initialize the activity log with a ring buffer."""
        self.log_buffer: deque = deque(maxlen=self.MAX_ENTRIES)
        self.lock = False  # Simple flag to prevent concurrent modification during iteration

    def append(self, message: str):
        """
        Add a message to the activity log with a timestamp.

        Args:
            message: Log message (without timestamp)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_entry = f"[{timestamp}] {message}"
        self.log_buffer.append(formatted_entry)

    def get_log(self) -> List[str]:
        """
        Get all log entries as a list.

        Returns:
            List of log entries in chronological order
        """
        return list(self.log_buffer)

    def get_log_text(self) -> str:
        """
        Get all log entries as a single text string.

        Returns:
            All log entries joined with newlines
        """
        return "\n".join(self.get_log())

    def clear(self):
        """Clear all log entries."""
        self.log_buffer.clear()

    def save_to_file(self, filepath: str) -> bool:
        """
        Save log entries to a JSON file.

        Args:
            filepath: Path to save the log file

        Returns:
            True if successful, False if error
        """
        try:
            data = {
                "saved_at": datetime.now().isoformat(),
                "entries": self.get_log()
            }
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving activity log: {e}")
            return False

    def load_from_file(self, filepath: str) -> bool:
        """
        Load log entries from a JSON file.

        Args:
            filepath: Path to load the log file from

        Returns:
            True if successful, False if error or file doesn't exist
        """
        try:
            if not os.path.exists(filepath):
                return False

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data.get("entries"), list):
                self.log_buffer.clear()
                for entry in data["entries"]:
                    # Don't re-timestamp, use original timestamp from file
                    self.log_buffer.append(entry)
                return True
            return False
        except Exception as e:
            print(f"Error loading activity log: {e}")
            return False

    def __len__(self) -> int:
        """Return the number of entries in the log."""
        return len(self.log_buffer)


# Global singleton instance
ACTIVITY_LOG = ActivityLog()


def log_activity(message: str):
    """
    Convenience function to log a message to the global activity log.

    Args:
        message: Message to log
    """
    ACTIVITY_LOG.append(message)
