"""
WatchedFoldersWindow Backend Integration
Connects WatchedFoldersWindow to WatcherManager and Config
"""

from typing import Dict, List, Optional
from pathlib import Path

from PySide6.QtCore import Signal, QObject

from folderfresh.config import load_config, save_config
from folderfresh.profile_store import ProfileStore
from folderfresh.ui_qt.dialogs import (
    show_confirmation_dialog,
    show_error_dialog,
    show_info_dialog,
    browse_folder_dialog
)
from folderfresh.logger_qt import log_info, log_error, log_warning
from folderfresh.actions import do_preview, do_organise


class WatchedFoldersBackend(QObject):
    """
    Backend integration for WatchedFoldersWindow.
    Manages watched folders and their profile mappings.
    """

    # Signals
    folder_added = Signal(str)  # folder_path
    folder_removed = Signal(str)  # folder_path
    folder_profile_changed = Signal(str, str)  # folder_path, profile_name
    folders_reloaded = Signal()

    def __init__(self, watcher_manager=None):
        """
        Initialize WatchedFolders backend

        Args:
            watcher_manager: Reference to WatcherManager (optional for Phase 9)
        """
        super().__init__()
        self.profile_store = ProfileStore()
        self.watcher_manager = watcher_manager

        # Load initial data
        self._load_data()

    def _load_data(self) -> None:
        """Load configuration and profiles"""
        try:
            self.config_data = load_config()
            self.profiles_doc = self.profile_store.load()

            log_info("Watched folders loaded")
            self.folders_reloaded.emit()

        except Exception as e:
            log_error(f"Failed to load watched folders: {e}")
            show_error_dialog(None, "Load Watched Folders Failed", f"Failed to load watched folders:\n{e}")

    def get_watched_folders(self) -> List[str]:
        """Get list of watched folders"""
        return self.config_data.get("watched_folders", [])

    def get_folder_profile(self, folder_path: str) -> str:
        """
        Get profile name for folder

        Args:
            folder_path: Folder path

        Returns:
            Profile name
        """
        folder_profile_map = self.config_data.get("folder_profile_map", {})
        return folder_profile_map.get(folder_path, "Default")

    def get_available_profiles(self) -> List[str]:
        """Get list of available profile names"""
        profiles = self.profiles_doc.get("profiles", [])
        return [p["name"] for p in profiles]

    def get_profiles_dict(self) -> Dict[str, str]:
        """
        Get profiles as a dictionary mapping profile ID to name.

        Returns:
            Dict of profile_id -> profile_name
        """
        profiles = self.profiles_doc.get("profiles", [])
        return {p["id"]: p.get("name", p["id"]) for p in profiles}

    def get_watched_folders_with_status(self) -> List[tuple]:
        """
        Get all watched folders with their profiles and active status.

        Returns:
            List of (folder_path, profile_id, is_active) tuples
        """
        folder_profile_map = self.config_data.get("folder_profile_map", {})
        watched_list = []

        for folder_path in self.get_watched_folders():
            # Get profile ID (need to map from profile_name to profile_id)
            profile_name = folder_profile_map.get(folder_path, "Default")
            profile_id = self._get_profile_id_by_name(profile_name)

            # Assume all folders in watched_folders list are active
            is_active = True

            watched_list.append((folder_path, profile_id, is_active))

        return watched_list

    def _get_profile_id_by_name(self, profile_name: str) -> str:
        """
        Get profile ID from profile name.

        Args:
            profile_name: Profile name

        Returns:
            Profile ID or "default" if not found
        """
        profiles = self.profiles_doc.get("profiles", [])
        for p in profiles:
            if p.get("name") == profile_name:
                return p["id"]
        return "default"

    def _get_profile_name_by_id(self, profile_id: str) -> Optional[str]:
        """
        Get profile name from profile ID.

        Args:
            profile_id: Profile ID

        Returns:
            Profile name or None if not found
        """
        profiles = self.profiles_doc.get("profiles", [])
        for p in profiles:
            if p.get("id") == profile_id:
                return p.get("name", profile_id)
        return None

    def add_watched_folder(self, folder_path: str = None) -> bool:
        """
        Add folder to watch list

        Args:
            folder_path: Path to add (uses dialog if None)

        Returns:
            True if successful
        """
        try:
            if folder_path is None:
                folder_path = browse_folder_dialog(None, "Select folder to watch")
                if not folder_path:
                    return False

            # Normalize path
            folder_path = str(Path(folder_path).resolve())

            # Check if already watching
            if folder_path in self.get_watched_folders():
                show_info_dialog(None, "Already Watching", f"Already watching: {folder_path}")
                return False

            # Check if folder exists
            if not Path(folder_path).is_dir():
                show_error_dialog(None, "Folder Not Found", f"Folder not found: {folder_path}")
                return False

            # Add to config
            if "watched_folders" not in self.config_data:
                self.config_data["watched_folders"] = []

            self.config_data["watched_folders"].append(folder_path)

            # Start watching in WatcherManager if available
            if self.watcher_manager:
                try:
                    self.watcher_manager.watch_folder(folder_path)
                    log_info(f"Watching folder: {folder_path}")
                except Exception as e:
                    log_warning(f"Failed to start watching folder: {e}")

            # Save config
            save_config(self.config_data)

            log_info(f"Folder added to watch list: {folder_path}")

            # Organize existing files in the folder
            try:
                self._organize_existing_files(folder_path)
            except Exception as e:
                log_error(f"Failed to organize existing files: {e}")

            self.folder_added.emit(folder_path)
            show_info_dialog(None, "Watching Folder", f"Now watching: {folder_path}\n\nOrganizing existing files...")

            return True

        except Exception as e:
            log_error(f"Failed to add watched folder: {e}")
            show_error_dialog(None, "Add Watched Folder Failed", f"Failed to add watched folder:\n{e}")
            return False

    def remove_watched_folder(self, folder_path: str) -> bool:
        """
        Remove folder from watch list

        Args:
            folder_path: Folder to remove

        Returns:
            True if successful
        """
        try:
            if folder_path not in self.get_watched_folders():
                show_error_dialog(None, "Not Watching", f"Not watching: {folder_path}")
                return False

            if not show_confirmation_dialog(
                None,
                "Remove Watched Folder",
                f"Stop watching: {folder_path}?"
            ):
                return False

            # Stop watching in WatcherManager if available
            if self.watcher_manager:
                try:
                    self.watcher_manager.unwatch_folder(folder_path)
                    log_info(f"Stopped watching folder: {folder_path}")
                except Exception as e:
                    log_warning(f"Failed to stop watching folder: {e}")

            # Remove from config
            watched_folders = self.config_data.get("watched_folders", [])
            if folder_path in watched_folders:
                watched_folders.remove(folder_path)
                self.config_data["watched_folders"] = watched_folders

            # Remove folder profile mapping
            folder_profile_map = self.config_data.get("folder_profile_map", {})
            if folder_path in folder_profile_map:
                del folder_profile_map[folder_path]
                self.config_data["folder_profile_map"] = folder_profile_map

            # Save config
            save_config(self.config_data)

            log_info(f"Folder removed from watch list: {folder_path}")
            self.folder_removed.emit(folder_path)
            show_info_dialog(None, "Stopped Watching", f"No longer watching: {folder_path}")

            return True

        except Exception as e:
            log_error(f"Failed to remove watched folder: {e}")
            show_error_dialog(None, "Remove Watched Folder Failed", f"Failed to remove watched folder:\n{e}")
            return False

    def set_folder_profile(self, folder_path: str, profile_id: str) -> bool:
        """
        Set profile for specific folder

        Args:
            folder_path: Folder path
            profile_id: Profile ID (from dropdown.currentData())

        Returns:
            True if successful
        """
        try:
            if folder_path not in self.get_watched_folders():
                show_error_dialog(None, "Not Watching", f"Not watching: {folder_path}")
                return False

            # Convert profile ID to profile name
            profile_name = self._get_profile_name_by_id(profile_id)
            if not profile_name:
                show_error_dialog(None, "Profile Not Found", f"Profile not found: {profile_id}")
                return False

            # Update mapping
            folder_profile_map = self.config_data.get("folder_profile_map", {})
            folder_profile_map[folder_path] = profile_name
            self.config_data["folder_profile_map"] = folder_profile_map

            # Save config
            save_config(self.config_data)

            log_info(f"Folder profile set: {folder_path} → {profile_name}")

            # Reorganize existing files with new profile
            try:
                self._organize_existing_files(folder_path)
            except Exception as e:
                log_error(f"Failed to reorganize files after profile change: {e}")

            self.folder_profile_changed.emit(folder_path, profile_name)

            return True

        except Exception as e:
            log_error(f"Failed to set folder profile: {e}")
            show_error_dialog(None, "Set Folder Profile Failed", f"Failed to set folder profile:\n{e}")
            return False

    def _organize_existing_files(self, folder_path: str) -> None:
        """
        Organize existing files in the folder when it's first added to watch list.

        Args:
            folder_path: Path to the folder to organize
        """
        try:
            folder_path = Path(folder_path)
            if not folder_path.is_dir():
                log_warning(f"Folder not found: {folder_path}")
                return

            # Get the profile assigned to this folder (or use default)
            profile_name = self.get_folder_profile(str(folder_path))
            profiles_doc = self.profile_store.load()

            # Find profile by name
            target_profile = None
            for profile in profiles_doc.get("profiles", []):
                if profile.get("name") == profile_name or profile.get("id") == profile_name:
                    target_profile = profile
                    break

            if not target_profile:
                log_warning(f"Profile not found for folder: {folder_path}")
                return

            # Load config with profile data
            config_data = load_config()

            # Merge profile category data into config
            config_data["custom_categories"] = target_profile.get("custom_categories", {})
            config_data["category_enabled"] = target_profile.get("category_enabled", {})
            category_overrides = target_profile.get("category_overrides", {})
            custom_category_names = {}
            for cat_name, override_data in category_overrides.items():
                if isinstance(override_data, dict) and "name" in override_data:
                    custom_category_names[cat_name] = override_data["name"]
            config_data["custom_category_names"] = custom_category_names

            # Create app-like object for do_preview and do_organise
            class TempApp:
                def __init__(self, folder, cfg, profile):
                    self.selected_folder = folder
                    self.config_data = cfg
                    self.profile = profile
                    # Use profile settings if available
                    self.include_sub = type('obj', (object,), {'get': lambda self: True})()
                    self.skip_hidden = type('obj', (object,), {'get': lambda self: True})()
                    self.smart_mode = type('obj', (object,), {'get': lambda self: profile.get("settings", {}).get("smart_mode", False)})()
                    self.safe_mode = type('obj', (object,), {'get': lambda self: profile.get("settings", {}).get("safe_mode", True)})()

            app = TempApp(folder_path, config_data, target_profile)

            # Generate preview of what will be organized
            moves = do_preview(app)

            if not moves:
                log_info(f"No files to organize in: {folder_path}")
                return

            # Organize the files
            results = do_organise(app, moves)

            # Log results
            success_count = sum(1 for r in results if not r.get("error"))
            log_info(f"Organized {success_count}/{len(results)} files in {folder_path}")

        except Exception as e:
            log_error(f"Failed to organize existing files in {folder_path}: {e}")

    def open_folder(self, folder_path: str) -> bool:
        """
        Open folder in file explorer

        Args:
            folder_path: Folder to open

        Returns:
            True if successful
        """
        try:
            import subprocess
            import platform

            folder_path = Path(folder_path).resolve()

            if not folder_path.is_dir():
                show_error_dialog(None, "Folder Not Found", f"Folder not found: {folder_path}")
                return False

            if platform.system() == "Windows":
                subprocess.Popen(f'explorer "{folder_path}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", str(folder_path)])
            else:  # Linux
                subprocess.Popen(["xdg-open", str(folder_path)])

            log_info(f"Opened folder: {folder_path}")
            return True

        except Exception as e:
            log_error(f"Failed to open folder: {e}")
            show_error_dialog(None, "Open Folder Failed", f"Failed to open folder:\n{e}")
            return False

    def reload_folders(self) -> None:
        """Reload folders from disk"""
        self._load_data()

    def save_config(self) -> bool:
        """Save configuration to disk"""
        try:
            save_config(self.config_data)
            log_info("Watched folders configuration saved")
            return True
        except Exception as e:
            log_error(f"Failed to save configuration: {e}")
            show_error_dialog(None, "Save Configuration Failed", f"Failed to save configuration:\n{e}")
            return False
