"""
PySide6 base widget classes for FolderFresh.
Reusable, pre-styled widgets with consistent theming.
"""

from typing import Optional, Callable, List

from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QCheckBox,
    QComboBox,
    QFrame,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

from .styles import (
    Colors,
    Fonts,
    get_button_stylesheet,
    get_lineedit_stylesheet,
    get_textedit_stylesheet,
    get_combobox_stylesheet,
    get_checkbox_stylesheet,
    get_label_stylesheet,
    get_frame_stylesheet,
    get_scrollbar_stylesheet,
)


# ========== BUTTONS ==========

class StyledButton(QPushButton):
    """Button with FolderFresh styling."""

    def __init__(
        self,
        text: str = "",
        bg_color: str = Colors.ACCENT,
        hover_color: Optional[str] = None,
        text_color: str = Colors.TEXT,
        font_size: int = Fonts.SIZE_NORMAL,
        parent=None,
    ):
        """
        Initialize styled button.

        Args:
            text: Button text
            bg_color: Background color
            hover_color: Hover state color (auto-darkened if None)
            text_color: Text color
            font_size: Font size in points
            parent: Parent widget
        """
        super().__init__(text, parent)
        self.setText(text)
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)

        # Apply styling
        stylesheet = get_button_stylesheet(
            bg_color=bg_color,
            hover_color=hover_color,
            text_color=text_color,
            font_size=font_size,
        )
        self.setStyleSheet(stylesheet)


class SuccessButton(StyledButton):
    """Green success button (for positive actions like Organize)."""

    def __init__(self, text: str = "OK", parent=None):
        super().__init__(
            text=text,
            bg_color=Colors.SUCCESS,
            text_color=Colors.TEXT,
            parent=parent,
        )


class DangerButton(StyledButton):
    """Red danger button (for destructive actions like Delete)."""

    def __init__(self, text: str = "Delete", parent=None):
        super().__init__(
            text=text,
            bg_color=Colors.DANGER,
            text_color=Colors.TEXT,
            parent=parent,
        )


class TealButton(StyledButton):
    """Teal button (for secondary positive actions)."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(
            text=text,
            bg_color=Colors.TEAL,
            text_color=Colors.TEXT,
            parent=parent,
        )


# ========== TEXT INPUTS ==========

class StyledLineEdit(QLineEdit):
    """Text input with FolderFresh styling."""

    def __init__(
        self,
        placeholder: str = "",
        font_size: int = Fonts.SIZE_NORMAL,
        parent=None,
    ):
        """
        Initialize styled line edit.

        Args:
            placeholder: Placeholder text
            font_size: Font size in points
            parent: Parent widget
        """
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(36)

        # Apply styling
        stylesheet = get_lineedit_stylesheet(font_size=font_size)
        self.setStyleSheet(stylesheet)


class StyledTextEdit(QPlainTextEdit):
    """Multi-line text input with FolderFresh styling."""

    def __init__(
        self,
        placeholder: str = "",
        font_size: int = Fonts.SIZE_NORMAL,
        parent=None,
    ):
        """
        Initialize styled text edit.

        Args:
            placeholder: Placeholder text
            font_size: Font size in points
            parent: Parent widget
        """
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(100)

        # Apply styling
        stylesheet = get_textedit_stylesheet(font_size=font_size)
        self.setStyleSheet(stylesheet)
        self.setFont(QFont(Fonts.PRIMARY_FAMILY, font_size))


# ========== DROPDOWNS ==========

class StyledComboBox(QComboBox):
    """Dropdown with FolderFresh styling."""

    def __init__(
        self,
        items: Optional[List[str]] = None,
        font_size: int = Fonts.SIZE_NORMAL,
        parent=None,
    ):
        """
        Initialize styled combo box.

        Args:
            items: List of items to populate
            font_size: Font size in points
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMinimumHeight(36)

        if items:
            self.addItems(items)

        # Apply styling
        stylesheet = get_combobox_stylesheet(font_size=font_size)
        self.setStyleSheet(stylesheet)


# ========== CHECKBOXES ==========

class StyledCheckBox(QCheckBox):
    """Checkbox with FolderFresh styling."""

    def __init__(
        self,
        text: str = "",
        checked: bool = False,
        font_size: int = Fonts.SIZE_NORMAL,
        parent=None,
    ):
        """
        Initialize styled checkbox.

        Args:
            text: Label text
            checked: Initial checked state
            font_size: Font size in points
            parent: Parent widget
        """
        super().__init__(text, parent)
        self.setChecked(checked)
        self.setMinimumHeight(24)

        # Apply styling
        stylesheet = get_checkbox_stylesheet(font_size=font_size)
        self.setStyleSheet(stylesheet)


# ========== LABELS ==========

class StyledLabel(QLabel):
    """Label with FolderFresh styling."""

    def __init__(
        self,
        text: str = "",
        font_size: int = Fonts.SIZE_NORMAL,
        bold: bool = False,
        parent=None,
    ):
        """
        Initialize styled label.

        Args:
            text: Label text
            font_size: Font size in points
            bold: Whether text should be bold
            parent: Parent widget
        """
        super().__init__(text, parent)

        # Apply styling
        stylesheet = get_label_stylesheet(
            font_size=font_size,
            bold=bold,
        )
        self.setStyleSheet(stylesheet)


class TitleLabel(StyledLabel):
    """Large bold title label."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(
            text=text,
            font_size=Fonts.SIZE_TITLE,
            bold=True,
            parent=parent,
        )


class HeadingLabel(StyledLabel):
    """Medium bold heading label."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(
            text=text,
            font_size=Fonts.SIZE_HEADING,
            bold=True,
            parent=parent,
        )


class MutedLabel(StyledLabel):
    """Dimmed text label for secondary information."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(
            text=text,
            font_size=Fonts.SIZE_SMALL,
            parent=parent,
        )
        self.setStyleSheet(
            get_label_stylesheet(
                text_color=Colors.MUTED,
                font_size=Fonts.SIZE_SMALL,
            )
        )


# ========== FRAMES ==========

class CardFrame(QFrame):
    """Card-style frame for grouping content (matching CustomTkinter card design)."""

    def __init__(
        self,
        bg_color: str = Colors.CARD_BG,
        border_color: Optional[str] = None,
        parent=None,
    ):
        """
        Initialize card frame.

        Args:
            bg_color: Background color
            border_color: Border color (None for no border)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)

        # Apply styling
        stylesheet = get_frame_stylesheet(
            bg_color=bg_color,
            border_color=border_color,
            border_width=0 if not border_color else 1,
            border_radius=8,
        )
        self.setStyleSheet(stylesheet)


class SeparatorFrame(QFrame):
    """Horizontal or vertical separator line."""

    def __init__(self, horizontal: bool = True, parent=None):
        """
        Initialize separator.

        Args:
            horizontal: True for horizontal line, False for vertical
            parent: Parent widget
        """
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BORDER};")

        if horizontal:
            self.setFrameStyle(QFrame.HLine | QFrame.Sunken)
            self.setMinimumHeight(1)
            self.setMaximumHeight(1)
        else:
            self.setFrameStyle(QFrame.VLine | QFrame.Sunken)
            self.setMinimumWidth(1)
            self.setMaximumWidth(1)


# ========== SCROLLABLE CONTAINERS ==========

class ScrollableFrame(QScrollArea):
    """Scrollable container matching FolderFresh design."""

    def __init__(self, parent=None, spacing: int = 0):
        """
        Initialize scrollable frame.

        Args:
            parent: Parent widget
            spacing: Spacing between items in layout
        """
        super().__init__(parent)

        # Setup scrollbar styling
        scrollbar_stylesheet = get_scrollbar_stylesheet()
        self.setStyleSheet(scrollbar_stylesheet)

        # Configure scroll area
        self.setWidgetResizable(True)
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: {Colors.PANEL_BG};
                border: none;
            }}
        """
        )

        # Create content widget
        self.content_widget = QFrame()
        self.content_widget.setStyleSheet(
            f"background-color: {Colors.PANEL_BG};"
        )
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(spacing)

        self.setWidget(self.content_widget)

    def add_widget(self, widget) -> None:
        """Add widget to scrollable content."""
        self.content_layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        """Add layout to scrollable content."""
        self.content_layout.addLayout(layout)

    def add_stretch(self) -> None:
        """Add stretch to end of content."""
        self.content_layout.addStretch()

    def clear(self) -> None:
        """Remove all widgets from scrollable content."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ========== CONTAINERS ==========

class HorizontalFrame(QFrame):
    """Horizontal container with pre-configured layout."""

    def __init__(
        self,
        spacing: int = 8,
        bg_color: Optional[str] = None,
        parent=None,
    ):
        """
        Initialize horizontal frame.

        Args:
            spacing: Space between widgets
            bg_color: Background color (None for transparent)
            parent: Parent widget
        """
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(spacing)

        if bg_color:
            self.setStyleSheet(get_frame_stylesheet(bg_color=bg_color))

    def add_widget(self, widget, stretch: int = 0) -> None:
        """Add widget to horizontal layout."""
        self.layout.addWidget(widget, stretch)

    def add_stretch(self) -> None:
        """Add stretch to end."""
        self.layout.addStretch()


class VerticalFrame(QFrame):
    """Vertical container with pre-configured layout."""

    def __init__(
        self,
        spacing: int = 8,
        bg_color: Optional[str] = None,
        parent=None,
    ):
        """
        Initialize vertical frame.

        Args:
            spacing: Space between widgets
            bg_color: Background color (None for transparent)
            parent: Parent widget
        """
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(spacing)

        if bg_color:
            self.setStyleSheet(get_frame_stylesheet(bg_color=bg_color))

    def add_widget(self, widget, stretch: int = 0) -> None:
        """Add widget to vertical layout."""
        self.layout.addWidget(widget, stretch)

    def add_layout(self, layout) -> None:
        """Add layout to vertical layout."""
        self.layout.addLayout(layout)

    def add_stretch(self) -> None:
        """Add stretch to end."""
        self.layout.addStretch()
