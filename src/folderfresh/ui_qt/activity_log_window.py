"""
PySide6 activity log window for FolderFresh.
Display real-time rule execution logs with search and export features.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)
from PySide6.QtCore import Qt, Signal, QTimer

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    DangerButton,
    StyledLineEdit,
    StyledTextEdit,
    HeadingLabel,
    MutedLabel,
    StyledLabel,
    VerticalFrame,
    HorizontalFrame,
)
from .dialogs import show_confirmation_dialog, show_info_dialog, show_error_dialog, save_file_dialog


class ActivityLogWindow(QDialog):
    """Dialog for displaying and managing activity log."""

    # Signals
    undo_last_requested = Signal()
    undo_history_requested = Signal()
    clear_log_clicked = Signal()
    export_log_clicked = Signal()
    search_requested = Signal(str)  # search query
    closed = Signal()

    def __init__(self, parent=None, log_entries=None):
        """
        Initialize activity log window.

        Args:
            parent: Parent widget
            log_entries: List of log entry dictionaries with 'timestamp', 'action', 'details'
        """
        super().__init__(parent)
        self.setWindowTitle("Activity Log")
        self.setGeometry(200, 100, 900, 700)
        self.setMinimumSize(700, 500)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.log_entries = log_entries or []
        self.filtered_entries = self.log_entries.copy()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._on_auto_refresh)
        self.refresh_timer.start(1000)  # Refresh every 1 second

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header with title and entry count
        header_frame = HorizontalFrame(spacing=12)

        title = HeadingLabel("Activity Log")
        header_frame.add_widget(title)

        self.entry_count_label = MutedLabel(f"({len(self.log_entries)} entries)")
        header_frame.add_widget(self.entry_count_label)

        header_frame.add_stretch()

        main_layout.addWidget(header_frame)

        # Search/filter section
        search_frame = HorizontalFrame(spacing=8)

        search_label = StyledLabel("Filter:", font_size=Fonts.SIZE_SMALL)
        search_frame.add_widget(search_label)

        self.search_entry = StyledLineEdit(
            placeholder="Search log entries...",
            font_size=Fonts.SIZE_SMALL,
        )
        self.search_entry.textChanged.connect(self._on_search_changed)
        search_frame.add_widget(self.search_entry)

        main_layout.addWidget(search_frame)

        # Log text area (read-only)
        self.log_text = StyledTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(300)
        self.log_text.setPlainText("(No activity yet)")
        main_layout.addWidget(self.log_text, 1)

        # Button bar
        button_frame = VerticalFrame(spacing=8)

        # Action buttons (left side)
        action_frame = HorizontalFrame(spacing=8)

        undo_last_btn = StyledButton("Undo Last", bg_color=Colors.ACCENT)
        undo_last_btn.clicked.connect(lambda: self.undo_last_requested.emit())
        action_frame.add_widget(undo_last_btn)

        undo_history_btn = StyledButton("Undo History", bg_color=Colors.ACCENT)
        undo_history_btn.clicked.connect(lambda: self.undo_history_requested.emit())
        action_frame.add_widget(undo_history_btn)

        clear_btn = DangerButton("Clear Log")
        clear_btn.clicked.connect(lambda: self.clear_log_clicked.emit())
        action_frame.add_widget(clear_btn)

        export_btn = StyledButton("Export Log", bg_color=Colors.ACCENT)
        export_btn.clicked.connect(lambda: self.export_log_clicked.emit())
        action_frame.add_widget(export_btn)

        action_frame.add_stretch()

        # Close button (right side)
        close_btn = StyledButton("Close", bg_color=Colors.BORDER_LIGHT)
        close_btn.clicked.connect(self._on_close)
        action_frame.add_widget(close_btn)

        button_frame.add_widget(action_frame)

        main_layout.addWidget(button_frame)

        # Refresh log display
        self._refresh_log_display()

    def _refresh_log_display(self) -> None:
        """Refresh log text display."""
        # Format log entries as text
        if not self.filtered_entries:
            log_text = "(No entries)"
        else:
            lines = []
            for entry in self.filtered_entries:
                # Handle both string and dict entries
                if isinstance(entry, dict):
                    timestamp = entry.get("timestamp", "")
                    action = entry.get("action", "")
                    details = entry.get("details", "")

                    line = f"[{timestamp}] {action}"
                    if details:
                        line += f"\n  {details}"
                    lines.append(line)
                elif isinstance(entry, str):
                    # Entry is already a formatted string
                    lines.append(entry)
                else:
                    # Fallback for unknown types
                    lines.append(str(entry))

            log_text = "\n".join(lines)

        self.log_text.setPlainText(log_text)

        # Scroll to end
        self.log_text.moveCursor(self.log_text.textCursor().__class__.End)

        # Update entry count
        self.entry_count_label.setText(
            f"({len(self.filtered_entries)}/{len(self.log_entries)} entries)"
        )

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        search_text = text.lower().strip()

        # Emit signal for backend to handle search
        self.search_requested.emit(text)

        if not search_text:
            self.filtered_entries = self.log_entries.copy()
        else:
            # Filter entries by searching in both dict and string entries
            filtered = []
            for entry in self.log_entries:
                if isinstance(entry, dict):
                    # Dict entry: search in action and details
                    if (search_text in entry.get("action", "").lower() or
                        search_text in entry.get("details", "").lower()):
                        filtered.append(entry)
                elif isinstance(entry, str):
                    # String entry: search in the full string
                    if search_text in entry.lower():
                        filtered.append(entry)
            self.filtered_entries = filtered

        self._refresh_log_display()

    def _on_auto_refresh(self) -> None:
        """Auto-refresh log display."""
        # This would be called periodically to pull new entries from backend
        # For now, just maintain the display
        pass

    def _on_clear_log(self) -> None:
        """Clear the activity log."""
        if not show_confirmation_dialog(
            self,
            "Clear Log",
            "Are you sure you want to clear the activity log?",
        ):
            return

        self.log_entries.clear()
        self.filtered_entries.clear()
        self.search_entry.clear()
        self._refresh_log_display()

    def _on_export_log(self) -> None:
        """Export log to file."""
        file_path = save_file_dialog(
            self,
            title="Save Activity Log",
            default_name="activity_log.txt",
            file_filter="Text files (*.txt);;JSON files (*.json);;All files (*.*)",
        )

        if not file_path:
            return

        try:
            # Get current log text
            log_text = self.log_text.toPlainText()

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(log_text)

            show_info_dialog(
                self,
                "Export Successful",
                f"Activity log exported to:\n{file_path}",
            )
        except Exception as e:
            show_error_dialog(
                self,
                "Export Failed",
                f"Failed to export activity log:\n{str(e)}",
            )

    def _on_close(self) -> None:
        """Handle close button."""
        self.refresh_timer.stop()
        self.closed.emit()
        self.accept()

    def closeEvent(self, event) -> None:
        """Handle window close."""
        self.refresh_timer.stop()
        self.closed.emit()
        self.accept()
        event.accept()

    # ========== PUBLIC METHODS FOR BACKEND INTEGRATION ==========

    def set_log_entries(self, entries: list) -> None:
        """
        Set log entries.

        Args:
            entries: List of log entry dictionaries
        """
        self.log_entries = entries
        self.filtered_entries = entries.copy()
        self._refresh_log_display()

    def add_log_entry(self, timestamp: str, action: str, details: str = "") -> None:
        """
        Add a log entry.

        Args:
            timestamp: Entry timestamp
            action: Action description
            details: Optional details
        """
        entry = {
            "timestamp": timestamp,
            "action": action,
            "details": details,
        }
        self.log_entries.append(entry)

        # Apply search filter if active
        search_text = self.search_entry.text().lower().strip()
        if not search_text or search_text in action.lower() or search_text in details.lower():
            self.filtered_entries.append(entry)

        self._refresh_log_display()

    def clear_log(self) -> None:
        """Clear all log entries."""
        self.log_entries.clear()
        self.filtered_entries.clear()
        self._refresh_log_display()

    def get_log_entries(self) -> list:
        """Get all log entries."""
        return self.log_entries
