"""
Integration glue code for WatchedFoldersWindow and WatchedFoldersBackend.

This module provides the controller class that connects the UI to the backend,
handling all signal-slot connections and data synchronization.

Usage:
    In your main controller class, call:

    from integration_watched_folders import WatchedFoldersController

    self.wf_controller = WatchedFoldersController(self.watcher_manager)
    self.wf_controller.open_watched_folders_manager()
"""

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from folderfresh.ui_qt.watched_folders_window import WatchedFoldersWindow
from folderfresh.ui_qt.watched_folders_backend import WatchedFoldersBackend
from folderfresh.logger_qt import log_info, log_error


def normalize_path(p: str) -> str:
    """Normalize a path to absolute canonical form."""
    return str(Path(p).resolve())


class WatchedFoldersController:
    """
    Controller that integrates WatchedFoldersWindow UI with WatchedFoldersBackend.

    Handles all signal-slot connections:
    - UI events (add/remove/profile change) → Backend methods
    - Backend signals → UI updates
    - Path normalization throughout
    - Profile lookups and UI refresh
    """

    def __init__(self, watcher_manager=None, parent: Optional[QWidget] = None):
        """
        Initialize the controller.

        Args:
            watcher_manager: Reference to WatcherManager (required for watching to work)
            parent: Parent widget (optional)
        """
        self.watcher_manager = watcher_manager
        self.parent = parent

        # Will be created when opening manager
        self.backend: Optional[WatchedFoldersBackend] = None
        self.window: Optional[WatchedFoldersWindow] = None

    def open_watched_folders_manager(self) -> None:
        """
        Create and show the watched folders manager window.

        This method:
        1. Creates the backend and window instances
        2. Connects all signals in both directions
        3. Reloads and populates the UI with current data
        4. Shows the window modally
        """
        try:
            log_info("Opening watched folders manager...")

            # Create backend (loads config and profiles)
            self.backend = WatchedFoldersBackend(self.watcher_manager)

            # Create window
            self.window = WatchedFoldersWindow(self.parent)

            # Connect UI → Backend
            self._connect_ui_to_backend()

            # Connect Backend → UI
            self._connect_backend_to_ui()

            # Initial UI population
            self._reload_wf_ui()

            # Show window modally
            self.window.exec()

            log_info("Watched folders manager closed")

        except Exception as e:
            log_error(f"Failed to open watched folders manager: {e}", exc_info=True)

    def _connect_ui_to_backend(self) -> None:
        """
        Connect UI signals to backend methods.

        Maps:
        - window.add_folder_clicked → backend.add_watched_folder
        - window.remove_folder_clicked → backend.remove_watched_folder
        - window.profile_changed → backend.set_folder_profile
        """
        try:
            # Add folder: Show dialog and add
            self.window.add_folder_clicked.connect(
                lambda: self._on_add_folder_clicked()
            )

            # Remove folder: Remove from backend
            self.window.remove_folder_clicked.connect(
                lambda path: self._on_remove_folder_clicked(path)
            )

            # Profile changed: Update backend
            self.window.profile_changed.connect(
                lambda path, profile_id: self._on_profile_changed(path, profile_id)
            )

            log_info("UI → Backend connections established")

        except Exception as e:
            log_error(f"Failed to connect UI to backend: {e}", exc_info=True)

    def _connect_backend_to_ui(self) -> None:
        """
        Connect backend signals to UI update methods.

        Maps:
        - backend.folder_added → window.add_folder_to_list
        - backend.folder_removed → window.remove_folder_from_list
        - backend.folder_profile_changed → window.update_folder_profile
        - backend.folder_toggled → window.set_folder_active
        - backend.folder_resumed → window.set_folder_active (resumed = active)
        """
        try:
            # Folder added to backend → Update UI
            self.backend.folder_added.connect(
                lambda path: self._on_backend_folder_added(path)
            )

            # Folder removed from backend → Update UI
            self.backend.folder_removed.connect(
                lambda path: self._on_backend_folder_removed(path)
            )

            # Profile changed in backend → Update UI
            self.backend.folder_profile_changed.connect(
                lambda path, profile_name: self._on_backend_profile_changed(path, profile_name)
            )

            # Folder toggled (paused/resumed) in backend → Update UI
            self.backend.folder_toggled.connect(
                lambda path, is_active: self._on_backend_folder_toggled(path, is_active)
            )

            # Folder resumed (paused → watching) → Update UI
            self.backend.folder_resumed.connect(
                lambda path: self._on_backend_folder_resumed(path)
            )

            # Folders reloaded → Refresh UI
            self.backend.folders_reloaded.connect(
                lambda: self._reload_wf_ui()
            )

            log_info("Backend → UI connections established")

        except Exception as e:
            log_error(f"Failed to connect backend to UI: {e}", exc_info=True)

    # UI Event Handlers (UI → Backend)

    def _on_add_folder_clicked(self) -> None:
        """
        Handle add folder button click.
        Calls backend.add_watched_folder() which shows folder dialog.
        """
        try:
            if self.backend:
                # backend.add_watched_folder(None) shows a dialog
                self.backend.add_watched_folder()
        except Exception as e:
            log_error(f"Failed to add folder: {e}")

    def _on_remove_folder_clicked(self, folder_path: str) -> None:
        """
        Handle remove folder button click.

        Args:
            folder_path: Normalized path of folder to remove
        """
        try:
            # Normalize path
            normalized_path = normalize_path(folder_path)

            if self.backend:
                self.backend.remove_watched_folder(normalized_path)
        except Exception as e:
            log_error(f"Failed to remove folder: {e}")

    def _on_profile_changed(self, folder_path: str, profile_id: str) -> None:
        """
        Handle profile dropdown change for a folder.

        Args:
            folder_path: Normalized path of folder
            profile_id: Profile ID from dropdown.currentData()
        """
        try:
            # Normalize path
            normalized_path = normalize_path(folder_path)

            if self.backend:
                self.backend.set_folder_profile(normalized_path, profile_id)
        except Exception as e:
            log_error(f"Failed to change profile: {e}")

    # Backend Signal Handlers (Backend → UI)

    def _on_backend_folder_added(self, folder_path: str) -> None:
        """
        Handle folder added from backend.
        Refreshes UI to show the new folder.

        Args:
            folder_path: Path of newly added folder
        """
        try:
            if self.backend and self.window:
                # Reload entire UI to show the new folder
                self._reload_wf_ui()
        except Exception as e:
            log_error(f"Failed to handle folder added: {e}")

    def _on_backend_folder_removed(self, folder_path: str) -> None:
        """
        Handle folder removed from backend.
        Updates UI to remove the folder.

        Args:
            folder_path: Path of removed folder
        """
        try:
            if self.backend and self.window:
                normalized_path = normalize_path(folder_path)
                self.window.remove_folder_from_list(normalized_path)
        except Exception as e:
            log_error(f"Failed to handle folder removed: {e}")

    def _on_backend_profile_changed(self, folder_path: str, profile_name: str) -> None:
        """
        Handle profile changed from backend.
        Updates UI to show new profile for folder.

        Args:
            folder_path: Path of folder
            profile_name: New profile name
        """
        try:
            if self.backend and self.window:
                normalized_path = normalize_path(folder_path)

                # Get profile ID from name
                profile_id = self.backend._get_profile_id_by_name(profile_name)
                if profile_id:
                    self.window.update_folder_profile(normalized_path, profile_id)
        except Exception as e:
            log_error(f"Failed to handle profile changed: {e}")

    def _on_backend_folder_toggled(self, folder_path: str, is_active: bool) -> None:
        """
        Handle folder watch status toggled from backend.
        Updates UI to show paused/watching status.

        Args:
            folder_path: Path of folder
            is_active: True if watching, False if paused
        """
        try:
            if self.backend and self.window:
                normalized_path = normalize_path(folder_path)
                self.window.set_folder_active(normalized_path, is_active)
        except Exception as e:
            log_error(f"Failed to handle folder toggled: {e}")

    def _on_backend_folder_resumed(self, folder_path: str) -> None:
        """
        Handle folder resumed (paused → watching) from backend.
        Updates UI to show watching status.

        Args:
            folder_path: Path of resumed folder
        """
        try:
            if self.backend and self.window:
                normalized_path = normalize_path(folder_path)
                self.window.set_folder_active(normalized_path, True)
        except Exception as e:
            log_error(f"Failed to handle folder resumed: {e}")

    # UI Population Helper

    def _reload_wf_ui(self) -> None:
        """
        Reload and populate the watched folders UI with current data.

        This method:
        1. Gets all profiles from backend
        2. Gets all watched folders with their status from backend
        3. Clears the window UI
        4. Populates profiles dropdown
        5. Adds all watched folders to the list

        This is idempotent and safe to call multiple times.
        """
        try:
            if not self.backend or not self.window:
                return

            log_info("Reloading watched folders UI...")

            # Get profiles: profile_id → profile_name
            profiles_dict = self.backend.get_profiles_dict()
            self.window.set_profiles(profiles_dict)

            # Get watched folders with status
            folders_with_status = self.backend.get_watched_folders_with_status()

            # Clear window (removes all folder rows)
            self.window.clear_folders()

            # Add each folder to the window
            for folder_path, profile_id, is_active in folders_with_status:
                normalized_path = normalize_path(folder_path)
                self.window.add_watched_folder(
                    Path(normalized_path),
                    profile_id,
                    is_active=is_active
                )

            log_info(f"Watched folders UI reloaded ({len(folders_with_status)} folders)")

        except Exception as e:
            log_error(f"Failed to reload watched folders UI: {e}", exc_info=True)


# Example usage in your main controller class:
#
# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.watcher_manager = WatcherManager(self)
#         self.wf_controller = WatchedFoldersController(self.watcher_manager, parent=self)
#
#     def on_watched_folders_button_clicked(self):
#         """Called when user clicks 'Manage Watched Folders' button"""
#         self.wf_controller.open_watched_folders_manager()
