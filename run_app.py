#!/usr/bin/env python3
"""Quick launcher for FolderFresh to test include_sub checkbox."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    print("="*60)
    print("Starting FolderFresh...")
    print("="*60)
    print("\nWatch the console output as you toggle the include_sub checkbox.")
    print("You should see:")
    print("  [MAIN_WINDOW] include_sub checkbox changed to [True/False]...")
    print("  [PROFILE_UPDATE_SILENT] Received update for profile...")
    print("  [PROFILE_UPDATE_SILENT] Update applied: True")
    print("\n" + "="*60 + "\n")

    from folderfresh.ui_qt.main import main
    main()
