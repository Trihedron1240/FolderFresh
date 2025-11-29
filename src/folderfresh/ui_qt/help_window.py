"""
PySide6 help window dialog for FolderFresh.
Displays application help and provides links to resources.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
)
from PySide6.QtCore import Qt, Signal, QUrl
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

        # Help text content with HTML formatting for links
        help_html = f"""
<html>
<body style="background-color: {Colors.PANEL_BG}; color: {Colors.TEXT}; font-family: Arial, sans-serif; line-height: 1.5;">
<p>FolderFresh is a powerful file organization tool that helps you automatically tidy your folders using customizable rules.</p>

<h3 style="color: {Colors.TEXT};">KEY FEATURES:</h3>

<p>
• <b>Preview Mode</b><br/>
&nbsp;&nbsp;See exactly what will happen before executing any changes. No surprises!
</p>

<p>
• <b>Safe Mode</b><br/>
&nbsp;&nbsp;Copy files instead of moving them as an extra layer of protection.
</p>

<p>
• <b>Smart Sorting</b><br/>
&nbsp;&nbsp;Uses advanced rules to detect screenshots, assignments, photos, invoices, messaging media and more.
</p>

<p>
• <b>Auto-Tidy</b><br/>
&nbsp;&nbsp;Automatically organize your folders in the background whenever new files arrive.
</p>

<p>
• <b>Undo Support</b><br/>
&nbsp;&nbsp;Made a mistake? Undo the last operation with a single click.
</p>

<p>
• <b>Custom Rules</b><br/>
&nbsp;&nbsp;Create complex rules with conditions and multiple actions to handle any file organization scenario.
</p>

<p>
• <b>Profile System</b><br/>
&nbsp;&nbsp;Save different rule sets for different folders, making it easy to organize multiple locations.
</p>

<h3 style="color: {Colors.TEXT};">GETTING STARTED:</h3>

<p>
1. Choose a folder or open a folder from Explorer<br/>
2. Review the default options (Safe Mode is recommended for beginners)<br/>
3. Click Preview to see what will happen<br/>
4. Click Organise Files to apply the changes
</p>

<p>
For more information, <a href="https://github.com/Trihedron1240/FolderFresh" style="color: #2196F3; text-decoration: underline;">visit FolderFresh on GitHub</a> or check the activity log.
</p>
</body>
</html>
        """

        # Create text browser for HTML content with clickable links
        text_browser = QTextBrowser()
        text_browser.setHtml(help_html)
        text_browser.setReadOnly(True)
        text_browser.setOpenExternalLinks(True)
        text_browser.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: {Colors.PANEL_BG};
                color: {Colors.TEXT};
                border: none;
            }}
            """
        )

        main_layout.addWidget(text_browser, 1)

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
