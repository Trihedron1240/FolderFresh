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
    from .stylesheet_cohesive import apply_cohesive_theme
except ImportError:
    # Direct execution - add parent package to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from folderfresh.ui_qt.application import FolderFreshApplication
    from folderfresh.ui_qt.stylesheet_cohesive import apply_cohesive_theme


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

    Applies cohesive dark theme that eliminates white space
    and creates unified, seamless UI appearance.

    Args:
        app: QApplication instance
    """
    # Apply cohesive dark theme with no white space
    apply_cohesive_theme(app)


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
