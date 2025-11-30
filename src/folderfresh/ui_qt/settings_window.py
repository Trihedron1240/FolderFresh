"""
PySide6 settings window for FolderFresh.
Provides application-wide settings like rule fallback behavior.
"""

from typing import Callable, Optional
from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtCore import Qt, Signal

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    StyledCheckBox,
    HeadingLabel,
    VerticalFrame,
    HorizontalFrame,
    CardFrame,
)


class SettingsWindow(QDialog):
    """Dialog for application settings."""

    # Signals
    settings_changed = Signal(dict)  # Emits settings dict
    closed = Signal()

    def __init__(self, parent=None, initial_settings: dict = None):
        """
        Initialize settings window.

        Args:
            parent: Parent widget
            initial_settings: Initial settings dict
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(400, 200, 500, 400)
        self.setMinimumSize(400, 300)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.settings = initial_settings or {}
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("Settings")
        main_layout.addWidget(title)

        # Rule Behavior section
        rule_section = CardFrame()
        rule_layout = VerticalFrame(spacing=12)

        section_title = HeadingLabel("Rule Behavior")
        rule_layout.add_widget(section_title)

        # Rule fallback checkbox
        self.rule_fallback_check = StyledCheckBox(
            "Fall back to category sort on rule failure",
            checked=self.settings.get("rule_fallback_to_sort", True)
        )
        self.rule_fallback_check.stateChanged.connect(self._on_settings_changed)
        rule_layout.add_widget(self.rule_fallback_check)

        # Help text
        from .base_widgets import MutedLabel
        help_text = MutedLabel(
            "When enabled: If a rule matches but fails to execute,\n"
            "the file will be sorted by normal/smart categories.\n\n"
            "When disabled: Failed rules stop processing,\n"
            "and files remain unsorted."
        )
        help_text.setWordWrap(True)
        rule_layout.add_widget(help_text)

        rule_section.setLayout(rule_layout.layout)
        main_layout.addWidget(rule_section)

        # Dry Run section
        dry_run_section = CardFrame()
        dry_run_layout = VerticalFrame(spacing=12)

        dry_run_title = HeadingLabel("Preview Mode")
        dry_run_layout.add_widget(dry_run_title)

        # Dry run checkbox
        self.dry_run_check = StyledCheckBox(
            "Enable dry run (preview-only mode)",
            checked=self.settings.get("dry_run", True)
        )
        self.dry_run_check.stateChanged.connect(self._on_settings_changed)
        dry_run_layout.add_widget(self.dry_run_check)

        # Help text for dry run
        dry_run_help = MutedLabel(
            "When enabled: Organize operations preview changes without\n"
            "actually moving/copying files. Preview shows what would happen.\n\n"
            "When disabled: Files are actually moved/copied during organize."
        )
        dry_run_help.setWordWrap(True)
        dry_run_layout.add_widget(dry_run_help)

        dry_run_section.setLayout(dry_run_layout.layout)
        main_layout.addWidget(dry_run_section)

        # Spacer
        main_layout.addStretch()

        # Close button
        button_frame = HorizontalFrame(spacing=8)
        close_btn = StyledButton("Close", bg_color=Colors.SUCCESS)
        close_btn.clicked.connect(self._on_close)
        button_frame.add_widget(close_btn)
        button_frame.add_stretch()
        main_layout.addWidget(button_frame)

    def _on_settings_changed(self) -> None:
        """Handle settings change."""
        self._update_settings()

    def _update_settings(self) -> None:
        """Update settings dict and emit signal."""
        self.settings["rule_fallback_to_sort"] = self.rule_fallback_check.isChecked()
        self.settings["dry_run"] = self.dry_run_check.isChecked()
        self.settings_changed.emit(self.settings)

    def _on_close(self) -> None:
        """Handle close button."""
        self.closed.emit()
        self.accept()

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.closed.emit()
        self.accept()
        event.accept()

    def get_settings(self) -> dict:
        """Get current settings."""
        return self.settings

    def set_settings(self, settings: dict) -> None:
        """Set settings."""
        self.settings = settings
        self.rule_fallback_check.setChecked(
            self.settings.get("rule_fallback_to_sort", True)
        )
        self.dry_run_check.setChecked(
            self.settings.get("dry_run", True)
        )
