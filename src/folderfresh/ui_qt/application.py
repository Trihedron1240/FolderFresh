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
from .duplicate_finder_window import DuplicateFinderWindow
from .desktop_clean_backend import DesktopCleanBackend
from .desktop_clean_dialog import DesktopCleanDialog
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
from .duplicate_finder_backend import DuplicateFinderBackend
from folderfresh.logger_qt import log_error, log_info
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

        # Restore checkbox options from config
        if self._config_data:
            try:
                # Map config keys to UI option keys
                options = {
                    "include_subfolders": self._config_data.get("include_sub", True),
                    "skip_hidden": self._config_data.get("skip_hidden", True),
                    "safe_mode": self._config_data.get("safe_mode", True),
                    "smart_sorting": self._config_data.get("smart_mode", False),
                    "auto_tidy": self._config_data.get("watch_mode", False),
                    "startup": self._config_data.get("startup", False),
                    "tray_mode": self._config_data.get("tray_mode", False),
                }
                self.main_window.set_options(options)
            except Exception as e:
                log_error(f"Failed to restore checkbox options: {e}")

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
            self.main_window.sidebar.activity_log_clicked.connect(self._on_view_activity_log)
            self.main_window.sidebar.categories_clicked.connect(self._on_categories_requested)
            self.main_window.sidebar.settings_clicked.connect(self._on_settings_requested)

    def _initialize_backends(self) -> None:
        """Initialize all backend modules."""
        try:
            self.main_window_backend = MainWindowBackend()
            self.profile_manager_backend = ProfileManagerBackend()
            self.rule_manager_backend = RuleManagerBackend()
            self.watched_folders_backend = WatchedFoldersBackend()
            self.activity_log_backend = ActivityLogBackend(auto_refresh=True)

            # Load active profile from storage at startup
            if self.profile_manager_backend:
                profiles = self.profile_manager_backend.get_all_profiles()
                self.set_profiles(profiles)

                # Load the stored active profile ID
                if self.profile_store:
                    profiles_doc = self.profile_store.load()
                    stored_active_id = profiles_doc.get("active_profile_id")
                    if stored_active_id and stored_active_id in self.profiles:
                        self.active_profile_id = stored_active_id
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
        Get config data merged with active profile's category data and settings.

        This ensures that preview/organize operations use the correct
        custom_categories, category_overrides, category_enabled,
        and settings (like rule_fallback_to_sort) from the active profile.

        Transforms profile-style category_overrides (with metadata) into
        the old-style custom_category_names (just name strings) for compatibility
        with the legacy naming.py resolve_category() function.

        Returns:
            Config dictionary with profile-specific category data and settings merged in
        """
        # Start with current config
        merged_config = self._config_data.copy() if self._config_data else {}

        # Load profile data and merge category information and settings
        try:
            if self.profile_store:
                profiles_doc = self.profile_store.load()
                active_id = profiles_doc.get("active_profile_id")

                # Find active profile and extract category data and settings
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

                        # Merge settings from profile
                        profile_settings = profile.get("settings", {})
                        for key, value in profile_settings.items():
                            merged_config[key] = value

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
        log_info("[OPTIONS_CHANGED] Signal fired!")
        from folderfresh.config import save_config
        from .tray import create_tray, hide_tray, update_tray_menu

        if not hasattr(self, '_config_data') or self._config_data is None:
            log_info("[OPTIONS_CHANGED] No _config_data, returning")
            return

        # Collect current settings from UI
        options = self.main_window.get_options()
        log_info(f"[OPTIONS_CHANGED] Tray active={self._tray_mode_active}, auto_tidy={options.get('auto_tidy')}")

        # Map UI option keys to config keys and update config
        config_updates = {
            "include_sub": options.get("include_subfolders"),
            "skip_hidden": options.get("skip_hidden"),
            "safe_mode": options.get("safe_mode"),
            "smart_mode": options.get("smart_sorting"),
            "watch_mode": options.get("auto_tidy"),
            "startup": options.get("startup"),
            "tray_mode": options.get("tray_mode"),
        }
        self._config_data.update(config_updates)
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
                        auto_tidy_enabled=options.get("auto_tidy", False),
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

        # Update tray menu if auto-tidy state changed (while tray is active)
        if "auto_tidy" in options and self._tray_mode_active:
            log_info(f"[TRAY_UPDATE] Updating menu: auto_tidy={options.get('auto_tidy')}")
            try:
                update_tray_menu(
                    on_open=lambda icon, item=None: self.main_window.show(),
                    on_toggle_watch=lambda icon, item=None: self._on_toggle_auto_watch(),
                    on_exit=lambda icon, item=None: self._request_exit(),
                    auto_tidy_enabled=options.get("auto_tidy", False),
                )
                log_info(f"[TRAY_UPDATE] Menu updated successfully")
            except Exception as e:
                log_error(f"[TRAY_UPDATE] Failed to update menu: {e}")

    def _on_toggle_auto_watch(self) -> None:
        """Toggle auto-watch from tray menu."""
        log_info("[TRAY] _on_toggle_auto_watch called!")
        # Use QTimer.singleShot to ensure this runs on the main thread
        # (tray callbacks run in a background thread)
        if hasattr(self.main_window, 'watch_mode_check'):
            def toggle():
                try:
                    current = self.main_window.watch_mode_check.isChecked()
                    new_state = not current
                    log_info(f"[TRAY] Toggling auto-tidy from {current} to {new_state}")
                    self.main_window.watch_mode_check.setChecked(new_state)
                    actual_state = self.main_window.watch_mode_check.isChecked()
                    log_info(f"[TRAY] After setChecked: checkbox state is now {actual_state}")

                    # Verify state changed, if not force the signal
                    if actual_state == current:
                        log_info(f"[TRAY] State didn't change! Was {current}, still {actual_state}. Forcing signal.")
                        self.main_window.options_changed.emit()
                except Exception as e:
                    log_error(f"[TRAY] Error toggling checkbox: {e}")
            QTimer.singleShot(0, toggle)
        else:
            log_info("[TRAY] watch_mode_check not found on main_window!")

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
                            mode = move.get("mode", "unknown")

                            # Check if this move has an error
                            if move.get("error"):
                                preview_lines.append(f"{i}. {src} - ERROR: {move.get('error')}")
                            else:
                                dst = move.get("category", move.get("rule_name", "Unknown"))
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

        # Sync updated sort mode back to main config
        from folderfresh.config import save_config
        self._config_data["last_sort_mode"] = config_with_profile.get("last_sort_mode")
        save_config(self._config_data)

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
            # Backend handles all dialog display, just call perform_undo
            self.main_window_backend.perform_undo()

    @Slot()
    def _on_duplicates_requested(self) -> None:
        """Find duplicate files."""
        if not self.selected_folder:
            show_warning_dialog(
                self.main_window,
                "No Folder Selected",
                "Please select a folder first.",
            )
            return

        # Get options from main window
        options = self.main_window.get_options()
        include_subfolders = options.get("include_subfolders", True)
        skip_hidden = options.get("skip_hidden", True)

        # Get ignore extensions from config
        ignore_exts = self._config_data.get("ignore_exts", "")
        ignore_extensions = [ext.strip().lower() for ext in ignore_exts.split(";") if ext.strip()]

        # Create backend if needed
        if not hasattr(self, "_duplicate_finder_backend"):
            self._duplicate_finder_backend = DuplicateFinderBackend()

        # Find duplicates (blocking call, but we skip the modal dialog)
        try:
            # Log the start
            log_info(f"Finding duplicates in: {self.selected_folder}")

            duplicate_groups = self._duplicate_finder_backend.find_duplicates(
                folder=self.selected_folder,
                include_subfolders=include_subfolders,
                skip_hidden=skip_hidden,
                ignore_extensions=ignore_extensions,
            )

            # Check if any duplicates found
            if not duplicate_groups:
                show_info_dialog(
                    self.main_window,
                    "No Duplicates Found",
                    f"No duplicate files found in:\n{self.selected_folder}",
                )
                return

            # Open duplicate finder window with results
            self._open_duplicate_finder_window(duplicate_groups)

        except Exception as e:
            log_error(f"Error finding duplicates: {e}")
            show_error_dialog(
                self.main_window,
                "Error",
                f"Failed to find duplicates: {e}",
            )

    def _open_duplicate_finder_window(self, duplicate_groups: List[List[Path]]) -> None:
        """
        Open duplicate finder window.

        Args:
            duplicate_groups: List of duplicate file groups
        """
        if "duplicates" not in self.active_windows or not self.active_windows["duplicates"].isVisible():
            window = DuplicateFinderWindow(self.main_window, duplicate_groups)
            window.closed.connect(lambda: self._on_duplicate_finder_closed())
            self.active_windows["duplicates"] = window

        self.active_windows["duplicates"].show()
        self.active_windows["duplicates"].raise_()
        self.active_windows["duplicates"].activateWindow()

    def _on_duplicate_finder_closed(self) -> None:
        """Handle duplicate finder window closed."""
        if "duplicates" in self.active_windows:
            del self.active_windows["duplicates"]

    @Slot()
    def _on_desktop_clean_requested(self) -> None:
        """Clean desktop folder with safety checks and preview."""
        # Create backend if needed
        if not hasattr(self, "_desktop_clean_backend"):
            self._desktop_clean_backend = DesktopCleanBackend()

        try:
            # Get desktop path
            desktop = self._desktop_clean_backend.get_desktop_path()
            if not desktop:
                show_error_dialog(
                    self.main_window,
                    "Desktop Error",
                    "Could not find your Desktop folder.",
                )
                return

            # Perform safety checks
            is_safe, warnings = self._desktop_clean_backend.check_desktop_safety(desktop)

            # If critical safety issues, warn user
            if warnings and not is_safe:
                show_error_dialog(
                    self.main_window,
                    "Desktop Safety Check Failed",
                    "\n".join(warnings),
                )
                return

            # Get file statistics
            protection_info = self._desktop_clean_backend.get_protection_info(desktop)
            file_count = protection_info.get("file_count", 0)
            folder_count = protection_info.get("folder_count", 0)

            # Generate preview
            preview, info_messages = self._desktop_clean_backend.generate_preview(
                desktop,
                self._config_data,
            )

            if file_count == 0:
                show_info_dialog(
                    self.main_window,
                    "Desktop Clean",
                    "Your Desktop is already clean! No files to organize.",
                )
                return

            # Open preview dialog
            self._open_desktop_clean_dialog(
                desktop,
                warnings,
                preview,
                protection_info.get("important_files", []),
                file_count,
                folder_count,
            )

        except Exception as e:
            log_error(f"Error in desktop clean: {e}")
            show_error_dialog(
                self.main_window,
                "Error",
                f"Failed to prepare desktop clean: {e}",
            )

    def _open_desktop_clean_dialog(
        self,
        desktop: Path,
        warnings: List[str],
        preview: List[Dict[str, Any]],
        important_files: List[str],
        file_count: int,
        folder_count: int,
    ) -> None:
        """
        Open desktop clean preview dialog.

        Args:
            desktop: Desktop path
            warnings: Warning messages
            preview: Preview of file organization
            important_files: List of important files to protect
            file_count: Number of files on desktop
            folder_count: Number of folders on desktop
        """
        dialog = DesktopCleanDialog(self.main_window)
        dialog.set_data(desktop, warnings, preview, important_files, file_count, folder_count)
        dialog.clean_confirmed.connect(lambda: self._execute_desktop_clean(desktop))
        dialog.closed.connect(lambda: self._on_desktop_clean_dialog_closed())
        dialog.show()

    def _execute_desktop_clean(self, desktop: Path) -> None:
        """
        Execute desktop cleaning.

        Args:
            desktop: Desktop path to clean
        """
        try:
            show_info_dialog(
                self.main_window,
                "Organizing Desktop",
                "Please wait while your Desktop is being organized...",
            )

            # Get options
            options = self.main_window.get_options()

            # Call the actual organization through main window backend
            if self.main_window_backend:
                # Generate preview first
                preview_result = self.main_window_backend.generate_preview(
                    desktop,
                    self._config_data,
                    include_subfolders=False,  # Never include subfolders on desktop
                    skip_hidden=options.get("skip_hidden", True),
                )

                if preview_result:
                    # Execute organization
                    self.main_window_backend.execute_organize(
                        preview_result,
                        safe_mode=options.get("safe_mode", True),  # Always safe mode for desktop
                        smart_mode=options.get("smart_sorting", False),
                    )

                    show_info_dialog(
                        self.main_window,
                        "Desktop Cleaned",
                        "Your Desktop has been organized successfully!\n\nFiles were copied to preserve originals.",
                    )
                else:
                    show_warning_dialog(
                        self.main_window,
                        "No Changes",
                        "No files found to organize.",
                    )
            else:
                show_warning_dialog(
                    self.main_window,
                    "Backend Not Ready",
                    "Organization backend is not ready. Please try again.",
                )

        except Exception as e:
            log_error(f"Error executing desktop clean: {e}")
            show_error_dialog(
                self.main_window,
                "Error",
                f"Failed to organize desktop: {e}",
            )

    def _on_desktop_clean_dialog_closed(self) -> None:
        """Handle desktop clean dialog closed."""
        # Dialog cleanup if needed
        pass

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
            # Check if we have an active profile
            if not self.active_profile_id:
                show_warning_dialog(
                    self.main_window,
                    "No Active Profile",
                    "Please create or select a profile first to manage categories."
                )
                return

            # Get active profile info
            profile_name = "Active Profile"
            if self.active_profile_id in self.profiles:
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

        # Close the rules window if open so it reloads with new profile's rules
        if "rules" in self.active_windows:
            self.active_windows["rules"].close()
            del self.active_windows["rules"]

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
            # Get profile name and ID
            profile_name = "Default"
            profile_id = self.active_profile_id

            if self.active_profile_id and self.active_profile_id in self.profiles:
                profile_name = self.profiles[self.active_profile_id].get("name", "Default")

            # Create rules window with profile_id for proper loading/saving
            rules_window = RuleManager(
                parent=self.main_window,
                profile_id=profile_id,
                profile_name=profile_name,
            )

            # Connect window closed signal
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

            # Connect undo signals to main window backend
            if self.main_window_backend:
                log_window.undo_last_requested.connect(
                    lambda: self.main_window_backend.perform_undo()
                )
                log_window.undo_history_requested.connect(
                    self._on_show_undo_history
                )

            log_window.closed.connect(lambda: self._on_window_closed("activity_log"))

            self.active_windows["activity_log"] = log_window
            log_window.show()

    def _on_settings_requested(self) -> None:
        """Open settings window."""
        from folderfresh.ui_qt.settings_window import SettingsWindow

        if "settings" not in self.active_windows or not self.active_windows["settings"].isVisible():
            # Get current settings from profile
            current_settings = {}
            if self.profile_store:
                doc = self.profile_store.load()
                active_profile = self.profile_store.get_active_profile(doc)
                if active_profile:
                    current_settings = active_profile.get("settings", {})

            settings_window = SettingsWindow(
                parent=self.main_window,
                initial_settings=current_settings,
            )

            # Connect settings changes to save
            settings_window.settings_changed.connect(self._on_settings_changed_in_window)
            settings_window.closed.connect(lambda: self._on_window_closed("settings"))

            self.active_windows["settings"] = settings_window
            settings_window.show()

    def _on_settings_changed_in_window(self, settings: dict) -> None:
        """Handle settings change from settings window."""
        if self.profile_store:
            doc = self.profile_store.load()
            active_profile = self.profile_store.get_active_profile(doc)
            if active_profile:
                # Update profile settings
                if "settings" not in active_profile:
                    active_profile["settings"] = {}
                for key, value in settings.items():
                    active_profile["settings"][key] = value
                # Save the updated profile
                self.profile_store.save(doc)

    def _on_show_undo_history(self) -> None:
        """Show undo history as a dialog."""
        try:
            if not self.main_window_backend:
                return

            from folderfresh.ui_qt.dialogs import show_info_dialog

            history = self.main_window_backend.get_undo_history()
            menu_items = self.main_window_backend.get_undo_menu_items(max_items=10)

            if not menu_items:
                show_info_dialog(
                    self.main_window,
                    "Undo History",
                    "No undo history available.\n\n"
                    "Undo history stores operations that can be reversed.\n"
                    "Once an action is undone, it is removed from the history.\n"
                    "For a complete activity log, see the Activity Log window."
                )
                return

            # Format history for display
            history_text = "Operations that can be undone (newest first):\n\n"
            for i, item in enumerate(menu_items, 1):
                history_text += f"{i}. {item}\n"

            history_text += "\n" + "="*50 + "\n"
            history_text += "Once you undo an operation, it will be removed from this list.\n"
            history_text += "For a complete activity log, see the Activity Log window."

            show_info_dialog(
                self.main_window,
                "Undo History",
                history_text
            )

        except Exception as e:
            log_error(f"Failed to show undo history: {e}")

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
            self.active_windows["activity_log"].set_log_entries(entries)

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
