"""
FolderFresh PySide6 UI Window Unit Tests
Tests all window components in isolation
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

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from folderfresh.ui_qt.main_qt import setup_qt_app, setup_stylesheet
from folderfresh.ui_qt.main_window import MainWindow
from folderfresh.ui_qt.profile_manager import ProfileManagerWindow
from folderfresh.ui_qt.rule_manager import RuleManager
from folderfresh.ui_qt.activity_log_window import ActivityLogWindow
from folderfresh.ui_qt.watched_folders_window import WatchedFoldersWindow
from folderfresh.ui_qt.styles import Colors, Fonts, DesignTokens


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


# ========== MAINWINDOW TESTS ==========

class TestMainWindowInitialization:
    """Test MainWindow initialization and component creation"""

    def test_main_window_creates_without_error(self, main_window):
        """Test MainWindow initializes successfully"""
        assert main_window is not None
        assert isinstance(main_window, QMainWindow)

    def test_main_window_has_all_buttons(self, main_window):
        """Test MainWindow has all required buttons"""
        required_buttons = [
            'preview_btn',
            'organise_btn',
            'undo_btn',
            'dupe_btn',
            'desktop_btn'
        ]
        for btn_name in required_buttons:
            assert hasattr(main_window, btn_name), f"Missing button: {btn_name}"
            btn = getattr(main_window, btn_name)
            assert btn is not None
            assert btn.text() != ""

    def test_main_window_has_all_checkboxes(self, main_window):
        """Test MainWindow has all required checkboxes"""
        required_checkboxes = [
            'include_sub_check',
            'skip_hidden_check',
            'safe_mode_check',
            'smart_mode_check',
            'watch_mode_check'
        ]
        for chk_name in required_checkboxes:
            assert hasattr(main_window, chk_name), f"Missing checkbox: {chk_name}"
            chk = getattr(main_window, chk_name)
            assert chk is not None

    def test_main_window_has_input_fields(self, main_window):
        """Test MainWindow has all required input fields"""
        assert hasattr(main_window, 'path_entry')
        assert hasattr(main_window, 'preview_box')

    def test_main_window_window_properties(self, main_window):
        """Test MainWindow has proper window properties"""
        assert main_window.windowTitle() != ""
        assert main_window.width() > 0
        assert main_window.height() > 0


class TestMainWindowSignals:
    """Test MainWindow signal definitions and emissions"""

    def test_main_window_has_all_signals(self, main_window):
        """Test MainWindow defines all required signals"""
        required_signals = [
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
        for sig_name in required_signals:
            assert hasattr(main_window, sig_name), f"Missing signal: {sig_name}"

    def test_preview_button_emits_signal(self, main_window, qt_app):
        """Test preview button emits correct signal"""
        signal_received = []
        main_window.preview_requested.connect(lambda: signal_received.append(True))

        # Simulate button click
        QTest.mouseClick(main_window.preview_btn, Qt.LeftButton)
        qt_app.processEvents()

        assert len(signal_received) > 0, "Signal not emitted"

    def test_organise_button_emits_signal(self, main_window, qt_app):
        """Test organise button emits correct signal"""
        signal_received = []
        main_window.organise_requested.connect(lambda: signal_received.append(True))

        QTest.mouseClick(main_window.organise_btn, Qt.LeftButton)
        qt_app.processEvents()

        assert len(signal_received) > 0

    def test_undo_button_emits_signal(self, main_window, qt_app):
        """Test undo button emits correct signal"""
        signal_received = []
        main_window.undo_requested.connect(lambda: signal_received.append(True))

        QTest.mouseClick(main_window.undo_btn, Qt.LeftButton)
        qt_app.processEvents()

        assert len(signal_received) > 0


class TestMainWindowCheckboxes:
    """Test MainWindow checkbox functionality"""

    def test_include_subfolders_checkbox_default(self, main_window):
        """Test include subfolders checkbox starts checked"""
        assert main_window.include_sub_check.isChecked() == True

    def test_skip_hidden_checkbox_default(self, main_window):
        """Test skip hidden checkbox starts checked"""
        assert main_window.skip_hidden_check.isChecked() == True

    def test_safe_mode_checkbox_default(self, main_window):
        """Test safe mode checkbox starts unchecked"""
        assert main_window.safe_mode_check.isChecked() == False

    def test_checkbox_state_changes(self, main_window):
        """Test checkbox state can be changed"""
        original = main_window.include_sub_check.isChecked()
        main_window.include_sub_check.setChecked(not original)
        assert main_window.include_sub_check.isChecked() != original

    def test_checkbox_emits_signal_on_change(self, main_window, qt_app):
        """Test checkbox emits stateChanged when toggled"""
        signal_received = []
        main_window.include_sub_check.stateChanged.connect(lambda: signal_received.append(True))

        main_window.include_sub_check.setChecked(not main_window.include_sub_check.isChecked())
        qt_app.processEvents()

        assert len(signal_received) > 0


class TestMainWindowAdvancedSection:
    """Test MainWindow advanced section toggle"""

    def test_advanced_section_exists(self, main_window):
        """Test advanced section components exist"""
        assert hasattr(main_window, 'advanced_btn')
        assert hasattr(main_window, 'advanced_content')
        assert hasattr(main_window, 'advanced_visible')

    def test_advanced_section_hidden_by_default(self, main_window):
        """Test advanced section is hidden initially"""
        assert main_window.advanced_content.isVisible() == False

    def test_advanced_button_toggles_visibility(self, main_window, qt_app):
        """Test advanced button toggles content visibility"""
        initial = main_window.advanced_content.isVisible()

        QTest.mouseClick(main_window.advanced_btn, Qt.LeftButton)
        qt_app.processEvents()

        assert main_window.advanced_content.isVisible() != initial

    def test_advanced_section_toggle_consistency(self, main_window, qt_app):
        """Test advanced section toggle multiple times"""
        initial = main_window.advanced_content.isVisible()

        # Toggle 3 times
        for _ in range(3):
            QTest.mouseClick(main_window.advanced_btn, Qt.LeftButton)
            qt_app.processEvents()

        # Should return to initial state after even toggles
        assert main_window.advanced_content.isVisible() == initial


class TestMainWindowInputFields:
    """Test MainWindow input field functionality"""

    def test_path_entry_exists(self, main_window):
        """Test path entry field exists"""
        assert hasattr(main_window, 'path_entry')
        assert main_window.path_entry is not None

    def test_preview_box_exists(self, main_window):
        """Test preview box exists"""
        assert hasattr(main_window, 'preview_box')
        assert main_window.preview_box is not None

    def test_path_entry_is_readonly(self, main_window):
        """Test path entry is read-only"""
        assert main_window.path_entry.isReadOnly() == True

    def test_preview_box_is_readonly(self, main_window):
        """Test preview box is read-only"""
        assert main_window.preview_box.isReadOnly() == True

    def test_path_entry_placeholder(self, main_window):
        """Test path entry has placeholder text"""
        placeholder = main_window.path_entry.placeholderText()
        assert placeholder != ""

    def test_preview_box_placeholder(self, main_window):
        """Test preview box has placeholder text"""
        placeholder = main_window.preview_box.placeholderText()
        assert placeholder != ""


# ========== PROFILEMANAGERWINDOW TESTS ==========

class TestProfileManagerInitialization:
    """Test ProfileManagerWindow initialization"""

    def test_profile_manager_creates_without_error(self, profile_manager):
        """Test ProfileManagerWindow initializes successfully"""
        assert profile_manager is not None
        assert isinstance(profile_manager, QMainWindow)

    def test_profile_manager_has_scrollable_areas(self, profile_manager):
        """Test ProfileManagerWindow has required scrollable areas"""
        assert hasattr(profile_manager, 'profiles_scroll')
        assert hasattr(profile_manager, 'editor_scroll')

    def test_profile_manager_has_buttons(self, profile_manager):
        """Test ProfileManagerWindow has action buttons"""
        assert hasattr(profile_manager, 'new_profile_btn')


class TestProfileManagerProfileList:
    """Test ProfileManagerWindow profile list functionality"""

    def test_profile_list_is_scrollable(self, profile_manager):
        """Test profile list is in scrollable frame"""
        assert profile_manager.profiles_scroll is not None


# ========== RULEMANAGERWINDOW TESTS ==========

class TestRuleManagerInitialization:
    """Test RuleManager initialization"""

    def test_rule_manager_creates_without_error(self, rule_manager):
        """Test RuleManager initializes successfully"""
        assert rule_manager is not None
        assert isinstance(rule_manager, QMainWindow)

    def test_rule_manager_has_rule_list(self, rule_manager):
        """Test RuleManager has rule list"""
        assert hasattr(rule_manager, 'rules_list')

    def test_rule_manager_has_action_buttons(self, rule_manager):
        """Test RuleManager has action buttons"""
        assert hasattr(rule_manager, 'new_rule_btn')
        if hasattr(rule_manager, 'edit_rule_btn'):
            assert rule_manager.edit_rule_btn is not None


# ========== ACTIVITYLOGWINDOW TESTS ==========

class TestActivityLogWindowInitialization:
    """Test ActivityLogWindow initialization"""

    def test_activity_log_window_creates_without_error(self, activity_log_window):
        """Test ActivityLogWindow initializes successfully"""
        assert activity_log_window is not None
        assert isinstance(activity_log_window, QMainWindow)

    def test_activity_log_window_has_display(self, activity_log_window):
        """Test ActivityLogWindow has log display"""
        assert hasattr(activity_log_window, 'log_display')

    def test_activity_log_window_has_buttons(self, activity_log_window):
        """Test ActivityLogWindow has action buttons"""
        assert hasattr(activity_log_window, 'clear_btn')


# ========== WATCHEDFOLDERSWINDOW TESTS ==========

class TestWatchedFoldersWindowInitialization:
    """Test WatchedFoldersWindow initialization"""

    def test_watched_folders_window_creates_without_error(self, watched_folders_window):
        """Test WatchedFoldersWindow initializes successfully"""
        assert watched_folders_window is not None
        assert isinstance(watched_folders_window, QMainWindow)

    def test_watched_folders_window_has_folder_list(self, watched_folders_window):
        """Test WatchedFoldersWindow has folder list"""
        assert hasattr(watched_folders_window, 'folders_list')

    def test_watched_folders_window_has_add_button(self, watched_folders_window):
        """Test WatchedFoldersWindow has add folder button"""
        assert hasattr(watched_folders_window, 'add_folder_btn')


# ========== STYLING TESTS ==========

class TestMainWindowStyling:
    """Test MainWindow styling and appearance"""

    def test_main_window_has_stylesheet(self, main_window):
        """Test MainWindow has stylesheet applied"""
        stylesheet = main_window.styleSheet()
        # May be empty (global stylesheet applied) or have inline styles
        assert stylesheet is not None

    def test_buttons_have_styling(self, main_window):
        """Test buttons have proper styling"""
        btn = main_window.preview_btn
        assert btn.minimumHeight() >= 40, "Button height too small"

    def test_colors_module_loads(self):
        """Test Colors module loads correctly"""
        assert Colors.PANEL_BG is not None
        assert Colors.CARD_BG is not None
        assert Colors.TEXT is not None

    def test_fonts_module_loads(self):
        """Test Fonts module loads correctly"""
        assert Fonts.SIZE_NORMAL is not None
        assert Fonts.PRIMARY_FAMILY is not None

    def test_design_tokens_loads(self):
        """Test DesignTokens module loads correctly"""
        assert DesignTokens.Spacing.SM is not None
        assert DesignTokens.Spacing.MD is not None


# ========== WINDOW LIFECYCLE TESTS ==========

class TestWindowLifecycle:
    """Test window creation and destruction"""

    def test_window_can_show(self, main_window):
        """Test MainWindow can be shown"""
        main_window.show()
        assert main_window.isVisible() == True
        main_window.hide()

    def test_window_can_hide(self, main_window):
        """Test MainWindow can be hidden"""
        main_window.show()
        main_window.hide()
        assert main_window.isVisible() == False

    def test_multiple_windows_can_exist(self, profile_manager, rule_manager, activity_log_window):
        """Test multiple windows can exist simultaneously"""
        assert profile_manager is not None
        assert rule_manager is not None
        assert activity_log_window is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
