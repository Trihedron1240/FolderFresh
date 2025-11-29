#!/usr/bin/env python3
"""
Test script to simulate the full CategoryManager UI workflow
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from folderfresh.profile_store import ProfileStore
from folderfresh.ui_qt.category_manager_backend import CategoryManagerBackend

def test_workflow():
    """
    Simulate the workflow:
    1. User opens CategoryManager
    2. Backend loads categories
    3. User adds a custom category
    4. User saves
    5. Verify it's in the file
    6. Reload UI and verify it shows
    """

    print("=" * 70)
    print("SIMULATING FULL USER WORKFLOW")
    print("=" * 70)

    store = ProfileStore()
    doc = store.load()

    profile_id = doc.get("active_profile_id", "profile_default")

    print(f"\nStep 1: Open CategoryManager for profile '{profile_id}'")
    backend = CategoryManagerBackend(profile_id)

    print("\nStep 2: Load categories from backend")
    overrides, custom, enabled = backend.load_categories()
    print(f"  Loaded {len(custom)} custom categories")
    print(f"  Custom categories: {list(custom.keys())}")

    # Simulate user adding a new category
    new_cat_name = f"UserCategory_{datetime.now().strftime('%H%M%S')}"
    new_extensions = ["user", "usr"]

    print(f"\nStep 3: User adds custom category '{new_cat_name}'")
    result = backend.add_custom_category(new_cat_name, new_extensions)
    print(f"  Add result: {result}")

    if result:
        print(f"  Working profile custom_categories: {backend.working_profile.get('custom_categories', {})}")
        print(f"  Working profile category_enabled: {backend.working_profile.get('category_enabled', {})}")

    print("\nStep 4: Verify changes were saved to file")
    doc_check = store.load()
    profile_check = None
    for p in doc_check["profiles"]:
        if p["id"] == profile_id:
            profile_check = p
            break

    if profile_check:
        custom_in_file = profile_check.get("custom_categories", {})
        enabled_in_file = profile_check.get("category_enabled", {})

        print(f"  Custom categories in file: {list(custom_in_file.keys())}")
        print(f"  New category in file: {new_cat_name in custom_in_file}")

        if new_cat_name in custom_in_file:
            print(f"    Extensions: {custom_in_file[new_cat_name]}")
            print(f"    Enabled: {enabled_in_file.get(new_cat_name)}")

    # Simulate UI reload (what happens when user opens window again)
    print(f"\nStep 5: Simulate UI reload (user opens window again)")
    backend2 = CategoryManagerBackend(profile_id)
    overrides2, custom2, enabled2 = backend2.load_categories()

    print(f"  Reloaded custom categories: {list(custom2.keys())}")
    print(f"  New category visible after reload: {new_cat_name in custom2}")

    if new_cat_name in custom2:
        print(f"    Extensions match: {custom2[new_cat_name] == new_extensions}")
        print(f"    Enabled state: {enabled2.get(new_cat_name)}")

    print("\n" + "=" * 70)
    print("WORKFLOW TEST COMPLETE")
    print("=" * 70)

    return new_cat_name in custom_in_file and new_cat_name in custom2

if __name__ == "__main__":
    success = test_workflow()
    sys.exit(0 if success else 1)
