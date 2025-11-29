"""
PySide6 help window dialog for FolderFresh.
Displays application help and provides links to resources.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    HeadingLabel,
    StyledLabel,
    VerticalFrame,
    HorizontalFrame,
)


class HelpWindow(QDialog):
    """Help dialog displaying application information and resources."""

    # Signals
    view_log_clicked = Signal()
    report_bug_clicked = Signal()
    closed = Signal()

    def __init__(self, parent=None):
        """
        Initialize help window.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("FolderFresh Help")
        self.setGeometry(200, 200, 500, 600)
        self.setMinimumWidth(400)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize help window UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("FolderFresh Help")
        main_layout.addWidget(title)

        # Help text content
        help_text = """
FolderFresh is a powerful file organization tool that helps you automatically tidy your folders using customizable rules.

KEY FEATURES:

• Preview Mode
  See exactly what will happen before executing any changes. No surprises!

• Safe Mode
  Copy files instead of moving them as an extra layer of protection.

• Smart Sorting
  Uses advanced rules to detect screenshots, assignments, photos, invoices, messaging media and more.

• Auto-Tidy
  Automatically organize your folders in the background whenever new files arrive.

• Undo Support
  Made a mistake? Undo the last operation with a single click.

• Custom Rules
  Create complex rules with conditions and multiple actions to handle any file organization scenario.

• Profile System
  Save different rule sets for different folders, making it easy to organize multiple locations.

GETTING STARTED:

1. Choose a folder or open a folder from Explorer
2. Review the default options (Safe Mode is recommended for beginners)
3. Click Preview to see what will happen
4. Click Organise Files to apply the changes

For more information, visit the GitHub repository or check the activity log.
        """.strip()

        help_label = StyledLabel(help_text, font_size=Fonts.SIZE_SMALL)
        help_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        help_label.setWordWrap(True)
        help_label.setStyleSheet(
            f"""
            QLabel {{
                color: {Colors.TEXT};
                line-height: 1.5;
            }}
        """
        )

        # Scrollable help text area
        from PySide6.QtWidgets import QScrollArea, QFrame
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {Colors.PANEL_BG}; border: none; }}")

        # Create text container
        text_container = QFrame()
        text_container.setStyleSheet(f"QFrame {{ background-color: {Colors.PANEL_BG}; }}")
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.addWidget(help_label)
        text_layout.addStretch()

        scroll.setWidget(text_container)
        main_layout.addWidget(scroll, 1)

        # Button row at bottom
        button_frame = HorizontalFrame(spacing=8)

        view_log_btn = StyledButton("View Log File", bg_color=Colors.ACCENT)
        view_log_btn.clicked.connect(lambda: self.view_log_clicked.emit())
        button_frame.add_widget(view_log_btn)

        report_btn = StyledButton("Report Bug", bg_color=Colors.DANGER)
        report_btn.clicked.connect(lambda: self.report_bug_clicked.emit())
        button_frame.add_widget(report_btn)

        button_frame.add_stretch()

        close_btn = StyledButton("Close", bg_color=Colors.BORDER_LIGHT)
        close_btn.clicked.connect(self.accept)
        button_frame.add_widget(close_btn)

        main_layout.addWidget(button_frame)

    def closeEvent(self, event):
        """Handle window close event."""
        self.closed.emit()
        self.accept()
        event.accept()
