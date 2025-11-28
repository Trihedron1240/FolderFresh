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
        folder_path = str(Path(folder_path))

        # Already watching?
        if folder_path in self.observers:
            return

        handler = AutoTidyHandler(self.app, folder_path)

        observer = Observer()
        observer.schedule(handler, folder_path, recursive=False)
        observer.start()

        self.observers[folder_path] = observer

    def unwatch_folder(self, folder_path: str):
        """Stop watching and remove from table."""
        folder_path = str(Path(folder_path))

        obs = self.observers.get(folder_path)
        if not obs:
            return

        obs.stop()
        obs.join()
        del self.observers[folder_path]

    def stop_all(self):
        """Stops all observers (called on app shutdown)."""
        for obs in self.observers.values():
            obs.stop()
            obs.join()
        self.observers.clear()

