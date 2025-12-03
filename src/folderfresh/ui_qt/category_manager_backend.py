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

    def _load_profile_from_disk(self) -> Optional[Dict]:
        """Load the current profile from disk."""
        full_doc = self.profile_store.load()
        for p in full_doc.get("profiles", []):
            if p["id"] == self.profile_id:
                return p
        return None

    def load_categories(self) -> Tuple[Dict, Dict, Dict]:
        """
        Load categories for the profile (always from disk)

        Returns:
            Tuple of (category_overrides, custom_categories, category_enabled)
        """
        try:
            # Load profile from disk (single source of truth)
            profile = self._load_profile_from_disk()
            if not profile:
                log_warning(f"Profile {self.profile_id} not found")
                return {}, {}, {}

            # Store working copy for edits
            self.working_profile = copy.deepcopy(profile)
            self.original_profile = copy.deepcopy(profile)

            # Extract category data directly from disk
            overrides = profile.get("category_overrides", {})
            custom_categories = profile.get("custom_categories", {})
            enabled = profile.get("category_enabled", {})

            # Ensure all default categories have enabled state
            for cat in DEFAULT_CATEGORIES:
                if cat not in enabled:
                    enabled[cat] = True

            log_info(f"Loaded categories for profile {self.profile_id}, overrides={overrides}")
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
            # Load fresh from disk
            doc = self.profile_store.load()

            # Find and update the profile directly
            for p in doc.get("profiles", []):
                if p["id"] == self.profile_id:
                    if "category_enabled" not in p:
                        p["category_enabled"] = {}
                    p["category_enabled"][category] = enabled
                    p["updated_at"] = datetime.now().isoformat()
                    self.profile_store.save(doc)

                    # Update working copy to match disk
                    self.working_profile = copy.deepcopy(p)

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
            # Load fresh from disk
            doc = self.profile_store.load()

            # Find and update the profile directly
            for p in doc.get("profiles", []):
                if p["id"] == self.profile_id:
                    # Initialize overrides if needed
                    if "category_overrides" not in p:
                        p["category_overrides"] = {}

                    # Store the override
                    if new_name != category or extensions != DEFAULT_CATEGORIES.get(category, []):
                        p["category_overrides"][category] = {
                            "name": new_name,
                            "extensions": extensions
                        }
                    elif category in p.get("category_overrides", {}):
                        # Remove override if it matches default
                        del p["category_overrides"][category]

                    p["updated_at"] = datetime.now().isoformat()
                    self.profile_store.save(doc)

                    # Update working copy to match disk
                    self.working_profile = copy.deepcopy(p)

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
            # Load fresh from disk
            doc = self.profile_store.load()

            # Find and update the profile directly
            for p in doc.get("profiles", []):
                if p["id"] == self.profile_id:
                    # Initialize custom categories if needed
                    if "custom_categories" not in p:
                        p["custom_categories"] = {}

                    custom = p["custom_categories"]

                    # Handle rename
                    if old_name != new_name and old_name in custom:
                        del custom[old_name]

                    # Update with new extensions
                    custom[new_name] = extensions

                    p["updated_at"] = datetime.now().isoformat()
                    self.profile_store.save(doc)

                    # Update working copy to match disk
                    self.working_profile = copy.deepcopy(p)

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
            # Load fresh from disk
            doc = self.profile_store.load()

            # Find and update the profile directly
            for p in doc.get("profiles", []):
                if p["id"] == self.profile_id:
                    custom = p.get("custom_categories", {})
                    if category in custom:
                        del custom[category]

                    # Also remove from enabled if present
                    enabled = p.get("category_enabled", {})
                    if category in enabled:
                        del enabled[category]

                    p["updated_at"] = datetime.now().isoformat()
                    self.profile_store.save(doc)

                    # Update working copy to match disk
                    self.working_profile = copy.deepcopy(p)

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
            # Load fresh from disk
            doc = self.profile_store.load()

            # Find and update the profile directly
            for p in doc.get("profiles", []):
                if p["id"] == self.profile_id:
                    # Check if category already exists
                    if name in p.get("custom_categories", {}):
                        log_warning(f"Custom category already exists: {name}")
                        return False

                    # Initialize custom categories if needed
                    if "custom_categories" not in p:
                        p["custom_categories"] = {}

                    # Add new category
                    p["custom_categories"][name] = extensions

                    # Enable by default
                    if "category_enabled" not in p:
                        p["category_enabled"] = {}
                    p["category_enabled"][name] = True

                    p["updated_at"] = datetime.now().isoformat()
                    self.profile_store.save(doc)

                    # Update working copy to match disk
                    self.working_profile = copy.deepcopy(p)

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
            # Load fresh from disk
            doc = self.profile_store.load()

            # Find and update the profile directly
            for p in doc.get("profiles", []):
                if p["id"] == self.profile_id:
                    # Clear overrides and custom categories
                    log_info(f"[restore_defaults] Before: category_overrides={p.get('category_overrides', {})}")
                    p["category_overrides"] = {}
                    p["custom_categories"] = {}

                    # Keep only default categories in enabled state
                    enabled = {}
                    for cat in DEFAULT_CATEGORIES:
                        enabled[cat] = True
                    p["category_enabled"] = enabled

                    p["updated_at"] = datetime.now().isoformat()
                    self.profile_store.save(doc)

                    # Update working copy to match disk
                    self.working_profile = copy.deepcopy(p)

                    log_info(f"[restore_defaults] After commit: category_overrides={p.get('category_overrides', {})}")
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
        2. Find the profile
        3. Update ONLY category-related fields
        4. Save document

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
                    # Update ONLY the category-related fields from working_profile
                    # Don't replace the entire profile to preserve other data
                    p["category_overrides"] = self.working_profile.get("category_overrides", {})
                    p["custom_categories"] = self.working_profile.get("custom_categories", {})
                    p["category_enabled"] = self.working_profile.get("category_enabled", {})
                    p["updated_at"] = datetime.now().isoformat()
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
