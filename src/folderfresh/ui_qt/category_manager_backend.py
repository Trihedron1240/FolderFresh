"""
CategoryManager Backend Integration
Manages category operations (default overrides, custom categories, enabled state)
with profile-specific storage and signal-based architecture
"""

from typing import Dict, List, Tuple, Optional
import copy
from datetime import datetime

from PySide6.QtCore import Signal, QObject

from folderfresh.profile_store import ProfileStore
from folderfresh.logger_qt import log_info, log_error, log_warning
from folderfresh.constants import CATEGORIES as DEFAULT_CATEGORIES


class CategoryManagerBackend(QObject):
    """
    Backend for CategoryManager window.
    Manages category overrides, custom categories, and enabled states.
    """

    # Signals
    categories_loaded = Signal(dict, dict, dict)  # overrides, custom_categories, enabled
    category_updated = Signal(str)  # category_name
    category_deleted = Signal(str)  # category_name
    category_added = Signal(str)  # category_name
    defaults_restored = Signal()

    def __init__(self, profile_id: str):
        """
        Initialize CategoryManager backend

        Args:
            profile_id: Profile ID to manage categories for
        """
        super().__init__()
        self.profile_store = ProfileStore()
        self.profile_id = profile_id
        self.working_profile = None
        self.original_profile = None

        log_info(f"CategoryManagerBackend initialized for profile: {profile_id}")

    def load_categories(self) -> Tuple[Dict, Dict, Dict]:
        """
        Load categories for the profile

        Returns:
            Tuple of (category_overrides, custom_categories, category_enabled)
        """
        try:
            # Load full document
            full_doc = self.profile_store.load()

            # Find the specific profile
            original = None
            for p in full_doc.get("profiles", []):
                if p["id"] == self.profile_id:
                    original = p
                    break

            if not original:
                log_warning(f"Profile {self.profile_id} not found")
                return {}, {}, {}

            # Store original and working copy
            self.original_profile = original
            self.working_profile = copy.deepcopy(original)

            # Extract category data
            overrides = self.working_profile.get("category_overrides", {})
            custom_categories = self.working_profile.get("custom_categories", {})
            enabled = self.working_profile.get("category_enabled", {})

            # Ensure all default categories have enabled state
            for cat in DEFAULT_CATEGORIES:
                if cat not in enabled:
                    enabled[cat] = True

            log_info(f"Loaded categories for profile {self.profile_id}")
            self.categories_loaded.emit(overrides, custom_categories, enabled)

            return overrides, custom_categories, enabled

        except Exception as e:
            log_error(f"Failed to load categories: {e}", exc_info=True)
            return {}, {}, {}

    def toggle_enabled(self, category: str, enabled: bool) -> bool:
        """
        Toggle category enabled state

        Args:
            category: Category name
            enabled: Enabled state

        Returns:
            True if successful
        """
        try:
            if not self.working_profile:
                log_warning("No working profile loaded")
                return False

            if "category_enabled" not in self.working_profile:
                self.working_profile["category_enabled"] = {}

            self.working_profile["category_enabled"][category] = enabled

            if self._commit_changes():
                self.category_updated.emit(category)
                log_info(f"Category {category} enabled: {enabled}")
                return True

            return False

        except Exception as e:
            log_error(f"Failed to toggle category: {e}", exc_info=True)
            return False

    def update_default_category(
        self,
        category: str,
        new_name: str,
        extensions: List[str]
    ) -> bool:
        """
        Update default category display name and extensions

        Args:
            category: Original category name
            new_name: New display name override
            extensions: List of file extensions

        Returns:
            True if successful
        """
        try:
            if not self.working_profile:
                log_warning("No working profile loaded")
                return False

            # Initialize overrides if needed
            if "category_overrides" not in self.working_profile:
                self.working_profile["category_overrides"] = {}

            # Store the override
            if new_name != category or extensions != DEFAULT_CATEGORIES.get(category, []):
                self.working_profile["category_overrides"][category] = {
                    "name": new_name,
                    "extensions": extensions
                }
            elif category in self.working_profile.get("category_overrides", {}):
                # Remove override if it matches default
                del self.working_profile["category_overrides"][category]

            if self._commit_changes():
                self.category_updated.emit(category)
                log_info(f"Updated default category: {category}")
                return True

            return False

        except Exception as e:
            log_error(f"Failed to update default category: {e}", exc_info=True)
            return False

    def update_custom_category(
        self,
        old_name: str,
        new_name: str,
        extensions: List[str]
    ) -> bool:
        """
        Update custom category (with rename support)

        Args:
            old_name: Original custom category name
            new_name: New custom category name
            extensions: List of file extensions

        Returns:
            True if successful
        """
        try:
            if not self.working_profile:
                log_warning("No working profile loaded")
                return False

            # Initialize custom categories if needed
            if "custom_categories" not in self.working_profile:
                self.working_profile["custom_categories"] = {}

            custom = self.working_profile["custom_categories"]

            # Handle rename
            if old_name != new_name and old_name in custom:
                del custom[old_name]

            # Update with new extensions
            custom[new_name] = extensions

            if self._commit_changes():
                self.category_updated.emit(new_name)
                log_info(f"Updated custom category: {old_name} -> {new_name}")
                return True

            return False

        except Exception as e:
            log_error(f"Failed to update custom category: {e}", exc_info=True)
            return False

    def delete_custom_category(self, category: str) -> bool:
        """
        Delete custom category

        Args:
            category: Custom category name to delete

        Returns:
            True if successful
        """
        try:
            if not self.working_profile:
                log_warning("No working profile loaded")
                return False

            custom = self.working_profile.get("custom_categories", {})
            if category in custom:
                del custom[category]

            # Also remove from enabled if present
            enabled = self.working_profile.get("category_enabled", {})
            if category in enabled:
                del enabled[category]

            if self._commit_changes():
                self.category_deleted.emit(category)
                log_info(f"Deleted custom category: {category}")
                return True

            return False

        except Exception as e:
            log_error(f"Failed to delete custom category: {e}", exc_info=True)
            return False

    def add_custom_category(self, name: str, extensions: List[str]) -> bool:
        """
        Add new custom category

        Args:
            name: Custom category name
            extensions: List of file extensions

        Returns:
            True if successful
        """
        try:
            if not self.working_profile:
                log_warning("No working profile loaded")
                return False

            # Check if category already exists
            if name in self.working_profile.get("custom_categories", {}):
                log_warning(f"Custom category already exists: {name}")
                return False

            # Initialize custom categories if needed
            if "custom_categories" not in self.working_profile:
                self.working_profile["custom_categories"] = {}

            # Add new category
            self.working_profile["custom_categories"][name] = extensions

            # Enable by default
            if "category_enabled" not in self.working_profile:
                self.working_profile["category_enabled"] = {}
            self.working_profile["category_enabled"][name] = True

            if self._commit_changes():
                self.category_added.emit(name)
                log_info(f"Added custom category: {name}")
                return True

            return False

        except Exception as e:
            log_error(f"Failed to add custom category: {e}", exc_info=True)
            return False

    def restore_defaults(self) -> bool:
        """
        Restore default categories (clear overrides and custom categories)

        Returns:
            True if successful
        """
        try:
            if not self.working_profile:
                log_warning("No working profile loaded")
                return False

            # Clear overrides and custom categories
            self.working_profile["category_overrides"] = {}
            self.working_profile["custom_categories"] = {}

            # Keep only default categories in enabled state
            enabled = {}
            for cat in DEFAULT_CATEGORIES:
                enabled[cat] = True
            self.working_profile["category_enabled"] = enabled

            if self._commit_changes():
                self.defaults_restored.emit()
                log_info("Restored default categories")
                return True

            return False

        except Exception as e:
            log_error(f"Failed to restore defaults: {e}", exc_info=True)
            return False

    def _commit_changes(self) -> bool:
        """
        Commit changes to profile in ProfileStore

        Uses reload-patch-save pattern to avoid conflicts:
        1. Reload fresh document
        2. Find and patch specific profile
        3. Save document

        Returns:
            True if successful
        """
        try:
            # Reload fresh document to avoid conflicts
            doc = self.profile_store.load()

            # Find and update the specific profile
            profiles = doc.get("profiles", [])
            for i, p in enumerate(profiles):
                if p["id"] == self.profile_id:
                    # Update timestamp
                    self.working_profile["updated_at"] = datetime.now().isoformat()
                    doc["profiles"][i] = self.working_profile
                    break

            # Save document
            self.profile_store.save(doc)

            log_info(f"Committed changes for profile {self.profile_id}")
            return True

        except Exception as e:
            log_error(f"Failed to commit changes: {e}", exc_info=True)
            return False

    def get_category_extensions(self, category: str) -> List[str]:
        """
        Get extensions for a category (accounting for overrides)

        Args:
            category: Category name

        Returns:
            List of extensions
        """
        if not self.working_profile:
            return []

        # Check for override
        overrides = self.working_profile.get("category_overrides", {})
        if category in overrides:
            return overrides[category].get("extensions", [])

        # Check for custom category
        custom = self.working_profile.get("custom_categories", {})
        if category in custom:
            return custom[category]

        # Return default
        return DEFAULT_CATEGORIES.get(category, [])

    def get_category_display_name(self, category: str) -> str:
        """
        Get display name for a category (accounting for overrides)

        Args:
            category: Category name

        Returns:
            Display name
        """
        # Check for override
        overrides = self.working_profile.get("category_overrides", {})
        if category in overrides:
            return overrides[category].get("name", category)

        # Return original name
        return category

    def is_category_enabled(self, category: str) -> bool:
        """
        Check if category is enabled

        Args:
            category: Category name

        Returns:
            True if enabled
        """
        if not self.working_profile:
            return True

        enabled = self.working_profile.get("category_enabled", {})
        return enabled.get(category, True)
