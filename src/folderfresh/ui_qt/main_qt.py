"""
PySide6 entry point for FolderFresh.
Launcher for the new Qt-based GUI (parallel to CustomTkinter version).
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Handle both relative imports (when used as module) and direct execution
try:
    from .application import FolderFreshApplication
    from .styles import Colors, Fonts
except ImportError:
    # Direct execution - add parent package to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from folderfresh.ui_qt.application import FolderFreshApplication
    from folderfresh.ui_qt.styles import Colors, Fonts


def setup_qt_app() -> QApplication:
    """
    Setup and configure Qt application.

    Returns:
        QApplication instance
    """
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("FolderFresh")
    app.setApplicationVersion("1.5.0")

    # Configure application style
    try:
        from PySide6.QtCore import QSize
        app.setStyle("Fusion")
    except Exception:
        pass  # Fall back to default style

    return app


def setup_stylesheet(app: QApplication) -> None:
    """
    Setup global application stylesheet.

    Args:
        app: QApplication instance
    """
    stylesheet = f"""
    * {{
        font-family: {Fonts.PRIMARY_FAMILY};
    }}

    QMainWindow {{
        background-color: {Colors.PANEL_BG};
        color: {Colors.TEXT};
    }}

    QDialog {{
        background-color: {Colors.PANEL_BG};
        color: {Colors.TEXT};
    }}

    QLabel {{
        color: {Colors.TEXT};
    }}

    QLineEdit, QTextEdit, QComboBox {{
        background-color: {Colors.CARD_BG};
        color: {Colors.TEXT};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 6px;
    }}

    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 2px solid {Colors.ACCENT};
        background-color: {Colors.PANEL_BG};
    }}

    QPushButton {{
        background-color: {Colors.ACCENT};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: #1e4fd8;
    }}

    QPushButton:pressed {{
        background-color: #1565c0;
    }}

    QScrollArea {{
        background-color: {Colors.PANEL_BG};
        border: none;
    }}

    QScrollBar:vertical {{
        background-color: {Colors.PANEL_ALT};
        width: 12px;
        border-radius: 6px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {Colors.BORDER};
        border-radius: 6px;
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {Colors.BORDER_LIGHT};
    }}
    """

    app.setStyleSheet(stylesheet)


def launch_qt_app(
    backend_config: Optional[dict] = None,
    launcher_callback: Optional[callable] = None,
) -> int:
    """
    Launch FolderFresh PySide6 application.

    Args:
        backend_config: Optional backend configuration dict
        launcher_callback: Optional callback to setup backend references

    Returns:
        Application exit code
    """
    # Create Qt application
    qt_app = setup_qt_app()
    setup_stylesheet(qt_app)

    # Create application orchestrator
    app = FolderFreshApplication(qt_app)

    # Setup backend references if callback provided
    if launcher_callback:
        launcher_callback(app)

    # Show main window
    app.show_main_window()

    # Run event loop
    return qt_app.exec()


def main():
    """
    Main entry point for standalone PySide6 launcher.
    Can be used to test PySide6 version without full backend integration.
    """
    sys.exit(launch_qt_app())


if __name__ == "__main__":
    main()
