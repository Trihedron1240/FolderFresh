"""
PySide6 tooltip widget for FolderFresh.
Floating label that appears on widget hover.
"""

from PySide6.QtWidgets import QLabel, QWidget
from PySide6.QtCore import Qt, QTimer, QPoint, QObject, QEvent
from PySide6.QtGui import QFont

from .styles import Colors, Fonts, get_label_stylesheet


class ToolTip(QLabel):
    """
    Floating tooltip that appears on mouse hover.
    Positions itself near the cursor and disappears on mouse leave.
    """

    def __init__(self, text: str, parent=None):
        """
        Initialize tooltip.

        Args:
            text: Tooltip text to display
            parent: Parent widget (the widget being tooltipped)
        """
        super().__init__(text, parent)
        self.target_widget = parent
        self.text_content = text

        # Tooltip styling
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setWordWrap(True)
        self.setMaximumWidth(250)
        self.setMinimumHeight(30)

        # Apply dark stylesheet
        self.setStyleSheet(f"""
            QLabel {{
                background-color: #1a1a1a;
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px 8px;
                font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
                font-size: {Fonts.SIZE_SMALL}pt;
            }}
        """)

        # Timer for auto-hide
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

        # Don't show immediately
        self.hide()

    def show_tooltip(self, event=None) -> None:
        """Show tooltip near the cursor."""
        if event:
            # Position near cursor
            pos = event.globalPos()
            self.move(pos.x() + 10, pos.y() + 10)
        elif self.target_widget:
            # Position below/right of target widget
            pos = self.target_widget.mapToGlobal(self.target_widget.rect().bottomRight())
            self.move(pos.x() + 5, pos.y() + 5)

        self.show()
        self.raise_()

        # Auto-hide after 5 seconds
        self.hide_timer.start(5000)

    def hide_tooltip(self, event=None) -> None:
        """Hide tooltip and cancel auto-hide timer."""
        self.hide_timer.stop()
        self.hide()

    @staticmethod
    def attach_to(widget: QWidget, text: str) -> "ToolTip":
        """
        Attach tooltip to a widget with automatic show/hide on hover.

        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text

        Returns:
            The created ToolTip instance
        """
        tooltip = ToolTip(text, widget)

        # Install event filter to detect hover
        class TooltipEventFilter(QObject):
            """Event filter for detecting mouse enter/leave events on widgets."""

            def __init__(self, tooltip_obj):
                super().__init__()
                self.tooltip = tooltip_obj

            def eventFilter(self, obj, event):
                """
                Handle mouse enter/leave events.

                Args:
                    obj: The object that received the event
                    event: The event object

                Returns:
                    False to allow event propagation
                """
                if event.type() == QEvent.Enter:
                    self.tooltip.show_tooltip(event)
                elif event.type() == QEvent.Leave:
                    self.tooltip.hide_tooltip()
                return False

        event_filter = TooltipEventFilter(tooltip)
        widget.installEventFilter(event_filter)

        # Store filter to prevent garbage collection
        widget._tooltip_filter = event_filter

        return tooltip
