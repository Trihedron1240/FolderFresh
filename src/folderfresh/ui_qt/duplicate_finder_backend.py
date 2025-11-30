"""
Backend for duplicate file finding.
Scans folders and groups duplicate files by content hash.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from threading import Thread

from PySide6.QtCore import QObject, Signal

from folderfresh.logger_qt import log_error, log_info
from folderfresh.utils import scan_dir, group_duplicates


class DuplicateFinderBackend(QObject):
    """Backend for finding duplicate files."""

    # Signals
    duplicates_found = Signal(list)  # List of duplicate groups
    scan_progress = Signal(int, int)  # current, total
    scan_complete = Signal()
    scan_error = Signal(str)  # error message

    def __init__(self):
        """Initialize duplicate finder backend."""
        super().__init__()
        self._scan_thread: Optional[Thread] = None
        self._is_scanning = False

    def find_duplicates(
        self,
        folder: Path,
        include_subfolders: bool = True,
        skip_hidden: bool = True,
        ignore_extensions: Optional[List[str]] = None,
    ) -> List[List[Path]]:
        """
        Find duplicate files in folder (blocking call).

        Args:
            folder: Folder to scan
            include_subfolders: Include subfolders in scan
            skip_hidden: Skip hidden files
            ignore_extensions: Extensions to ignore (e.g., ['.exe', '.tmp'])

        Returns:
            List of duplicate groups (each group is a list of Paths)
        """
        try:
            # Create ignore set
            ignore_set = set()
            if ignore_extensions:
                ignore_set = {ext.lower() for ext in ignore_extensions}

            log_info(f"Scanning for duplicates in: {folder}")

            # Scan directory
            files = scan_dir(
                folder,
                include_subfolders=include_subfolders,
                skip_hidden=skip_hidden,
                ignore_exts=ignore_set,
                skip_categories=False,  # Include all files, even in category folders
            )

            log_info(f"Found {len(files)} files to check for duplicates")

            # Group duplicates
            groups = group_duplicates(files)

            # Filter to only include groups with actual duplicates (more than 1 file)
            duplicate_groups = [group for group in groups if len(group) > 1]

            log_info(f"Found {len(duplicate_groups)} duplicate groups")

            return duplicate_groups

        except Exception as e:
            error_msg = f"Error finding duplicates: {e}"
            log_error(error_msg)
            self.scan_error.emit(error_msg)
            return []

    def find_duplicates_async(
        self,
        folder: Path,
        include_subfolders: bool = True,
        skip_hidden: bool = True,
        ignore_extensions: Optional[List[str]] = None,
    ) -> None:
        """
        Find duplicates asynchronously.

        Args:
            folder: Folder to scan
            include_subfolders: Include subfolders in scan
            skip_hidden: Skip hidden files
            ignore_extensions: Extensions to ignore
        """
        if self._is_scanning:
            log_error("Scan already in progress")
            return

        self._is_scanning = True

        def _scan():
            try:
                duplicate_groups = self.find_duplicates(
                    folder=folder,
                    include_subfolders=include_subfolders,
                    skip_hidden=skip_hidden,
                    ignore_extensions=ignore_extensions,
                )
                self.duplicates_found.emit(duplicate_groups)
                self.scan_complete.emit()
            except Exception as e:
                error_msg = f"Error in async scan: {e}"
                log_error(error_msg)
                self.scan_error.emit(error_msg)
            finally:
                self._is_scanning = False

        self._scan_thread = Thread(target=_scan, daemon=True)
        self._scan_thread.start()

    def is_scanning(self) -> bool:
        """Check if scan is in progress."""
        return self._is_scanning

    def cancel_scan(self) -> None:
        """Cancel ongoing scan (if possible)."""
        self._is_scanning = False
