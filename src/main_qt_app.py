"""
FolderFresh PySide6 Application
Complete application wrapper with backend integration and lifecycle management
"""

import sys
import signal
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from folderfresh.logger_qt import QtLogger, log_info, log_error, log_warning, shutdown_logger
from folderfresh.error_handler_qt import QtErrorHandler
from folderfresh.config import load_config, save_config
from folderfresh.profile_store import ProfileStore
from folderfresh.watcher_manager import WatcherManager
from folderfresh.undo_manager import UNDO_MANAGER
from folderfresh.activity_log import ACTIVITY_LOG, log_activity

from folderfresh.ui_qt.main_qt import setup_qt_app, setup_stylesheet
from folderfresh.ui_qt.application import FolderFreshApplication
from folderfresh.ui_qt.profile_manager_backend import ProfileManagerBackend
from folderfresh.ui_qt.rule_manager_backend import RuleManagerBackend
from folderfresh.ui_qt.watched_folders_backend import WatchedFoldersBackend
from folderfresh.ui_qt.activity_log_backend import ActivityLogBackend
from folderfresh.ui_qt.main_window_backend import MainWindowBackend


class FolderFreshQtApplication:
    """
    Complete FolderFresh PySide6 Application.
    Manages all backend systems, UI initialization, and application lifecycle.
    """

    def __init__(self):
        """Initialize application"""
        # Initialize logging first
        self.logger_instance = QtLogger("folderfresh")
        log_info("=" * 70)
        log_info("FolderFresh PySide6 Application Initializing")
        log_info("=" * 70)

        # Backend systems
        self.profile_store = None
        self.watcher_manager = None
        self.config_data = None
        self.profiles_doc = None
        self.active_profile = None

        # UI components
        self.qt_app = None
        self.main_app = None
        self.main_window = None

        # Backend integrations
        self.profile_backend = None
        self.rule_backend = None
        self.folders_backend = None
        self.log_backend = None
        self.main_backend = None

        # Shutdown flag
        self.is_shutting_down = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        log_info("Application initialization started")

    def _handle_signal(self, signum, frame) -> None:
        """Handle system signals for graceful shutdown"""
        if not self.is_shutting_down:
            log_info(f"Signal {signum} received, shutting down...")
            self.shutdown()
            sys.exit(0)

    def _load_configuration(self) -> bool:
        """
        Load all configuration and profiles

        Returns:
            True if successful
        """
        try:
            log_info("Loading configuration and profiles...")

            self.profile_store = ProfileStore()

            self.config_data = load_config()
            self.profiles_doc = self.profile_store.load()

            log_info("Configuration loaded successfully")

            # Get active profile
            active_id = self.profiles_doc.get("active_profile_id")
            for profile in self.profiles_doc.get("profiles", []):
                if profile["id"] == active_id:
                    self.active_profile = profile
                    break

            if self.active_profile:
                log_info(f"Active profile: {self.active_profile.get('name')}")
            else:
                log_warning("No active profile found, using default")

            return True

        except Exception as e:
            log_error(f"Failed to load configuration: {e}", exc_info=True)
            QtErrorHandler.handle_config_error(e)
            return False

    def _initialize_ui(self) -> bool:
        """
        Initialize PySide6 UI components

        Returns:
            True if successful
        """
        try:
            log_info("Initializing PySide6 UI...")

            # Create QApplication
            self.qt_app = setup_qt_app()
            setup_stylesheet(self.qt_app)

            log_info("QApplication created and styled")

            # Create main application window, passing profile_store so it can be used during initialization
            self.main_app = FolderFreshApplication(self.qt_app, self.config_data, profile_store=self.profile_store)
            self.main_window = self.main_app.main_window

            log_info("Main window created")

            return True

        except Exception as e:
            log_error(f"Failed to initialize UI: {e}", exc_info=True)
            QtErrorHandler.handle_fatal_error(e)
            return False

    def _initialize_backends(self) -> bool:
        """
        Initialize all backend integrations

        Returns:
            True if successful
        """
        try:
            log_info("Initializing backend integrations...")

            # Initialize backend modules
            self.profile_backend = ProfileManagerBackend()
            self.rule_backend = RuleManagerBackend()
            self.folders_backend = WatchedFoldersBackend(self.watcher_manager)
            self.log_backend = ActivityLogBackend(auto_refresh=True)
            self.main_backend = MainWindowBackend()

            log_info("Backend integrations initialized")

            # Connect signals from backends to update UI
            self._connect_backend_signals()

            return True

        except Exception as e:
            log_error(f"Failed to initialize backends: {e}", exc_info=True)
            QtErrorHandler.handle_fatal_error(e)
            return False

    def _connect_backend_signals(self) -> None:
        """Connect backend signals to UI updates"""
        try:
            # Profile backend signals
            if self.profile_backend:
                self.profile_backend.profile_created.connect(
                    lambda pid: log_activity(f"Profile created: {pid}")
                )
                self.profile_backend.profile_updated.connect(
                    lambda pid: log_activity(f"Profile updated: {pid}")
                )

            # Rule backend signals
            if self.rule_backend:
                self.rule_backend.rule_created.connect(
                    lambda rid: log_activity(f"Rule created: {rid}")
                )
                self.rule_backend.rule_tested.connect(
                    lambda results: log_activity(f"Rule tested: {len(results)} files")
                )

            # Watched folders signals
            if self.folders_backend:
                self.folders_backend.folder_added.connect(
                    lambda path: log_activity(f"Watching folder: {path}")
                )
                self.folders_backend.folder_removed.connect(
                    lambda path: log_activity(f"Stopped watching: {path}")
                )

            # Main window signals
            if self.main_window:
                if self.main_window.preview_requested:
                    self.main_window.preview_requested.connect(
                        lambda: log_activity("Preview requested")
                    )
                if self.main_window.organise_requested:
                    self.main_window.organise_requested.connect(
                        lambda: log_activity("Organisation requested")
                    )

            # Main backend signals
            if self.main_backend:
                self.main_backend.undo_state_changed.connect(
                    lambda enabled, text: log_activity(f"Undo state: {text}")
                )

            log_info("Backend signals connected to UI")

        except Exception as e:
            log_warning(f"Failed to connect some signals: {e}")

    def _initialize_watcher(self) -> bool:
        """
        Initialize file watcher for auto-tidy

        Returns:
            True if successful
        """
        try:
            log_info("Initializing file watcher...")

            self.watcher_manager = WatcherManager(self.main_app)

            # Watch configured folders
            watched_folders = self.config_data.get("watched_folders", [])
            for folder_path in watched_folders:
                try:
                    self.watcher_manager.watch_folder(folder_path)
                    log_info(f"Watching folder: {folder_path}")
                except Exception as e:
                    log_warning(f"Failed to watch folder {folder_path}: {e}")

            log_info(f"File watcher initialized ({len(watched_folders)} folders)")

            return True

        except Exception as e:
            log_error(f"Failed to initialize file watcher: {e}", exc_info=True)
            QtErrorHandler.handle_folder_watch_error(e, "watcher")
            return False

    def run(self) -> int:
        """
        Run the application

        Returns:
            Exit code (0 = success, 1 = error)
        """
        try:
            # Load configuration
            if not self._load_configuration():
                return 1

            # Initialize UI
            if not self._initialize_ui():
                return 1

            # Initialize watcher
            if not self._initialize_watcher():
                log_warning("Watcher initialization failed, continuing without auto-tidy")

            # Initialize backends
            if not self._initialize_backends():
                return 1

            # Show main window
            self.main_window.show()
            log_info("Main window displayed")

            # Log startup completion
            log_activity("FolderFresh started")
            log_info("=" * 70)
            log_info("Application started successfully")
            log_info("=" * 70)

            # Run event loop
            exit_code = self.qt_app.exec()

            log_info(f"Application event loop exited with code: {exit_code}")

            return exit_code

        except Exception as e:
            log_error(f"Fatal error in application run: {e}", exc_info=True)
            QtErrorHandler.handle_fatal_error(e)
            return 1

        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown application gracefully"""
        if self.is_shutting_down:
            return

        self.is_shutting_down = True

        try:
            log_info("Application shutdown started...")

            # Stop auto-refresh in activity log backend
            if self.log_backend:
                try:
                    self.log_backend.stop_auto_refresh()
                except Exception as e:
                    log_warning(f"Failed to stop activity log refresh: {e}")

            # Stop undo state check
            if self.main_backend:
                try:
                    self.main_backend.cleanup()
                except Exception as e:
                    log_warning(f"Failed to cleanup main backend: {e}")

            # Stop file watcher
            if self.watcher_manager:
                try:
                    self.watcher_manager.stop_all()
                    log_info("File watcher stopped")
                except Exception as e:
                    log_warning(f"Failed to stop file watcher: {e}")

            # Save configuration
            if self.config_data:
                try:
                    save_config(self.config_data)
                    log_info("Configuration saved")
                except Exception as e:
                    log_warning(f"Failed to save configuration: {e}")

            # Close main window
            if self.main_window:
                try:
                    self.main_window.close()
                except Exception as e:
                    log_warning(f"Failed to close main window: {e}")

            # Log activity log entry
            log_activity("FolderFresh closed")

            # Flush activity log
            try:
                if ACTIVITY_LOG:
                    # Save activity log if needed
                    log_path = Path.home() / ".folderfresh" / "logs" / "activity.log"
                    ACTIVITY_LOG.save_to_file(str(log_path))
            except Exception as e:
                log_warning(f"Failed to save activity log: {e}")

            log_info("=" * 70)
            log_info("Application shutdown complete")
            log_info("=" * 70)

            # Shutdown logger (flushes all handlers)
            shutdown_logger()

        except Exception as e:
            print(f"Error during shutdown: {e}")
            if self.logger_instance:
                log_error(f"Error during shutdown: {e}", exc_info=True)


def main() -> int:
    """
    Application entry point

    Returns:
        Exit code
    """
    app = FolderFreshQtApplication()

    try:
        return app.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        app.shutdown()
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        app.shutdown()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
