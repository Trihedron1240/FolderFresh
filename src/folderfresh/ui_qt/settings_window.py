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
from folderfresh.profile_store import ProfileStore


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
            initial_settings: Initial settings dict (deprecated, reads from profiles.json instead)
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(400, 200, 500, 400)
        self.setMinimumSize(400, 300)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        # Initialize profile store for loading settings on show
        self.profile_store = ProfileStore()
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

        # Rule fallback checkbox (will be updated from disk in showEvent)
        self.rule_fallback_check = StyledCheckBox(
            "Fall back to category sort on rule failure",
            checked=self._load_initial_state()
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
        """Update settings dict and save directly to disk."""
        current_settings = {
            "rule_fallback_to_sort": self.rule_fallback_check.isChecked()
        }

        # Save directly to disk
        try:
            doc = self.profile_store.load()
            active_profile = self.profile_store.get_active_profile(doc)
            if active_profile:
                if "settings" not in active_profile:
                    active_profile["settings"] = {}
                active_profile["settings"]["rule_fallback_to_sort"] = current_settings["rule_fallback_to_sort"]
                self.profile_store.save(doc)
        except Exception as e:
            print(f"Error saving settings to disk: {e}")

        # Emit signal for listeners
        self.settings_changed.emit(current_settings)

    def _on_close(self) -> None:
        """Handle close button."""
        self.closed.emit()
        self.accept()

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.closed.emit()
        self.accept()
        event.accept()

    def showEvent(self, event) -> None:
        """Handle window show event - refresh from disk."""
        super().showEvent(event)
        self._refresh_from_disk()

    def _refresh_from_disk(self) -> None:
        """Reload settings from active profile in profiles.json."""
        doc = self.profile_store.load()
        active_profile = self.profile_store.get_active_profile(doc)
        if active_profile:
            # Read directly from disk, don't cache in self.settings
            disk_settings = active_profile.get("settings", {})
            # Update UI to reflect fresh data without triggering signals
            self.rule_fallback_check.blockSignals(True)
            self.rule_fallback_check.setChecked(
                disk_settings.get("rule_fallback_to_sort", True)
            )
            self.rule_fallback_check.blockSignals(False)

    def get_settings(self) -> dict:
        """Get current settings - always read from checkbox, not memory."""
        return {
            "rule_fallback_to_sort": self.rule_fallback_check.isChecked()
        }

    def set_settings(self, settings: dict) -> None:
        """Set settings from external source (e.g., ProfileManager)."""
        # Block signals to prevent triggering _on_settings_changed
        self.rule_fallback_check.blockSignals(True)
        self.rule_fallback_check.setChecked(
            settings.get("rule_fallback_to_sort", True)
        )
        self.rule_fallback_check.blockSignals(False)

    def _load_initial_state(self) -> bool:
        """Load initial checkbox state from profiles.json."""
        doc = self.profile_store.load()
        active_profile = self.profile_store.get_active_profile(doc)
        if active_profile:
            return active_profile.get("settings", {}).get("rule_fallback_to_sort", True)
        return True