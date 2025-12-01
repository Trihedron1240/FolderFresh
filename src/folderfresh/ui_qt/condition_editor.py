"""
PySide6 condition editor dialog for FolderFresh.
Create and configure conditions with dynamic parameter fields.
"""

from typing import Optional, Callable, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
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
    VerticalFrame,
    HorizontalFrame,
    CardFrame,
)
from .condition_selector import ConditionSelectorPopup


# UI Schema for each condition type
UI_SCHEMA = {
    "Name Contains": [{"label": "Text to search for:", "parameter_name": "substring", "type": "text", "placeholder": "e.g., backup"}],
    "Name Starts With": [{"label": "Text:", "parameter_name": "prefix", "type": "text", "placeholder": "e.g., DSC"}],
    "Name Ends With": [{"label": "Text:", "parameter_name": "suffix", "type": "text", "placeholder": "e.g., final"}],
    "Name Equals": [
        {"label": "Name:", "parameter_name": "value", "type": "text", "placeholder": "e.g., report"},
        {"label": "Case sensitive:", "parameter_name": "case_sensitive", "type": "checkbox"},
    ],
    "Regex Match": [
        {"label": "Pattern:", "parameter_name": "pattern", "type": "text", "placeholder": "e.g., .*\\d+.*"},
        {"label": "Ignore case:", "parameter_name": "ignore_case", "type": "checkbox"},
    ],
    "Extension Is": [{"label": "Extension:", "parameter_name": "extension", "type": "text", "placeholder": "e.g., jpg, pdf"}],
    "File Size > X bytes": [{"label": "Minimum size:", "parameter_name": "min_bytes", "type": "size", "unit": "MB"}],
    "File Age > X days": [{"label": "Minimum age (days):", "parameter_name": "days", "type": "numeric", "placeholder": "e.g., 30"}],
    "Last Modified Before": [{"label": "Date (YYYY-MM-DD):", "parameter_name": "timestamp", "type": "date", "placeholder": "2024-01-01"}],
    "Is Hidden": [],
    "Is Read-Only": [],
    "Is Directory": [],
    "Parent Folder Contains": [{"label": "Text:", "parameter_name": "substring", "type": "text", "placeholder": "e.g., Documents"}],
    "File is in folder containing": [{"label": "Text:", "parameter_name": "folder_pattern", "type": "text", "placeholder": "e.g., Archive"}],
    "Content Contains": [{"label": "Text to search for:", "parameter_name": "keyword", "type": "text", "placeholder": "Search in file content"}],
    "Date Pattern": [
        {"label": "Type:", "type": "dropdown", "options": ["Created", "Modified"]},
        {"label": "Pattern:", "type": "text", "placeholder": "e.g., 2024-*"},
    ],
    "Color Is": [{"label": "Color:", "parameter_name": "color", "type": "dropdown", "options": ["Red", "Blue", "Green", "Yellow"]}],
    "Has Tag": [{"label": "Tag name:", "parameter_name": "tag", "type": "text", "placeholder": "e.g., important"}],
    "Metadata Contains": [
        {"label": "Field name:", "parameter_name": "field", "type": "text", "placeholder": "e.g., author"},
        {"label": "Keyword:", "parameter_name": "keyword", "type": "text", "placeholder": "e.g., John"},
    ],
    "Metadata Field Equals": [
        {"label": "Field name:", "parameter_name": "field", "type": "text", "placeholder": "e.g., status"},
        {"label": "Value:", "parameter_name": "value", "type": "text", "placeholder": "e.g., complete"},
    ],
    "Is Duplicate": [{"label": "Detection method:", "parameter_name": "match_type", "type": "dropdown", "options": ["Quick Hash", "Full Hash"]}],
}

# Descriptions for each condition type
DESCRIPTIONS = {
    "Name Contains": "Matches files whose name contains the specified text (case-insensitive).",
    "Name Starts With": "Matches files whose name starts with the specified text.",
    "Name Ends With": "Matches files whose name ends with the specified text.",
    "Name Equals": "Matches files whose name (without extension) exactly matches the specified text.",
    "Regex Match": "Matches files using regular expression patterns.",
    "Extension Is": "Matches files with the specified file extension.",
    "File Size > X bytes": "Matches files larger than the specified size in MB.",
    "File Age > X days": "Matches files older than the specified number of days.",
    "Last Modified Before": "Matches files last modified before the specified date.",
    "Is Hidden": "Matches files that are marked as hidden.",
    "Is Read-Only": "Matches files that are read-only.",
    "Is Directory": "Matches directories (folders).",
    "Parent Folder Contains": "Matches files in folders whose name contains the text.",
    "File is in folder containing": "Matches files in folders at any depth that contain the text.",
    "Content Contains": "Matches files whose content contains the specified text.",
    "Date Pattern": "Matches files based on date patterns (e.g., 2024-*, *-12-25).",
    "Color Is": "Matches files with the specified color label.",
    "Has Tag": "Matches files with the specified tag.",
    "Metadata Contains": "Matches files whose metadata field contains the keyword.",
    "Metadata Field Equals": "Matches files whose metadata field exactly matches the value.",
    "Is Duplicate": "Matches files that are duplicates based on hash comparison.",
}


class ConditionEditor(QDialog):
    """Dialog for creating and editing conditions."""

    # Signals
    condition_created = Signal(dict)  # {"type": str, "parameters": dict}
    cancelled = Signal()

    def __init__(self, parent=None, on_condition_created: Optional[Callable] = None):
        """
        Initialize condition editor.

        Args:
            parent: Parent widget
            on_condition_created: Optional callback for condition creation (legacy support)
        """
        super().__init__(parent)
        self.setWindowTitle("Create New Condition")
        self.setGeometry(200, 200, 550, 700)
        self.setMinimumWidth(450)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.on_condition_created = on_condition_created
        self.selected_condition_type = None
        self.param_widgets: Dict[str, Any] = {}

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("Create a New Condition")
        main_layout.addWidget(title)

        # Condition type selection
        type_frame = VerticalFrame(spacing=8)
        type_label = StyledLabel("Condition Type:", font_size=Fonts.SIZE_NORMAL, bold=True)
        type_frame.add_widget(type_label)

        btn_frame = HorizontalFrame(spacing=8)
        self.type_display = StyledLabel(
            "Click to select...",
            font_size=Fonts.SIZE_NORMAL,
        )
        btn_frame.add_widget(self.type_display, 1)

        select_btn = StyledButton("Select...", bg_color=Colors.ACCENT)
        select_btn.setMaximumWidth(100)
        select_btn.clicked.connect(self._on_select_type)
        btn_frame.add_widget(select_btn)

        type_frame.add_widget(btn_frame)
        main_layout.addWidget(type_frame)

        # Parameter fields section (dynamically created)
        self.param_frame = CardFrame()
        self.param_layout = VerticalFrame(spacing=10)
        self.param_layout.add_stretch()
        self.param_frame.setLayout(self.param_layout.layout)
        main_layout.addWidget(self.param_frame)

        # Preview section
        preview_frame = CardFrame()
        preview_layout = VerticalFrame(spacing=8)
        preview_label = StyledLabel("Preview:", font_size=Fonts.SIZE_SMALL, bold=True)
        preview_layout.add_widget(preview_label)
        self.preview_text = StyledLabel("Select a condition to see preview", font_size=Fonts.SIZE_NORMAL)
        self.preview_text.setWordWrap(True)
        self.preview_text.setStyleSheet(f"color: {Colors.ACCENT};")
        preview_layout.add_widget(self.preview_text)
        preview_frame.setLayout(preview_layout.layout)
        main_layout.addWidget(preview_frame)

        # Description area
        desc_frame = VerticalFrame(spacing=8)
        desc_label = StyledLabel("About this condition:", font_size=Fonts.SIZE_SMALL, bold=True)
        desc_frame.add_widget(desc_label)

        self.desc_text = MutedLabel("")
        self.desc_text.setWordWrap(True)
        desc_frame.add_widget(self.desc_text)

        main_layout.addWidget(desc_frame)

        # Spacer
        main_layout.addStretch()

        # Buttons
        button_frame = HorizontalFrame(spacing=8)

        create_btn = StyledButton("Add Condition", bg_color=Colors.SUCCESS)
        create_btn.clicked.connect(self._on_create_condition)
        button_frame.add_widget(create_btn)

        cancel_btn = StyledButton("Cancel", bg_color=Colors.BORDER_LIGHT)
        cancel_btn.clicked.connect(self._on_cancel)
        button_frame.add_widget(cancel_btn)

        main_layout.addWidget(button_frame)

    def _on_select_type(self) -> None:
        """Show condition selector popup."""
        selector = ConditionSelectorPopup(self, self._on_condition_selected)
        selector.exec()

    def _on_condition_selected(self, condition_name: str) -> None:
        """
        Handle condition selection from popup.

        Args:
            condition_name: Name of selected condition
        """
        self.selected_condition_type = condition_name
        self.type_display.setText(condition_name)
        self._rebuild_parameter_fields()

    def _rebuild_parameter_fields(self) -> None:
        """Rebuild parameter input fields based on selected condition."""
        # Clear existing widgets
        self.param_widgets.clear()

        # Remove all widgets from param_layout except stretch
        while self.param_layout.layout.count() > 1:
            item = self.param_layout.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get schema for selected condition
        if not self.selected_condition_type:
            self._update_description("")
            return

        schema = UI_SCHEMA.get(self.selected_condition_type, [])

        # Create fields based on schema
        for spec in schema:
            field_type = spec.get("type", "text")
            label = spec.get("label", "")

            if field_type == "text":
                self._create_text_field(label, spec)
            elif field_type == "numeric":
                self._create_numeric_field(label, spec)
            elif field_type == "size":
                self._create_size_field(label, spec)
            elif field_type == "date":
                self._create_date_field(label, spec)
            elif field_type == "dropdown":
                self._create_dropdown_field(label, spec)
            elif field_type == "checkbox":
                self._create_checkbox_field(label, spec)

        # Update description
        self._update_description(self.selected_condition_type)

    def _create_text_field(self, label: str, spec: Dict[str, Any]) -> None:
        """Create text input field."""
        field_name = spec.get("parameter_name", label)
        field_layout = VerticalFrame(spacing=4)

        field_label = StyledLabel(label, font_size=Fonts.SIZE_SMALL)
        field_layout.add_widget(field_label)

        text_input = StyledLineEdit(placeholder=spec.get("placeholder", ""))
        text_input.textChanged.connect(self._update_preview)
        field_layout.add_widget(text_input)

        self.param_widgets[field_name] = text_input
        self.param_layout.layout.insertWidget(len(self.param_widgets) - 1, field_layout)

    def _create_numeric_field(self, label: str, spec: Dict[str, Any]) -> None:
        """Create numeric input field."""
        field_name = spec.get("parameter_name", label)
        field_layout = VerticalFrame(spacing=4)

        field_label = StyledLabel(label, font_size=Fonts.SIZE_SMALL)
        field_layout.add_widget(field_label)

        numeric_input = StyledLineEdit(placeholder=spec.get("placeholder", "0"))
        numeric_input.setValidator(None)  # TODO: Add QIntValidator for numeric validation
        numeric_input.textChanged.connect(self._update_preview)
        field_layout.add_widget(numeric_input)

        self.param_widgets[field_name] = numeric_input
        self.param_layout.layout.insertWidget(len(self.param_widgets) - 1, field_layout)

    def _create_size_field(self, label: str, spec: Dict[str, Any]) -> None:
        """Create size input with unit dropdown (defaults to MB)."""
        field_name = spec.get("parameter_name", label)
        field_layout = VerticalFrame(spacing=4)

        field_label = StyledLabel(label, font_size=Fonts.SIZE_SMALL)
        field_layout.add_widget(field_label)

        input_row = HorizontalFrame(spacing=8)

        size_input = StyledLineEdit(placeholder="0")
        size_input.textChanged.connect(self._update_preview)
        input_row.add_widget(size_input, 1)

        unit_combo = StyledComboBox(["MB", "KB", "GB", "Bytes"])
        unit_combo.setMaximumWidth(100)
        unit_combo.setCurrentIndex(0)  # Default to MB
        unit_combo.currentIndexChanged.connect(self._update_preview)
        input_row.add_widget(unit_combo)

        field_layout.add_widget(input_row)

        self.param_widgets[field_name] = (size_input, unit_combo)
        self.param_layout.layout.insertWidget(len(self.param_widgets) - 1, field_layout)

    def _create_date_field(self, label: str, spec: Dict[str, Any]) -> None:
        """Create date input field."""
        field_name = spec.get("parameter_name", label)
        field_layout = VerticalFrame(spacing=4)

        field_label = StyledLabel(label, font_size=Fonts.SIZE_SMALL)
        field_layout.add_widget(field_label)

        date_input = StyledLineEdit(placeholder=spec.get("placeholder", "YYYY-MM-DD"))
        date_input.textChanged.connect(self._update_preview)
        field_layout.add_widget(date_input)

        self.param_widgets[field_name] = date_input
        self.param_layout.layout.insertWidget(len(self.param_widgets) - 1, field_layout)

    def _create_dropdown_field(self, label: str, spec: Dict[str, Any]) -> None:
        """Create dropdown field."""
        field_name = spec.get("parameter_name", label)
        field_layout = VerticalFrame(spacing=4)

        field_label = StyledLabel(label, font_size=Fonts.SIZE_SMALL)
        field_layout.add_widget(field_label)

        options = spec.get("options", [])
        dropdown = StyledComboBox(options)
        dropdown.currentIndexChanged.connect(self._update_preview)
        field_layout.add_widget(dropdown)

        self.param_widgets[field_name] = dropdown
        self.param_layout.layout.insertWidget(len(self.param_widgets) - 1, field_layout)

    def _create_checkbox_field(self, label: str, spec: Dict[str, Any]) -> None:
        """Create checkbox field."""
        field_name = spec.get("parameter_name", label)
        checkbox = StyledCheckBox(label, checked=False)
        checkbox.stateChanged.connect(self._update_preview)
        self.param_widgets[field_name] = checkbox
        self.param_layout.layout.insertWidget(len(self.param_widgets) - 1, checkbox)

    def _update_description(self, condition_type: str) -> None:
        """Update description based on selected condition."""
        desc = DESCRIPTIONS.get(condition_type, "")
        self.desc_text.setText(desc)

    def _update_preview(self) -> None:
        """Update the preview display based on current parameters."""
        if not self.selected_condition_type:
            self.preview_text.setText("Select a condition to see preview")
            return

        parameters = self._collect_parameters()
        preview = self._format_condition_preview(parameters)
        self.preview_text.setText(preview)

    def _format_condition_preview(self, parameters: Dict[str, Any]) -> str:
        """Format condition for preview display with parameters."""
        cond_type = self.selected_condition_type or "Unknown"

        # Get the main parameter value(s)
        parts = []
        for label, value in parameters.items():
            if value and value != "":  # Skip empty values
                if isinstance(value, bool):
                    if value:
                        parts.append(label.rstrip(":"))
                else:
                    parts.append(f"{label.rstrip(':')}={value}")

        # Format the display text
        if parts:
            return f"{cond_type}: {', '.join(parts)}"
        else:
            return cond_type

    def _collect_parameters(self) -> Dict[str, Any]:
        """
        Collect parameter values from all input fields.

        Returns:
            Dictionary of parameter_name -> value
        """
        parameters = {}

        for field_name, widget in self.param_widgets.items():
            if isinstance(widget, tuple):
                # Size field (input, dropdown)
                value_input, unit_combo = widget
                value = value_input.text()
                unit = unit_combo.currentText()
                parameters[field_name] = f"{value} {unit}"
            elif isinstance(widget, StyledCheckBox):
                parameters[field_name] = widget.isChecked()
            elif isinstance(widget, StyledComboBox):
                parameters[field_name] = widget.currentText()
            elif isinstance(widget, StyledLineEdit):
                parameters[field_name] = widget.text()

        return parameters

    def _on_create_condition(self) -> None:
        """Create condition and emit signal."""
        if not self.selected_condition_type:
            return

        parameters = self._collect_parameters()

        # Convert size to bytes for "File Size > X bytes" condition
        if self.selected_condition_type == "File Size > X bytes" and "min_bytes" in parameters:
            size_str = parameters["min_bytes"]  # e.g., "5 MB"
            try:
                # Parse value and unit
                parts = size_str.strip().split()
                if len(parts) >= 2:
                    value = float(parts[0])
                    unit = parts[1].upper()

                    # Convert to bytes
                    unit_multipliers = {
                        "B": 1,
                        "BYTES": 1,
                        "KB": 1024,
                        "MB": 1024 * 1024,
                        "GB": 1024 * 1024 * 1024,
                    }

                    multiplier = unit_multipliers.get(unit, 1)
                    size_bytes = int(value * multiplier)
                    parameters["min_bytes"] = size_bytes
            except (ValueError, IndexError):
                # If parsing fails, keep the original value
                pass

        # Convert display values to backend values for "Is Duplicate" condition
        if self.selected_condition_type == "Is Duplicate" and "match_type" in parameters:
            match_type_display = parameters["match_type"]  # e.g., "Quick Hash" or "Full Hash"
            if match_type_display == "Quick Hash":
                parameters["match_type"] = "quick"
            elif match_type_display == "Full Hash":
                parameters["match_type"] = "full"

        # Convert display values to backend values for "Color Is" condition
        if self.selected_condition_type == "Color Is" and "color" in parameters:
            color_display = parameters["color"]  # e.g., "Red", "Blue"
            parameters["color"] = color_display.lower()

        condition_data = {
            "type": self.selected_condition_type,
            "parameters": parameters,
        }

        # Emit signal
        self.condition_created.emit(condition_data)

        # Legacy callback support
        if self.on_condition_created:
            self.on_condition_created(condition_data)

        self.accept()

    def _on_cancel(self) -> None:
        """Handle cancel button."""
        self.cancelled.emit()
        self.reject()

    def closeEvent(self, event):
        """Handle window close event."""
        self.cancelled.emit()
        self.reject()
        event.accept()
