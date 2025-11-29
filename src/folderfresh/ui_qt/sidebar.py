"""
PySide6 sidebar widget for FolderFresh.
Navigation buttons for Rules, Preview, Settings, and Activity Log.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class SidebarWidget(QWidget):
    """Sidebar navigation widget with buttons for main sections."""

    # Signals for button clicks (no logic yet, just UI events)
    rules_clicked = Signal()
    preview_clicked = Signal()
    settings_clicked = Signal()
    activity_log_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(200)
        self.setMaximumWidth(250)
        self._init_ui()

    def _init_ui(self):
        """Initialize the sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        # Sidebar title
        title = QLabel("FolderFresh")
        title.setFont(QFont("Segoe UI Variable", 14, QFont.Bold))
        title.setStyleSheet("color: #e6eef8;")
        layout.addWidget(title)

        # Separator spacing
        layout.addSpacing(12)

        # Rules button
        self.rules_btn = self._create_nav_button("📋 Rules")
        self.rules_btn.clicked.connect(self.rules_clicked.emit)
        layout.addWidget(self.rules_btn)

        # Preview button
        self.preview_btn = self._create_nav_button("👁️ Preview")
        self.preview_btn.clicked.connect(self.preview_clicked.emit)
        layout.addWidget(self.preview_btn)

        # Settings button
        self.settings_btn = self._create_nav_button("⚙️ Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)

        # Activity Log button
        self.activity_log_btn = self._create_nav_button("📝 Activity Log")
        self.activity_log_btn.clicked.connect(self.activity_log_clicked.emit)
        layout.addWidget(self.activity_log_btn)

        # Spacer to push buttons to top
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Apply sidebar styling
        self.setStyleSheet("""
            QWidget {
                background-color: #0f1720;
                border-right: 1px solid #1f2937;
            }
            QPushButton {
                background-color: #1f2937;
                color: #e6eef8;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 10px 12px;
                text-align: left;
                font: 11pt "Segoe UI Variable";
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2d3748;
                border: 1px solid #475569;
            }
            QPushButton:pressed {
                background-color: #1a202c;
            }
        """)

    def _create_nav_button(self, text: str) -> QPushButton:
        """Create a styled navigation button."""
        button = QPushButton(text)
        button.setMinimumHeight(44)
        button.setCursor(Qt.PointingHandCursor)
        return button

    def set_active_button(self, button_name: str):
        """Highlight the active navigation button."""
        buttons = {
            "rules": self.rules_btn,
            "preview": self.preview_btn,
            "settings": self.settings_btn,
            "activity_log": self.activity_log_btn,
        }

        for btn in buttons.values():
            btn.setStyleSheet(self._get_button_style(False))

        if button_name in buttons:
            buttons[button_name].setStyleSheet(self._get_button_style(True))

    def _get_button_style(self, is_active: bool) -> str:
        """Return button style based on active state."""
        if is_active:
            return """
                QPushButton {
                    background-color: #2563eb;
                    color: #ffffff;
                    border: 1px solid #1e4fd8;
                    border-radius: 6px;
                    padding: 10px 12px;
                    text-align: left;
                    font: 11pt "Segoe UI Variable";
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #1e4fd8;
                    border: 1px solid #1939b8;
                }
                QPushButton:pressed {
                    background-color: #1636c4;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #1f2937;
                    color: #e6eef8;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 10px 12px;
                    text-align: left;
                    font: 11pt "Segoe UI Variable";
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                    border: 1px solid #475569;
                }
                QPushButton:pressed {
                    background-color: #1a202c;
                }
            """
