"""
PySide6 action editor dialog for FolderFresh.
Create and configure actions for rules.
"""

from typing import Optional, Callable

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
    StyledComboBox,
    StyledLineEdit,
    StyledLabel,
    HeadingLabel,
    MutedLabel,
    VerticalFrame,
    HorizontalFrame,
    CardFrame,
)


# Action types with descriptions
ACTION_TYPES = {
    "Rename File": "Rename a file to a new name",
    "Move to Folder": "Move file to a folder (supports tokens for dynamic paths like <year>/<month>)",
    "Copy to Folder": "Copy file to a folder (supports tokens for dynamic paths like <year>/<month>)",
    "Delete File": "Permanently delete the file",
    "Rename with Tokens": "Rename using tokens: <name>, <extension>, <date_created>, <date_modified>, <year>, <month>, <day>, <hour>, <minute>, <date_created_year>, <date_created_month>, <date_created_day>, <date_modified_year>, <date_modified_month>, <date_modified_day>",
    "Run Command": "Execute a script or command on the file",
    "Archive to ZIP": "Create a ZIP archive from the file",
    "Extract Archive": "Extract archive file to a folder",
    "Create Folder": "Create a folder with optional tokens",
    "Set Color Label": "Apply a color label to the file",
    "Add Tag": "Add a tag to the file metadata",
    "Remove Tag": "Remove a tag from the file",
    "Delete to Trash": "Send file to recycle bin (safe delete)",
    "Mark as Duplicate": "Mark file as a duplicate",
}

# Parameter labels for each action
ACTION_PARAMETERS = {
    "Rename File": "New name (without extension)",
    "Move to Folder": "Destination path with optional tokens (e.g., /archive/<year>/<month>)",
    "Copy to Folder": "Destination path with optional tokens (e.g., /backup/<year>/<month>)",
    "Delete File": "",
    "Rename with Tokens": "Pattern with tokens (e.g., <date_modified>_<name><extension>)",
    "Run Command": "Command to execute",
    "Archive to ZIP": "Destination path",
    "Extract Archive": "Destination folder",
    "Create Folder": "Folder path pattern",
    "Set Color Label": "Color name",
    "Add Tag": "Tag name",
    "Remove Tag": "Tag name",
    "Delete to Trash": "",
    "Mark as Duplicate": "Duplicate method (quick/full)",
}


class ActionEditor(QDialog):
    """Dialog for creating and editing actions."""

    # Signals
    action_created = Signal(dict)  # {"type": str, "parameters": dict}
    cancelled = Signal()

    def __init__(self, parent=None, on_action_created: Optional[Callable] = None):
        """
        Initialize action editor.

        Args:
            parent: Parent widget
            on_action_created: Optional callback for action creation (legacy support)
        """
        super().__init__(parent)
        self.setWindowTitle("Create New Action")
        self.setGeometry(200, 200, 500, 400)
        self.setMinimumWidth(400)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.on_action_created = on_action_created
        self.selected_action_type = None

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("Create a New Action")
        main_layout.addWidget(title)

        # Action type selection
        type_frame = VerticalFrame(spacing=8)
        type_label = StyledLabel("Action Type:", font_size=Fonts.SIZE_NORMAL, bold=True)
        type_frame.add_widget(type_label)

        self.type_combo = StyledComboBox(list(ACTION_TYPES.keys()))
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_frame.add_widget(self.type_combo)

        main_layout.addWidget(type_frame)

        # Parameter input section
        self.param_frame = CardFrame()
        param_layout = VerticalFrame(spacing=8)

        self.param_label = StyledLabel(
            ACTION_PARAMETERS[list(ACTION_TYPES.keys())[0]],
            font_size=Fonts.SIZE_SMALL,
        )
        param_layout.add_widget(self.param_label)

        self.param_entry = StyledLineEdit(placeholder="Enter parameter value")
        self.param_entry.textChanged.connect(self._update_preview)
        param_layout.add_widget(self.param_entry)

        self.param_frame.setLayout(param_layout.layout)
        main_layout.addWidget(self.param_frame)

        # Preview section
        preview_frame = CardFrame()
        preview_layout = VerticalFrame(spacing=8)
        preview_label = StyledLabel("Preview:", font_size=Fonts.SIZE_SMALL, bold=True)
        preview_layout.add_widget(preview_label)
        self.preview_text = StyledLabel("", font_size=Fonts.SIZE_NORMAL)
        self.preview_text.setWordWrap(True)
        self.preview_text.setStyleSheet(f"color: {Colors.ACCENT};")
        preview_layout.add_widget(self.preview_text)
        preview_frame.setLayout(preview_layout.layout)
        main_layout.addWidget(preview_frame)

        # Description area
        desc_frame = VerticalFrame(spacing=8)
        desc_label = StyledLabel("Description:", font_size=Fonts.SIZE_SMALL, bold=True)
        desc_frame.add_widget(desc_label)

        self.desc_text = StyledLabel(
            ACTION_TYPES[list(ACTION_TYPES.keys())[0]],
            font_size=Fonts.SIZE_SMALL,
        )
        self.desc_text.setWordWrap(True)
        self.desc_text.setStyleSheet(f"color: {Colors.MUTED};")
        desc_frame.add_widget(self.desc_text)

        main_layout.addWidget(desc_frame)

        # Spacer
        main_layout.addStretch()

        # Buttons
        button_frame = HorizontalFrame(spacing=8)

        create_btn = StyledButton("Add Action", bg_color=Colors.SUCCESS)
        create_btn.clicked.connect(self._on_create_action)
        button_frame.add_widget(create_btn)

        cancel_btn = StyledButton("Cancel", bg_color=Colors.BORDER_LIGHT)
        cancel_btn.clicked.connect(self._on_cancel)
        button_frame.add_widget(cancel_btn)

        main_layout.addWidget(button_frame)

        # Set initial selection
        self._on_type_changed(0)

    def _on_type_changed(self, index: int) -> None:
        """Handle action type selection change."""
        action_type = self.type_combo.currentText()
        self.selected_action_type = action_type

        # Update parameter label
        param_label = ACTION_PARAMETERS.get(action_type, "")
        if param_label:
            self.param_label.setText(param_label)
            self.param_entry.setVisible(True)
        else:
            self.param_label.setText("(No parameters required)")
            self.param_entry.setVisible(False)

        # Update description
        self.desc_text.setText(ACTION_TYPES.get(action_type, ""))

        # Update preview
        self._update_preview()

    def _update_preview(self) -> None:
        """Update the preview display based on current action and parameter."""
        if not self.selected_action_type:
            self.preview_text.setText("Select an action to see preview")
            return

        parameter = self.param_entry.text().strip() if self.param_entry.isVisible() else ""
        preview = self._format_action_preview(parameter)
        self.preview_text.setText(preview)

    def _format_action_preview(self, parameter: str) -> str:
        """Format action for preview display with parameter."""
        action_type = self.selected_action_type or "Unknown"

        # Truncate long commands for display
        display_param = parameter
        if len(display_param) > 50:
            display_param = display_param[:50] + "..."

        # Format the display text
        if parameter:
            return f"{action_type}: {display_param}"
        else:
            return action_type

    def _on_create_action(self) -> None:
        """Create action and emit signal."""
        action_type = self.type_combo.currentText()
        parameter = self.param_entry.text().strip() if self.param_entry.isVisible() else ""

        action_data = {
            "type": action_type,
            "parameters": parameter,
        }

        # Emit signal
        self.action_created.emit(action_data)

        # Legacy callback support
        if self.on_action_created:
            self.on_action_created(action_data)

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
