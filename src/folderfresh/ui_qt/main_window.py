"""
PySide6 main window for FolderFresh migration.
QMainWindow with sidebar, main content area, and status bar.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QStackedWidget,
    QScrollArea,
    QFrame,
    QGridLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from .sidebar import SidebarWidget
from .status_bar import StatusBar
from .tooltip import ToolTip
from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    SuccessButton,
    TealButton,
    StyledLineEdit,
    StyledCheckBox,
    StyledLabel,
    StyledTextEdit,
    HeadingLabel,
    CardFrame,
    HorizontalFrame,
    VerticalFrame,
)


class MainWindow(QMainWindow):
    """Main application window with sidebar, content area, and status bar."""

    # Signals for main actions (no logic in UI, just event notification)
    folder_chosen = Signal(Path)
    preview_requested = Signal()
    organise_requested = Signal()
    undo_requested = Signal()
    duplicates_requested = Signal()
    desktop_clean_requested = Signal()
    profiles_requested = Signal()
    watched_folders_requested = Signal()
    help_requested = Signal()
    options_changed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FolderFresh")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(760, 520)
        self.setStyleSheet(f"QMainWindow {{ background-color: {Colors.PANEL_BG}; }}")

        self.selected_folder: Optional[Path] = None
        self.advanced_visible = False

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize main window UI."""
        # Create main container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main layout (vertical: content + status bar)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create horizontal splitter (sidebar + content)
        splitter = QSplitter(Qt.Horizontal)

        # Sidebar navigation
        self.sidebar = SidebarWidget()
        splitter.addWidget(self.sidebar)

        # Content area (scrollable)
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameStyle(QFrame.NoFrame)
        content_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Colors.PANEL_BG};
                border: none;
            }}
        """)

        # Content container
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {Colors.PANEL_BG};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)

        # Header section (title + folder selection)
        self._create_header_section(content_layout)

        # Main card (options, buttons, preview)
        self._create_main_card(content_layout)

        # Footer (credits)
        self._create_footer(content_layout)

        # Add stretch to push content to top
        content_layout.addStretch()

        content_scroll.setWidget(content_widget)
        splitter.addWidget(content_scroll)

        # Set splitter sizes
        splitter.setSizes([200, 1000])
        splitter.setCollapsible(0, False)

        main_layout.addWidget(splitter, 1)

        # Status bar at bottom
        self.status_bar_widget = StatusBar()
        main_layout.addWidget(self.status_bar_widget)

    def _create_header_section(self, parent_layout) -> None:
        """Create header with title and folder selection."""
        header_frame = CardFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(10)

        # Title
        title_label = StyledLabel(
            "FolderFresh",
            font_size=Fonts.SIZE_TITLE,
            bold=True,
        )
        header_layout.addWidget(title_label)

        # Folder path display (disabled entry)
        self.path_entry = StyledLineEdit(placeholder="Choose a folder to tidy…")
        self.path_entry.setReadOnly(True)
        header_layout.addWidget(self.path_entry, 1)

        # Folder selection buttons
        open_btn = StyledButton("Open Folder", bg_color=Colors.ACCENT)
        open_btn.clicked.connect(self._on_open_folder)
        header_layout.addWidget(open_btn)

        choose_btn = StyledButton("Choose Folder", bg_color=Colors.ACCENT)
        choose_btn.clicked.connect(self._on_choose_folder)
        header_layout.addWidget(choose_btn)

        parent_layout.addWidget(header_frame)

    def _create_main_card(self, parent_layout) -> None:
        """Create main card with options, buttons, and preview."""
        main_card = CardFrame()
        main_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
            }}
        """)
        main_layout = QVBoxLayout(main_card)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Basic options row
        self._create_basic_options(main_layout)

        # Action buttons row
        self._create_action_buttons(main_layout)

        # Preview section
        self._create_preview_section(main_layout)

        # Advanced options (collapsible)
        self._create_advanced_section(main_layout)

        parent_layout.addWidget(main_card)

    def _create_basic_options(self, parent_layout) -> None:
        """Create basic options checkboxes."""
        options_frame = HorizontalFrame(spacing=12)

        self.include_sub_check = StyledCheckBox("Include subfolders", checked=True)
        self.include_sub_check.stateChanged.connect(lambda: self.options_changed.emit())
        options_frame.add_widget(self.include_sub_check)

        self.skip_hidden_check = StyledCheckBox("Ignore hidden/system files", checked=True)
        self.skip_hidden_check.stateChanged.connect(lambda: self.options_changed.emit())
        options_frame.add_widget(self.skip_hidden_check)

        self.safe_mode_check = StyledCheckBox("Safe Mode (copy)", checked=False)
        self.safe_mode_check.stateChanged.connect(lambda: self.options_changed.emit())
        options_frame.add_widget(self.safe_mode_check)

        self.smart_mode_check = StyledCheckBox("Smart Sorting", checked=False)
        self.smart_mode_check.stateChanged.connect(lambda: self.options_changed.emit())
        options_frame.add_widget(self.smart_mode_check)
        ToolTip.attach_to(
            self.smart_mode_check,
            "Uses advanced rules to detect screenshots, assignments,\nphotos, invoices, messaging media and more."
        )

        self.watch_mode_check = StyledCheckBox("Auto-tidy", checked=False)
        self.watch_mode_check.stateChanged.connect(lambda: self.options_changed.emit())
        options_frame.add_widget(self.watch_mode_check)

        options_frame.add_stretch()

        parent_layout.addWidget(options_frame)

    def _create_action_buttons(self, parent_layout) -> None:
        """Create main action buttons row."""
        buttons_frame = HorizontalFrame(spacing=8)

        self.preview_btn = StyledButton("Preview", bg_color=Colors.ACCENT)
        self.preview_btn.clicked.connect(lambda: self.preview_requested.emit())
        buttons_frame.add_widget(self.preview_btn)

        self.organise_btn = SuccessButton("Organise Files")
        self.organise_btn.clicked.connect(lambda: self.organise_requested.emit())
        buttons_frame.add_widget(self.organise_btn)

        self.undo_btn = StyledButton("Undo Last", bg_color=Colors.BORDER_LIGHT)
        self.undo_btn.clicked.connect(lambda: self.undo_requested.emit())
        buttons_frame.add_widget(self.undo_btn)

        self.dupe_btn = StyledButton("Find Duplicates", bg_color=Colors.LIGHT_BLUE)
        self.dupe_btn.clicked.connect(lambda: self.duplicates_requested.emit())
        buttons_frame.add_widget(self.dupe_btn)

        self.desktop_btn = TealButton("Clean Desktop")
        self.desktop_btn.clicked.connect(lambda: self.desktop_clean_requested.emit())
        buttons_frame.add_widget(self.desktop_btn)

        parent_layout.addWidget(buttons_frame)

    def _create_preview_section(self, parent_layout) -> None:
        """Create preview text display area."""
        preview_label = HeadingLabel("Preview")
        parent_layout.addWidget(preview_label)

        self.preview_box = StyledTextEdit(placeholder="Select a folder and click Preview to see planned moves.")
        self.preview_box.setReadOnly(True)
        self.preview_box.setMaximumHeight(200)
        parent_layout.addWidget(self.preview_box)

    def _create_advanced_section(self, parent_layout) -> None:
        """Create collapsible advanced options section."""
        adv_frame = VerticalFrame(spacing=8)

        # Toggle button
        self.advanced_btn = StyledButton("Advanced Options ▼", bg_color=Colors.BORDER_LIGHT)
        self.advanced_btn.clicked.connect(self._toggle_advanced)
        adv_frame.add_widget(self.advanced_btn)

        # Hidden content frame
        self.advanced_content = VerticalFrame(spacing=6)
        self.advanced_content.setVisible(False)

        # Buttons in advanced section
        advanced_buttons = HorizontalFrame(spacing=6)

        manage_profiles_btn = StyledButton("Manage Profiles", bg_color=Colors.ACCENT)
        manage_profiles_btn.clicked.connect(lambda: self.profiles_requested.emit())
        advanced_buttons.add_widget(manage_profiles_btn)

        manage_folders_btn = StyledButton("Manage Watched Folders…", bg_color=Colors.ACCENT)
        manage_folders_btn.clicked.connect(lambda: self.watched_folders_requested.emit())
        advanced_buttons.add_widget(manage_folders_btn)

        advanced_buttons.add_stretch()
        self.advanced_content.add_widget(advanced_buttons)

        # Checkboxes in advanced section
        advanced_checks = HorizontalFrame(spacing=12)

        self.startup_check = StyledCheckBox("Run FolderFresh at Windows startup", checked=False)
        self.startup_check.stateChanged.connect(lambda: self.options_changed.emit())
        advanced_checks.add_widget(self.startup_check)

        self.tray_mode_check = StyledCheckBox("Run in background (tray)", checked=False)
        self.tray_mode_check.stateChanged.connect(lambda: self.options_changed.emit())
        advanced_checks.add_widget(self.tray_mode_check)

        advanced_checks.add_stretch()
        self.advanced_content.add_widget(advanced_checks)

        adv_frame.add_widget(self.advanced_content)
        parent_layout.addWidget(adv_frame)

        # Help button (positioned in advanced section)
        help_btn = StyledButton("?", bg_color=Colors.BORDER_LIGHT)
        help_btn.setMaximumWidth(40)
        help_btn.setMinimumHeight(40)
        help_btn.clicked.connect(lambda: self.help_requested.emit())
        adv_frame.add_widget(help_btn)

    def _create_footer(self, parent_layout) -> None:
        """Create footer with credits and version."""
        footer_frame = HorizontalFrame(spacing=8)

        credit_label = StyledLabel(
            "Made with ❤️ by Trihedron1240  |  Visit FolderFresh on GitHub",
            font_size=Fonts.SIZE_SMALL,
        )
        credit_label.setStyleSheet(
            f"""
            QLabel {{
                color: {Colors.MUTED};
                text-decoration: underline;
            }}
        """
        )
        footer_frame.add_widget(credit_label)

        footer_frame.add_stretch()

        version_label = StyledLabel(
            "v1.5.0",
            font_size=Fonts.SIZE_SMALL,
        )
        footer_frame.add_widget(version_label)

        parent_layout.addWidget(footer_frame)

    def _on_choose_folder(self) -> None:
        """Handle choose folder button (emits signal, no logic)."""
        self.folder_chosen.emit(None)

    def _on_open_folder(self) -> None:
        """Handle open folder button (emits signal, no logic)."""
        self.folder_chosen.emit(None)

    def _toggle_advanced(self) -> None:
        """Toggle advanced options visibility."""
        self.advanced_visible = not self.advanced_visible
        self.advanced_content.setVisible(self.advanced_visible)

        # Update button text
        arrow = "▲" if self.advanced_visible else "▼"
        self.advanced_btn.setText(f"Advanced Options {arrow}")

    # ========== PUBLIC METHODS FOR BACKEND INTEGRATION ==========

    def set_selected_folder(self, folder_path: Optional[Path]) -> None:
        """
        Set the selected folder path display.

        Args:
            folder_path: Path to display (None to clear)
        """
        if folder_path:
            self.selected_folder = folder_path
            self.path_entry.setText(str(folder_path))
        else:
            self.selected_folder = None
            self.path_entry.setText("")

    def get_selected_folder(self) -> Optional[Path]:
        """Get currently selected folder path."""
        return self.selected_folder

    def set_preview_text(self, text: str) -> None:
        """
        Update preview box text.

        Args:
            text: Preview text to display
        """
        self.preview_box.setPlainText(text)

    def set_status(self, text: str) -> None:
        """
        Update status bar message.

        Args:
            text: Status message
        """
        self.status_bar_widget.set_status(text)

    def set_progress(self, value: float) -> None:
        """
        Update progress bar (0.0-1.0).

        Args:
            value: Progress value from 0.0 to 1.0
        """
        self.status_bar_widget.set_progress(value)

    def set_progress_label(self, current: int, total: int) -> None:
        """
        Update progress label (e.g., "5/50").

        Args:
            current: Current count
            total: Total count
        """
        self.status_bar_widget.set_progress_label(current, total)

    def enable_action_buttons(self, enable: bool) -> None:
        """
        Enable/disable main action buttons based on folder selection.

        Args:
            enable: True to enable, False to disable
        """
        self.preview_btn.setEnabled(enable)
        self.organise_btn.setEnabled(enable)
        self.dupe_btn.setEnabled(enable)

    def get_options(self) -> dict:
        """
        Get current option states.

        Returns:
            Dictionary with option states
        """
        return {
            "include_subfolders": self.include_sub_check.isChecked(),
            "skip_hidden": self.skip_hidden_check.isChecked(),
            "safe_mode": self.safe_mode_check.isChecked(),
            "smart_sorting": self.smart_mode_check.isChecked(),
            "auto_tidy": self.watch_mode_check.isChecked(),
            "startup": self.startup_check.isChecked(),
            "tray_mode": self.tray_mode_check.isChecked(),
        }

    def set_options(self, options: dict) -> None:
        """
        Set option states from dictionary.

        Args:
            options: Dictionary with option states
        """
        if "include_subfolders" in options:
            self.include_sub_check.setChecked(options["include_subfolders"])
        if "skip_hidden" in options:
            self.skip_hidden_check.setChecked(options["skip_hidden"])
        if "safe_mode" in options:
            self.safe_mode_check.setChecked(options["safe_mode"])
        if "smart_sorting" in options:
            self.smart_mode_check.setChecked(options["smart_sorting"])
        if "auto_tidy" in options:
            self.watch_mode_check.setChecked(options["auto_tidy"])
        if "startup" in options:
            self.startup_check.setChecked(options["startup"])
        if "tray_mode" in options:
            self.tray_mode_check.setChecked(options["tray_mode"])


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
