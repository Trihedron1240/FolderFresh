#!/usr/bin/env python3
"""
FolderFresh PySide6 Qt GUI Launcher
Launches the new Qt-based GUI (parallel to CustomTkinter version).

Usage:
    python launch_qt.py                    # Launch with no backend
    python launch_qt.py --with-backend     # Launch with backend integration (future)
"""

import sys
from pathlib import Path

# Add src directory to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def main():
    """Main launcher entry point."""
    from folderfresh.ui_qt.main_qt import launch_qt_app

    exit_code = launch_qt_app()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
