from watchdog.observers import Observer
from pathlib import Path
from .watcher import AutoTidyHandler


class WatcherManager:
    """
    Manages multiple folder watchers.
    Each folder has its own Observer + AutoTidyHandler with its own root path.
    """

    def __init__(self, app):
        self.app = app
        self.observers = {}  # path -> Observer()

    def watch_folder(self, folder_path: str):
        """Start watching the folder if not already active."""
        from folderfresh.logger_qt import log_info

        folder_path = str(Path(folder_path).resolve())

        # Already watching?
        if folder_path in self.observers:
            log_info(f"[WATCHER] Already watching: {folder_path}")
            return

        handler = AutoTidyHandler(self.app, folder_path)

        observer = Observer()
        observer.schedule(handler, folder_path, recursive=False)
        observer.start()

        self.observers[folder_path] = observer
        log_info(f"[WATCHER] Started watching: {folder_path} (observer is_alive: {observer.is_alive()})")

    def unwatch_folder(self, folder_path: str):
        """Stop watching and remove from table."""
        from folderfresh.logger_qt import log_info

        folder_path = str(Path(folder_path).resolve())

        obs = self.observers.get(folder_path)
        if not obs:
            log_info(f"[WATCHER] Not watching (cannot unwatch): {folder_path}")
            return

        obs.stop()
        obs.join()
        del self.observers[folder_path]
        log_info(f"[WATCHER] Stopped watching: {folder_path}")

    def stop_all(self):
        """Stops all observers (called on app shutdown)."""
        for obs in self.observers.values():
            obs.stop()
            obs.join()
        self.observers.clear()

