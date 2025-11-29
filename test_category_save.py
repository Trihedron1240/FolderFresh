#!/usr/bin/env python3
"""
Debug script to test category manager save persistence
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from folderfresh.profile_store import ProfileStore
from folderfresh.ui_qt.category_manager_backend import CategoryManagerBackend

def main():
    # Load profiles
    store = ProfileStore()
    doc = store.load()

    print("=" * 70)
    print("BEFORE CHANGES")
    print("=" * 70)

    # Get default profile
    profile_id = doc.get("active_profile_id", "profile_default")
    profile = None
    for p in doc["profiles"]:
        if p["id"] == profile_id:
            profile = p
            break

    if not profile:
        print(f"Profile {profile_id} not found!")
        return

    print(f"Profile ID: {profile_id}")
    print(f"Profile Name: {profile.get('name')}")
    print(f"Custom Categories: {profile.get('custom_categories', {})}")
    print(f"Category Overrides: {profile.get('category_overrides', {})}")
    print(f"Category Enabled: {profile.get('category_enabled', {})}")

    # Test backend
    print("\n" + "=" * 70)
    print("TESTING BACKEND ADD CUSTOM CATEGORY")
    print("=" * 70)

    backend = CategoryManagerBackend(profile_id)

    # Load from backend
    overrides, custom, enabled = backend.load_categories()
    print(f"\nLoaded from backend:")
    print(f"  Overrides: {overrides}")
    print(f"  Custom Categories: {custom}")
    print(f"  Enabled: {enabled}")

    # Add a test custom category
    test_category = "TestCategory"
    test_extensions = ["test", "tst"]

    print(f"\nAdding custom category: {test_category}")
    result = backend.add_custom_category(test_category, test_extensions)
    print(f"Add result: {result}")

    if result:
        # Check working profile
        print(f"\nWorking profile after add:")
        print(f"  Custom Categories: {backend.working_profile.get('custom_categories', {})}")
        print(f"  Category Enabled: {backend.working_profile.get('category_enabled', {})}")

    # Check file on disk
    print("\n" + "=" * 70)
    print("CHECKING FILE ON DISK")
    print("=" * 70)

    doc_reloaded = store.load()
    profile_reloaded = None
    for p in doc_reloaded["profiles"]:
        if p["id"] == profile_id:
            profile_reloaded = p
            break

    if profile_reloaded:
        print(f"Reloaded profile {profile_id}:")
        print(f"  Custom Categories: {profile_reloaded.get('custom_categories', {})}")
        print(f"  Category Overrides: {profile_reloaded.get('category_overrides', {})}")
        print(f"  Category Enabled: {profile_reloaded.get('category_enabled', {})}")

        if test_category in profile_reloaded.get("custom_categories", {}):
            print(f"\nSUCCESS: {test_category} found in saved profile!")
        else:
            print(f"\nFAILURE: {test_category} NOT found in saved profile!")

    # Show file path
    print(f"\nProfile file path: {store.path}")
    print(f"Profile file exists: {store.path.exists()}")

if __name__ == "__main__":
    main()
