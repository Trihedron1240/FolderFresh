"""
PySide6 category manager window for FolderFresh.
Manage file categories and custom mappings per profile.
"""

from typing import Dict, List, Optional, Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)
from PySide6.QtCore import Qt, Signal

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    DangerButton,
    StyledLineEdit,
    StyledCheckBox,
    HeadingLabel,
    StyledLabel,
    VerticalFrame,
    HorizontalFrame,
    CardFrame,
    ScrollableFrame,
)
from .dialogs import show_confirmation_dialog, show_info_dialog, show_error_dialog
from .category_manager_backend import CategoryManagerBackend
from folderfresh.constants import CATEGORIES as DEFAULT_CATEGORIES


class CategoryManagerWindow(QDialog):
    """Dialog for managing file categories and mappings."""

    # Signals
    categories_changed = Signal()
    closed = Signal()

    def __init__(
        self,
        parent=None,
        backend: Optional[CategoryManagerBackend] = None,
        profile_id: str = None,
        profile_name: str = "Default",
        categories: Dict[str, List[str]] = None,
        overrides: Dict[str, str] = None,
        enabled: Dict[str, bool] = None,
    ):
        """
        Initialize category manager.

        Args:
            parent: Parent widget
            backend: CategoryManagerBackend instance for data operations
            profile_id: Profile ID being managed
            profile_name: Name of profile being managed
            categories: Dict of category_name -> [extensions]
            overrides: Dict of category_name -> override_name
            enabled: Dict of category_name -> is_enabled
        """
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.setGeometry(200, 100, 900, 800)
        self.setMinimumSize(750, 600)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.backend = backend
        self.profile_id = profile_id
        self.profile_name = profile_name
        self.categories = categories or {}
        self.overrides = overrides or {}
        self.enabled = enabled or {cat: True for cat in self.categories.keys()}

        # Track editing widgets
        self.category_rows: Dict[str, Dict[str, Any]] = {}

        self._init_ui()

        # Load categories from backend if available
        if self.backend:
            self._load_from_backend()

    def _load_from_backend(self) -> None:
        """Load categories from backend."""
        if not self.backend:
            return

        overrides, custom_categories, enabled = self.backend.load_categories()

        # Build complete categories dict using backend helper methods
        # This ensures we get the actual saved extensions, not hardcoded defaults
        self.categories = {}

        # Add all default categories with their actual (potentially overridden) extensions
        for cat in DEFAULT_CATEGORIES.keys():
            self.categories[cat] = self.backend.get_category_extensions(cat)

        # Add custom categories
        self.categories.update(custom_categories)

        # Apply display name overrides
        self.overrides = {}
        for cat, override_data in overrides.items():
            if isinstance(override_data, dict):
                self.overrides[cat] = override_data.get("name", cat)
            else:
                self.overrides[cat] = override_data

        # Set enabled states
        self.enabled = enabled

        # Re-render UI
        self._render_categories()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("Manage Categories")
        main_layout.addWidget(title)

        # Scrollable categories list
        self.categories_scroll = ScrollableFrame(spacing=8)
        main_layout.addWidget(self.categories_scroll, 1)

        # Render categories
        self._render_categories()

        # Button bar
        button_frame = HorizontalFrame(spacing=8)

        add_custom_btn = StyledButton("+ Add Custom Category", bg_color=Colors.SUCCESS)
        add_custom_btn.clicked.connect(self._on_add_custom_category)
        button_frame.add_widget(add_custom_btn)

        restore_btn = DangerButton("Restore Default Categories")
        restore_btn.clicked.connect(self._on_restore_defaults)
        button_frame.add_widget(restore_btn)

        button_frame.add_stretch()

        close_btn = StyledButton("Close", bg_color=Colors.BORDER_LIGHT)
        close_btn.clicked.connect(self._on_close)
        button_frame.add_widget(close_btn)

        main_layout.addWidget(button_frame)

    def _render_categories(self) -> None:
        """Render category rows."""
        self.categories_scroll.clear()
        self.category_rows.clear()

        for category_name in sorted(self.categories.keys()):
            self._create_category_row(category_name)

        self.categories_scroll.add_stretch()

    def _create_category_row(self, category_name: str) -> None:
        """
        Create a category management row.

        Args:
            category_name: Name of the category
        """
        # Main row frame
        row_frame = CardFrame()
        row_layout = QVBoxLayout(row_frame)
        row_layout.setContentsMargins(12, 12, 12, 12)
        row_layout.setSpacing(8)

        # Top row: enabled checkbox and category name
        top_row = HorizontalFrame(spacing=12)

        # Enabled checkbox
        enabled_check = StyledCheckBox(
            "Enabled",
            checked=self.enabled.get(category_name, True),
        )
        enabled_check.setMaximumWidth(100)
        top_row.add_widget(enabled_check)

        # Category name label
        name_label = StyledLabel(
            category_name,
            font_size=Fonts.SIZE_NORMAL,
            bold=True,
        )
        name_label.setMaximumWidth(150)
        top_row.add_widget(name_label)

        # Category display name override
        override_label = StyledLabel("Display name:", font_size=Fonts.SIZE_SMALL)
        top_row.add_widget(override_label)

        override_entry = StyledLineEdit(
            placeholder="Keep original name",
            font_size=Fonts.SIZE_SMALL,
        )
        if category_name in self.overrides:
            override_entry.setText(self.overrides[category_name])
        top_row.add_widget(override_entry, 1)

        row_layout.addWidget(top_row)

        # Bottom row: extensions
        ext_row = HorizontalFrame(spacing=12)

        ext_label = StyledLabel("Extensions:", font_size=Fonts.SIZE_SMALL)
        ext_label.setMaximumWidth(100)
        ext_row.add_widget(ext_label)

        ext_entry = StyledLineEdit(
            placeholder="e.g., jpg;png;gif (semicolon-separated)",
            font_size=Fonts.SIZE_SMALL,
        )
        extensions = self.categories.get(category_name, [])
        ext_entry.setText(";".join(extensions))
        ext_row.add_widget(ext_entry, 1)

        row_layout.addWidget(ext_row)

        # Add to scroll area
        self.categories_scroll.add_widget(row_frame)

        # Store references
        self.category_rows[category_name] = {
            "frame": row_frame,
            "enabled_check": enabled_check,
            "override_entry": override_entry,
            "ext_entry": ext_entry,
        }

    def _save_all_changes(self) -> bool:
        """
        Save all category changes at once.
        Called when the window is closed.

        Returns:
            True if successful, False if errors occurred
        """
        if not self.backend:
            return True

        has_errors = False

        # Process each category row
        for category_name, row_data in self.category_rows.items():
            enabled_check = row_data["enabled_check"]
            override_entry = row_data["override_entry"]
            ext_entry = row_data["ext_entry"]

            # Get values
            is_enabled = enabled_check.isChecked()
            override_name = override_entry.text().strip()
            extensions_text = ext_entry.text().strip()

            # Parse extensions
            if extensions_text:
                extensions = [ext.strip().lower() for ext in extensions_text.split(";")]
                extensions = [ext for ext in extensions if ext]  # Remove empty
            else:
                extensions = []

            # Update enabled state
            if not self.backend.toggle_enabled(category_name, is_enabled):
                show_error_dialog(
                    self,
                    "Error",
                    f"Failed to update enabled state for '{category_name}'."
                )
                has_errors = True
                continue

            # Determine if this is a default or custom category
            is_default = category_name in DEFAULT_CATEGORIES
            is_custom = category_name in self.backend.working_profile.get("custom_categories", {})

            # Save accordingly
            if is_default:
                # For default categories, save with override name and extensions
                if not self.backend.update_default_category(category_name, override_name if override_name else category_name, extensions):
                    show_error_dialog(
                        self,
                        "Error",
                        f"Failed to update default category '{category_name}'."
                    )
                    has_errors = True
                    continue
            elif is_custom:
                # For custom categories, save with new name and extensions
                new_category_name = override_name if override_name else category_name
                if not self.backend.update_custom_category(category_name, new_category_name, extensions):
                    show_error_dialog(
                        self,
                        "Error",
                        f"Failed to update custom category '{category_name}'."
                    )
                    has_errors = True
                    continue

        # Reload from backend to ensure UI is in sync
        self._load_from_backend()

        # Emit signal
        self.categories_changed.emit()

        return not has_errors

    def _on_restore_defaults(self) -> None:
        """Restore default categories."""
        if not show_confirmation_dialog(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all categories to their default settings?",
        ):
            return

        # Restore through backend if available
        if self.backend:
            if not self.backend.restore_defaults():
                show_confirmation_dialog(
                    self,
                    "Error",
                    "Failed to restore default categories."
                )
                return
            # Reload from backend
            self._load_from_backend()
        else:
            # Fallback: clear overrides and reset to defaults
            self.overrides.clear()
            self.enabled = {cat: True for cat in self.categories.keys()}
            self._render_categories()

        self.categories_changed.emit()

        show_info_dialog(
            self,
            "Restored",
            "Categories have been reset to defaults.",
        )

    def _on_add_custom_category(self) -> None:
        """Add a new custom category."""
        from .dialogs import ask_text_dialog

        # Ask for category name
        category_name = ask_text_dialog(
            self,
            title="New Custom Category",
            label="Enter category name (e.g., Documents, Photos):",
            default_text="",
        )

        if not category_name:
            return

        # Check if category already exists
        if category_name in self.categories:
            show_confirmation_dialog(
                self,
                "Duplicate Category",
                f"Category '{category_name}' already exists."
            )
            return

        # Ask for extensions
        extensions_text = ask_text_dialog(
            self,
            title="Category Extensions",
            label="Enter file extensions (semicolon-separated, e.g., .doc;.docx;.pdf):",
            default_text="",
        )

        if not extensions_text:
            return

        # Parse extensions
        extensions = [ext.strip().lower() for ext in extensions_text.split(";")]
        extensions = [ext for ext in extensions if ext]

        if not extensions:
            show_confirmation_dialog(
                self,
                "No Extensions",
                "Please provide at least one file extension."
            )
            return

        # Add through backend if available
        if self.backend:
            if not self.backend.add_custom_category(category_name, extensions):
                show_confirmation_dialog(
                    self,
                    "Error",
                    f"Failed to add custom category '{category_name}'."
                )
                return
            # Reload from backend
            self._load_from_backend()
        else:
            # Fallback: add to local state
            self.categories[category_name] = extensions
            self.enabled[category_name] = True
            self._render_categories()

        self.categories_changed.emit()

        show_info_dialog(
            self,
            "Category Added",
            f"Custom category '{category_name}' added successfully.",
        )

    def _on_close(self) -> None:
        """Handle close button - save all changes and close."""
        self._save_all_changes()
        self.closed.emit()
        self.accept()

    def closeEvent(self, event) -> None:
        """Handle window close - save all changes."""
        self._save_all_changes()
        self.closed.emit()
        self.accept()
        event.accept()

    # ========== PUBLIC METHODS FOR BACKEND INTEGRATION ==========

    def set_categories(self, categories: Dict[str, List[str]]) -> None:
        """
        Set categories.

        Args:
            categories: Dict of category_name -> [extensions]
        """
        self.categories = categories
        self.enabled = {cat: self.enabled.get(cat, True) for cat in categories.keys()}
        self._render_categories()

    def get_categories(self) -> Dict[str, List[str]]:
        """
        Get current categories.

        Returns:
            Dict of category_name -> [extensions]
        """
        return self.categories

    def get_overrides(self) -> Dict[str, str]:
        """
        Get category name overrides.

        Returns:
            Dict of category_name -> override_name
        """
        return self.overrides

    def get_enabled(self) -> Dict[str, bool]:
        """
        Get category enabled states.

        Returns:
            Dict of category_name -> is_enabled
        """
        return self.enabled
