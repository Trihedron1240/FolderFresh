#!/usr/bin/env python3
"""
Debug script to verify save persistence with file timestamps
"""

import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from folderfresh.profile_store import ProfileStore
from folderfresh.ui_qt.category_manager_backend import CategoryManagerBackend

def main():
    store = ProfileStore()
    file_path = store.path

    print("=" * 70)
    print("PERSISTENCE DEBUG TEST")
    print("=" * 70)
    print(f"Profile file: {file_path}")
    print(f"File exists: {file_path.exists()}")

    if file_path.exists():
        stat_before = file_path.stat()
        print(f"\nBefore save:")
        print(f"  File size: {stat_before.st_size} bytes")
        print(f"  Modified: {stat_before.st_mtime}")

    # Load profile
    doc = store.load()
    profile_id = doc.get("active_profile_id", "profile_default")

    # Get current custom categories
    profile = None
    for p in doc["profiles"]:
        if p["id"] == profile_id:
            profile = p
            break

    custom_before = list(profile.get("custom_categories", {}).keys())
    print(f"\nBefore add: {custom_before}")

    # Wait a moment to ensure timestamp changes
    time.sleep(0.2)

    # Add new category
    backend = CategoryManagerBackend(profile_id)
    backend.load_categories()

    new_cat = f"DebugCat_{int(time.time() * 1000) % 100000}"
    print(f"\nAdding category: {new_cat}")
    result = backend.add_custom_category(new_cat, ["dbg"])

    if not result:
        print("ERROR: Failed to add category!")
        return False

    # Check file stats after save
    time.sleep(0.1)  # Give file system time to update

    if file_path.exists():
        stat_after = file_path.stat()
        print(f"\nAfter save:")
        print(f"  File size: {stat_after.st_size} bytes (was {stat_before.st_size})")
        print(f"  Modified: {stat_after.st_mtime} (was {stat_before.st_mtime})")
        print(f"  File was modified: {stat_after.st_mtime > stat_before.st_mtime}")

    # Reload and verify
    doc_check = store.load()
    profile_check = None
    for p in doc_check["profiles"]:
        if p["id"] == profile_id:
            profile_check = p
            break

    custom_after = list(profile_check.get("custom_categories", {}).keys())
    print(f"\nAfter reload: {custom_after}")
    print(f"New category present: {new_cat in custom_after}")

    # Show file contents
    print(f"\nFile contents (first 1000 chars):")
    with open(file_path, "r") as f:
        content = f.read(1000)
        print(content)

    return new_cat in custom_after

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
