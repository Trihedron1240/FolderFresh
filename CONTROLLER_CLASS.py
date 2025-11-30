"""
WatchedFoldersController - Integration Glue Code

Copy this class into your main controller/window class.
This provides complete UI ↔ Backend integration for watched folders management.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QWidget

from folderfresh.ui_qt.watched_folders_window import WatchedFoldersWindow
from folderfresh.ui_qt.watched_folders_backend import WatchedFoldersBackend
from folderfresh.logger_qt import log_info, log_error


def normalize_path(p: str) -> str:
    """Normalize a path to absolute canonical form."""
    return str(Path(p).resolve())


class WatchedFoldersController:
    """
    Controller integrating WatchedFoldersWindow UI with WatchedFoldersBackend.

    Usage in your MainWindow class:

        def __init__(self):
            # ... other init ...
            self.watcher_manager = WatcherManager(self)
            self.wf_controller = WatchedFoldersController(self.watcher_manager, parent=self)

        def on_managed_folders_button_clicked(self):
            self.wf_controller.open_watched_folders_manager()
    """

    def __init__(self, watcher_manager=None, parent: Optional[QWidget] = None):
        self.watcher_manager = watcher_manager
        self.parent = parent
        self.backend: Optional[WatchedFoldersBackend] = None
        self.window: Optional[WatchedFoldersWindow] = None

    def open_watched_folders_manager(self) -> None:
        """
        Create and show the watched folders manager window.

        Handles:
        1. Backend and window creation
        2. All signal connections
        3. Initial UI population
        4. Modal window display
        """
        try:
            log_info("Opening watched folders manager...")

            # Create backend and window
            self.backend = WatchedFoldersBackend(self.watcher_manager)
            self.window = WatchedFoldersWindow(self.parent)

            # Connect signals
            self._connect_ui_to_backend()
            self._connect_backend_to_ui()

            # Populate UI
            self._reload_wf_ui()

            # Show
            self.window.exec()

            log_info("Watched folders manager closed")

        except Exception as e:
            log_error(f"Failed to open watched folders manager: {e}", exc_info=True)

    def _connect_ui_to_backend(self) -> None:
        """Connect UI events to backend methods."""
        try:
            self.window.add_folder_clicked.connect(
                lambda: self._on_add_folder_clicked()
            )
            self.window.remove_folder_clicked.connect(
                lambda path: self._on_remove_folder_clicked(path)
            )
            self.window.profile_changed.connect(
                lambda path, pid: self._on_profile_changed(path, pid)
            )
            log_info("UI → Backend connections established")
        except Exception as e:
            log_error(f"Failed to connect UI to backend: {e}", exc_info=True)

    def _connect_backend_to_ui(self) -> None:
        """Connect backend signals to UI updates."""
        try:
            self.backend.folder_added.connect(
                lambda path: self._on_backend_folder_added(path)
            )
            self.backend.folder_removed.connect(
                lambda path: self._on_backend_folder_removed(path)
            )
            self.backend.folder_profile_changed.connect(
                lambda path, name: self._on_backend_profile_changed(path, name)
            )
            self.backend.folder_toggled.connect(
                lambda path, active: self._on_backend_folder_toggled(path, active)
            )
            self.backend.folder_resumed.connect(
                lambda path: self._on_backend_folder_resumed(path)
            )
            self.backend.folders_reloaded.connect(
                lambda: self._reload_wf_ui()
            )
            log_info("Backend → UI connections established")
        except Exception as e:
            log_error(f"Failed to connect backend to UI: {e}", exc_info=True)

    # ============================================================================
    # UI Event Handlers (UI → Backend)
    # ============================================================================

    def _on_add_folder_clicked(self) -> None:
        """Add folder button clicked - show dialog and add to backend."""
        try:
            if self.backend:
                self.backend.add_watched_folder()
        except Exception as e:
            log_error(f"Failed to add folder: {e}")

    def _on_remove_folder_clicked(self, folder_path: str) -> None:
        """Remove folder button clicked - remove from backend."""
        try:
            if self.backend:
                self.backend.remove_watched_folder(normalize_path(folder_path))
        except Exception as e:
            log_error(f"Failed to remove folder: {e}")

    def _on_profile_changed(self, folder_path: str, profile_id: str) -> None:
        """Profile dropdown changed - update backend."""
        try:
            if self.backend:
                self.backend.set_folder_profile(normalize_path(folder_path), profile_id)
        except Exception as e:
            log_error(f"Failed to change profile: {e}")

    # ============================================================================
    # Backend Signal Handlers (Backend → UI)
    # ============================================================================

    def _on_backend_folder_added(self, folder_path: str) -> None:
        """Folder added from backend - refresh UI."""
        try:
            if self.backend and self.window:
                self._reload_wf_ui()
        except Exception as e:
            log_error(f"Failed to handle folder added: {e}")

    def _on_backend_folder_removed(self, folder_path: str) -> None:
        """Folder removed from backend - update UI."""
        try:
            if self.window:
                self.window.remove_folder_from_list(normalize_path(folder_path))
        except Exception as e:
            log_error(f"Failed to handle folder removed: {e}")

    def _on_backend_profile_changed(self, folder_path: str, profile_name: str) -> None:
        """Profile changed from backend - update UI."""
        try:
            if self.backend and self.window:
                profile_id = self.backend._get_profile_id_by_name(profile_name)
                if profile_id:
                    self.window.update_folder_profile(normalize_path(folder_path), profile_id)
        except Exception as e:
            log_error(f"Failed to handle profile changed: {e}")

    def _on_backend_folder_toggled(self, folder_path: str, is_active: bool) -> None:
        """Folder toggled (pause/resume) from backend - update UI."""
        try:
            if self.window:
                self.window.set_folder_active(normalize_path(folder_path), is_active)
        except Exception as e:
            log_error(f"Failed to handle folder toggled: {e}")

    def _on_backend_folder_resumed(self, folder_path: str) -> None:
        """Folder resumed (paused → watching) from backend - update UI."""
        try:
            if self.window:
                self.window.set_folder_active(normalize_path(folder_path), True)
        except Exception as e:
            log_error(f"Failed to handle folder resumed: {e}")

    # ============================================================================
    # UI Population Helper
    # ============================================================================

    def _reload_wf_ui(self) -> None:
        """
        Reload and populate the watched folders UI.

        Fetches profiles and folders from backend, clears and repopulates window.
        Safe to call multiple times (idempotent).
        """
        try:
            if not self.backend or not self.window:
                return

            log_info("Reloading watched folders UI...")

            # Get and set profiles
            profiles_dict = self.backend.get_profiles_dict()
            self.window.set_profiles(profiles_dict)

            # Get watched folders with status
            folders_with_status = self.backend.get_watched_folders_with_status()

            # Clear and repopulate
            self.window.clear_folders()
            for folder_path, profile_id, is_active in folders_with_status:
                normalized = normalize_path(folder_path)
                self.window.add_watched_folder(Path(normalized), profile_id, is_active)

            log_info(f"Watched folders UI reloaded ({len(folders_with_status)} folders)")

        except Exception as e:
            log_error(f"Failed to reload watched folders UI: {e}", exc_info=True)
