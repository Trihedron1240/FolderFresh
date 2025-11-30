"""
PySide6 duplicate finder window for FolderFresh.
Find and manage duplicate files.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
)
from PySide6.QtCore import Qt, Signal, QTimer

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    DangerButton,
    StyledLineEdit,
    HeadingLabel,
    MutedLabel,
    StyledLabel,
    VerticalFrame,
    HorizontalFrame,
    CardFrame,
    ScrollableFrame,
)
from .dialogs import (
    show_confirmation_dialog,
    show_info_dialog,
    show_error_dialog,
)


class DuplicateFinderWindow(QDialog):
    """Dialog for finding and managing duplicate files."""

    # Signals
    closed = Signal()

    def __init__(self, parent=None, duplicate_groups: List[List[Path]] = None):
        """
        Initialize duplicate finder window.

        Args:
            parent: Parent widget
            duplicate_groups: List of duplicate file groups (each group is a list of Paths)
        """
        super().__init__(parent)
        self.setWindowTitle("Find Duplicates")
        self.setGeometry(200, 100, 1000, 700)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.duplicate_groups = duplicate_groups or []
        self.selected_file_path: Optional[Path] = None

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header with title and count
        header_frame = HorizontalFrame(spacing=12)

        title = HeadingLabel("Find Duplicates")
        header_frame.add_widget(title)

        if self.duplicate_groups:
            total_dupes = sum(len(group) for group in self.duplicate_groups) - len(
                self.duplicate_groups
            )
            info_text = f"({len(self.duplicate_groups)} groups, {total_dupes} duplicate files)"
        else:
            info_text = "(No duplicates found)"

        info_label = MutedLabel(info_text)
        header_frame.add_widget(info_label)

        header_frame.add_stretch()

        main_layout.addWidget(header_frame)

        # Duplicate groups display
        if self.duplicate_groups:
            self.groups_scroll = ScrollableFrame(spacing=12)

            for group_idx, group in enumerate(self.duplicate_groups):
                group_frame = self._create_group_frame(group_idx, group)
                self.groups_scroll.add_widget(group_frame)

            self.groups_scroll.add_stretch()
            main_layout.addWidget(self.groups_scroll, 1)
        else:
            no_dupes_label = StyledLabel(
                "No duplicate files found in selected folder.",
                font_size=Fonts.SIZE_NORMAL,
            )
            no_dupes_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(no_dupes_label, 1)

        # Bottom buttons
        bottom_buttons = HorizontalFrame(spacing=8)
        bottom_buttons.add_stretch()

        close_btn = StyledButton("Close", bg_color=Colors.BORDER_LIGHT)
        close_btn.clicked.connect(self._on_close)
        bottom_buttons.add_widget(close_btn)

        main_layout.addWidget(bottom_buttons)

    def _create_group_frame(self, group_idx: int, group: List[Path]) -> CardFrame:
        """
        Create a frame for a duplicate group.

        Args:
            group_idx: Index of the group
            group: List of duplicate file paths

        Returns:
            CardFrame containing group info and files
        """
        group_frame = CardFrame()
        group_layout = QVBoxLayout(group_frame)
        group_layout.setContentsMargins(12, 12, 12, 12)
        group_layout.setSpacing(8)

        # Group header
        header = HorizontalFrame(spacing=8)

        header_label = StyledLabel(
            f"Duplicate Group {group_idx + 1} ({len(group)} files)",
            font_size=Fonts.SIZE_NORMAL,
            bold=True,
        )
        header.add_widget(header_label)

        if group and group[0]:
            file_size = group[0].stat().st_size
            size_kb = file_size / 1024
            size_mb = size_kb / 1024
            if size_mb >= 1:
                size_str = f"{size_mb:.2f} MB"
            else:
                size_str = f"{size_kb:.2f} KB"
            size_label = MutedLabel(size_str)
            header.add_widget(size_label)

        header.add_stretch()

        group_layout.addWidget(header)

        # File list in group
        for file_path in group:
            file_frame = HorizontalFrame(spacing=8)
            file_frame.setStyleSheet(
                f"background-color: {Colors.CARD_BG}; border-radius: 6px; padding: 8px; border: 1px solid {Colors.BORDER};"
            )

            # File path label
            file_label = StyledLabel(
                str(file_path),
                font_size=Fonts.SIZE_SMALL,
            )
            file_label.setWordWrap(True)
            file_frame.add_widget(file_label, 1)

            # Open button
            open_btn = StyledButton("Open", bg_color=Colors.ACCENT)
            open_btn.setMaximumWidth(80)
            open_btn.clicked.connect(lambda checked=False, fp=file_path: self._on_open_file(fp))
            file_frame.add_widget(open_btn)

            group_layout.addWidget(file_frame)

        group_frame.setLayout(group_layout)
        return group_frame

    def _on_open_file(self, file_path: Path) -> None:
        """Open file location in explorer."""
        try:
            import subprocess
            import sys

            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", str(file_path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", str(file_path)])
            else:
                subprocess.Popen(["xdg-open", str(file_path.parent)])
        except Exception as e:
            show_error_dialog(
                self, "Error", f"Could not open file location: {e}"
            )

    def _on_close(self) -> None:
        """Close the window."""
        self.closed.emit()
        self.close()

    def closeEvent(self, event) -> None:
        """Handle window close."""
        self.closed.emit()
        event.accept()

    def set_duplicates(self, duplicate_groups: List[List[Path]]) -> None:
        """
        Update duplicate groups display.

        Args:
            duplicate_groups: List of duplicate file groups
        """
        self.duplicate_groups = duplicate_groups
        # Rebuild the UI
        self._init_ui()
