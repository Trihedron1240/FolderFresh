"""
ActivityLogWindow Backend Integration
Connects ActivityLogWindow to ActivityLog backend
"""

from typing import List

from PySide6.QtCore import Signal, QTimer, QObject

from folderfresh.activity_log import ACTIVITY_LOG
from folderfresh.ui_qt.dialogs import (
    show_confirmation_dialog,
    show_error_dialog,
    show_info_dialog,
    save_file_dialog
)
from folderfresh.logger_qt import log_info, log_error


class ActivityLogBackend(QObject):
    """
    Backend integration for ActivityLogWindow.
    Provides access to activity log entries and operations.
    """

    # Signals
    log_updated = Signal(list)  # entries
    log_cleared = Signal()
    log_exported = Signal(str)  # file_path

    def __init__(self, auto_refresh: bool = True, refresh_interval: int = 1000):
        """
        Initialize ActivityLog backend

        Args:
            auto_refresh: Enable auto-refresh of log
            refresh_interval: Refresh interval in ms
        """
        super().__init__()
        self.activity_log = ACTIVITY_LOG
        self.last_log_count = 0
        self.auto_refresh = auto_refresh

        # Setup auto-refresh timer
        if auto_refresh:
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self._check_for_updates)
            self.refresh_timer.start(refresh_interval)
        else:
            self.refresh_timer = None

        log_info("ActivityLogBackend initialized")

    def get_log_entries(self) -> List[str]:
        """
        Get all activity log entries

        Returns:
            List of log entries (newest first)
        """
        entries = self.activity_log.get_log()
        return list(reversed(entries))  # Newest first

    def get_log_text(self) -> str:
        """
        Get activity log as formatted text

        Returns:
            Log text
        """
        return self.activity_log.get_log_text()

    def get_log_count(self) -> int:
        """Get number of log entries"""
        return len(self.activity_log.get_log())

    def _check_for_updates(self) -> None:
        """Check if log has been updated and emit signal"""
        current_count = self.get_log_count()
        if current_count != self.last_log_count:
            self.last_log_count = current_count
            entries = self.get_log_entries()
            self.log_updated.emit(entries)

    def clear_log(self) -> bool:
        """
        Clear all activity log entries

        Returns:
            True if successful
        """
        try:
            if not show_confirmation_dialog(
                None,
                "Clear Activity Log",
                "Clear all activity log entries?\nThis cannot be undone."
            ):
                return False

            self.activity_log.clear()
            self.last_log_count = 0

            log_info("Activity log cleared")
            self.log_cleared.emit()
            show_info_dialog(None, "Activity Log Cleared", "Activity log cleared")

            return True

        except Exception as e:
            log_error(f"Failed to clear log: {e}")
            show_error_dialog(None, "Clear Log Failed", f"Failed to clear log:\n{e}")
            return False

    def export_log(self, file_path: str = None, format: str = "txt") -> bool:
        """
        Export log to file

        Args:
            file_path: Destination file path (uses dialog if None)
            format: "txt" or "csv"

        Returns:
            True if successful
        """
        try:
            if file_path is None:
                if format == "csv":
                    filter_str = "CSV Files (*.csv)"
                else:
                    filter_str = "Text Files (*.txt)"

                file_path = save_file_dialog(
                    None,
                    "Export Activity Log",
                    file_filter=filter_str
                )
                if not file_path:
                    return False

            # Export based on format
            if format == "csv":
                self._export_csv(file_path)
            else:
                self.activity_log.save_to_file(file_path)

            log_info(f"Activity log exported: {file_path}")
            self.log_exported.emit(file_path)
            show_info_dialog(None, "Log Exported", f"Log exported to:\n{file_path}")

            return True

        except Exception as e:
            log_error(f"Failed to export log: {e}")
            show_error_dialog(None, "Export Log Failed", f"Failed to export log:\n{e}")
            return False

    def _export_csv(self, file_path: str) -> None:
        """Export log as CSV"""
        import csv
        from datetime import datetime

        entries = self.get_log_entries()

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Message"])

            for entry in entries:
                # Try to parse timestamp from entry
                parts = entry.split(" - ", 1) if " - " in entry else [datetime.now().isoformat(), entry]
                timestamp = parts[0]
                message = parts[1] if len(parts) > 1 else entry

                writer.writerow([timestamp, message])

    def search_log(self, query: str) -> List[str]:
        """
        Search log entries

        Args:
            query: Search query

        Returns:
            Matching entries
        """
        entries = self.get_log_entries()
        query_lower = query.lower()
        return [e for e in entries if query_lower in e.lower()]

    def filter_log(self, pattern: str) -> List[str]:
        """
        Filter log entries by pattern

        Args:
            pattern: Regex pattern

        Returns:
            Matching entries
        """
        import re

        entries = self.get_log_entries()
        try:
            regex = re.compile(pattern)
            return [e for e in entries if regex.search(e)]
        except re.error:
            log_error(f"Invalid regex pattern: {pattern}")
            return []

    def copy_to_clipboard(self, text: str) -> bool:
        """
        Copy text to clipboard

        Args:
            text: Text to copy

        Returns:
            True if successful
        """
        try:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            return True
        except Exception as e:
            log_error(f"Failed to copy to clipboard: {e}")
            return False

    def start_auto_refresh(self, interval: int = 1000) -> None:
        """
        Start auto-refresh of log display

        Args:
            interval: Refresh interval in ms
        """
        if not self.refresh_timer:
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self._check_for_updates)

        self.refresh_timer.start(interval)
        log_info(f"Activity log auto-refresh started ({interval}ms)")

    def stop_auto_refresh(self) -> None:
        """Stop auto-refresh of log display"""
        if self.refresh_timer:
            self.refresh_timer.stop()
            log_info("Activity log auto-refresh stopped")

    def get_recent_entries(self, count: int = 10) -> List[str]:
        """
        Get most recent log entries

        Args:
            count: Number of entries to return

        Returns:
            Recent entries
        """
        entries = self.get_log_entries()
        return entries[:count]

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.refresh_timer:
            self.refresh_timer.stop()
            log_info("ActivityLogBackend cleanup complete")
