"""
PySide6 rule editor dialog for FolderFresh.
Create and edit rules with conditions and actions.
"""

from typing import Optional, List, Dict, Any, Callable

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    StyledComboBox,
    StyledLineEdit,
    StyledCheckBox,
    StyledLabel,
    HeadingLabel,
    MutedLabel,
    CardFrame,
    VerticalFrame,
    HorizontalFrame,
    ScrollableFrame,
)
from .action_editor import ActionEditor
from .condition_editor import ConditionEditor


class RuleEditor(QDialog):
    """Dialog for creating and editing rules."""

    # Signals
    rule_saved = Signal(dict)  # Rule data
    cancelled = Signal()

    def __init__(self, parent=None, on_rule_saved: Optional[Callable] = None):
        """
        Initialize rule editor.

        Args:
            parent: Parent widget
            on_rule_saved: Optional callback for rule saving (legacy support)
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Rule")
        self.setGeometry(150, 150, 700, 850)
        self.setMinimumSize(600, 700)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.on_rule_saved = on_rule_saved

        # Rule data
        self.rule_name = ""
        self.match_mode = "all"  # "all" or "any"
        self.stop_on_match = False
        self.conditions: List[Dict[str, Any]] = []
        self.actions: List[Dict[str, Any]] = []

        self.selected_condition_index = None
        self.selected_action_index = None
        self.condition_frames: List[QFrame] = []
        self.action_frames: List[QFrame] = []

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("Edit Rule")
        main_layout.addWidget(title)

        # Name section
        name_frame = VerticalFrame(spacing=8)
        name_label = StyledLabel("Rule Name:", font_size=Fonts.SIZE_NORMAL, bold=True)
        name_frame.add_widget(name_label)

        self.name_entry = StyledLineEdit(placeholder="e.g., Archive Old Screenshots")
        self.name_entry.textChanged.connect(lambda text: setattr(self, "rule_name", text))
        name_frame.add_widget(self.name_entry)

        main_layout.addWidget(name_frame)

        # Match mode section
        mode_frame = VerticalFrame(spacing=8)
        mode_label = StyledLabel("Match Mode:", font_size=Fonts.SIZE_NORMAL, bold=True)
        mode_frame.add_widget(mode_label)

        self.mode_combo = StyledComboBox(["all (AND)", "any (OR)"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_frame.add_widget(self.mode_combo)

        help_text = MutedLabel(
            "ALL: File must match all conditions  |  ANY: File must match at least one condition"
        )
        mode_frame.add_widget(help_text)

        main_layout.addWidget(mode_frame)

        # Stop on match section
        self.stop_check = StyledCheckBox("Stop on match", checked=False)
        self.stop_check.stateChanged.connect(lambda: setattr(self, "stop_on_match", self.stop_check.isChecked()))
        main_layout.addWidget(self.stop_check)

        # Conditions section
        self._create_conditions_section(main_layout)

        # Actions section
        self._create_actions_section(main_layout)

        # Spacer
        main_layout.addStretch()

        # Buttons
        button_frame = HorizontalFrame(spacing=8)

        test_btn = StyledButton("Test Rule", bg_color=Colors.ACCENT)
        test_btn.clicked.connect(self._on_test_rule)
        button_frame.add_widget(test_btn)

        save_btn = StyledButton("Save & Close", bg_color=Colors.SUCCESS)
        save_btn.clicked.connect(self._on_save)
        button_frame.add_widget(save_btn)

        cancel_btn = StyledButton("Cancel", bg_color=Colors.BORDER_LIGHT)
        cancel_btn.clicked.connect(self._on_cancel)
        button_frame.add_widget(cancel_btn)

        main_layout.addWidget(button_frame)

    def _create_conditions_section(self, parent_layout) -> None:
        """Create conditions list section."""
        section_frame = VerticalFrame(spacing=8)

        section_label = StyledLabel("Conditions:", font_size=Fonts.SIZE_NORMAL, bold=True)
        section_frame.add_widget(section_label)

        # Conditions list (scrollable)
        self.conditions_scroll = ScrollableFrame()
        section_frame.add_widget(self.conditions_scroll)

        # Add/Delete buttons
        button_row = HorizontalFrame(spacing=8)

        add_btn = StyledButton("+ Add Condition", bg_color=Colors.ACCENT)
        add_btn.clicked.connect(self._on_add_condition)
        button_row.add_widget(add_btn)

        delete_btn = StyledButton("- Delete Condition", bg_color=Colors.DANGER)
        delete_btn.clicked.connect(self._on_delete_condition)
        button_row.add_widget(delete_btn)

        button_row.add_stretch()
        section_frame.add_widget(button_row)

        parent_layout.addWidget(section_frame)

    def _create_actions_section(self, parent_layout) -> None:
        """Create actions list section."""
        section_frame = VerticalFrame(spacing=8)

        section_label = StyledLabel("Actions:", font_size=Fonts.SIZE_NORMAL, bold=True)
        section_frame.add_widget(section_label)

        # Actions list (scrollable)
        self.actions_scroll = ScrollableFrame()
        section_frame.add_widget(self.actions_scroll)

        # Add/Delete buttons
        button_row = HorizontalFrame(spacing=8)

        add_btn = StyledButton("+ Add Action", bg_color=Colors.ACCENT)
        add_btn.clicked.connect(self._on_add_action)
        button_row.add_widget(add_btn)

        delete_btn = StyledButton("- Delete Action", bg_color=Colors.DANGER)
        delete_btn.clicked.connect(self._on_delete_action)
        button_row.add_widget(delete_btn)

        button_row.add_stretch()
        section_frame.add_widget(button_row)

        parent_layout.addWidget(section_frame)

    def _on_mode_changed(self, index: int) -> None:
        """Handle match mode change."""
        self.match_mode = "all" if index == 0 else "any"

    def _on_add_condition(self) -> None:
        """Open condition editor."""
        editor = ConditionEditor(self, self._on_condition_created)
        editor.exec()

    def _on_condition_created(self, condition_data: Dict[str, Any]) -> None:
        """Handle condition creation."""
        self.conditions.append(condition_data)
        self._refresh_conditions_display()

    def _on_delete_condition(self) -> None:
        """Delete selected condition."""
        if self.selected_condition_index is not None:
            del self.conditions[self.selected_condition_index]
            self.selected_condition_index = None
            self._refresh_conditions_display()

    def _refresh_conditions_display(self) -> None:
        """Refresh conditions list display."""
        self.conditions_scroll.clear()
        self.condition_frames.clear()

        for i, condition in enumerate(self.conditions):
            row_frame = self._create_condition_row(i, condition)
            self.conditions_scroll.add_widget(row_frame)

    def _create_condition_row(self, index: int, condition: Dict[str, Any]) -> QFrame:
        """Create a condition display row."""
        row_frame = CardFrame()
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(10, 8, 10, 8)
        row_layout.setSpacing(12)

        # Condition text with parameters
        condition_type = condition.get("type", "")
        condition_display = self._format_condition_display(condition)
        condition_text = StyledLabel(condition_display, font_size=Fonts.SIZE_NORMAL)
        condition_text.setWordWrap(True)
        row_layout.addWidget(condition_text, 1)

        # Make row clickable for selection
        row_frame.setCursor(Qt.PointingHandCursor)

        def on_click():
            self.selected_condition_index = index
            self._highlight_condition(index)

        row_frame.mousePressEvent = lambda e: on_click()

        self.condition_frames.append(row_frame)
        return row_frame

    def _highlight_condition(self, index: int) -> None:
        """Highlight selected condition."""
        for i, frame in enumerate(self.condition_frames):
            if i == index:
                frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Colors.ACCENT};
                        border: 2px solid {Colors.ACCENT};
                        border-radius: 6px;
                    }}
                """)
            else:
                frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Colors.CARD_BG};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 6px;
                    }}
                """)

    def _on_add_action(self) -> None:
        """Open action editor."""
        editor = ActionEditor(self, self._on_action_created)
        editor.exec()

    def _on_action_created(self, action_data: Dict[str, Any]) -> None:
        """Handle action creation."""
        self.actions.append(action_data)
        self._refresh_actions_display()

    def _on_delete_action(self) -> None:
        """Delete selected action."""
        if self.selected_action_index is not None:
            del self.actions[self.selected_action_index]
            self.selected_action_index = None
            self._refresh_actions_display()

    def _refresh_actions_display(self) -> None:
        """Refresh actions list display."""
        self.actions_scroll.clear()
        self.action_frames.clear()

        for i, action in enumerate(self.actions):
            row_frame = self._create_action_row(i, action)
            self.actions_scroll.add_widget(row_frame)

    def _create_action_row(self, index: int, action: Dict[str, Any]) -> QFrame:
        """Create an action display row."""
        row_frame = CardFrame()
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(10, 8, 10, 8)
        row_layout.setSpacing(12)

        # Action text with parameters
        action_type = action.get("type", "")
        action_display = self._format_action_display(action)
        action_text = StyledLabel(action_display, font_size=Fonts.SIZE_NORMAL)
        action_text.setWordWrap(True)
        row_layout.addWidget(action_text, 1)

        # Make row clickable for selection
        row_frame.setCursor(Qt.PointingHandCursor)

        def on_click():
            self.selected_action_index = index
            self._highlight_action(index)

        row_frame.mousePressEvent = lambda e: on_click()

        self.action_frames.append(row_frame)
        return row_frame

    def _highlight_action(self, index: int) -> None:
        """Highlight selected action."""
        for i, frame in enumerate(self.action_frames):
            if i == index:
                frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Colors.SUCCESS};
                        border: 2px solid {Colors.SUCCESS};
                        border-radius: 6px;
                    }}
                """)
            else:
                frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Colors.CARD_BG};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 6px;
                    }}
                """)

    def _validate_rule(self) -> tuple[bool, str]:
        """
        Validate rule for completeness.

        Returns:
            (is_valid, error_message)
        """
        # Conditions that don't require parameters (both display names and internal camelCase names)
        PARAM_FREE_CONDITIONS = {
            # Display names (with spaces)
            "is hidden", "is read-only", "is directory",
            # Internal camelCase names (from backend)
            "ishidden", "isreadonly", "isdirectory"
        }

        # Actions that don't require parameters
        PARAM_FREE_ACTIONS = {
            "delete file", "delete to trash"
        }

        # Check rule name
        if not self.rule_name or not self.rule_name.strip():
            return False, "Rule name is required. Please enter a name for this rule."

        # Check at least one action
        if not self.actions:
            return False, "At least one action is required.\n\nAdd an action that describes what to do with matched files."

        # Validate all conditions have parameters (if they require them)
        for i, condition in enumerate(self.conditions):
            cond_type = condition.get("type", "")
            cond_params = condition.get("parameters", condition.get("args", {}))

            if not cond_type:
                return False, f"Condition {i + 1} has no type selected."

            # Normalize type for comparison: handle both display names and internal names
            cond_type_normalized = cond_type.lower().replace(" ", "").replace("-", "")

            # Check if this condition is in the param-free list
            # Match both "is read-only" -> "isreadonly" and "IsReadOnly" -> "isreadonly"
            is_param_free = False
            for param_free_name in PARAM_FREE_CONDITIONS:
                if param_free_name.replace(" ", "").replace("-", "") == cond_type_normalized:
                    is_param_free = True
                    break

            if not is_param_free:
                # Check that condition has parameters
                if not cond_params or (isinstance(cond_params, dict) and not any(cond_params.values())):
                    return False, f"Condition {i + 1} ({cond_type}) is missing required parameters."

        # Validate all actions have parameters (if they require them)
        for i, action in enumerate(self.actions):
            action_type = action.get("type", "")
            action_params = action.get("parameters", action.get("args", {}))

            if not action_type:
                return False, f"Action {i + 1} has no type selected."

            # Skip parameter check for actions that don't require parameters
            action_type_lower = action_type.lower()
            if action_type_lower not in PARAM_FREE_ACTIONS:
                if not action_params or (isinstance(action_params, dict) and not any(action_params.values())):
                    if isinstance(action_params, str):
                        if not action_params.strip():
                            return False, f"Action {i + 1} ({action_type}) is missing required parameters."
                    else:
                        return False, f"Action {i + 1} ({action_type}) is missing required parameters."

        return True, ""

    def _on_save(self) -> None:
        """Save rule and emit signal."""
        # Validate rule before saving
        is_valid, error_message = self._validate_rule()
        if not is_valid:
            from .dialogs import show_error_dialog
            show_error_dialog(self, "Cannot Save Rule", error_message)
            return

        # Normalize conditions: convert "parameters" to "args" for backend compatibility
        normalized_conditions = []
        for cond in self.conditions:
            normalized_cond = {
                "type": cond.get("type", ""),
                "args": cond.get("parameters", cond.get("args", {}))
            }
            normalized_conditions.append(normalized_cond)

        # Normalize actions: convert display names to internal names and convert string parameters to dicts
        normalized_actions = []
        for action in self.actions:
            action_type = action.get("type", "")
            action_params = action.get("parameters", action.get("args", {}))

            # Convert action display names to internal names using the mapping
            from folderfresh.rule_engine.rule_store import ACTION_DISPLAY_NAME_TO_INTERNAL
            internal_action_type = ACTION_DISPLAY_NAME_TO_INTERNAL.get(action_type, action_type)

            # Convert string parameters to proper dict format based on action type
            if isinstance(action_params, str):
                # ActionEditor stores parameters as strings, need to convert to dicts
                action_args = self._convert_action_parameters(internal_action_type, action_params)
            else:
                # Already a dict (from backend or pre-normalized)
                action_args = action_params

            normalized_action = {
                "type": internal_action_type,
                "args": action_args
            }
            normalized_actions.append(normalized_action)

        rule_data = {
            "name": self.rule_name,
            "match_mode": self.match_mode,
            "stop_on_match": self.stop_on_match,
            "conditions": normalized_conditions,
            "actions": normalized_actions,
        }

        self.rule_saved.emit(rule_data)

        if self.on_rule_saved:
            self.on_rule_saved(rule_data)

        self.accept()

    def _on_test_rule(self) -> None:
        """Open rule simulator dialog."""
        if not self.rule_name:
            from .dialogs import show_warning_dialog
            show_warning_dialog(self, "Rule Name Required", "Please enter a rule name before testing.")
            return

        from .rule_simulator import RuleSimulator
        from folderfresh.rule_engine.rule_store import ACTION_DISPLAY_NAME_TO_INTERNAL, DISPLAY_NAME_TO_INTERNAL

        # Normalize conditions: convert display names and "parameters" to "args" for backend compatibility
        normalized_conditions = []
        for cond in self.conditions:
            cond_type = cond.get("type", "")
            cond_params = cond.get("parameters", cond.get("args", {}))

            # Convert condition display names to internal names using the mapping
            internal_cond_type = DISPLAY_NAME_TO_INTERNAL.get(cond_type, cond_type)

            normalized_cond = {
                "type": internal_cond_type,
                "args": cond_params
            }
            normalized_conditions.append(normalized_cond)

        # Normalize actions: convert display names to internal names and convert string parameters to dicts
        normalized_actions = []
        for action in self.actions:
            action_type = action.get("type", "")
            action_params = action.get("parameters", action.get("args", {}))

            # Convert action display names to internal names using the mapping
            internal_action_type = ACTION_DISPLAY_NAME_TO_INTERNAL.get(action_type, action_type)

            # Convert string parameters to proper dict format based on action type
            if isinstance(action_params, str):
                # ActionEditor stores parameters as strings, need to convert to dicts
                action_args = self._convert_action_parameters(internal_action_type, action_params)
            else:
                # Already a dict (from backend or pre-normalized)
                action_args = action_params

            normalized_action = {
                "type": internal_action_type,
                "args": action_args
            }
            normalized_actions.append(normalized_action)

        # Collect rule data with normalized format
        rule_data = {
            "name": self.rule_name,
            "match_mode": "all" if self.match_mode == "all (AND)" else "any",
            "stop_on_match": self.stop_on_match,
            "conditions": normalized_conditions,
            "actions": normalized_actions,
        }

        # Create and show simulator
        simulator = RuleSimulator(self, rule_name=self.rule_name)
        simulator.set_rule_info(rule_data)
        simulator.exec()

    def _on_cancel(self) -> None:
        """Handle cancel button."""
        self.cancelled.emit()
        self.reject()

    def closeEvent(self, event):
        """Handle window close event."""
        self.cancelled.emit()
        self.reject()
        event.accept()

    # ========== DISPLAY FORMATTING ==========

    def _format_condition_display(self, condition: Dict[str, Any]) -> str:
        """Format condition for display with parameters in user-friendly format."""
        cond_type = condition.get("type", "Unknown")

        # Get parameters from either "parameters" or "args" key
        parameters = None
        if "parameters" in condition:
            if isinstance(condition["parameters"], dict):
                parameters = condition["parameters"]
        elif "args" in condition:
            if isinstance(condition["args"], dict):
                parameters = condition["args"]

        # Handle dict-based parameters (both "parameters" and "args" formats)
        if parameters:
            parts = []
            for label, value in parameters.items():
                if value and value != "":  # Skip empty values
                    if isinstance(value, bool):
                        if value:
                            parts.append(label.rstrip(":"))
                    else:
                        # Convert bytes to MB for display if this is a file size condition
                        display_value = value
                        if cond_type == "File Size > X bytes" and label == "min_bytes" and isinstance(value, int):
                            # Convert bytes to MB for display
                            mb_value = value / (1024 * 1024)
                            # Round to 2 decimal places and remove trailing zeros
                            display_value = f"{mb_value:.2f}".rstrip('0').rstrip('.') + " MB"
                        parts.append(f"{display_value}")
            if parts:
                return f"{cond_type}: {', '.join(parts)}"
            else:
                return cond_type

        # Fallback for old structure with flat parameters in condition dict
        param = ""
        if "value" in condition:
            param = str(condition["value"])
        elif "pattern" in condition:
            param = str(condition["pattern"])
        elif "size_bytes" in condition:
            # Convert bytes to MB for display
            size_bytes = condition["size_bytes"]
            if isinstance(size_bytes, int):
                mb_value = size_bytes / (1024 * 1024)
                param = f"{mb_value:.2f}".rstrip('0').rstrip('.') + " MB"
            else:
                param = str(size_bytes)
        elif "days" in condition:
            param = str(condition["days"])
        elif "date" in condition:
            param = str(condition["date"])
        elif "color" in condition:
            param = str(condition["color"])
        elif "tag" in condition:
            param = str(condition["tag"])
        elif "content" in condition:
            param = str(condition["content"])

        # Format the display text
        if param:
            return f"{cond_type}: {param}"
        else:
            return cond_type

    def _format_action_display(self, action: Dict[str, Any]) -> str:
        """Format action for display with parameters in user-friendly format."""
        action_type = action.get("type", "Unknown")

        # Get parameters from either "parameters" or "args" key
        parameters = None
        if "parameters" in action:
            param_value = action["parameters"]
            if isinstance(param_value, dict):
                parameters = param_value
            elif isinstance(param_value, str):
                # String format (for simple actions like command or single parameter)
                if param_value:
                    # Truncate long commands for display
                    display_param = param_value
                    if len(display_param) > 50:
                        display_param = display_param[:50] + "..."
                    return f"{action_type}: {display_param}"
                else:
                    return action_type
        elif "args" in action:
            if isinstance(action["args"], dict):
                parameters = action["args"]

        # Handle dict-based parameters
        if parameters:
            parts = []
            for param_name, value in parameters.items():
                if value and value != "":  # Skip empty values
                    # Truncate long values for display
                    display_value = str(value)
                    if len(display_value) > 40:
                        display_value = display_value[:40] + "..."
                    parts.append(display_value)
            if parts:
                return f"{action_type}: {', '.join(parts)}"
            else:
                return action_type

        # Fallback for old structure with flat parameters in action dict
        param = ""
        if "destination" in action:
            param = str(action["destination"])
        elif "name_template" in action:
            param = str(action["name_template"])
        elif "command" in action:
            # Truncate long commands
            cmd = str(action["command"])
            param = cmd[:50] + "..." if len(cmd) > 50 else cmd
        elif "target_dir" in action:
            param = str(action["target_dir"])
        elif "folder_path" in action:
            param = str(action["folder_path"])
        elif "tag" in action:
            param = str(action["tag"])
        elif "color" in action:
            param = str(action["color"])

        # Format the display text
        if param:
            return f"{action_type}: {param}"
        else:
            return action_type

    def _convert_action_parameters(self, action_type: str, param_string: str) -> Dict[str, Any]:
        """
        Convert string parameter from ActionEditor to dict format expected by backend.

        Args:
            action_type: Internal action type name (e.g., "Rename", "Move", "Copy", "Delete", etc.)
            param_string: String parameter value from ActionEditor

        Returns:
            Dict with correct parameter names for the action class
        """
        # Map internal action type names to their parameter names
        param_mappings = {
            # Tier 0 actions
            "Rename": {"param_key": "new_name"},
            "Move": {"param_key": "target_dir"},
            "Copy": {"param_key": "target_dir"},
            "Delete": {"param_key": None},  # Delete takes no parameters
            # Tier 1 actions
            "TokenRename": {"param_key": "name_pattern"},
            "RunCommand": {"param_key": "command"},
            "Archive": {"param_key": "target_dir"},
            "Extract": {"param_key": "target_dir"},
            "CreateFolder": {"param_key": "folder_path"},
            # Tier 2 actions
            "AddTag": {"param_key": "tag"},
            "RemoveTag": {"param_key": "tag"},
            "DeleteToTrash": {"param_key": None},  # DeleteToTrash takes no parameters
            "MarkAsDuplicate": {"param_key": "method"},
        }

        mapping = param_mappings.get(action_type, {})
        param_key = mapping.get("param_key")

        if param_key is None:
            # No parameters for this action (e.g., Delete, DeleteToTrash)
            return {}
        else:
            # Return dict with the correct parameter name
            return {param_key: param_string}

    # ========== PUBLIC API ==========

    def load_rule(self, rule_data: Dict[str, Any]) -> None:
        """Load rule data into editor."""
        self.rule_name = rule_data.get("name", "")
        self.name_entry.setText(self.rule_name)

        self.match_mode = rule_data.get("match_mode", "all")
        mode_index = 0 if self.match_mode == "all" else 1
        self.mode_combo.setCurrentIndex(mode_index)

        self.stop_on_match = rule_data.get("stop_on_match", False)
        self.stop_check.setChecked(self.stop_on_match)

        self.conditions = rule_data.get("conditions", [])
        self._refresh_conditions_display()

        self.actions = rule_data.get("actions", [])
        self._refresh_actions_display()

    def get_rule(self) -> Dict[str, Any]:
        """Get rule data."""
        return {
            "name": self.rule_name,
            "match_mode": self.match_mode,
            "stop_on_match": self.stop_on_match,
            "conditions": self.conditions,
            "actions": self.actions,
        }
