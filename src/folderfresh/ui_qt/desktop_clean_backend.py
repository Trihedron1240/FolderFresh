"""
Backend for safe desktop cleaning.
Performs pre-checks, generates preview, and executes desktop organization.
"""

from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
import os
import shutil

from PySide6.QtCore import QObject, Signal

from folderfresh.logger_qt import log_error, log_info
from folderfresh.utils import scan_dir


class DesktopCleanBackend(QObject):
    """Backend for safe desktop cleaning with pre-checks and preview."""

    # Signals
    preview_generated = Signal(list)  # List of file moves
    operation_complete = Signal(bool, str)  # success, message
    error_occurred = Signal(str)  # error message

    def __init__(self):
        """Initialize desktop clean backend."""
        super().__init__()

    def get_desktop_path(self) -> Optional[Path]:
        """
        Get the user's desktop path.

        Returns:
            Path to desktop or None if not found
        """
        try:
            desktop = Path(os.path.expanduser("~")) / "Desktop"
            if desktop.exists():
                return desktop
        except Exception as e:
            log_error(f"Error getting desktop path: {e}")
        return None

    def check_desktop_safety(self, desktop: Path) -> Tuple[bool, List[str]]:
        """
        Perform pre-organization safety checks on desktop.

        Args:
            desktop: Desktop path

        Returns:
            Tuple of (safe: bool, warnings: List[str])
        """
        warnings = []

        # Check if desktop exists
        if not desktop.exists():
            warnings.append("Desktop folder does not exist")
            return False, warnings

        # Check if desktop is accessible
        try:
            list(desktop.iterdir())
        except PermissionError:
            warnings.append("No permission to access Desktop")
            return False, warnings
        except Exception as e:
            warnings.append(f"Error accessing Desktop: {e}")
            return False, warnings

        # Check for cloud sync
        try:
            # Look for cloud sync markers
            for item in desktop.iterdir():
                if item.name.startswith("~$"):
                    warnings.append(f"Cloud synced file detected: {item.name}")
                if item.is_dir() and item.name in ["OneDrive", "Dropbox", "iCloud Drive"]:
                    warnings.append(f"Cloud sync folder found: {item.name}")
        except Exception as e:
            log_error(f"Error checking for cloud sync: {e}")

        # Check available disk space (need at least 100MB free)
        try:
            stat_info = shutil.disk_usage(desktop)
            free_mb = stat_info.free / (1024 * 1024)
            if free_mb < 100:
                warnings.append(f"Low disk space: only {free_mb:.0f}MB free (need 100MB+)")
        except Exception as e:
            log_error(f"Error checking disk space: {e}")

        return len(warnings) == 0, warnings

    def count_files_to_organize(self, desktop: Path) -> Tuple[int, int]:
        """
        Count files and folders on desktop.

        Args:
            desktop: Desktop path

        Returns:
            Tuple of (file_count, folder_count)
        """
        try:
            file_count = 0
            folder_count = 0
            for item in desktop.iterdir():
                if item.is_file():
                    file_count += 1
                elif item.is_dir():
                    folder_count += 1
            return file_count, folder_count
        except Exception as e:
            log_error(f"Error counting desktop files: {e}")
            return 0, 0

    def get_important_files(self, desktop: Path) -> List[str]:
        """
        Identify important files that should be protected.

        Args:
            desktop: Desktop path

        Returns:
            List of important file names
        """
        important_patterns = [
            ".lnk",      # Shortcuts
            ".url",      # URL shortcuts
            ".exe",      # Executables
            ".bat",      # Batch files
            ".cmd",      # CMD files
            ".com",      # COM files
            "thumbs.db", # System file
            "desktop.ini", # System file
        ]

        important_files = []
        try:
            for item in desktop.iterdir():
                if item.is_file():
                    if item.name.lower() in [p.lower() for p in important_patterns]:
                        important_files.append(item.name)
                    if item.suffix.lower() in important_patterns:
                        important_files.append(item.name)
        except Exception as e:
            log_error(f"Error scanning for important files: {e}")

        return important_files

    def generate_preview(
        self,
        desktop: Path,
        config: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Generate a preview of what will be organized.

        Args:
            desktop: Desktop path
            config: Configuration dictionary with ignore options

        Returns:
            Tuple of (preview_list, info_messages)
        """
        preview = []
        info = []

        try:
            # Get ignore extensions
            ignore_exts = config.get("ignore_exts", "")
            ignore_set = {ext.strip().lower() for ext in ignore_exts.split(";") if ext.strip()}

            # Scan desktop (no subfolders for desktop)
            files = scan_dir(
                desktop,
                include_sub=False,
                skip_hidden=config.get("skip_hidden", True),
                ignore_set=ignore_set,
                skip_categories=False,
            )

            # Group by file type
            file_count = len(files)
            if file_count == 0:
                info.append("No files to organize on Desktop")
                return [], info

            # Simple categorization preview
            categories = {}
            for file_path in files:
                # Determine category
                ext = file_path.suffix.lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.heic']:
                    category = 'Images'
                elif ext == '.pdf':
                    category = 'PDF'
                elif ext in ['.doc', '.docx', '.txt', '.rtf', '.odt', '.ppt', '.pptx', '.xls', '.xlsx', '.csv']:
                    category = 'Documents'
                elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
                    category = 'Videos'
                elif ext in ['.mp3', '.wav', '.flac', '.m4a', '.aac']:
                    category = 'Audio'
                elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    category = 'Archives'
                else:
                    category = 'Other'

                if category not in categories:
                    categories[category] = []
                categories[category].append(file_path)

            # Build preview
            for category, file_list in sorted(categories.items()):
                preview.append({
                    'category': category,
                    'count': len(file_list),
                    'files': [str(f.name) for f in file_list[:5]],  # First 5 files
                    'has_more': len(file_list) > 5,
                })

            # Generate info messages
            info.append(f"Found {file_count} files on Desktop")
            info.append(f"Will create {len(categories)} categories: {', '.join(sorted(categories.keys()))}")

            return preview, info

        except Exception as e:
            error_msg = f"Error generating preview: {e}"
            log_error(error_msg)
            return [], [error_msg]

    def get_protection_info(self, desktop: Path) -> Dict[str, Any]:
        """
        Get information about file protection status.

        Args:
            desktop: Desktop path

        Returns:
            Dictionary with protection info
        """
        important_files = self.get_important_files(desktop)
        file_count, folder_count = self.count_files_to_organize(desktop)

        return {
            'file_count': file_count,
            'folder_count': folder_count,
            'important_files': important_files,
            'has_important': len(important_files) > 0,
        }
