"""Test ProfileManager fallback checkbox save functionality."""

import pytest
import json
import tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Ensure we can import from src
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from folderfresh.profile_store import ProfileStore
from folderfresh.ui_qt.base_widgets import StyledCheckBox


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestProfileManagerCheckbox:
    """Test ProfileManager checkbox save functionality."""

    def test_checkbox_signal_firing(self, qapp):
        """Test that checkbox stateChanged signal fires when toggled."""
        checkbox = StyledCheckBox("Test", checked=True)

        # Track if signal fires
        signal_fired = []
        checkbox.stateChanged.connect(
            lambda state: signal_fired.append(state)
        )

        # Toggle checkbox
        checkbox.setChecked(False)

        # Signal should have fired
        assert len(signal_fired) == 1
        assert signal_fired[0] == 0  # Qt.Unchecked

    def test_checkbox_capture_in_lambda(self, qapp):
        """Test that checkbox reference is correctly captured in lambda."""
        checkbox = StyledCheckBox("Test", checked=True)

        # Simulate what profile_manager does
        captured_checks = []
        profile_id = "test_profile"

        def on_checkbox_changed(state):
            # This simulates the _on_fallback_changed handler
            captured_checks.append({
                'state': state,
                'checked': checkbox.isChecked(),
                'profile_id': profile_id
            })

        checkbox.stateChanged.connect(on_checkbox_changed)

        # Toggle checkbox
        checkbox.setChecked(False)

        # Verify the handler was called and captured correct state
        assert len(captured_checks) == 1
        assert captured_checks[0]['checked'] == False
        assert captured_checks[0]['profile_id'] == 'test_profile'

    def test_fallback_setting_save_and_load(self):
        """Test that fallback setting is correctly saved and loaded."""
        # Create temp profile store
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            store = ProfileStore(temp_path)

            # Get initial doc
            doc = store.load()
            initial_profile_id = doc['profiles'][0]['id']

            # Simulate what _on_fallback_changed does:
            # 1. Load document
            doc = store.load()

            # 2. Find profile by ID
            found = False
            for profile in doc.get("profiles", []):
                if profile["id"] == initial_profile_id:
                    # 3. Update setting
                    if "settings" not in profile:
                        profile["settings"] = {}
                    profile["settings"]["rule_fallback_to_sort"] = False
                    found = True
                    break

            # 4. Save
            assert found, f"Profile {initial_profile_id} not found"
            store.save(doc)

            # 5. Verify by loading again
            doc2 = store.load()
            for profile in doc2["profiles"]:
                if profile["id"] == initial_profile_id:
                    assert profile["settings"]["rule_fallback_to_sort"] == False
                    break

        finally:
            temp_path.unlink()

    def test_fallback_setting_toggle_cycle(self):
        """Test toggling fallback setting multiple times."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            store = ProfileStore(temp_path)
            doc = store.load()
            profile_id = doc['profiles'][0]['id']

            # Simulate multiple toggles
            for expected_value in [False, True, False]:
                doc = store.load()
                for profile in doc.get("profiles", []):
                    if profile["id"] == profile_id:
                        if "settings" not in profile:
                            profile["settings"] = {}
                        profile["settings"]["rule_fallback_to_sort"] = expected_value
                        break
                store.save(doc)

                # Verify
                doc_check = store.load()
                for profile in doc_check.get("profiles", []):
                    if profile["id"] == profile_id:
                        assert profile["settings"]["rule_fallback_to_sort"] == expected_value
                        break

        finally:
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
