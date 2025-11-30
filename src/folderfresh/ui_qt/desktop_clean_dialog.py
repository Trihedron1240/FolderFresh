"""
PySide6 desktop clean dialog.
Safe desktop cleaning with preview, warnings, and protection features.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    DangerButton,
    HeadingLabel,
    MutedLabel,
    StyledLabel,
    VerticalFrame,
    HorizontalFrame,
    CardFrame,
    ScrollableFrame,
)
from .dialogs import show_warning_dialog, show_error_dialog


class DesktopCleanDialog(QDialog):
    """Dialog for safe desktop cleaning with preview and warnings."""

    # Signals
    clean_confirmed = Signal()  # User confirmed cleanup
    closed = Signal()

    def __init__(self, parent=None):
        """
        Initialize desktop clean dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Clean Desktop - Preview & Safety Check")
        self.setGeometry(300, 150, 700, 600)
        self.setMinimumSize(600, 500)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.desktop_path: Optional[Path] = None
        self.preview_data: List[Dict[str, Any]] = []
        self.warnings: List[str] = []
        self.important_files: List[str] = []

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("Clean Desktop - Safety Preview")
        main_layout.addWidget(title)

        # Info message
        info_label = MutedLabel(
            "Review the preview below. This will COPY files (Safe Mode) to preserve originals."
        )
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        # Warnings section (if any)
        self.warnings_frame = None
        self.important_files_frame = None
        self.preview_frame = None
        self.stats_frame = None

        scroll_layout.addSpacing(8)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setStyleSheet(f"QScrollArea {{ background-color: {Colors.PANEL_BG}; border: none; }}")
        main_layout.addWidget(scroll_area, 1)

        # Store layout for dynamic content
        self.scroll_layout = scroll_layout

        # Bottom buttons
        bottom_buttons = HorizontalFrame(spacing=8)
        bottom_buttons.add_stretch()

        cancel_btn = StyledButton("Cancel", bg_color=Colors.BORDER_LIGHT)
        cancel_btn.clicked.connect(self._on_cancel)
        bottom_buttons.add_widget(cancel_btn)

        self.confirm_btn = StyledButton(
            "Clean Desktop (Copy Mode)",
            bg_color=Colors.SUCCESS,
        )
        self.confirm_btn.clicked.connect(self._on_confirm)
        bottom_buttons.add_widget(self.confirm_btn)

        main_layout.addWidget(bottom_buttons)

    def set_data(
        self,
        desktop_path: Path,
        warnings: List[str],
        preview: List[Dict[str, Any]],
        important_files: List[str],
        file_count: int,
        folder_count: int,
    ) -> None:
        """
        Set preview data to display.

        Args:
            desktop_path: Path to desktop
            warnings: List of warning messages
            preview: Preview of categorization
            important_files: List of important files found
            file_count: Number of files on desktop
            folder_count: Number of folders on desktop
        """
        self.desktop_path = desktop_path
        self.warnings = warnings
        self.preview_data = preview
        self.important_files = important_files

        # Clear previous content
        while self.scroll_layout.count() > 0:
            widget = self.scroll_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        # Add statistics
        self._add_statistics(file_count, folder_count)

        # Add warnings if any
        if warnings:
            self._add_warnings_section(warnings)

        # Add important files warning if any
        if important_files:
            self._add_important_files_section(important_files)

        # Add preview
        self._add_preview_section(preview)

        # Add final safety note
        self._add_safety_note()

        self.scroll_layout.addStretch()

    def _add_statistics(self, file_count: int, folder_count: int) -> None:
        """Add statistics section."""
        stats_frame = CardFrame()
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(12, 12, 12, 12)
        stats_layout.setSpacing(8)

        title = StyledLabel("Desktop Statistics", font_size=Fonts.SIZE_NORMAL, bold=True)
        stats_layout.addWidget(title)

        stats_text = f"{file_count} files, {folder_count} folders on Desktop"
        stats_label = MutedLabel(stats_text)
        stats_layout.addWidget(stats_label)

        stats_frame.setLayout(stats_layout)
        self.scroll_layout.addWidget(stats_frame)

    def _add_warnings_section(self, warnings: List[str]) -> None:
        """Add warnings section."""
        warning_frame = CardFrame()
        warning_frame.setStyleSheet(
            f"background-color: {Colors.PANEL_ALT}; border-left: 4px solid {Colors.WARNING};"
        )
        warning_layout = QVBoxLayout(warning_frame)
        warning_layout.setContentsMargins(12, 12, 12, 12)
        warning_layout.setSpacing(8)

        title = StyledLabel(
            "Warnings",
            font_size=Fonts.SIZE_NORMAL,
            bold=True,
        )
        title.setStyleSheet(f"color: {Colors.WARNING};")
        warning_layout.addWidget(title)

        for warning in warnings:
            warning_label = MutedLabel(f"• {warning}")
            warning_label.setWordWrap(True)
            warning_layout.addWidget(warning_label)

        warning_frame.setLayout(warning_layout)
        self.scroll_layout.addWidget(warning_frame)

    def _add_important_files_section(self, important_files: List[str]) -> None:
        """Add important files warning section."""
        important_frame = CardFrame()
        important_frame.setStyleSheet(
            f"background-color: {Colors.PANEL_ALT}; border-left: 4px solid {Colors.DANGER};"
        )
        important_layout = QVBoxLayout(important_frame)
        important_layout.setContentsMargins(12, 12, 12, 12)
        important_layout.setSpacing(8)

        title = StyledLabel(
            "Important Files Detected",
            font_size=Fonts.SIZE_NORMAL,
            bold=True,
        )
        title.setStyleSheet(f"color: {Colors.DANGER};")
        important_layout.addWidget(title)

        info_label = MutedLabel(
            "These files will NOT be organized (protected):"
        )
        important_layout.addWidget(info_label)

        for filename in important_files:
            file_label = MutedLabel(f"  • {filename}")
            important_layout.addWidget(file_label)

        important_frame.setLayout(important_layout)
        self.scroll_layout.addWidget(important_frame)

    def _add_preview_section(self, preview: List[Dict[str, Any]]) -> None:
        """Add preview section."""
        if not preview:
            return

        preview_frame = CardFrame()
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        preview_layout.setSpacing(10)

        title = StyledLabel(
            "Preview: How Files Will Be Organized",
            font_size=Fonts.SIZE_NORMAL,
            bold=True,
        )
        preview_layout.addWidget(title)

        for category_info in preview:
            category_name = category_info['category']
            count = category_info['count']
            files = category_info.get('files', [])
            has_more = category_info.get('has_more', False)

            # Filter out important files from preview display
            non_protected_files = [f for f in files if f not in self.important_files]
            non_protected_count = sum(1 for f in (category_info.get('all_files', files)) if f not in self.important_files)

            # Only show category if there are non-protected files
            if non_protected_count == 0:
                continue

            # Category header - show actual count of files that will be organized
            category_label = StyledLabel(
                f"📁 {category_name} ({non_protected_count} files will be organized)",
                font_size=Fonts.SIZE_SMALL,
                bold=True,
            )
            preview_layout.addWidget(category_label)

            # File list (first 5 non-protected files)
            for filename in non_protected_files:
                file_label = MutedLabel(f"    • {filename}")
                file_label.setWordWrap(True)
                preview_layout.addWidget(file_label)

            # "More" indicator
            remaining_count = non_protected_count - len(non_protected_files)
            if remaining_count > 0:
                more_label = MutedLabel(f"    ... and {remaining_count} more files")
                preview_layout.addWidget(more_label)

            preview_layout.addSpacing(4)

        preview_frame.setLayout(preview_layout)
        self.scroll_layout.addWidget(preview_frame)

    def _add_safety_note(self) -> None:
        """Add final safety note."""
        note_frame = CardFrame()
        note_frame.setStyleSheet(
            f"background-color: {Colors.PANEL_ALT}; border-left: 4px solid {Colors.SUCCESS};"
        )
        note_layout = QVBoxLayout(note_frame)
        note_layout.setContentsMargins(12, 12, 12, 12)
        note_layout.setSpacing(8)

        title = StyledLabel("Safety Notes", font_size=Fonts.SIZE_SMALL, bold=True)
        title.setStyleSheet(f"color: {Colors.SUCCESS};")
        note_layout.addWidget(title)

        notes = [
            "Files will be COPIED (not moved) to preserve originals",
            "Shortcuts and executables are protected",
            "You can undo this operation from the Activity Log",
            "All changes are logged for your safety",
        ]

        for note in notes:
            note_label = MutedLabel(f"✓ {note}")
            note_label.setWordWrap(True)
            note_layout.addWidget(note_label)

        note_frame.setLayout(note_layout)
        self.scroll_layout.addWidget(note_frame)

    def _on_confirm(self) -> None:
        """Handle confirm button click."""
        self.clean_confirmed.emit()
        self.close()

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.close()

    def closeEvent(self, event) -> None:
        """Handle dialog close."""
        self.closed.emit()
        event.accept()
