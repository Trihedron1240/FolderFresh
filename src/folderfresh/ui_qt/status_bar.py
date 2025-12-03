"""
PySide6 status bar component for FolderFresh.
Progress bar, progress label, and status label display.
"""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QProgressBar,
    QLabel,
)
from PySide6.QtCore import Qt

from .styles import Colors, Fonts, get_label_stylesheet, get_progressbar_stylesheet
from .base_widgets import MutedLabel, CardFrame


class StatusBar(QWidget):
    """
    Status bar component with progress bar and status/progress labels.
    """

    def __init__(self, parent=None):
        """
        Initialize status bar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Progress bar (0-1 range, starts at 0)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setMaximumWidth(400)
        self.progress_bar.setMinimumHeight(16)
        self.progress_bar.setTextVisible(False)

        # Apply progress bar styling
        progressbar_stylesheet = get_progressbar_stylesheet(
            chunk_color=Colors.ACCENT,
            bg_color=Colors.PANEL_ALT,
        )
        self.progress_bar.setStyleSheet(progressbar_stylesheet)

        layout.addWidget(self.progress_bar)

        # Progress label (e.g., "0/50")
        self.progress_label = QLabel("0/0")
        self.progress_label.setMinimumWidth(60)
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet(
            get_label_stylesheet(
                text_color=Colors.MUTED,
                font_size=Fonts.SIZE_SMALL,
            )
        )

        layout.addWidget(self.progress_label)

        # Spacer
        layout.addSpacing(16)

        # Status label (e.g., "Ready", "Running...", "Complete!")
        self.status_label = QLabel("Ready ✨")
        self.status_label.setMinimumWidth(150)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label.setStyleSheet(
            get_label_stylesheet(
                text_color=Colors.TEXT,
                font_size=Fonts.SIZE_NORMAL,
            )
        )

        layout.addWidget(self.status_label)

        # Stretch to fill remaining space
        layout.addStretch()

        # Apply background styling
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {Colors.CARD_BG};
                border-top: 1px solid {Colors.BORDER};
            }}
        """
        )

    def set_status(self, text: str) -> None:
        """
        Update status label text.

        Args:
            text: Status text (e.g., "Ready", "Processing...")
        """
        self.status_label.setText(text)

    def set_progress(self, value: float) -> None:
        """
        Update progress bar value.

        Args:
            value: Progress value (0.0 to 1.0, or use set_progress_range for custom max)
        """
        # Convert 0-1 range to 0-100
        progress_value = int(value * 100)
        self.progress_bar.setValue(min(100, max(0, progress_value)))

    def set_progress_label(self, current: int, total: int) -> None:
        """
        Update progress label (e.g., "5/50").

        Args:
            current: Current progress count
            total: Total count
        """
        self.progress_label.setText(f"{current}/{total}")

    def set_progress_range(self, min_value: int, max_value: int) -> None:
        """
        Set custom progress bar range.

        Args:
            min_value: Minimum value
            max_value: Maximum value
        """
        self.progress_bar.setMinimum(min_value)
        self.progress_bar.setMaximum(max_value)

    def set_progress_value(self, value: int) -> None:
        """
        Set progress bar value directly (when using custom range).

        Args:
            value: Progress value in current range
        """
        self.progress_bar.setValue(value)

    def reset(self) -> None:
        """Reset status bar to initial state."""
        self.progress_bar.setValue(0)
        self.progress_label.setText("0/0")
        self.status_label.setText("Ready ✨")

    def show_busy(self, message: str = "Processing...") -> None:
        """Show busy state with message."""
        self.set_status(message)
        self.progress_bar.setMaximum(0)  # Indeterminate progress

    def show_complete(self, message: str = "Complete!") -> None:
        """Show complete state with message."""
        self.set_status(message)
        self.progress_bar.setValue(100)

    def show_error(self, message: str = "Error!") -> None:
        """Show error state with message."""
        self.set_status(message)
        self.status_label.setStyleSheet(
            get_label_stylesheet(
                text_color=Colors.DANGER,
                font_size=Fonts.SIZE_NORMAL,
            )
        )
