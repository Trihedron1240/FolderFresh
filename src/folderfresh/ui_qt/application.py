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
from .main_window_backend import MainWindowBackend
from .profile_manager_backend import ProfileManagerBackend
from .rule_manager_backend import RuleManagerBackend
from .watched_folders_backend import WatchedFoldersBackend
from .activity_log_backend import ActivityLogBackend
from .category_manager_backend import CategoryManagerBackend
from folderfresh.logger_qt import log_error
from folderfresh.config import save_config


class FolderFreshApplication:
    """
    Main application orchestrator.
    Manages UI windows, state, and backend integration.
    """

    def __init__(self, qt_app: QApplication, config_data: Optional[Dict[str, Any]] = None):
        """
        Initialize application.

        Args:
            qt_app: QApplication instance
            config_data: Configuration dictionary (optional)
        """
        self.qt_app = qt_app
        self.main_window: Optional[MainWindow] = None
        self.active_windows: Dict[str, Any] = {}

        # Backend references (will be set by launcher)
        self.watcher_manager = None
        self.profile_store = None
        self.rule_engine = None
        self._config_data = config_data or {}

        # Backend modules (instantiate now)
        self.main_window_backend: Optional[MainWindowBackend] = None
        self.profile_manager_backend: Optional[ProfileManagerBackend] = None
        self.rule_manager_backend: Optional[RuleManagerBackend] = None
        self.watched_folders_backend: Optional[WatchedFoldersBackend] = None
        self.activity_log_backend: Optional[ActivityLogBackend] = None
        self.category_manager_backend: Optional[CategoryManagerBackend] = None

        # Application state
        self.selected_folder: Optional[Path] = None
        self.active_profile_id: Optional[str] = None
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.rules: List[Dict[str, Any]] = []
        self.log_entries: List[Dict[str, Any]] = []
        self._tray_mode_active = False  # Track if tray mode is currently active

        self._setup_main_window()
        self._initialize_backends()
        self._connect_signals()

    @property
    def config_data(self) -> Dict[str, Any]:
        """Public accessor for configuration data."""
        return self._config_data

    def _setup_main_window(self) -> None:
        """Setup and display main window."""
        self.main_window = MainWindow()
        self._connect_main_window_signals()

        # Restore last selected folder from config
        if self._config_data and self._config_data.get("last_folder"):
            try:
                last_folder = Path(self._config_data["last_folder"])
                if last_folder.exists():
                    self.selected_folder = last_folder
                    self.main_window.set_selected_folder(last_folder)
                    self.main_window.enable_action_buttons(True)
            except Exception:
                pass

    def _connect_main_window_signals(self) -> None:
        """Connect main window signals to application slots."""
        # Folder selection
        self.main_window.folder_chosen.connect(self._on_folder_chosen)
        self.main_window.folder_open_requested.connect(self._on_folder_open_requested)

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

        # Options/settings changes
        self.main_window.options_changed.connect(self._on_options_changed)

        # Sidebar signals
        if self.main_window.sidebar:
            self.main_window.sidebar.rules_clicked.connect(self._on_rules_requested)
            self.main_window.sidebar.preview_clicked.connect(self._on_preview_requested)
            self.main_window.sidebar.activity_log_clicked.connect(self._on_view_activity_log)
            self.main_window.sidebar.categories_clicked.connect(self._on_categories_requested)

    def _initialize_backends(self) -> None:
        """Initialize all backend modules."""
        try:
            self.main_window_backend = MainWindowBackend()
            self.profile_manager_backend = ProfileManagerBackend()
            self.rule_manager_backend = RuleManagerBackend()
            self.watched_folders_backend = WatchedFoldersBackend()
            self.activity_log_backend = ActivityLogBackend(auto_refresh=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            show_error_dialog(
                self.main_window,
                "Backend Initialization Error",
                f"Failed to initialize backends:\n{str(e)}"
            )

    def _get_config_with_profile_data(self) -> Dict[str, Any]:
        """
        Get config data merged with active profile's category data.

        This ensures that preview/organize operations use the correct
        custom_categories, category_overrides, and category_enabled
        from the active profile, not stale data from the old config file.

        Transforms profile-style category_overrides (with metadata) into
        the old-style custom_category_names (just name strings) for compatibility
        with the legacy naming.py resolve_category() function.

        Returns:
            Config dictionary with profile-specific category data merged in
        """
        # Start with current config
        merged_config = self._config_data.copy() if self._config_data else {}

        # Load profile data and merge category information
        try:
            if self.profile_store:
                profiles_doc = self.profile_store.load()
                active_id = profiles_doc.get("active_profile_id")

                # Find active profile and extract category data
                for profile in profiles_doc.get("profiles", []):
                    if profile.get("id") == active_id:
                        # Merge category data from profile
                        merged_config["custom_categories"] = profile.get("custom_categories", {})
                        merged_config["category_enabled"] = profile.get("category_enabled", {})

                        # Transform category_overrides format for legacy compatibility
                        # Profile format: {"cat_name": {"name": "Display Name", "extensions": [...]}}
                        # Legacy format: {"cat_name": "Display Name"}
                        category_overrides = profile.get("category_overrides", {})
                        custom_category_names = {}
                        for cat_name, override_data in category_overrides.items():
                            if isinstance(override_data, dict) and "name" in override_data:
                                custom_category_names[cat_name] = override_data["name"]
                            elif isinstance(override_data, str):
                                # Handle old-style string overrides
                                custom_category_names[cat_name] = override_data

                        merged_config["custom_category_names"] = custom_category_names
                        break
        except Exception as e:
            # If profile loading fails, just use the config as-is
            import traceback
            log_error(f"Failed to merge profile data into config: {e}")
            log_error(traceback.format_exc())

        return merged_config

    def _connect_signals(self) -> None:
        """Setup additional signal connections."""
        self._connect_main_window_backend_signals()
        self._connect_profile_manager_backend_signals()
        self._connect_rule_manager_backend_signals()
        self._connect_watched_folders_backend_signals()
        self._connect_activity_log_backend_signals()

    # ========== BACKEND SIGNAL CONNECTIONS ==========

    def _connect_main_window_backend_signals(self) -> None:
        """Connect MainWindowBackend signals to UI updates."""
        if self.main_window_backend:
            # Connect backend signal for undo state changes to update UI button
            self.main_window_backend.undo_state_changed.connect(
                self._on_undo_state_changed
            )

    def _connect_profile_manager_backend_signals(self) -> None:
        """Connect ProfileManagerBackend signals to UI updates."""
        if self.profile_manager_backend:
            # Connect profile signals to UI
            self.profile_manager_backend.profiles_reloaded.connect(
                self._on_profiles_reloaded
            )
            self.profile_manager_backend.profile_created.connect(
                self._on_profile_created_backend
            )
            self.profile_manager_backend.profile_updated.connect(
                self._on_profile_updated
            )
            self.profile_manager_backend.profile_deleted.connect(
                self._on_profile_deleted
            )
            self.profile_manager_backend.profile_activated.connect(
                self._on_profile_activated
            )

    def _connect_rule_manager_backend_signals(self) -> None:
        """Connect RuleManagerBackend signals to UI updates."""
        if self.rule_manager_backend:
            # Connect rule signals to UI
            self.rule_manager_backend.rules_reloaded.connect(
                self._on_rules_reloaded
            )
            self.rule_manager_backend.rule_created.connect(
                self._on_rule_created
            )
            self.rule_manager_backend.rule_updated.connect(
                self._on_rule_updated
            )
            self.rule_manager_backend.rule_deleted.connect(
                self._on_rule_deleted
            )
            self.rule_manager_backend.rule_tested.connect(
                self._on_rule_tested
            )

    def _connect_watched_folders_backend_signals(self) -> None:
        """Connect WatchedFoldersBackend signals to UI updates."""
        if self.watched_folders_backend:
            # Connect folder signals to UI
            self.watched_folders_backend.folders_reloaded.connect(
                self._on_folders_reloaded
            )
            self.watched_folders_backend.folder_added.connect(
                self._on_folder_added
            )
            self.watched_folders_backend.folder_removed.connect(
                self._on_folder_removed
            )
            self.watched_folders_backend.folder_profile_changed.connect(
                self._on_folder_profile_changed
            )

    def _connect_activity_log_backend_signals(self) -> None:
        """Connect ActivityLogBackend signals to UI updates."""
        if self.activity_log_backend:
            # Connect log signals to UI
            self.activity_log_backend.log_updated.connect(
                self._on_activity_log_updated
            )
            self.activity_log_backend.log_cleared.connect(
                self._on_activity_log_cleared
            )
            self.activity_log_backend.log_exported.connect(
                self._on_activity_log_exported
            )

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

            # Save folder path to config
            from folderfresh.config import save_config
            self._config_data["last_folder"] = str(folder_path)
            save_config(self._config_data)

            # Update preview automatically
            self._on_preview_requested()

    @Slot()
    def _on_folder_open_requested(self) -> None:
        """Open the selected folder in the system file explorer."""
        if not self.selected_folder:
            show_warning_dialog(
                self.main_window,
                "No Folder Selected",
                "Please select a folder first.",
            )
            return

        try:
            import subprocess
            import platform
            import os

            folder_path = str(self.selected_folder)

            if platform.system() == "Windows":
                # Windows: use explorer.exe
                os.startfile(folder_path)
            elif platform.system() == "Darwin":
                # macOS: use open command
                subprocess.run(["open", folder_path], check=True)
            else:
                # Linux: try xdg-open
                subprocess.run(["xdg-open", folder_path], check=True)

        except Exception as e:
            show_error_dialog(
                self.main_window,
                "Cannot Open Folder",
                f"Failed to open folder:\n{str(e)}",
            )

    @Slot()
    def _on_options_changed(self) -> None:
        """
        Handle options/settings changes (save mode, auto-watch, tray mode, etc).
        """
        from folderfresh.config import save_config
        from .tray import create_tray, hide_tray, update_tray_menu

        if not hasattr(self, '_config_data') or self._config_data is None:
            return

        # Collect current settings from UI
        options = self.main_window.get_options()

        # Update config
        self._config_data.update(options)
        save_config(self._config_data)

        # Handle tray mode toggle
        if "tray_mode" in options:
            tray_enabled = options["tray_mode"]

            if tray_enabled:
                # Try to enable tray mode
                try:
                    success = create_tray(
                        app_name="FolderFresh",
                        on_open=lambda icon, item=None: self.main_window.show(),
                        on_toggle_watch=lambda icon, item=None: self._on_toggle_auto_watch(),
                        on_exit=lambda icon, item=None: self._request_exit(),
                        auto_tidy_enabled=options.get("watch_mode", False),
                    )

                    if not success:
                        show_warning_dialog(
                            self.main_window,
                            "Tray Mode",
                            "Failed to enable tray mode. pystray may not be available on your system.",
                        )
                        # Revert checkbox
                        self.main_window.tray_mode_check.setChecked(False)
                        self._config_data["tray_mode"] = False
                        save_config(self._config_data)
                    else:
                        # Successfully enabled tray mode - update window state
                        self._tray_mode_active = True
                        self.main_window.set_tray_mode_enabled(True)
                except Exception as e:
                    show_error_dialog(
                        self.main_window,
                        "Tray Mode Error",
                        f"Failed to enable tray mode: {str(e)}",
                    )
                    self.main_window.tray_mode_check.setChecked(False)
                    self._config_data["tray_mode"] = False
                    save_config(self._config_data)
            else:
                # Disable tray mode
                try:
                    hide_tray()
                    self._tray_mode_active = False
                    self.main_window.set_tray_mode_enabled(False)
                except Exception:
                    pass

    def _on_toggle_auto_watch(self) -> None:
        """Toggle auto-watch from tray menu."""
        if hasattr(self.main_window, 'watch_mode_check'):
            current = self.main_window.watch_mode_check.isChecked()
            self.main_window.watch_mode_check.setChecked(not current)
            # This will trigger options_changed signal

    def _request_exit(self) -> None:
        """Request exit from tray menu - properly quit the application."""
        # Disable tray mode to allow main window to close
        if self._tray_mode_active:
            self._tray_mode_active = False
            if self.main_window:
                self.main_window.set_tray_mode_enabled(False)

        # Hide tray icon
        from .tray import hide_tray
        try:
            hide_tray()
        except Exception:
            pass

        # Close all windows and quit application
        self.close_all_windows()
        self.qt_app.quit()

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
        Generate preview text for current folder using backend.

        Returns:
            Preview text formatted for display
        """
        if not self.selected_folder or not self.selected_folder.exists():
            return "Folder not found or not accessible."

        try:
            # Get options from UI
            options = self.main_window.get_options()

            # Get config merged with profile data
            config_with_profile = self._get_config_with_profile_data()

            # Generate preview using backend
            if self.main_window_backend:
                moves = self.main_window_backend.generate_preview(
                    self.selected_folder,
                    config_with_profile,
                    include_subfolders=options.get("include_subfolders", True),
                    skip_hidden=options.get("skip_hidden", True),
                    smart_mode=options.get("smart_sorting", False)
                )

                # Format moves for display
                preview_lines = [
                    f"Preview for: {self.selected_folder}",
                    f"Total moves: {len(moves)}",
                    ""
                ]

                if moves:
                    preview_lines.append("File Operations:")
                    for i, move in enumerate(moves[:20], 1):  # Show first 20
                        try:
                            src_path = move.get("src", "Unknown")
                            src = Path(src_path).name if isinstance(src_path, str) else str(src_path)
                            dst = move.get("category", move.get("rule_name", "Unknown"))
                            mode = move.get("mode", "unknown")
                            preview_lines.append(f"{i}. {src} → {dst} ({mode})")
                        except Exception:
                            # Skip malformed moves
                            continue

                    if len(moves) > 20:
                        preview_lines.append(f"\n... and {len(moves) - 20} more moves")
                else:
                    preview_lines.append("No files to organize")

                return "\n".join(preview_lines)
            else:
                return "Backend not initialized"

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

        # Get current preview (or generate if needed)
        options = self.main_window.get_options()

        # Get config merged with profile data
        config_with_profile = self._get_config_with_profile_data()

        if self.main_window_backend:
            moves = self.main_window_backend.generate_preview(
                self.selected_folder,
                config_with_profile,
                include_subfolders=options.get("include_subfolders", True),
                skip_hidden=options.get("skip_hidden", True),
                smart_mode=options.get("smart_sorting", False)
            )
        else:
            show_error_dialog(
                self.main_window,
                "Organize Error",
                "Backend not initialized",
            )
            return

        if not moves:
            show_info_dialog(
                self.main_window,
                "No Files to Organize",
                "No files found that need organizing.",
            )
            return

        # Show confirmation with operation count
        if not show_confirmation_dialog(
            self.main_window,
            "Organize Files",
            f"Organize files in:\n{self.selected_folder}\n\nOperations: {len(moves)}\n\nContinue?",
        ):
            return

        # Execute organization
        results = self.main_window_backend.execute_organize(
            self.selected_folder,
            moves,
            config_with_profile,
            safe_mode=options.get("safe_mode", True),
            smart_mode=options.get("smart_sorting", False)
        )

        # Show summary
        success_count = sum(1 for r in results if not r.get("error"))
        total_count = len(results)

        message = f"Organization completed!\n\n"
        message += f"Successful: {success_count}/{total_count}"

        if success_count == total_count:
            show_info_dialog(
                self.main_window,
                "Organization Complete",
                message,
            )
        else:
            failed_count = total_count - success_count
            message += f"\nFailed: {failed_count}"
            show_warning_dialog(
                self.main_window,
                "Organization Complete (with errors)",
                message,
            )

        # Refresh preview
        self._on_preview_requested()

    @Slot()
    def _on_undo_requested(self) -> None:
        """Undo last operation."""
        if self.main_window_backend:
            if self.main_window_backend.perform_undo():
                show_info_dialog(
                    self.main_window,
                    "Undo",
                    "Undo operation completed successfully.",
                )
            else:
                show_warning_dialog(
                    self.main_window,
                    "Undo",
                    "No operations to undo.",
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
            # Load profiles from backend if not already loaded
            if self.profile_manager_backend and not self.profiles:
                profiles = self.profile_manager_backend.get_all_profiles()
                self.set_profiles(profiles)

            profiles_window = ProfileManagerWindow(
                parent=self.main_window,
                profiles=list(self.profiles.values()),
                active_profile_id=self.active_profile_id,
            )

            # Connect UI signals to backend
            if self.profile_manager_backend:
                profiles_window.profile_created.connect(
                    lambda name: self.profile_manager_backend.create_profile(name)
                )
                profiles_window.profile_deleted.connect(
                    lambda pid: self.profile_manager_backend.delete_profile(pid)
                )
                profiles_window.profile_renamed.connect(
                    lambda pid, name: self.profile_manager_backend.update_profile(pid, name=name)
                )
                profiles_window.profile_duplicated.connect(
                    lambda pid: self.profile_manager_backend.duplicate_profile(pid)
                )
                profiles_window.active_profile_changed.connect(
                    lambda pid: self.profile_manager_backend.set_active_profile(pid)
                )

            # Connect signal to handler
            profiles_window.profile_selected.connect(self._on_profile_selected)
            profiles_window.closed.connect(lambda: self._on_window_closed("profiles"))

            self.active_windows["profiles"] = profiles_window
            profiles_window.show()

    @Slot()
    def _on_categories_requested(self) -> None:
        """Open categories manager window for the active profile."""
        if "categories" not in self.active_windows or not self.active_windows["categories"].isVisible():
            # Get active profile info
            profile_name = "Active Profile"
            if self.active_profile_id and self.active_profile_id in self.profiles:
                profile_name = self.profiles[self.active_profile_id].get("name", "Active Profile")

            # Create backend for the active profile
            try:
                category_manager_backend = CategoryManagerBackend(self.active_profile_id)
            except Exception as e:
                show_error_dialog(
                    self.main_window,
                    "Category Manager Error",
                    f"Failed to initialize category manager:\n{str(e)}"
                )
                return

            # Create window with backend for proper data loading
            categories_window = CategoryManagerWindow(
                parent=self.main_window,
                backend=category_manager_backend,
                profile_id=self.active_profile_id,
                profile_name=profile_name
            )

            # Close handler
            categories_window.closed.connect(lambda: self._on_window_closed("categories"))

            self.active_windows["categories"] = categories_window
            categories_window.show()

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

            # Load initial data from backend
            if self.watched_folders_backend:
                folders = self.watched_folders_backend.get_watched_folders_with_status()
                profiles = self.watched_folders_backend.get_profiles_dict()
                watched_window.refresh_folders(folders, profiles)

                # Connect UI signals to backend
                watched_window.add_folder_clicked.connect(
                    lambda: self.watched_folders_backend.add_watched_folder()
                )
                watched_window.remove_folder_clicked.connect(
                    lambda path: self.watched_folders_backend.remove_watched_folder(path)
                )
                watched_window.profile_changed.connect(
                    lambda path, profile: self.watched_folders_backend.set_folder_profile(path, profile)
                )

                # Connect backend signals to update UI
                self.watched_folders_backend.folder_added.connect(
                    lambda path: watched_window.add_folder_to_list(path)
                )
                self.watched_folders_backend.folder_removed.connect(
                    lambda path: watched_window.remove_folder_from_list(path)
                )

            watched_window.closed.connect(lambda: self._on_window_closed("watched"))

            self.active_windows["watched"] = watched_window
            watched_window.show()

    @Slot()
    def _on_rules_requested(self) -> None:
        """Open rules manager window."""
        if "rules" not in self.active_windows or not self.active_windows["rules"].isVisible():
            # Load rules from backend if not already loaded
            if self.rule_manager_backend and not self.rules:
                rules = self.rule_manager_backend.get_all_rules()
                self.rules = rules

            rules_window = RuleManager(
                parent=self.main_window,
                rules=self.rules,
                active_profile_id=self.active_profile_id,
            )

            # Connect UI signals to backend
            if self.rule_manager_backend:
                rules_window.rule_created.connect(
                    lambda name, match_mode: self.rule_manager_backend.create_rule(name, match_mode)
                )
                rules_window.rule_deleted.connect(
                    lambda rid: self.rule_manager_backend.delete_rule(rid)
                )
                rules_window.rule_reordered.connect(
                    lambda rid, direction: self.rule_manager_backend.move_rule(rid, direction)
                )

            rules_window.closed.connect(lambda: self._on_window_closed("rules"))

            self.active_windows["rules"] = rules_window
            rules_window.show()

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

            # Connect UI signals to backend
            if self.activity_log_backend:
                log_window.clear_log_clicked.connect(
                    lambda: self.activity_log_backend.clear_log()
                )
                log_window.export_log_clicked.connect(
                    lambda: self.activity_log_backend.export_log()
                )
                log_window.search_requested.connect(
                    lambda query: self.activity_log_backend.search_log(query)
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

    # ========== BACKEND SIGNAL HANDLERS ==========

    @Slot(bool, str)
    def _on_undo_state_changed(self, enabled: bool, button_text: str) -> None:
        """Handle undo state changes from backend."""
        if self.main_window:
            self.main_window.set_undo_button_state(enabled, button_text)

    @Slot()
    def _on_profiles_reloaded(self) -> None:
        """Handle profiles reloaded from backend."""
        if self.profile_manager_backend:
            profiles = self.profile_manager_backend.get_all_profiles()
            self.set_profiles(profiles)
            if "profiles" in self.active_windows:
                self.active_windows["profiles"].refresh_profiles(profiles)

    @Slot(str)
    def _on_profile_created_backend(self, profile_id: str) -> None:
        """Handle profile created from backend."""
        if self.profile_manager_backend:
            profile = self.profile_manager_backend.get_profile_by_id(profile_id)
            if profile:
                self.profiles[profile_id] = profile
                show_info_dialog(
                    self.main_window,
                    "Profile Created",
                    f"Profile '{profile.get('name')}' created successfully.",
                )

    @Slot(str)
    def _on_profile_updated(self, profile_id: str) -> None:
        """Handle profile updated from backend."""
        if self.profile_manager_backend:
            profile = self.profile_manager_backend.get_profile_by_id(profile_id)
            if profile:
                self.profiles[profile_id] = profile
                if "profiles" in self.active_windows:
                    self.active_windows["profiles"].refresh_profiles(
                        list(self.profiles.values())
                    )

    @Slot(str)
    def _on_profile_deleted(self, profile_id: str) -> None:
        """Handle profile deleted from backend."""
        if profile_id in self.profiles:
            del self.profiles[profile_id]
        if "profiles" in self.active_windows:
            self.active_windows["profiles"].refresh_profiles(
                list(self.profiles.values())
            )

    @Slot(str)
    def _on_profile_activated(self, profile_id: str) -> None:
        """Handle profile activated from backend."""
        self.active_profile_id = profile_id
        if profile_id in self.profiles:
            profile_name = self.profiles[profile_id].get("name", "Unknown")
            self.main_window.set_status(f"Active Profile: {profile_name}")

    @Slot()
    def _on_rules_reloaded(self) -> None:
        """Handle rules reloaded from backend."""
        if self.rule_manager_backend:
            rules = self.rule_manager_backend.get_all_rules()
            self.rules = rules
            if "rules" in self.active_windows:
                self.active_windows["rules"].refresh_rules(rules)

    @Slot(str)
    def _on_rule_created(self, rule_id: str) -> None:
        """Handle rule created from backend."""
        if self.rule_manager_backend:
            rule = self.rule_manager_backend.get_rule_by_id(rule_id)
            if rule:
                self.rules.append(rule)
                show_info_dialog(
                    self.main_window,
                    "Rule Created",
                    f"Rule created successfully.",
                )

    @Slot(str)
    def _on_rule_updated(self, rule_id: str) -> None:
        """Handle rule updated from backend."""
        if self.rule_manager_backend:
            rule = self.rule_manager_backend.get_rule_by_id(rule_id)
            if rule:
                # Update rule in list
                for i, r in enumerate(self.rules):
                    if r.get("id") == rule_id:
                        self.rules[i] = rule
                        break

    @Slot(str)
    def _on_rule_deleted(self, rule_id: str) -> None:
        """Handle rule deleted from backend."""
        self.rules = [r for r in self.rules if r.get("id") != rule_id]
        if "rules" in self.active_windows:
            self.active_windows["rules"].refresh_rules(self.rules)

    @Slot(list)
    def _on_rule_tested(self, test_results: list) -> None:
        """Handle rule test results from backend."""
        if "rules" in self.active_windows:
            self.active_windows["rules"].show_test_results(test_results)

    @Slot()
    def _on_folders_reloaded(self) -> None:
        """Handle watched folders reloaded from backend."""
        if "watched" in self.active_windows:
            self.active_windows["watched"].refresh_folders()

    @Slot(str)
    def _on_folder_added(self, folder_path: str) -> None:
        """Handle folder added from backend."""
        if "watched" in self.active_windows:
            self.active_windows["watched"].add_folder_to_list(folder_path)

    @Slot(str)
    def _on_folder_removed(self, folder_path: str) -> None:
        """Handle folder removed from backend."""
        if "watched" in self.active_windows:
            self.active_windows["watched"].remove_folder_from_list(folder_path)

    @Slot(str, str)
    def _on_folder_profile_changed(self, folder_path: str, profile_name: str) -> None:
        """Handle folder profile changed from backend."""
        if "watched" in self.active_windows:
            self.active_windows["watched"].update_folder_profile(folder_path, profile_name)

    @Slot(list)
    def _on_activity_log_updated(self, entries: list) -> None:
        """Handle activity log updated from backend."""
        self.log_entries = entries
        if "activity_log" in self.active_windows:
            self.active_windows["activity_log"].refresh_log(entries)

    @Slot()
    def _on_activity_log_cleared(self) -> None:
        """Handle activity log cleared from backend."""
        self.log_entries = []
        if "activity_log" in self.active_windows:
            self.active_windows["activity_log"].clear_log()

    @Slot(str)
    def _on_activity_log_exported(self, file_path: str) -> None:
        """Handle activity log exported from backend."""
        show_info_dialog(
            self.main_window,
            "Export Complete",
            f"Activity log exported to:\n{file_path}",
        )
