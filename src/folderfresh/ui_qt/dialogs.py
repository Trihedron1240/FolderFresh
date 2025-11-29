"""
PySide6 common dialog utilities for FolderFresh.
File dialogs, folder dialogs, and message boxes.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from .styles import Colors


# ========== CONFIRMATION DIALOGS ==========

def show_confirmation_dialog(
    parent,
    title: str,
    message: str,
    detail: str = "",
) -> bool:
    """
    Show a confirmation dialog (Yes/No).

    Args:
        parent: Parent widget
        title: Dialog title
        message: Main message text
        detail: Detailed explanation (optional)

    Returns:
        True if "Yes" clicked, False otherwise
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    if detail:
        msg_box.setDetailedText(detail)
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.No)
    msg_box.setIcon(QMessageBox.Question)

    _apply_dialog_styling(msg_box)

    return msg_box.exec() == QMessageBox.Yes


def show_info_dialog(
    parent,
    title: str,
    message: str,
    detail: str = "",
) -> None:
    """
    Show an information dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Message text
        detail: Detailed explanation (optional)
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    if detail:
        msg_box.setDetailedText(detail)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.setIcon(QMessageBox.Information)

    _apply_dialog_styling(msg_box)

    msg_box.exec()


def show_warning_dialog(
    parent,
    title: str,
    message: str,
    detail: str = "",
) -> None:
    """
    Show a warning dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Message text
        detail: Detailed explanation (optional)
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    if detail:
        msg_box.setDetailedText(detail)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.setIcon(QMessageBox.Warning)

    _apply_dialog_styling(msg_box)

    msg_box.exec()


def show_error_dialog(
    parent,
    title: str,
    message: str,
    detail: str = "",
) -> None:
    """
    Show an error dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Message text
        detail: Detailed explanation (optional)
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    if detail:
        msg_box.setDetailedText(detail)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.setIcon(QMessageBox.Critical)

    _apply_dialog_styling(msg_box)

    msg_box.exec()


def ask_save_changes_dialog(parent) -> Optional[bool]:
    """
    Show a "Save changes?" dialog (Save/Don't Save/Cancel).

    Args:
        parent: Parent widget

    Returns:
        True if "Save" clicked, False if "Don't Save", None if "Cancel"
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle("Unsaved Changes")
    msg_box.setText("You have unsaved changes. Do you want to save before closing?")
    msg_box.setStandardButtons(
        QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
    )
    msg_box.setDefaultButton(QMessageBox.Save)
    msg_box.setIcon(QMessageBox.Warning)

    _apply_dialog_styling(msg_box)

    result = msg_box.exec()
    if result == QMessageBox.Save:
        return True
    elif result == QMessageBox.Discard:
        return False
    else:
        return None


# ========== FILE/FOLDER DIALOGS ==========

def browse_folder_dialog(
    parent,
    title: str = "Select Folder",
    start_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Show a folder selection dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        start_dir: Starting directory (defaults to home or last used)

    Returns:
        Selected folder path, or None if cancelled
    """
    start_path = str(start_dir) if start_dir else str(Path.home())

    folder = QFileDialog.getExistingDirectory(
        parent,
        title,
        start_path,
        options=QFileDialog.ShowDirsOnly,
    )

    if folder:
        return Path(folder)
    return None


def browse_file_dialog(
    parent,
    title: str = "Select File",
    start_dir: Optional[Path] = None,
    file_filter: str = "All Files (*.*)",
) -> Optional[Path]:
    """
    Show a file selection dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        start_dir: Starting directory
        file_filter: File type filter (e.g., "Text Files (*.txt);;All Files (*.*)")

    Returns:
        Selected file path, or None if cancelled
    """
    start_path = str(start_dir) if start_dir else str(Path.home())

    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        title,
        start_path,
        file_filter,
    )

    if file_path:
        return Path(file_path)
    return None


def browse_multiple_files_dialog(
    parent,
    title: str = "Select Files",
    start_dir: Optional[Path] = None,
    file_filter: str = "All Files (*.*)",
) -> list[Path]:
    """
    Show a multiple file selection dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        start_dir: Starting directory
        file_filter: File type filter

    Returns:
        List of selected file paths (empty list if cancelled)
    """
    start_path = str(start_dir) if start_dir else str(Path.home())

    files, _ = QFileDialog.getOpenFileNames(
        parent,
        title,
        start_path,
        file_filter,
    )

    return [Path(f) for f in files] if files else []


def save_file_dialog(
    parent,
    title: str = "Save File",
    start_dir: Optional[Path] = None,
    file_filter: str = "All Files (*.*)",
    default_filename: str = "",
) -> Optional[Path]:
    """
    Show a file save dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        start_dir: Starting directory
        file_filter: File type filter
        default_filename: Default filename to suggest

    Returns:
        Selected file path, or None if cancelled
    """
    start_path = str(start_dir) if start_dir else str(Path.home())
    if default_filename:
        start_path = str(Path(start_path) / default_filename)

    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        title,
        start_path,
        file_filter,
    )

    if file_path:
        return Path(file_path)
    return None


# ========== INPUT DIALOGS ==========

def ask_text_dialog(
    parent,
    title: str,
    label: str,
    default_text: str = "",
) -> Optional[str]:
    """
    Show a text input dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        label: Input label
        default_text: Default text value

    Returns:
        Entered text, or None if cancelled
    """
    text, ok = QInputDialog.getText(
        parent,
        title,
        label,
        text=default_text,
    )

    return text if ok else None


def ask_int_dialog(
    parent,
    title: str,
    label: str,
    default_value: int = 0,
    min_value: int = -2147483647,
    max_value: int = 2147483647,
) -> Optional[int]:
    """
    Show an integer input dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        label: Input label
        default_value: Default integer value
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Entered integer, or None if cancelled
    """
    value, ok = QInputDialog.getInt(
        parent,
        title,
        label,
        default_value,
        min_value,
        max_value,
    )

    return value if ok else None


def ask_choice_dialog(
    parent,
    title: str,
    label: str,
    choices: list[str],
    current_index: int = 0,
) -> Optional[str]:
    """
    Show a choice dialog (combo box).

    Args:
        parent: Parent widget
        title: Dialog title
        label: Prompt text
        choices: List of options
        current_index: Currently selected index

    Returns:
        Selected choice, or None if cancelled
    """
    choice, ok = QInputDialog.getItem(
        parent,
        title,
        label,
        choices,
        current_index,
    )

    return choice if ok else None


# ========== HELPER FUNCTIONS ==========

def _apply_dialog_styling(dialog) -> None:
    """Apply FolderFresh theme to message boxes and dialogs."""
    # Set window background
    dialog.setStyleSheet(
        f"""
        QMessageBox {{
            background-color: {Colors.PANEL_BG};
        }}
        QLabel {{
            color: {Colors.TEXT};
        }}
        QPushButton {{
            background-color: {Colors.ACCENT};
            color: {Colors.TEXT};
            border: 1px solid #1e4fd8;
            border-radius: 4px;
            padding: 6px 12px;
            min-width: 60px;
        }}
        QPushButton:hover {{
            background-color: #1e4fd8;
        }}
        QPushButton:pressed {{
            background-color: #1636c4;
        }}
    """
    )

    # Apply to all buttons
    for button in dialog.findChildren(type(dialog.findChildren(object)[0]).__bases__[0]):
        if hasattr(button, "setText"):
            continue
