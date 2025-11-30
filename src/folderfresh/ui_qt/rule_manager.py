"""
PySide6 rule manager window for FolderFresh.
Manage rules for a profile with CRUD operations and ordering.
"""

from pathlib import Path
from typing import Optional, Dict, List, Any

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
    HeadingLabel,
    MutedLabel,
    StyledLabel,
    VerticalFrame,
    HorizontalFrame,
    CardFrame,
    ScrollableFrame,
)
from .dialogs import ask_text_dialog, show_confirmation_dialog, show_warning_dialog
from .rule_editor import RuleEditor
from folderfresh.profile_store import ProfileStore


class RuleManager(QDialog):
    """Dialog for managing rules in a profile."""

    # Signals
    rule_selected = Signal(str)  # Emits rule name when rule is selected
    rule_added = Signal(str)  # Emits new rule name
    rule_deleted = Signal(str)  # Emits deleted rule name
    rule_reordered = Signal()  # Emits when rule order changes
    closed = Signal()

    def __init__(self, parent=None, profile_id: str = None, profile_name: str = "Default", initial_rules: List[Dict[str, Any]] = None):
        """
        Initialize rule manager.

        Args:
            parent: Parent widget
            profile_id: ID of the profile being managed
            profile_name: Name of the profile being managed
            initial_rules: List of rule dictionaries with 'name', 'conditions', 'actions' (optional, will load from store if not provided)
        """
        super().__init__(parent)
        self.setWindowTitle(f"Rule Manager - {profile_name}")
        self.setGeometry(300, 100, 400, 700)
        self.setMinimumSize(300, 500)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.profile_id = profile_id
        self.profile_name = profile_name
        self.profile_store = ProfileStore()
        self.selected_rule_index: Optional[int] = None
        self.rule_frames: List[CardFrame] = []

        # Load rules from profile store if profile_id provided, otherwise use initial_rules
        if profile_id:
            self.rules = self.profile_store.get_rules_for_profile_id(profile_id)
        else:
            self.rules = initial_rules or []

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel(f"Rules - {self.profile_name}")
        main_layout.addWidget(title)

        # Priority help text
        help_text = MutedLabel("Rules run top to bottom.\nOrder = priority.")
        help_text.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(help_text)

        # Scrollable rule list
        self.rules_scroll = ScrollableFrame(spacing=6)
        main_layout.addWidget(self.rules_scroll, 1)

        # Button group
        button_frame = VerticalFrame(spacing=6)

        # CRUD buttons
        crud_frame = HorizontalFrame(spacing=6)

        add_btn = StyledButton("+ Add", bg_color=Colors.ACCENT)
        add_btn.clicked.connect(self._on_add_rule)
        crud_frame.add_widget(add_btn)

        delete_btn = DangerButton("- Delete")
        delete_btn.clicked.connect(self._on_delete_rule)
        crud_frame.add_widget(delete_btn)

        up_btn = StyledButton("↑ Up", bg_color=Colors.ACCENT)
        up_btn.setMaximumWidth(80)
        up_btn.clicked.connect(self._on_move_up)
        crud_frame.add_widget(up_btn)

        down_btn = StyledButton("↓ Down", bg_color=Colors.ACCENT)
        down_btn.setMaximumWidth(80)
        down_btn.clicked.connect(self._on_move_down)
        crud_frame.add_widget(down_btn)

        button_frame.add_widget(crud_frame)

        # Close button
        close_btn = StyledButton("Close", bg_color=Colors.BORDER_LIGHT)
        close_btn.clicked.connect(self._on_close)
        button_frame.add_widget(close_btn)

        main_layout.addWidget(button_frame)

        # Render initial rules
        self._refresh_rules_display()

    def _refresh_rules_display(self) -> None:
        """Rebuild the rules list display."""
        # Clear old frames
        self.rules_scroll.clear()
        self.rule_frames.clear()

        # Add new rule frames
        for i, rule in enumerate(self.rules):
            frame = self._create_rule_frame(i, rule)
            self.rule_frames.append(frame)
            self.rules_scroll.add_widget(frame)

        self.rules_scroll.add_stretch()

    def _create_rule_frame(self, index: int, rule: Dict[str, Any]) -> CardFrame:
        """
        Create a rule frame with selection and edit button.

        Args:
            index: Rule index in list
            rule: Rule dictionary

        Returns:
            CardFrame for the rule
        """
        frame = CardFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Rule name label - clickable for selection
        rule_name = rule.get("name", "Unnamed Rule")
        label = StyledLabel(
            rule_name,
            font_size=Fonts.SIZE_NORMAL,
            bold=True,
        )
        layout.addWidget(label, 1)

        # Edit button
        edit_btn = StyledButton("Edit", bg_color=Colors.ACCENT)
        edit_btn.setMaximumWidth(60)
        edit_btn.clicked.connect(lambda: self._on_rule_clicked(index))
        layout.addWidget(edit_btn)

        # Make frame selectable by clicking on it
        frame.setCursor(Qt.PointingHandCursor)
        frame.rule_index = index
        frame.mousePressEvent = lambda event: self._on_rule_selected(index)

        # Apply highlight if selected
        if index == self.selected_rule_index:
            frame.setStyleSheet(
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
        else:
            frame.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {Colors.CARD_BG};
                    border-radius: 8px;
                    border: 1px solid {Colors.BORDER};
                }}
                """
            )

        return frame

    def _on_rule_selected(self, index: int) -> None:
        """Handle rule selection for deletion/management."""
        if not (0 <= index < len(self.rules)):
            return

        self.selected_rule_index = index
        self._refresh_rules_display()

    def _on_rule_clicked(self, index: int) -> None:
        """Handle rule edit button - opens rule editor."""
        if not (0 <= index < len(self.rules)):
            return

        self.selected_rule_index = index
        rule = self.rules[index]

        # Create and show rule editor
        editor = RuleEditor(self, on_rule_saved=self._on_rule_saved)
        editor.load_rule(rule)
        editor.rule_saved.connect(lambda rule_data: self._on_rule_saved(rule_data))
        editor.exec()

    def _on_add_rule(self) -> None:
        """Add a new rule."""
        name = ask_text_dialog(
            self,
            title="New Rule",
            label="Enter rule name:",
            default_text="My Rule",
        )

        if not name:
            return

        # Create new rule dict
        new_rule = {
            "name": name,
            "conditions": [],
            "actions": [],
            "match_mode": "all",
            "stop_on_match": False,
        }

        self.rules.append(new_rule)

        # Save to profile store if profile_id is set
        if self.profile_id:
            self._save_rules_to_store()

        self._refresh_rules_display()

        # Auto-select new rule
        self.selected_rule_index = len(self.rules) - 1
        self._refresh_rules_display()

        self.rule_added.emit(name)

    def _on_delete_rule(self) -> None:
        """Delete the selected rule."""
        if self.selected_rule_index is None:
            show_warning_dialog(
                self,
                "Delete Rule",
                "Please select a rule first.",
            )
            return

        rule = self.rules[self.selected_rule_index]
        rule_name = rule.get("name", "Unknown")

        if not show_confirmation_dialog(
            self,
            "Delete Rule",
            f"Delete rule '{rule_name}'?",
        ):
            return

        self.rules.pop(self.selected_rule_index)

        # Save to profile store if profile_id is set
        if self.profile_id:
            self._save_rules_to_store()

        self.rule_deleted.emit(rule_name)

        self.selected_rule_index = None
        self._refresh_rules_display()

    def _on_move_up(self) -> None:
        """Move selected rule up."""
        index = self.selected_rule_index

        if index is None or index == 0:
            show_warning_dialog(
                self,
                "Move Up",
                "Cannot move the first rule up.",
            )
            return

        # Swap rules
        self.rules[index - 1], self.rules[index] = self.rules[index], self.rules[index - 1]
        self.selected_rule_index = index - 1

        # Save to profile store if profile_id is set
        if self.profile_id:
            self._save_rules_to_store()

        self.rule_reordered.emit()
        self._refresh_rules_display()

    def _on_move_down(self) -> None:
        """Move selected rule down."""
        index = self.selected_rule_index

        if index is None or index >= len(self.rules) - 1:
            show_warning_dialog(
                self,
                "Move Down",
                "Cannot move the last rule down.",
            )
            return

        # Swap rules
        self.rules[index + 1], self.rules[index] = self.rules[index], self.rules[index + 1]
        self.selected_rule_index = index + 1

        # Save to profile store if profile_id is set
        if self.profile_id:
            self._save_rules_to_store()

        self.rule_reordered.emit()
        self._refresh_rules_display()

    def _on_rule_saved(self, rule_data: Dict[str, Any]) -> None:
        """Handle rule saved from editor."""
        if self.selected_rule_index is not None and 0 <= self.selected_rule_index < len(self.rules):
            # Update the rule in the list
            self.rules[self.selected_rule_index] = rule_data
            # Save to profile store if profile_id is set
            if self.profile_id:
                self._save_rules_to_store()
            # Refresh display to show updated rule
            self._refresh_rules_display()

    def _save_rules_to_store(self) -> None:
        """Save current rules to profile store for this profile."""
        if not self.profile_id:
            return
        try:
            # Save rules directly - ProfileStore handles both dicts and Rule objects
            self.profile_store.set_rules(self.rules, profile_id=self.profile_id)
        except Exception as e:
            # Silently fail to avoid disrupting UI - rules are still in memory
            pass

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

    def set_rules(self, rules: List[Dict[str, Any]]) -> None:
        """
        Set the rules list.

        Args:
            rules: List of rule dictionaries
        """
        self.rules = rules
        self.selected_rule_index = None
        self._refresh_rules_display()

    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Get current rules list.

        Returns:
            List of rule dictionaries
        """
        return self.rules

    def get_selected_rule_index(self) -> Optional[int]:
        """Get currently selected rule index."""
        return self.selected_rule_index

    def update_rule(self, index: int, rule_data: Dict[str, Any]) -> None:
        """
        Update a rule at given index.

        Args:
            index: Rule index
            rule_data: Updated rule dictionary
        """
        if 0 <= index < len(self.rules):
            self.rules[index] = rule_data
            self._refresh_rules_display()
