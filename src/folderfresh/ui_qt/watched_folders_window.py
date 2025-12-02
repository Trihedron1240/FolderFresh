"""
PySide6 watched folders window for FolderFresh.
Manage which folders are monitored for Auto-Tidy.
"""

from pathlib import Path
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    StyledComboBox,
    StyledLabel,
    HeadingLabel,
    ScrollableFrame,
    HorizontalFrame,
    VerticalFrame,
    CardFrame,
)


class WatchedFoldersWindow(QDialog):
    """Dialog for managing watched folders and their associated profiles."""

    # Signals
    add_folder_clicked = Signal()
    remove_folder_clicked = Signal(str)  # folder_path
    profile_changed = Signal(str, str)  # folder_path, profile_id
    folder_toggled = Signal(str, bool)  # folder_path, is_active
    closed = Signal()

    def __init__(self, parent=None):
        """
        Initialize watched folders window.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Manage Watched Folders")
        self.setGeometry(200, 200, 600, 500)
        self.setMinimumSize(500, 400)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        # Internal state
        self.folder_rows: Dict[str, dict] = {}  # folder_path -> {"frame": QFrame, "dropdown": QComboBox}
        self.available_profiles: List[str] = []  # List of profile IDs
        self.profile_names: Dict[str, str] = {}  # profile_id -> profile_name
        self.selected_folder: Optional[str] = None  # Currently selected folder path

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel("Watched Folders")
        main_layout.addWidget(title)

        # Help text
        help_text = StyledLabel(
            "These folders are monitored by Auto-Tidy. Select a profile for each folder to determine which rules apply.",
            font_size=Fonts.SIZE_SMALL,
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet(f"color: {Colors.MUTED};")
        main_layout.addWidget(help_text)

        # Scrollable folder list
        self.folder_scroll = ScrollableFrame()
        main_layout.addWidget(self.folder_scroll, 0)  # Don't stretch - use content size

        # Add stretch after scroll area so buttons stay at bottom
        main_layout.addStretch()

        # Button row
        button_frame = HorizontalFrame(spacing=8)

        add_btn = StyledButton("Add Folder", bg_color=Colors.ACCENT)
        add_btn.clicked.connect(lambda: self.add_folder_clicked.emit())
        button_frame.add_widget(add_btn)

        self.remove_btn = StyledButton("Remove Folder", bg_color=Colors.DANGER)
        self.remove_btn.clicked.connect(self._on_remove_folder_clicked)
        self.remove_btn.setEnabled(False)  # Disabled until folder is selected
        button_frame.add_widget(self.remove_btn)

        button_frame.add_stretch()

        close_btn = StyledButton("Close", bg_color=Colors.BORDER_LIGHT)
        close_btn.clicked.connect(self.accept)
        button_frame.add_widget(close_btn)

        main_layout.addWidget(button_frame)

    def set_profiles(self, profiles: Dict[str, str]) -> None:
        """
        Set available profiles.

        Args:
            profiles: Dict of profile_id -> profile_name
        """
        self.profile_names = profiles
        self.available_profiles = list(profiles.keys())

        # Update all dropdowns with new profiles
        for folder_path, row_data in self.folder_rows.items():
            dropdown = row_data["dropdown"]
            dropdown.clear()
            for pid in self.available_profiles:
                dropdown.addItem(self.profile_names.get(pid, pid), pid)

    def add_watched_folder(self, folder_path: Path, profile_id: str, is_active: bool = True) -> None:
        """
        Add a watched folder to the list.

        Args:
            folder_path: Path to the folder
            profile_id: Profile ID assigned to this folder
            is_active: Whether the folder is actively monitored
        """
        folder_str = str(folder_path)

        # Skip if already exists
        if folder_str in self.folder_rows:
            return

        # Create folder row frame (clickable)
        row_frame = CardFrame()
        row_frame.setCursor(Qt.PointingHandCursor)
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(10, 8, 10, 8)
        row_layout.setSpacing(12)

        # Folder path label
        folder_label = StyledLabel(folder_str, font_size=Fonts.SIZE_NORMAL)
        folder_label.setWordWrap(True)
        row_layout.addWidget(folder_label, 1)

        # Status indicator (small circle)
        status_label = QLabel("●")
        status_color = Colors.SUCCESS if is_active else Colors.MUTED
        status_label.setStyleSheet(f"color: {status_color}; font-size: 12pt;")
        status_label.setMaximumWidth(20)
        row_layout.addWidget(status_label)

        # Profile dropdown
        profile_dropdown = StyledComboBox(font_size=Fonts.SIZE_NORMAL)
        profile_dropdown.setMinimumWidth(150)
        profile_dropdown.currentIndexChanged.connect(
            lambda: self._on_profile_changed(folder_str)
        )

        # Populate dropdown
        for pid in self.available_profiles:
            profile_dropdown.addItem(self.profile_names.get(pid, pid), pid)

        # Select current profile
        index = profile_dropdown.findData(profile_id)
        if index >= 0:
            profile_dropdown.setCurrentIndex(index)

        row_layout.addWidget(profile_dropdown)

        # Pause/Resume button
        pause_btn = StyledButton(
            "⏸ Pause" if is_active else "▶ Resume",
            bg_color=Colors.DANGER if is_active else Colors.ACCENT,
        )
        pause_btn.setMaximumWidth(100)
        pause_btn.clicked.connect(lambda: self._on_pause_resume_clicked(folder_str))
        row_layout.addWidget(pause_btn)

        # Store row data
        self.folder_rows[folder_str] = {
            "frame": row_frame,
            "label": folder_label,
            "status": status_label,
            "dropdown": profile_dropdown,
            "pause_btn": pause_btn,
            "is_active": is_active,
            "is_selected": False,
        }

        # Make row clickable
        row_frame.mousePressEvent = lambda event: self._on_folder_row_clicked(folder_str)

        self.folder_scroll.add_widget(row_frame)

    def remove_watched_folder(self, folder_path: Path) -> None:
        """
        Remove a watched folder from the list.

        Args:
            folder_path: Path to the folder to remove
        """
        folder_str = str(folder_path)

        if folder_str in self.folder_rows:
            row_data = self.folder_rows[folder_str]
            row_data["frame"].deleteLater()
            del self.folder_rows[folder_str]

            # Clear selection if the removed folder was selected
            if self.selected_folder == folder_str:
                self.selected_folder = None
                self.remove_btn.setEnabled(False)

    def clear_folders(self) -> None:
        """Clear all watched folders."""
        self.folder_scroll.clear()
        self.folder_rows.clear()
        self.selected_folder = None
        self.remove_btn.setEnabled(False)

    def get_watched_folders(self) -> Dict[str, str]:
        """
        Get current watched folders and their profiles.

        Returns:
            Dict of folder_path -> profile_id
        """
        result = {}
        for folder_str, row_data in self.folder_rows.items():
            dropdown = row_data["dropdown"]
            profile_id = dropdown.currentData()
            result[folder_str] = profile_id
        return result

    def set_folder_active(self, folder_path: Path, is_active: bool) -> None:
        """
        Update the active status of a watched folder.

        Args:
            folder_path: Path to the folder
            is_active: Whether the folder is actively monitored
        """
        folder_str = str(folder_path)

        if folder_str in self.folder_rows:
            row_data = self.folder_rows[folder_str]
            row_data["is_active"] = is_active

            # Update status indicator
            status_color = Colors.SUCCESS if is_active else Colors.MUTED
            row_data["status"].setStyleSheet(f"color: {status_color}; font-size: 12pt;")

            # Update pause/resume button
            if "pause_btn" in row_data:
                pause_btn = row_data["pause_btn"]
                pause_btn.setText("⏸ Pause" if is_active else "▶ Resume")
                bg_color = Colors.DANGER if is_active else Colors.ACCENT
                pause_btn.setStyleSheet(f"background-color: {bg_color}; color: white; border: none; border-radius: 6px; padding: 8px 12px;")

    def _on_profile_changed(self, folder_path: str) -> None:
        """
        Handle profile dropdown change.

        Args:
            folder_path: Path to the folder
        """
        if folder_path in self.folder_rows:
            dropdown = self.folder_rows[folder_path]["dropdown"]
            profile_id = dropdown.currentData()
            self.profile_changed.emit(folder_path, profile_id)

    def _on_pause_resume_clicked(self, folder_path: str) -> None:
        """
        Handle pause/resume button click.

        Args:
            folder_path: Path to the folder
        """
        if folder_path in self.folder_rows:
            row_data = self.folder_rows[folder_path]
            current_state = row_data["is_active"]
            new_state = not current_state
            self.folder_toggled.emit(folder_path, new_state)

    def refresh_folders(self, folders: List[tuple], profiles: Dict[str, str]) -> None:
        """
        Refresh the watched folders list.

        Args:
            folders: List of (folder_path, profile_id, is_active) tuples
            profiles: Dict of profile_id -> profile_name
        """
        self.clear_folders()
        self.set_profiles(profiles)

        for folder_path, profile_id, is_active in folders:
            self.add_watched_folder(Path(folder_path), profile_id, is_active)

    def add_folder_to_list(self, folder_path: str) -> None:
        """
        Add a folder to the watched folders list.

        Args:
            folder_path: Path to the folder
        """
        self.add_watched_folder(Path(folder_path), "Default", is_active=True)

    def remove_folder_from_list(self, folder_path: str) -> None:
        """
        Remove a folder from the watched folders list.

        Args:
            folder_path: Path to the folder
        """
        self.remove_watched_folder(Path(folder_path))

    def update_folder_profile(self, folder_path: str, profile_id: str) -> None:
        """
        Update the profile for a watched folder.

        Args:
            folder_path: Path to the folder
            profile_id: Profile ID to assign
        """
        folder_str = str(folder_path)
        if folder_str in self.folder_rows:
            dropdown = self.folder_rows[folder_str]["dropdown"]
            index = dropdown.findData(profile_id)
            if index >= 0:
                dropdown.setCurrentIndex(index)

    def _on_folder_row_clicked(self, folder_path: str) -> None:
        """
        Handle folder row click for selection.

        Args:
            folder_path: Path to the folder that was clicked
        """
        # Deselect previous folder
        if self.selected_folder and self.selected_folder in self.folder_rows:
            old_row_data = self.folder_rows[self.selected_folder]
            old_row_data["is_selected"] = False
            old_row_data["frame"].setStyleSheet(
                f"background-color: {Colors.CARD_BG}; border-radius: 4px;"
            )

        # Select new folder
        self.selected_folder = folder_path
        if folder_path in self.folder_rows:
            row_data = self.folder_rows[folder_path]
            row_data["is_selected"] = True
            # Highlight selected folder with accent color
            row_data["frame"].setStyleSheet(
                f"background-color: {Colors.ACCENT}; border-radius: 4px; opacity: 0.2;"
            )

        # Enable remove button when folder is selected
        self.remove_btn.setEnabled(True)

    def _on_remove_folder_clicked(self) -> None:
        """Handle remove folder button click."""
        if self.selected_folder:
            self.remove_folder_clicked.emit(self.selected_folder)
            # Reset selection
            self.selected_folder = None
            self.remove_btn.setEnabled(False)

    def closeEvent(self, event):
        """Handle window close event."""
        self.closed.emit()
        self.accept()
        event.accept()
