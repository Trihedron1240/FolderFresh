"""
PySide6 UI components for FolderFresh.
Parallel migration from CustomTkinter.
"""

# Main components
from .main_window import MainWindow
from .sidebar import SidebarWidget
from .status_bar import StatusBar
from .tooltip import ToolTip
from .help_window import HelpWindow
from .watched_folders_window import WatchedFoldersWindow
from .action_editor import ActionEditor
from .condition_editor import ConditionEditor
from .condition_selector import ConditionSelectorPopup
from .rule_editor import RuleEditor
from .rule_simulator import RuleSimulator
from .rule_manager import RuleManager
from .activity_log_window import ActivityLogWindow
from .category_manager import CategoryManagerWindow
from .profile_manager import ProfileManagerWindow
from .duplicate_finder_window import DuplicateFinderWindow
from .duplicate_finder_backend import DuplicateFinderBackend
from .desktop_clean_backend import DesktopCleanBackend
from .desktop_clean_dialog import DesktopCleanDialog

# Application and integration (Phase 7)
from .application import FolderFreshApplication
from .tray import TrayIcon, create_tray, hide_tray, is_tray_visible, update_tray_menu
from .main_qt import launch_qt_app, setup_qt_app, setup_stylesheet

# Styling and utilities
from .styles import Colors, Fonts, DesignTokens
from .component_showcase import ComponentShowcaseWindow
from .stylesheet_cohesive import get_global_stylesheet, apply_cohesive_theme
from .dialogs import (
    show_confirmation_dialog,
    show_info_dialog,
    show_warning_dialog,
    show_error_dialog,
    ask_save_changes_dialog,
    browse_folder_dialog,
    browse_file_dialog,
    browse_multiple_files_dialog,
    save_file_dialog,
    ask_text_dialog,
    ask_int_dialog,
    ask_choice_dialog,
)

# Base widgets
from .base_widgets import (
    StyledButton,
    SuccessButton,
    DangerButton,
    TealButton,
    StyledLineEdit,
    StyledTextEdit,
    StyledComboBox,
    StyledCheckBox,
    StyledLabel,
    TitleLabel,
    HeadingLabel,
    MutedLabel,
    CardFrame,
    SeparatorFrame,
    ScrollableFrame,
    HorizontalFrame,
    VerticalFrame,
)

__all__ = [
    # Main components
    "MainWindow",
    "SidebarWidget",
    "StatusBar",
    "ToolTip",
    "HelpWindow",
    "WatchedFoldersWindow",
    # Editors
    "ActionEditor",
    "ConditionEditor",
    "ConditionSelectorPopup",
    "RuleEditor",
    "RuleSimulator",
    # Manager windows (Phase 6)
    "RuleManager",
    "ActivityLogWindow",
    "CategoryManagerWindow",
    "ProfileManagerWindow",
    "DuplicateFinderWindow",
    "DuplicateFinderBackend",
    "DesktopCleanBackend",
    "DesktopCleanDialog",
    # Application and integration (Phase 7)
    "FolderFreshApplication",
    "TrayIcon",
    "create_tray",
    "hide_tray",
    "is_tray_visible",
    "update_tray_menu",
    "launch_qt_app",
    "setup_qt_app",
    "setup_stylesheet",
    # Styling
    "Colors",
    "Fonts",
    "DesignTokens",
    "ComponentShowcaseWindow",
    "get_global_stylesheet",
    "apply_cohesive_theme",
    # Dialogs
    "show_confirmation_dialog",
    "show_info_dialog",
    "show_warning_dialog",
    "show_error_dialog",
    "ask_save_changes_dialog",
    "browse_folder_dialog",
    "browse_file_dialog",
    "browse_multiple_files_dialog",
    "save_file_dialog",
    "ask_text_dialog",
    "ask_int_dialog",
    "ask_choice_dialog",
    # Base widgets
    "StyledButton",
    "SuccessButton",
    "DangerButton",
    "TealButton",
    "StyledLineEdit",
    "StyledTextEdit",
    "StyledComboBox",
    "StyledCheckBox",
    "StyledLabel",
    "TitleLabel",
    "HeadingLabel",
    "MutedLabel",
    "CardFrame",
    "SeparatorFrame",
    "ScrollableFrame",
    "HorizontalFrame",
    "VerticalFrame",
]
