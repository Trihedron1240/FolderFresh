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
from .dialogs import show_confirmation_dialog, show_info_dialog


class CategoryManagerWindow(QDialog):
    """Dialog for managing file categories and mappings."""

    # Signals
    categories_changed = Signal()
    closed = Signal()

    def __init__(
        self,
        parent=None,
        profile_name: str = "Default",
        categories: Dict[str, List[str]] = None,
        overrides: Dict[str, str] = None,
        enabled: Dict[str, bool] = None,
    ):
        """
        Initialize category manager.

        Args:
            parent: Parent widget
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

        self.profile_name = profile_name
        self.categories = categories or {}
        self.overrides = overrides or {}
        self.enabled = enabled or {cat: True for cat in self.categories.keys()}

        # Track editing widgets
        self.category_rows: Dict[str, Dict[str, Any]] = {}

        self._init_ui()

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

        row_layout.addLayout(top_row)

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

        # Save button
        save_btn = StyledButton("Save", bg_color=Colors.SUCCESS)
        save_btn.setMaximumWidth(100)
        save_btn.clicked.connect(
            lambda: self._on_save_category(
                category_name,
                enabled_check,
                override_entry,
                ext_entry,
            )
        )
        ext_row.add_widget(save_btn)

        row_layout.addLayout(ext_row)

        # Add to scroll area
        self.categories_scroll.add_widget(row_frame)

        # Store references
        self.category_rows[category_name] = {
            "frame": row_frame,
            "enabled_check": enabled_check,
            "override_entry": override_entry,
            "ext_entry": ext_entry,
        }

    def _on_save_category(
        self,
        category_name: str,
        enabled_check: StyledCheckBox,
        override_entry: StyledLineEdit,
        ext_entry: StyledLineEdit,
    ) -> None:
        """
        Save category changes.

        Args:
            category_name: Category to save
            enabled_check: Enabled checkbox widget
            override_entry: Override name entry widget
            ext_entry: Extensions entry widget
        """
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

        # Update internal state
        self.enabled[category_name] = is_enabled

        if override_name:
            self.overrides[category_name] = override_name
        else:
            self.overrides.pop(category_name, None)

        if extensions:
            self.categories[category_name] = extensions

        # Emit signal
        self.categories_changed.emit()

        # Show confirmation
        show_info_dialog(
            self,
            "Category Saved",
            f"Category '{category_name}' has been updated.",
        )

    def _on_restore_defaults(self) -> None:
        """Restore default categories."""
        if not show_confirmation_dialog(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all categories to their default settings?",
        ):
            return

        # Clear overrides and reset to defaults
        # This would be set by parent during initialization
        self.overrides.clear()
        self.enabled = {cat: True for cat in self.categories.keys()}

        # Re-render
        self._render_categories()

        self.categories_changed.emit()

        show_info_dialog(
            self,
            "Restored",
            "Categories have been reset to defaults.",
        )

    def _on_close(self) -> None:
        """Handle close button."""
        self.closed.emit()
        self.accept()

    def closeEvent(self, event) -> None:
        """Handle window close."""
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
