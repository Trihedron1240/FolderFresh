"""
PySide6 application orchestrator for FolderFresh.
Manages main window, dialogs, state, and backend integration.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QTimer, Slot

from .main_window import MainWindow
from .rule_manager import RuleManager
from .activity_log_window import ActivityLogWindow
from .category_manager import CategoryManagerWindow
from .profile_manager import ProfileManagerWindow
from .help_window import HelpWindow
from .watched_folders_window import WatchedFoldersWindow
from .styles import Colors, Fonts
from .dialogs import (
    browse_folder_dialog,
    show_confirmation_dialog,
    show_info_dialog,
    show_warning_dialog,
    show_error_dialog,
)


class FolderFreshApplication:
    """
    Main application orchestrator.
    Manages UI windows, state, and backend integration.
    """

    def __init__(self, qt_app: QApplication):
        """
        Initialize application.

        Args:
            qt_app: QApplication instance
        """
        self.qt_app = qt_app
        self.main_window: Optional[MainWindow] = None
        self.active_windows: Dict[str, Any] = {}

        # Backend references (will be set by launcher)
        self.watcher_manager = None
        self.profile_store = None
        self.rule_engine = None

        # Application state
        self.selected_folder: Optional[Path] = None
        self.active_profile_id: Optional[str] = None
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.rules: List[Dict[str, Any]] = []
        self.log_entries: List[Dict[str, Any]] = []

        self._setup_main_window()
        self._connect_signals()

    def _setup_main_window(self) -> None:
        """Setup and display main window."""
        self.main_window = MainWindow()
        self._connect_main_window_signals()

    def _connect_main_window_signals(self) -> None:
        """Connect main window signals to application slots."""
        # Folder selection
        self.main_window.folder_chosen.connect(self._on_folder_chosen)

        # Actions
        self.main_window.preview_requested.connect(self._on_preview_requested)
        self.main_window.organise_requested.connect(self._on_organise_requested)
        self.main_window.undo_requested.connect(self._on_undo_requested)
        self.main_window.duplicates_requested.connect(self._on_duplicates_requested)
        self.main_window.desktop_clean_requested.connect(self._on_desktop_clean_requested)

        # Managers
        self.main_window.profiles_requested.connect(self._on_profiles_requested)
        self.main_window.watched_folders_requested.connect(self._on_watched_folders_requested)
        self.main_window.help_requested.connect(self._on_help_requested)

    def _connect_signals(self) -> None:
        """Setup additional signal connections."""
        pass

    # ========== FOLDER SELECTION ==========

    @Slot(Path)
    def _on_folder_chosen(self, folder_path: Optional[Path]) -> None:
        """
        Handle folder selection.

        Args:
            folder_path: Selected folder path (None to open dialog)
        """
        if folder_path is None:
            # Open folder browser
            folder_path = browse_folder_dialog(
                self.main_window,
                title="Select Folder to Organize",
            )

        if folder_path:
            self.selected_folder = folder_path
            self.main_window.set_selected_folder(folder_path)
            self.main_window.enable_action_buttons(True)

            # Update preview automatically
            self._on_preview_requested()

    # ========== PREVIEW & ORGANIZATION ==========

    @Slot()
    def _on_preview_requested(self) -> None:
        """Generate and display preview of file operations."""
        if not self.selected_folder:
            show_warning_dialog(
                self.main_window,
                "Preview",
                "Please select a folder first.",
            )
            return

        # Generate preview (integrate with backend)
        preview_text = self._generate_preview()
        self.main_window.set_preview_text(preview_text)

    def _generate_preview(self) -> str:
        """
        Generate preview text for current folder.

        Returns:
            Preview text
        """
        if not self.selected_folder or not self.selected_folder.exists():
            return "Folder not found or not accessible."

        # Placeholder: In real integration, this would call rule_engine.preview()
        try:
            files = list(self.selected_folder.iterdir())
            preview_lines = [
                f"Preview for: {self.selected_folder}",
                f"Files found: {len(files)}",
                "",
                "Sample files:",
            ]

            for file_path in files[:10]:
                if file_path.is_file():
                    preview_lines.append(f"  • {file_path.name}")

            if len(files) > 10:
                preview_lines.append(f"  ... and {len(files) - 10} more")

            return "\n".join(preview_lines)
        except Exception as e:
            return f"Error generating preview: {str(e)}"

    @Slot()
    def _on_organise_requested(self) -> None:
        """Execute organization on selected folder."""
        if not self.selected_folder:
            show_warning_dialog(
                self.main_window,
                "Organize Files",
                "Please select a folder first.",
            )
            return

        if not show_confirmation_dialog(
            self.main_window,
            "Organize Files",
            f"Organize files in:\n{self.selected_folder}\n\nContinue?",
        ):
            return

        # Placeholder: In real integration, this would execute rules
        show_info_dialog(
            self.main_window,
            "Organization Complete",
            "Files have been organized. (Backend integration pending)",
        )

    @Slot()
    def _on_undo_requested(self) -> None:
        """Undo last operation."""
        # Placeholder: Would integrate with undo_manager
        show_info_dialog(
            self.main_window,
            "Undo",
            "Undo operation completed. (Backend integration pending)",
        )

    @Slot()
    def _on_duplicates_requested(self) -> None:
        """Find duplicate files."""
        show_info_dialog(
            self.main_window,
            "Find Duplicates",
            "Duplicate finder opened. (Backend integration pending)",
        )

    @Slot()
    def _on_desktop_clean_requested(self) -> None:
        """Clean desktop folder."""
        if not show_confirmation_dialog(
            self.main_window,
            "Clean Desktop",
            "This will organize files on your desktop. Continue?",
        ):
            return

        show_info_dialog(
            self.main_window,
            "Desktop Cleaned",
            "Desktop has been organized. (Backend integration pending)",
        )

    # ========== MANAGER WINDOWS ==========

    @Slot()
    def _on_profiles_requested(self) -> None:
        """Open profiles manager window."""
        if "profiles" not in self.active_windows or not self.active_windows["profiles"].isVisible():
            profiles_window = ProfileManagerWindow(
                parent=self.main_window,
                profiles=list(self.profiles.values()),
                active_profile_id=self.active_profile_id,
            )

            # Connect signals
            profiles_window.profile_selected.connect(self._on_profile_selected)
            profiles_window.profile_created.connect(self._on_profile_created)
            profiles_window.active_profile_changed.connect(self._on_active_profile_changed)
            profiles_window.closed.connect(lambda: self._on_window_closed("profiles"))

            self.active_windows["profiles"] = profiles_window
            profiles_window.show()

    @Slot(str)
    def _on_profile_selected(self, profile_id: str) -> None:
        """Handle profile selection."""
        self.active_profile_id = profile_id
        # Load profile rules
        if profile_id in self.profiles:
            self.rules = self.profiles[profile_id].get("rules", [])

    @Slot(str)
    def _on_profile_created(self, profile_id: str) -> None:
        """Handle new profile creation."""
        show_info_dialog(
            self.main_window,
            "Profile Created",
            f"New profile created. ID: {profile_id}",
        )

    @Slot(str)
    def _on_active_profile_changed(self, profile_id: str) -> None:
        """Handle active profile change."""
        self.active_profile_id = profile_id
        show_info_dialog(
            self.main_window,
            "Active Profile Changed",
            f"Active profile is now: {self.profiles.get(profile_id, {}).get('name', 'Unknown')}",
        )

    @Slot()
    def _on_watched_folders_requested(self) -> None:
        """Open watched folders manager."""
        if "watched" not in self.active_windows or not self.active_windows["watched"].isVisible():
            watched_window = WatchedFoldersWindow(parent=self.main_window)

            watched_window.closed.connect(lambda: self._on_window_closed("watched"))

            self.active_windows["watched"] = watched_window
            watched_window.show()

    @Slot()
    def _on_help_requested(self) -> None:
        """Open help window."""
        if "help" not in self.active_windows or not self.active_windows["help"].isVisible():
            help_window = HelpWindow(parent=self.main_window)

            help_window.view_log_clicked.connect(self._on_view_activity_log)
            help_window.report_bug_clicked.connect(self._on_report_bug)
            help_window.closed.connect(lambda: self._on_window_closed("help"))

            self.active_windows["help"] = help_window
            help_window.show()

    @Slot()
    def _on_view_activity_log(self) -> None:
        """Open activity log window."""
        if "activity_log" not in self.active_windows or not self.active_windows["activity_log"].isVisible():
            log_window = ActivityLogWindow(
                parent=self.main_window,
                log_entries=self.log_entries,
            )

            log_window.closed.connect(lambda: self._on_window_closed("activity_log"))

            self.active_windows["activity_log"] = log_window
            log_window.show()

    @Slot()
    def _on_report_bug(self) -> None:
        """Handle bug report."""
        import webbrowser
        webbrowser.open("https://github.com/Trihedron1240/FolderFresh/issues")

    def _on_window_closed(self, window_key: str) -> None:
        """Handle window close."""
        if window_key in self.active_windows:
            del self.active_windows[window_key]

    # ========== PUBLIC API ==========

    def show_main_window(self) -> None:
        """Show and focus main window."""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def hide_main_window(self) -> None:
        """Hide main window."""
        if self.main_window:
            self.main_window.hide()

    def close_all_windows(self) -> None:
        """Close all windows gracefully."""
        # Close any open dialogs
        for window in list(self.active_windows.values()):
            try:
                window.close()
            except Exception:
                pass

        # Close main window
        if self.main_window:
            try:
                self.main_window.close()
            except Exception:
                pass

    def set_profiles(self, profiles: List[Dict[str, Any]]) -> None:
        """
        Set profiles from backend.

        Args:
            profiles: List of profile dictionaries
        """
        self.profiles = {p["id"]: p for p in profiles}
        if profiles and not self.active_profile_id:
            self.active_profile_id = profiles[0]["id"]

    def set_log_entries(self, entries: List[Dict[str, Any]]) -> None:
        """
        Set activity log entries.

        Args:
            entries: List of log entries
        """
        self.log_entries = entries

    def add_log_entry(self, timestamp: str, action: str, details: str = "") -> None:
        """
        Add activity log entry.

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

        # Update activity log if visible
        if "activity_log" in self.active_windows:
            log_window = self.active_windows["activity_log"]
            if log_window.isVisible():
                log_window.add_log_entry(timestamp, action, details)

    def update_status(self, message: str, progress: float = None) -> None:
        """
        Update status bar.

        Args:
            message: Status message
            progress: Optional progress value (0.0-1.0)
        """
        if self.main_window:
            self.main_window.set_status(message)
            if progress is not None:
                self.main_window.set_progress(progress)
