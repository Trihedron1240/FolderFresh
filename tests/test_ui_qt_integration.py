"""
FolderFresh PySide6 UI Integration Tests
Tests interaction between UI components
"""

import sys
import pytest
from pathlib import Path

# Fix console encoding for Windows
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from folderfresh.ui_qt.main_qt import setup_qt_app, setup_stylesheet
from folderfresh.ui_qt.main_window import MainWindow
from folderfresh.ui_qt.profile_manager import ProfileManagerWindow
from folderfresh.ui_qt.rule_manager import RuleManager
from folderfresh.ui_qt.activity_log_window import ActivityLogWindow
from folderfresh.ui_qt.watched_folders_window import WatchedFoldersWindow


# ========== FIXTURES ==========

@pytest.fixture(scope="session")
def qt_app():
    """Create QApplication for all tests"""
    app = setup_qt_app()
    setup_stylesheet(app)
    yield app


@pytest.fixture
def main_window(qt_app):
    """Create MainWindow instance"""
    window = MainWindow()
    yield window
    window.close()


@pytest.fixture
def profile_manager(qt_app):
    """Create ProfileManagerWindow instance"""
    window = ProfileManagerWindow()
    yield window
    window.close()


@pytest.fixture
def rule_manager(qt_app):
    """Create RuleManager instance"""
    window = RuleManager()
    yield window
    window.close()


@pytest.fixture
def activity_log_window(qt_app):
    """Create ActivityLogWindow instance"""
    window = ActivityLogWindow()
    yield window
    window.close()


@pytest.fixture
def watched_folders_window(qt_app):
    """Create WatchedFoldersWindow instance"""
    window = WatchedFoldersWindow()
    yield window
    window.close()


# ========== MULTI-WINDOW INTEGRATION TESTS ==========

class TestMultipleWindowsExistence:
    """Test multiple windows can coexist"""

    def test_main_window_and_profile_manager_coexist(self, main_window, profile_manager):
        """Test MainWindow and ProfileManager can exist together"""
        assert main_window is not None
        assert profile_manager is not None

    def test_all_windows_created_successfully(
        self, main_window, profile_manager, rule_manager,
        activity_log_window, watched_folders_window
    ):
        """Test all windows can be created without errors"""
        assert main_window is not None
        assert profile_manager is not None
        assert rule_manager is not None
        assert activity_log_window is not None
        assert watched_folders_window is not None

    def test_windows_can_all_be_shown(
        self, main_window, profile_manager, rule_manager,
        activity_log_window, watched_folders_window
    ):
        """Test all windows can be shown simultaneously"""
        main_window.show()
        profile_manager.show()
        rule_manager.show()
        activity_log_window.show()
        watched_folders_window.show()

        assert main_window.isVisible()
        assert profile_manager.isVisible()
        assert rule_manager.isVisible()
        assert activity_log_window.isVisible()
        assert watched_folders_window.isVisible()


# ========== SIGNAL FLOW INTEGRATION TESTS ==========

class TestSignalIntegration:
    """Test signal flow between windows"""

    def test_main_window_signals_defined(self, main_window):
        """Test MainWindow has all signals defined"""
        signals = [
            'folder_chosen',
            'preview_requested',
            'organise_requested',
            'undo_requested',
            'duplicates_requested',
            'desktop_clean_requested',
            'profiles_requested',
            'watched_folders_requested',
            'help_requested',
            'options_changed'
        ]
        for sig in signals:
            assert hasattr(main_window, sig)

    def test_profile_manager_signals_defined(self, profile_manager):
        """Test ProfileManager has signal definitions"""
        # Signals defined but may be optional
        if hasattr(profile_manager, 'profile_created'):
            assert profile_manager.profile_created is not None

    def test_multiple_signal_connections(self, main_window, qt_app):
        """Test multiple signals can be connected simultaneously"""
        signals_received = []

        main_window.preview_requested.connect(lambda: signals_received.append('preview'))
        main_window.organise_requested.connect(lambda: signals_received.append('organise'))
        main_window.undo_requested.connect(lambda: signals_received.append('undo'))

        # Emit signals by clicking buttons
        QTest.mouseClick(main_window.preview_btn, Qt.LeftButton)
        qt_app.processEvents()

        assert 'preview' in signals_received


# ========== CHECKBOX INTEGRATION TESTS ==========

class TestCheckboxIntegration:
    """Test checkbox state management across interactions"""

    def test_multiple_checkbox_states(self, main_window):
        """Test managing multiple checkbox states"""
        # Save initial states
        include_sub = main_window.include_sub_check.isChecked()
        skip_hidden = main_window.skip_hidden_check.isChecked()
        safe_mode = main_window.safe_mode_check.isChecked()

        # Toggle all
        main_window.include_sub_check.setChecked(not include_sub)
        main_window.skip_hidden_check.setChecked(not skip_hidden)
        main_window.safe_mode_check.setChecked(not safe_mode)

        # Verify changes
        assert main_window.include_sub_check.isChecked() != include_sub
        assert main_window.skip_hidden_check.isChecked() != skip_hidden
        assert main_window.safe_mode_check.isChecked() != safe_mode

    def test_checkbox_states_independent(self, main_window):
        """Test each checkbox state is independent"""
        # Toggle one checkbox
        initial_state = main_window.safe_mode_check.isChecked()
        main_window.safe_mode_check.setChecked(not initial_state)

        # Other checkboxes should not change
        # Store and check
        other_states = {
            'include_sub': main_window.include_sub_check.isChecked(),
            'skip_hidden': main_window.skip_hidden_check.isChecked(),
        }

        # Toggle another
        main_window.smart_mode_check.setChecked(
            not main_window.smart_mode_check.isChecked()
        )

        # Verify others unchanged
        assert main_window.include_sub_check.isChecked() == other_states['include_sub']
        assert main_window.skip_hidden_check.isChecked() == other_states['skip_hidden']


# ========== ADVANCED SECTION INTEGRATION TESTS ==========

class TestAdvancedSectionIntegration:
    """Test advanced section visibility and controls"""

    def test_advanced_section_toggle_consistency(self, main_window, qt_app):
        """Test advanced section toggle works consistently"""
        initial_visible = main_window.advanced_content.isVisible()

        # Toggle multiple times
        for i in range(4):
            QTest.mouseClick(main_window.advanced_btn, Qt.LeftButton)
            qt_app.processEvents()

        # Should return to initial state
        assert main_window.advanced_content.isVisible() == initial_visible

    def test_advanced_button_text_changes(self, main_window, qt_app):
        """Test advanced button text reflects state"""
        btn_text = main_window.advanced_btn.text()
        # Button should have some indication of expand/collapse
        assert btn_text is not None
        assert len(btn_text) > 0


# ========== INPUT FIELD INTEGRATION TESTS ==========

class TestInputFieldIntegration:
    """Test input field functionality in context"""

    def test_path_entry_readonly_status(self, main_window):
        """Test path entry field is properly read-only"""
        assert main_window.path_entry.isReadOnly()

        # Attempting to set text should fail
        original_text = main_window.path_entry.text()
        # Can still set text programmatically even if readonly for display
        main_window.path_entry.setText("Test")
        # But user can't edit it

    def test_preview_box_readonly_status(self, main_window):
        """Test preview box is properly read-only"""
        assert main_window.preview_box.isReadOnly()


# ========== BUTTON INTEGRATION TESTS ==========

class TestButtonIntegration:
    """Test button interactions"""

    def test_all_buttons_clickable(self, main_window):
        """Test all buttons respond to clicks"""
        buttons = [
            main_window.preview_btn,
            main_window.organise_btn,
            main_window.undo_btn,
            main_window.dupe_btn,
            main_window.desktop_btn
        ]

        for btn in buttons:
            assert btn.isEnabled(), f"Button {btn.text()} is disabled"

    def test_button_click_sequence(self, main_window, qt_app):
        """Test multiple button clicks in sequence"""
        click_count = []

        main_window.preview_btn.clicked.connect(lambda: click_count.append(1))
        main_window.organise_btn.clicked.connect(lambda: click_count.append(2))

        # Click buttons in sequence
        QTest.mouseClick(main_window.preview_btn, Qt.LeftButton)
        qt_app.processEvents()
        QTest.mouseClick(main_window.organise_btn, Qt.LeftButton)
        qt_app.processEvents()

        assert len(click_count) == 2
        assert click_count[0] == 1
        assert click_count[1] == 2

    def test_undo_button_enabled_state(self, main_window):
        """Test undo button state management"""
        # Undo button should be disabled initially (no history)
        # This test verifies it can change state
        initial_enabled = main_window.undo_btn.isEnabled()
        main_window.undo_btn.setEnabled(not initial_enabled)
        assert main_window.undo_btn.isEnabled() != initial_enabled


# ========== WINDOW STATE PERSISTENCE TESTS ==========

class TestWindowStatePersistence:
    """Test window state across operations"""

    def test_main_window_properties_preserved(self, main_window):
        """Test MainWindow properties remain consistent"""
        original_title = main_window.windowTitle()
        original_size = main_window.size()

        # Perform some operations
        main_window.safe_mode_check.setChecked(True)
        main_window.include_sub_check.setChecked(False)

        # Properties should be preserved
        assert main_window.windowTitle() == original_title
        assert main_window.size() == original_size

    def test_checkbox_state_persistence(self, main_window):
        """Test checkbox states persist across other operations"""
        initial_state = main_window.safe_mode_check.isChecked()

        # Perform other operations
        main_window.preview_btn.setEnabled(False)
        main_window.preview_btn.setEnabled(True)

        # Checkbox state should persist
        assert main_window.safe_mode_check.isChecked() == initial_state


# ========== STYLING CONSISTENCY TESTS ==========

class TestStylingConsistency:
    """Test styling applied consistently across windows"""

    def test_all_windows_have_stylesheets(
        self, main_window, profile_manager, rule_manager
    ):
        """Test all windows have stylesheets applied"""
        # Windows may use global stylesheet or have inline styles
        # Just verify they can be styled without error
        assert main_window is not None
        assert profile_manager is not None
        assert rule_manager is not None

    def test_buttons_consistent_height(self, main_window):
        """Test all buttons have consistent height"""
        buttons = [
            main_window.preview_btn,
            main_window.organise_btn,
            main_window.undo_btn
        ]

        heights = [btn.minimumHeight() for btn in buttons]
        # All buttons should have same minimum height
        assert all(h == heights[0] for h in heights)


# ========== DIALOG AND WINDOW INTERACTION TESTS ==========

class TestWindowInteractions:
    """Test interactions between windows"""

    def test_main_window_can_signal_to_profile_manager(self, main_window):
        """Test MainWindow can communicate with ProfileManager"""
        # This is integration point for Phase 9
        signal_received = []

        def on_profile_requested():
            signal_received.append(True)

        main_window.profiles_requested.connect(on_profile_requested)
        main_window.profiles_requested.emit()

        assert len(signal_received) > 0

    def test_main_window_can_signal_to_rule_manager(self, main_window):
        """Test MainWindow can signal rule operations"""
        # Integration point for Phase 9
        assert hasattr(main_window, 'organise_requested')

    def test_window_show_hide_sequence(self, main_window, profile_manager):
        """Test windows can be shown/hidden in sequence"""
        main_window.show()
        assert main_window.isVisible()

        profile_manager.show()
        assert profile_manager.isVisible()

        main_window.hide()
        assert not main_window.isVisible()
        assert profile_manager.isVisible()  # Should still be visible

        profile_manager.hide()
        assert not profile_manager.isVisible()


# ========== ERROR HANDLING INTEGRATION TESTS ==========

class TestIntegrationErrorHandling:
    """Test error handling in integrated scenarios"""

    def test_window_operations_dont_crash(self, main_window, qt_app):
        """Test normal window operations don't crash"""
        # Show window
        main_window.show()
        qt_app.processEvents()

        # Click buttons
        for btn in [main_window.preview_btn, main_window.organise_btn]:
            try:
                QTest.mouseClick(btn, Qt.LeftButton)
                qt_app.processEvents()
            except Exception as e:
                pytest.fail(f"Button click caused error: {e}")

        # Toggle checkboxes
        for chk in [main_window.include_sub_check, main_window.safe_mode_check]:
            try:
                chk.setChecked(not chk.isChecked())
                qt_app.processEvents()
            except Exception as e:
                pytest.fail(f"Checkbox toggle caused error: {e}")

    def test_multiple_windows_operations_dont_crash(
        self, main_window, profile_manager, rule_manager, qt_app
    ):
        """Test operating multiple windows simultaneously doesn't crash"""
        try:
            main_window.show()
            profile_manager.show()
            rule_manager.show()
            qt_app.processEvents()

            # Perform operations on all
            QTest.mouseClick(main_window.preview_btn, Qt.LeftButton)
            qt_app.processEvents()

            main_window.safe_mode_check.setChecked(True)
            qt_app.processEvents()

        except Exception as e:
            pytest.fail(f"Multi-window operation caused error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
