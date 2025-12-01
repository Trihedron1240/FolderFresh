"""
PySide6 profile manager window for FolderFresh.
Two-pane interface for managing multiple profiles.
"""

from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QFrame,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    DangerButton,
    StyledLineEdit,
    StyledTextEdit,
    StyledCheckBox,
    HeadingLabel,
    MutedLabel,
    StyledLabel,
    VerticalFrame,
    HorizontalFrame,
    CardFrame,
    ScrollableFrame,
)
from .dialogs import ask_text_dialog, show_confirmation_dialog, show_info_dialog, show_warning_dialog, show_error_dialog
from .category_manager import CategoryManagerWindow
from .category_manager_backend import CategoryManagerBackend
from folderfresh.profile_store import ProfileStore
from folderfresh.logger_qt import log_error


class ProfileManagerWindow(QDialog):
    """Dialog for managing profiles with sidebar and editor pane."""

    # Signals
    profile_selected = Signal(str)  # Emits profile ID
    profile_created = Signal(str)  # Emits new profile ID
    profile_deleted = Signal(str)  # Emits deleted profile ID
    profile_renamed = Signal(str, str)  # Emits (profile_id, new_name)
    profile_duplicated = Signal(str)  # Emits new profile ID
    active_profile_changed = Signal(str)  # Emits active profile ID
    profile_changed = Signal()  # Emits when any profile changes
    customize_categories_requested = Signal(str)  # Emits profile ID
    manage_rules_requested = Signal(str)  # Emits profile ID
    profile_update_requested = Signal(str, dict)  # Emits (profile_id, updates_dict)
    profile_update_silent_requested = Signal(str, dict)  # Emits (profile_id, updates_dict) without dialog
    set_active_requested = Signal(str)  # Emits profile_id
    closed = Signal()

    def __init__(self, parent=None, profiles: List[Dict[str, Any]] = None, active_profile_id: str = None):
        """
        Initialize profile manager.

        Args:
            parent: Parent widget
            profiles: List of profile dictionaries
            active_profile_id: ID of currently active profile
        """
        super().__init__(parent)
        self.setWindowTitle("Manage Profiles")
        self.setGeometry(200, 100, 1000, 700)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.selected_profile_id: Optional[str] = None
        self.profile_list_items: Dict[str, CardFrame] = {}
        self.profile_store = ProfileStore()
        self.open_category_windows: Dict[str, CategoryManagerWindow] = {}
        self.open_rules_windows: Dict[str, Any] = {}  # Stores RuleManager windows

        self._init_ui()

    def _get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all profiles directly from disk."""
        doc = self.profile_store.load()
        return {p["id"]: p for p in doc.get("profiles", [])}

    def _get_active_profile_id(self) -> str:
        """Get active profile ID directly from disk."""
        doc = self.profile_store.load()
        return doc.get("active_profile_id", "profile_default")

    def _set_active_profile_id(self, profile_id: str) -> None:
        """Set active profile ID directly to disk."""
        doc = self.profile_store.load()
        doc["active_profile_id"] = profile_id
        self.profile_store.save(doc)

    def _load_profile_from_disk(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a single profile from disk (source of truth).

        Args:
            profile_id: Profile ID to load

        Returns:
            Profile dict or None if not found
        """
        try:
            doc = self.profile_store.load()
            for p in doc.get("profiles", []):
                if p["id"] == profile_id:
                    # Return directly from disk, no caching
                    return p
        except Exception as e:
            log_error(f"Failed to load profile {profile_id} from disk: {e}")
        return None

    def _init_ui(self) -> None:
        """Initialize UI with splitter."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("Manage Profiles")
        main_layout.addWidget(title)

        # Splitter for sidebar + editor
        splitter = QSplitter(Qt.Horizontal)

        # Left sidebar (profile list)
        sidebar_widget = QFrame()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(8)

        # Sidebar buttons
        sidebar_buttons = HorizontalFrame(spacing=6)

        new_btn = StyledButton("+ New", bg_color=Colors.ACCENT)
        new_btn.clicked.connect(self._on_new_profile)
        sidebar_buttons.add_widget(new_btn)

        import_btn = StyledButton("Import", bg_color=Colors.ACCENT)
        import_btn.clicked.connect(self._on_import_profiles)
        sidebar_buttons.add_widget(import_btn)

        export_btn = StyledButton("Export", bg_color=Colors.ACCENT)
        export_btn.clicked.connect(self._on_export_profile)
        sidebar_buttons.add_widget(export_btn)

        sidebar_layout.addWidget(sidebar_buttons)

        # Profile list (scrollable)
        self.profiles_scroll = ScrollableFrame(spacing=6)
        sidebar_layout.addWidget(self.profiles_scroll, 1)

        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setMaximumWidth(280)
        splitter.addWidget(sidebar_widget)

        # Right editor pane
        self.editor_scroll = ScrollableFrame(spacing=12)
        splitter.addWidget(self.editor_scroll)

        # Set splitter proportions
        splitter.setSizes([280, 700])
        splitter.setCollapsible(0, False)

        main_layout.addWidget(splitter, 1)

        # Bottom buttons
        bottom_buttons = HorizontalFrame(spacing=8)
        bottom_buttons.add_stretch()

        close_btn = StyledButton("Close", bg_color=Colors.BORDER_LIGHT)
        close_btn.clicked.connect(self._on_close)
        bottom_buttons.add_widget(close_btn)

        main_layout.addWidget(bottom_buttons)

        # Render initial state
        self._refresh_profile_list()

    def refresh_profiles(self, profiles: List[Dict[str, Any]] = None) -> None:
        """
        Refresh profile list from disk.

        Args:
            profiles: Ignored, always loads from disk
        """
        self._refresh_profile_list()

    def _refresh_profile_list(self) -> None:
        """Rebuild profile list from disk."""
        self.profiles_scroll.clear()
        self.profile_list_items.clear()

        profiles = self._get_all_profiles()
        for profile_id in sorted(profiles.keys(), key=lambda pid: profiles[pid].get("name", "")):
            self._create_profile_list_item(profile_id)

        self.profiles_scroll.add_stretch()

    def _create_profile_list_item(self, profile_id: str) -> None:
        """
        Create a profile list item.

        Args:
            profile_id: Profile ID
        """
        profiles = self._get_all_profiles()
        profile = profiles.get(profile_id, {})
        profile_name = profile.get("name", "Unknown")

        # Main item frame
        item_frame = CardFrame()
        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(12, 12, 12, 12)
        item_layout.setSpacing(8)

        # Profile name label
        name_label = StyledLabel(
            profile_name,
            font_size=Fonts.SIZE_NORMAL,
            bold=True,
        )
        item_layout.addWidget(name_label, 1)

        # Active indicator
        if profile_id == self._get_active_profile_id():
            active_label = MutedLabel("(active)")
            active_label.setMaximumWidth(80)
            item_layout.addWidget(active_label)

        # Menu button
        menu_btn = StyledButton("⋯", bg_color=Colors.BORDER_LIGHT)
        menu_btn.setMaximumWidth(40)
        menu_btn.clicked.connect(lambda: self._show_profile_menu(profile_id))
        item_layout.addWidget(menu_btn)

        item_frame.setLayout(item_layout)

        # Make clickable for selection
        item_frame.setCursor(Qt.PointingHandCursor)
        item_frame.profile_id = profile_id
        item_frame.mousePressEvent = lambda event: self._on_profile_clicked(profile_id)

        # Highlight if selected
        if profile_id == self.selected_profile_id:
            item_frame.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {Colors.ACCENT};
                    border-radius: 8px;
                    border: 2px solid {Colors.ACCENT};
                }}
                QLabel {{
                    color: white;
                }}
                """
            )

        self.profiles_scroll.add_widget(item_frame)
        self.profile_list_items[profile_id] = item_frame

    def _on_profile_clicked(self, profile_id: str) -> None:
        """Handle profile selection."""
        self.selected_profile_id = profile_id
        self.profile_selected.emit(profile_id)
        self._refresh_profile_list()
        self._render_editor_pane(profile_id)

    def _show_profile_menu(self, profile_id: str) -> None:
        """Show context menu for profile."""
        # Simplified menu - in real app would use QMenu
        profiles = self._get_all_profiles()
        profile = profiles.get(profile_id, {})
        is_builtin = profile.get("is_builtin", False)

        # For now, just show quick action buttons
        # A full implementation would use QMenu for popup
        self._on_profile_clicked(profile_id)

    def _reload_editor_if_selected(self, profile_id: str) -> None:
        """
        Reload editor pane if the given profile is currently selected.
        Called when data for a profile changes (e.g., categories).

        Args:
            profile_id: Profile ID that changed
        """
        if profile_id == self.selected_profile_id:
            self._render_editor_pane(profile_id)

    def _render_editor_pane(self, profile_id: str) -> None:
        """
        Render profile editor in right pane.

        Args:
            profile_id: Profile to edit
        """
        self.editor_scroll.clear()

        # Load profile from disk (source of truth)
        profile = self._load_profile_from_disk(profile_id)

        if not profile:
            self.editor_scroll.add_widget(
                StyledLabel("No profile selected", font_size=Fonts.SIZE_SMALL)
            )
            return

        # Profile name section
        name_section = VerticalFrame(spacing=8)

        name_label = StyledLabel("Profile Name:", font_size=Fonts.SIZE_NORMAL, bold=True)
        name_section.add_widget(name_label)

        name_entry = StyledLineEdit(
            placeholder="Profile name",
            font_size=Fonts.SIZE_NORMAL,
        )
        name_entry.setText(profile.get("name", ""))
        name_section.add_widget(name_entry)

        self.editor_scroll.add_widget(name_section)

        # Description section
        desc_section = VerticalFrame(spacing=8)

        desc_label = StyledLabel("Description:", font_size=Fonts.SIZE_NORMAL, bold=True)
        desc_section.add_widget(desc_label)

        desc_entry = StyledTextEdit()
        desc_entry.setPlainText(profile.get("description", ""))
        desc_entry.setMaximumHeight(100)
        desc_section.add_widget(desc_entry)

        self.editor_scroll.add_widget(desc_section)

        # Info section
        info_section = VerticalFrame(spacing=6)

        info_label = StyledLabel("Profile Info:", font_size=Fonts.SIZE_NORMAL, bold=True)
        info_section.add_widget(info_label)

        info_text = f"""ID: {profile.get('id', 'unknown')}
Created: {profile.get('created_at', 'unknown')}
Updated: {profile.get('updated_at', 'unknown')}
Type: {'Built-in' if profile.get('is_builtin') else 'Custom'}"""

        info_display = MutedLabel(info_text)
        info_display.setWordWrap(True)
        info_section.add_widget(info_display)

        self.editor_scroll.add_widget(info_section)

        # Rule fallback setting section
        fallback_section = VerticalFrame(spacing=8)

        fallback_label = StyledLabel("Rule Fallback Behavior:", font_size=Fonts.SIZE_NORMAL, bold=True)
        fallback_section.add_widget(fallback_label)

        fallback_check = StyledCheckBox(
            "Fall back to category sort on rule failure",
            checked=profile.get("settings", {}).get("rule_fallback_to_sort", True)
        )
        fallback_check.stateChanged.connect(
            lambda state: self._on_fallback_changed(profile_id, fallback_check)
        )
        fallback_section.add_widget(fallback_check)

        fallback_help = MutedLabel(
            "When enabled: Failed rules fall back to category sorting.\n"
            "When disabled: Failed rules stop processing."
        )
        fallback_help.setWordWrap(True)
        fallback_section.add_widget(fallback_help)

        self.editor_scroll.add_widget(fallback_section)

        # Action buttons
        action_section = HorizontalFrame(spacing=8)

        dup_btn = StyledButton("Duplicate", bg_color=Colors.ACCENT)
        dup_btn.clicked.connect(lambda: self._on_duplicate_profile(profile_id))
        action_section.add_widget(dup_btn)

        if not profile.get("is_builtin", False):
            del_btn = DangerButton("Delete")
            del_btn.clicked.connect(lambda: self._on_delete_profile(profile_id))
            action_section.add_widget(del_btn)

        if profile_id != self._get_active_profile_id():
            activate_btn = StyledButton("Set Active", bg_color=Colors.SUCCESS)
            activate_btn.clicked.connect(lambda: self._on_set_active(profile_id))
            action_section.add_widget(activate_btn)

        customize_btn = StyledButton("Customise Categories", bg_color=Colors.ACCENT)
        customize_btn.clicked.connect(lambda: self._on_customize_categories(profile_id))
        action_section.add_widget(customize_btn)

        manage_rules_btn = StyledButton("Manage Rules", bg_color=Colors.ACCENT)
        manage_rules_btn.clicked.connect(lambda: self._on_manage_rules(profile_id))
        action_section.add_widget(manage_rules_btn)

        action_section.add_stretch()

        self.editor_scroll.add_widget(action_section)

        # Save button
        save_btn = StyledButton("Save Changes", bg_color=Colors.SUCCESS)
        save_btn.clicked.connect(
            lambda: self._on_save_profile(profile_id, name_entry, desc_entry)
        )
        self.editor_scroll.add_widget(save_btn)

        self.editor_scroll.add_stretch()

    def _on_new_profile(self) -> None:
        """Create new profile."""
        name = ask_text_dialog(
            self,
            title="New Profile",
            label="Enter profile name:",
            default_text="My Profile",
        )

        if not name:
            return

        # Create new profile dict
        import time
        new_id = f"profile_{int(time.time())}"

        new_profile = {
            "id": new_id,
            "name": name,
            "description": "",
            "rules": [],
            "created_at": "",  # Backend will set
            "updated_at": "",  # Backend will set
            "is_builtin": False,
        }

        # Save directly to disk (don't cache in memory)
        doc = self.profile_store.load()
        doc["profiles"].append(new_profile)
        self.profile_store.save(doc)

        self._refresh_profile_list()
        self.profile_created.emit(name)

    def _on_rename_profile(self, profile_id: str, name_entry: StyledLineEdit) -> None:
        """Rename profile."""
        new_name = name_entry.text().strip()

        if not new_name:
            show_warning_dialog(self, "Rename", "Profile name cannot be empty.")
            return

        # Load fresh from disk
        doc = self.profile_store.load()
        old_name = None
        for p in doc.get("profiles", []):
            if p["id"] == profile_id:
                old_name = p["name"]
                p["name"] = new_name
                p["updated_at"] = datetime.now().isoformat()
                break

        if old_name:
            self.profile_store.save(doc)
            self._refresh_profile_list()
            self.profile_renamed.emit(profile_id, new_name)
            show_info_dialog(self, "Renamed", f"Profile '{old_name}' renamed to '{new_name}'.")

    def _on_fallback_changed(self, profile_id: str, checkbox: StyledCheckBox) -> None:
        """Handle fallback checkbox change - emit silent signal for backend to handle."""
        updates = {
            "settings": {
                "rule_fallback_to_sort": checkbox.isChecked()
            }
        }
        self.profile_update_silent_requested.emit(profile_id, updates)

    def _on_duplicate_profile(self, profile_id: str) -> None:
        """Duplicate profile."""
        # Load from disk
        profiles = self._get_all_profiles()
        source = profiles.get(profile_id)
        if not source:
            return

        # Emit signal with SOURCE profile ID - let backend handle the actual duplication
        self.profile_duplicated.emit(profile_id)
        # Backend will handle duplication and emit profile_created signal

    def _on_delete_profile(self, profile_id: str) -> None:
        """Delete profile."""
        # Load from disk
        profiles = self._get_all_profiles()
        profile = profiles.get(profile_id)
        if not profile:
            return

        if profile.get("is_builtin", False):
            show_warning_dialog(self, "Protected", "Cannot delete built-in profile.")
            return

        if not show_confirmation_dialog(
            self,
            "Delete Profile",
            f"Delete profile '{profile.get('name')}'?",
        ):
            return

        # Delete from disk
        doc = self.profile_store.load()
        doc["profiles"] = [p for p in doc.get("profiles", []) if p["id"] != profile_id]
        self.profile_store.save(doc)

        # Update active profile if needed
        remaining_profiles = self._get_all_profiles()
        if profile_id == self._get_active_profile_id() and remaining_profiles:
            new_active = next(iter(remaining_profiles.keys()))
            self._set_active_profile_id(new_active)

        self.selected_profile_id = None
        self._refresh_profile_list()
        self.editor_scroll.clear()
        self.profile_deleted.emit(profile_id)

    def _on_set_active(self, profile_id: str) -> None:
        """Set profile as active - emit signal for backend to handle."""
        self.set_active_requested.emit(profile_id)

    def _on_customize_categories(self, profile_id: str) -> None:
        """Open category customization dialog for profile."""
        # Check if window already open for this profile
        if profile_id in self.open_category_windows:
            # Bring existing window to front
            window = self.open_category_windows[profile_id]
            window.raise_()
            window.activateWindow()
            return

        # Create backend for this profile
        backend = CategoryManagerBackend(profile_id)

        # Create and show category manager window
        category_window = CategoryManagerWindow(
            parent=self,
            backend=backend,
            profile_id=profile_id
        )

        # Store reference to keep window alive
        self.open_category_windows[profile_id] = category_window

        # When categories change, reload the editor pane if this profile is selected
        category_window.categories_changed.connect(
            lambda: self._reload_editor_if_selected(profile_id)
        )

        # Connect close signal to clean up reference
        category_window.closed.connect(lambda: self.open_category_windows.pop(profile_id, None))

        # Show the window (non-modal so user can keep profile manager open)
        category_window.show()

        # Emit signal for any external handlers
        self.customize_categories_requested.emit(profile_id)

    def _on_manage_rules(self, profile_id: str) -> None:
        """Open rule manager for profile."""
        # Check if window already open for this profile
        if profile_id in self.open_rules_windows:
            # Bring existing window to front
            window = self.open_rules_windows[profile_id]
            window.raise_()
            window.activateWindow()
            return

        # Import here to avoid circular imports
        from .rule_manager import RuleManager

        # Create and show rule manager window
        profiles = self._get_all_profiles()
        rules_window = RuleManager(
            parent=self,
            profile_id=profile_id,
            profile_name=profiles.get(profile_id, {}).get("name", "Unknown")
        )

        # Store reference to keep window alive
        self.open_rules_windows[profile_id] = rules_window

        # Connect close signal to clean up reference
        if hasattr(rules_window, 'closed'):
            rules_window.closed.connect(lambda: self.open_rules_windows.pop(profile_id, None))

        # Show the window (non-modal so user can keep profile manager open)
        rules_window.show()

        # Emit signal for any external handlers
        self.manage_rules_requested.emit(profile_id)

    def _on_save_profile(
        self,
        profile_id: str,
        name_entry: StyledLineEdit,
        desc_entry: StyledTextEdit,
    ) -> None:
        """Save profile changes - emit signal for backend to handle."""
        new_name = name_entry.text().strip()
        new_desc = desc_entry.toPlainText().strip()

        if not new_name:
            show_warning_dialog(self, "Save", "Profile name cannot be empty.")
            return

        updates = {
            "name": new_name,
            "description": new_desc
        }
        self.profile_update_requested.emit(profile_id, updates)

    def _on_import_profiles(self) -> None:
        """Import profiles from a JSON file."""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Profiles",
            "",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            # Load and validate file
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "profiles" not in data:
                show_error_dialog(
                    self,
                    "Import Error",
                    "Invalid file. Must contain a 'profiles' key."
                )
                return

            # Load current document from store
            doc = self.profile_store.load()

            # Import profiles with new IDs
            for profile in data["profiles"]:
                # Generate new ID to avoid conflicts
                profile["id"] = f"profile_{int(datetime.now().timestamp())}"
                doc["profiles"].append(profile)

            # Save updated document
            self.profile_store.save(doc)

            # Refresh profile list from disk
            self._refresh_profile_list()

            show_info_dialog(
                self,
                "Import Successful",
                f"Imported {len(data['profiles'])} profile(s)."
            )

        except json.JSONDecodeError:
            show_error_dialog(
                self,
                "Import Error",
                "Invalid JSON file format."
            )
        except Exception as e:
            show_error_dialog(
                self,
                "Import Error",
                f"Failed to import profiles: {str(e)}"
            )

    def _on_export_profile(self) -> None:
        """Export the currently selected profile to a JSON file."""
        if not self.selected_profile_id:
            show_warning_dialog(
                self,
                "No Profile Selected",
                "Please select a profile to export."
            )
            return

        profiles = self._get_all_profiles()
        profile = profiles.get(self.selected_profile_id)
        if not profile:
            return

        # Open save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Profile",
            f"{profile.get('name', 'profile')}.json",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            # Export profile as JSON
            export_data = {"profiles": [profile]}

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            show_info_dialog(
                self,
                "Export Successful",
                f"Profile exported to:\n{file_path}"
            )

        except Exception as e:
            show_error_dialog(
                self,
                "Export Error",
                f"Failed to export profile: {str(e)}"
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

    def set_profiles(self, profiles: List[Dict[str, Any]] = None) -> None:
        """
        Refresh profiles list from disk.

        Args:
            profiles: Ignored, always loads from disk
        """
        self.selected_profile_id = None
        self._refresh_profile_list()

    def get_profiles(self) -> List[Dict[str, Any]]:
        """Get all profiles directly from disk."""
        return list(self._get_all_profiles().values())

    def set_active_profile(self, profile_id: str) -> None:
        """Set active profile."""
        self._set_active_profile_id(profile_id)
        self._refresh_profile_list()
