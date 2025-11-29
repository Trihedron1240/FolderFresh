"""
ProfileManager Backend Integration
Connects ProfileManagerWindow to ProfileStore
"""

import uuid
from typing import Dict, List, Optional
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import QMessageBox

from folderfresh.profile_store import ProfileStore
from folderfresh.ui_qt.dialogs import (
    show_confirmation_dialog,
    show_error_dialog,
    show_info_dialog,
    ask_text_dialog
)
from folderfresh.logger_qt import log_info, log_error, log_warning


class ProfileManagerBackend(QObject):
    """
    Backend integration for ProfileManager window.
    Handles all profile operations with ProfileStore.
    """

    # Signals
    profile_created = Signal(str)  # profile_id
    profile_updated = Signal(str)  # profile_id
    profile_deleted = Signal(str)  # profile_id
    profile_activated = Signal(str)  # profile_id
    profiles_reloaded = Signal()

    def __init__(self):
        """Initialize ProfileManager backend"""
        super().__init__()
        self.profile_store = ProfileStore()
        self.profiles_doc = None
        self.active_profile = None

        # Load initial data
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load all profiles from storage"""
        try:
            self.profiles_doc = self.profile_store.load()
            self._set_active_profile()
            log_info("Profiles loaded successfully")
            self.profiles_reloaded.emit()
        except Exception as e:
            log_error(f"Failed to load profiles: {e}")
            show_error_dialog("Load Error", f"Failed to load profiles:\n{e}")

    def _set_active_profile(self) -> None:
        """Set the currently active profile"""
        active_id = self.profiles_doc.get("active_profile_id")
        self.active_profile = None

        for profile in self.profiles_doc.get("profiles", []):
            if profile["id"] == active_id:
                self.active_profile = profile
                break

        if not self.active_profile and self.profiles_doc.get("profiles"):
            self.active_profile = self.profiles_doc["profiles"][0]

    def get_all_profiles(self) -> List[Dict]:
        """Get list of all profiles"""
        return self.profiles_doc.get("profiles", [])

    def get_active_profile(self) -> Optional[Dict]:
        """Get currently active profile"""
        return self.active_profile

    def get_profile_by_id(self, profile_id: str) -> Optional[Dict]:
        """Get profile by ID"""
        for profile in self.profiles_doc.get("profiles", []):
            if profile["id"] == profile_id:
                return profile
        return None

    def create_profile(self, name: str = None) -> Optional[str]:
        """
        Create new profile

        Args:
            name: Profile name (auto-generated if None)

        Returns:
            Profile ID or None if failed
        """
        try:
            if name is None:
                name = ask_text_dialog(None, "New Profile", "Enter profile name:")
                if not name:
                    return None

            # Check for duplicate names
            for p in self.profiles_doc.get("profiles", []):
                if p["name"].lower() == name.lower():
                    show_error_dialog(f"Profile '{name}' already exists")
                    return None

            # Create new profile
            new_profile = {
                "id": f"profile_{uuid.uuid4().hex[:8]}",
                "name": name,
                "settings": {
                    "smart_mode": False,
                    "safe_mode": False,
                    "dry_run": False,
                    "include_sub": True,
                    "skip_hidden": True,
                    "ignore_exts": "",
                    "age_filter_days": 0
                },
                "rules": []
            }

            self.profiles_doc["profiles"].append(new_profile)
            self.profile_store.save(self.profiles_doc)

            log_info(f"Profile created: {name} ({new_profile['id']})")
            self.profile_created.emit(new_profile["id"])
            show_info_dialog(f"Profile '{name}' created successfully")

            return new_profile["id"]

        except Exception as e:
            log_error(f"Failed to create profile: {e}")
            show_error_dialog(f"Failed to create profile:\n{e}")
            return None

    def update_profile(self, profile_id: str, **kwargs) -> bool:
        """
        Update profile settings

        Args:
            profile_id: Profile to update
            **kwargs: Settings to update

        Returns:
            True if successful
        """
        try:
            profile = self.get_profile_by_id(profile_id)
            if not profile:
                show_error_dialog(f"Profile not found: {profile_id}")
                return False

            # Update name if provided
            if "name" in kwargs:
                new_name = kwargs["name"]
                # Check for duplicates
                for p in self.profiles_doc.get("profiles", []):
                    if p["id"] != profile_id and p["name"].lower() == new_name.lower():
                        show_error_dialog(f"Profile '{new_name}' already exists")
                        return False
                profile["name"] = new_name

            # Update settings if provided
            if "settings" in kwargs:
                profile["settings"].update(kwargs["settings"])

            self.profile_store.save(self.profiles_doc)

            log_info(f"Profile updated: {profile['name']}")
            self.profile_updated.emit(profile_id)

            return True

        except Exception as e:
            log_error(f"Failed to update profile: {e}")
            show_error_dialog(f"Failed to update profile:\n{e}")
            return False

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete profile

        Args:
            profile_id: Profile to delete

        Returns:
            True if successful
        """
        try:
            profile = self.get_profile_by_id(profile_id)
            if not profile:
                show_error_dialog(f"Profile not found: {profile_id}")
                return False

            # Cannot delete active profile
            if profile_id == self.profiles_doc.get("active_profile_id"):
                show_error_dialog(f"Cannot delete active profile '{profile['name']}'")
                return False

            # Confirm deletion
            if not show_confirmation_dialog(
                None,
                f"Delete Profile",
                f"Delete profile '{profile['name']}'?\nThis cannot be undone."
            ):
                return False

            # Remove profile
            self.profiles_doc["profiles"] = [
                p for p in self.profiles_doc["profiles"]
                if p["id"] != profile_id
            ]
            self.profile_store.save(self.profiles_doc)

            log_info(f"Profile deleted: {profile['name']}")
            self.profile_deleted.emit(profile_id)
            show_info_dialog(f"Profile '{profile['name']}' deleted")

            return True

        except Exception as e:
            log_error(f"Failed to delete profile: {e}")
            show_error_dialog(f"Failed to delete profile:\n{e}")
            return False

    def set_active_profile(self, profile_id: str) -> bool:
        """
        Set profile as active

        Args:
            profile_id: Profile to activate

        Returns:
            True if successful
        """
        try:
            profile = self.get_profile_by_id(profile_id)
            if not profile:
                show_error_dialog(f"Profile not found: {profile_id}")
                return False

            self.profiles_doc["active_profile_id"] = profile_id
            self.profile_store.save(self.profiles_doc)
            self._set_active_profile()

            log_info(f"Active profile set: {profile['name']}")
            self.profile_activated.emit(profile_id)

            return True

        except Exception as e:
            log_error(f"Failed to set active profile: {e}")
            show_error_dialog(f"Failed to set active profile:\n{e}")
            return False

    def duplicate_profile(self, profile_id: str) -> Optional[str]:
        """
        Duplicate existing profile

        Args:
            profile_id: Profile to duplicate

        Returns:
            New profile ID or None if failed
        """
        try:
            profile = self.get_profile_by_id(profile_id)
            if not profile:
                show_error_dialog(f"Profile not found: {profile_id}")
                return None

            # Create duplicate
            new_name = f"{profile['name']} (Copy)"
            counter = 1
            while any(p["name"] == new_name for p in self.profiles_doc["profiles"]):
                new_name = f"{profile['name']} (Copy {counter})"
                counter += 1

            new_profile = {
                "id": f"profile_{uuid.uuid4().hex[:8]}",
                "name": new_name,
                "settings": profile["settings"].copy(),
                "rules": [r.copy() for r in profile.get("rules", [])]
            }

            self.profiles_doc["profiles"].append(new_profile)
            self.profile_store.save(self.profiles_doc)

            log_info(f"Profile duplicated: {profile['name']} → {new_name}")
            self.profile_created.emit(new_profile["id"])

            return new_profile["id"]

        except Exception as e:
            log_error(f"Failed to duplicate profile: {e}")
            show_error_dialog(f"Failed to duplicate profile:\n{e}")
            return None

    def reload_profiles(self) -> None:
        """Reload profiles from disk"""
        self._load_profiles()

    def save_profiles(self) -> bool:
        """Save current profiles to disk"""
        try:
            self.profile_store.save(self.profiles_doc)
            log_info("Profiles saved")
            return True
        except Exception as e:
            log_error(f"Failed to save profiles: {e}")
            show_error_dialog(f"Failed to save profiles:\n{e}")
            return False
