"""
PySide6 condition selector popup for FolderFresh.
Categorized list of available conditions for easy selection.
"""

from typing import Callable

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
    StyledLabel,
    HeadingLabel,
    ScrollableFrame,
    HorizontalFrame,
)


# Condition categories and items
CONDITION_CATEGORIES = {
    "Name": [
        "Name Contains",
        "Name Starts With",
        "Name Ends With",
        "Name Equals",
        "Regex Match",
    ],
    "File Properties": [
        "Extension Is",
        "File Size > X bytes",
        "File Age > X days",
        "Last Modified Before",
    ],
    "File Attributes": [
        "Is Hidden",
        "Is Read-Only",
        "Is Directory",
    ],
    "Path": [
        "Parent Folder Contains",
        "File is in folder containing",
    ],
    "Content & Patterns": [
        "Content Contains",
        "Date Pattern",
    ],
    "Metadata & Tags": [
        "Color Is",
        "Has Tag",
        "Metadata Contains",
        "Metadata Field Equals",
        "Is Duplicate",
    ],
}


class ConditionSelectorPopup(QDialog):
    """Dialog displaying categorized list of available conditions."""

    # Signals
    condition_selected = Signal(str)  # condition_name

    def __init__(self, parent=None, on_condition_selected: Callable = None):
        """
        Initialize condition selector.

        Args:
            parent: Parent widget
            on_condition_selected: Optional callback for selection (legacy support)
        """
        super().__init__(parent)
        self.setWindowTitle("Select Condition Type")
        self.setGeometry(300, 300, 350, 600)
        self.setMinimumSize(320, 500)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.on_condition_selected = on_condition_selected

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("Select Condition Type")
        main_layout.addWidget(title)

        # Scrollable condition list
        self.condition_scroll = ScrollableFrame()
        self._build_condition_list()
        main_layout.addWidget(self.condition_scroll, 1)

        # Close button
        button_frame = HorizontalFrame(spacing=8)
        button_frame.add_stretch()

        close_btn = StyledButton("Close", bg_color=Colors.BORDER_LIGHT)
        close_btn.clicked.connect(self.reject)
        button_frame.add_widget(close_btn)

        main_layout.addWidget(button_frame)

    def _build_condition_list(self) -> None:
        """Build the categorized condition list."""
        for category_name, conditions in CONDITION_CATEGORIES.items():
            # Category header
            category_label = StyledLabel(
                category_name,
                font_size=Fonts.SIZE_HEADING,
                bold=True,
            )
            category_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {Colors.ACCENT};
                    padding: 8px 0px 4px 0px;
                    background-color: {Colors.PANEL_ALT};
                    padding-left: 8px;
                    border-radius: 4px;
                }}
            """
            )
            self.condition_scroll.add_widget(category_label)

            # Condition items
            for condition_name in conditions:
                item_btn = self._create_condition_item(condition_name)
                self.condition_scroll.add_widget(item_btn)

            # Spacing between categories
            spacing_frame = QFrame()
            spacing_frame.setMinimumHeight(4)
            self.condition_scroll.add_widget(spacing_frame)

    def _create_condition_item(self, condition_name: str) -> QFrame:
        """
        Create a clickable condition item.

        Args:
            condition_name: Name of the condition

        Returns:
            Frame widget for the condition item
        """
        item_frame = QFrame()
        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(8, 6, 8, 6)
        item_layout.setSpacing(0)

        item_label = StyledLabel(condition_name, font_size=Fonts.SIZE_NORMAL)
        item_label.setCursor(Qt.PointingHandCursor)
        item_layout.addWidget(item_label)

        # Styling
        item_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {Colors.CARD_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
            QFrame:hover {{
                background-color: {Colors.HOVER_BG};
                border: 1px solid {Colors.BORDER_LIGHT};
            }}
        """
        )

        # Make frame clickable
        item_frame.setCursor(Qt.PointingHandCursor)

        def on_click():
            self.condition_selected.emit(condition_name)
            if self.on_condition_selected:
                self.on_condition_selected(condition_name)
            self.accept()

        item_frame.mousePressEvent = lambda e: on_click()

        return item_frame

    def closeEvent(self, event):
        """Handle window close event."""
        self.reject()
        event.accept()
