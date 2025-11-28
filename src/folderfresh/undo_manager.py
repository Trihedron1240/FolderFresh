# undo_manager.py
"""
Undo/Rollback system for FolderFresh.

Provides UndoManager class for recording and reverting file operations
(move, rename, copy) with safety checks and Activity Log integration.
"""

import os
import shutil
from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional


def normalize_path(path: str) -> str:
    """Normalize a file path for consistent comparisons."""
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.abspath(path)
    return path


def _avoid_overwrite(dest_path: str) -> str:
    """
    If a file already exists at dest_path, generate a new path with a suffix.
    Used when restoring files during undo to prevent overwriting existing content.

    Examples:
        "file.txt" -> "file.txt" (if doesn't exist)
        "file.txt" -> "file (1).txt" (if file.txt exists)
        "file.txt" -> "file (2).txt" (if file (1).txt exists, etc.)

    Args:
        dest_path: The intended destination path

    Returns:
        A safe destination path that doesn't overwrite existing files
    """
    if not os.path.exists(dest_path):
        return dest_path

    # Split path into components
    parent_dir = os.path.dirname(dest_path)
    filename = os.path.basename(dest_path)
    name, ext = os.path.splitext(filename)

    # Try incrementing counter until we find an available name
    counter = 1
    while True:
        new_filename = f"{name} ({counter}){ext}"
        new_path = os.path.join(parent_dir, new_filename)
        if not os.path.exists(new_path):
            return new_path
        counter += 1


class UndoManager:
    """
    Manages undo/rollback operations for file actions.

    Stores a LIFO stack of undo entries, each containing the information
    needed to reverse a file operation (move, rename, copy).

    Attributes:
        MAX_ENTRIES: Maximum number of undo entries to keep in memory (default 200)
    """

    MAX_ENTRIES = 200

    def __init__(self):
        """Initialize the undo manager with an empty stack."""
        self.stack: deque = deque(maxlen=self.MAX_ENTRIES)

    def record_action(self, entry: Dict[str, Any]) -> None:
        """
        Record an action in the undo stack.

        Expected entry schema:
        {
            "type": "move" | "rename" | "copy",
            "src": str,                    # Original path
            "dst": str,                    # New path (for move)
            "old_name": str,               # Original name (for rename)
            "new_name": str,               # New name (for rename)
            "collision_handled": bool,     # If safe_mode created a different path
            "was_dry_run": bool,           # False for real operations
            "timestamp": str,              # ISO format timestamp
            "status": str                  # "recorded" or other status
        }

        Args:
            entry: Undo entry dict with action metadata
        """
        if not isinstance(entry, dict):
            return

        # Ensure timestamp exists
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()

        # Mark as recorded
        entry["status"] = "recorded"

        self.stack.append(entry)

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get all undo entries in reverse chronological order (newest first).

        Returns:
            List of undo entries (most recent first)
        """
        return list(reversed(list(self.stack)))

    def clear_history(self) -> None:
        """Clear all undo entries."""
        self.stack.clear()

    def pop_last(self) -> Optional[Dict[str, Any]]:
        """
        Remove and return the most recent undo entry without executing it.

        Returns:
            The entry dict or None if stack is empty
        """
        if not self.stack:
            return None
        return self.stack.pop()

    def undo_last(self) -> Dict[str, Any]:
        """
        Undo the most recent action.

        Returns a result dict with:
        {
            "success": bool,
            "message": str,
            "entry": dict or None
        }

        The message is also appended to Activity Log.
        """
        if not self.stack:
            result = {
                "success": False,
                "message": "No undo history available",
                "entry": None
            }
            self._log_result(result)
            return result

        entry = self.stack.pop()
        return self.undo_entry(entry)

    def undo_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an undo operation for a specific entry.

        Implements reversal for move, rename, and copy operations:
        - move: src -> dst becomes dst -> src (if dst exists)
        - rename: old_name -> new_name becomes new_name -> old_name (if new_name exists)
        - copy: delete the copy (if it exists)

        Args:
            entry: Undo entry dict from the stack

        Returns:
            Result dict with success status and message
        """
        action_type = entry.get("type", "unknown")

        if action_type == "move":
            return self._undo_move(entry)
        elif action_type == "rename":
            return self._undo_rename(entry)
        elif action_type == "copy":
            return self._undo_copy(entry)
        else:
            result = {
                "success": False,
                "message": f"Unknown undo action type: {action_type}",
                "entry": entry
            }
            self._log_result(result)
            return result

    def _undo_move(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Undo a move operation: restore file from dst back to src.

        Args:
            entry: Move undo entry with src and dst paths

        Returns:
            Result dict with success status and message
        """
        try:
            src = entry.get("src")
            dst = entry.get("dst")

            # Validate entry
            if not src or not dst:
                result = {
                    "success": False,
                    "message": "UNDO MOVE: Missing source or destination path in entry",
                    "entry": entry
                }
                self._log_result(result)
                return result

            # Normalize paths
            src = normalize_path(src)
            dst = normalize_path(dst)

            # Check if destination (where we moved the file) exists
            if not os.path.exists(dst):
                result = {
                    "success": False,
                    "message": f"UNDO MOVE: File not found at destination: {dst}",
                    "entry": entry
                }
                self._log_result(result)
                return result

            # Handle collision: if source path now exists, use safe name
            restore_path = src
            collision_handled = False
            if os.path.exists(src):
                restore_path = _avoid_overwrite(src)
                collision_handled = True

            # Move file back to original location
            shutil.move(dst, restore_path)

            message = f"UNDO MOVE: Restored {dst} -> {restore_path}"
            if collision_handled:
                message += " (collision avoided)"

            result = {
                "success": True,
                "message": message,
                "entry": entry,
                "restore_path": restore_path
            }
            self._log_result(result)
            return result

        except Exception as e:
            result = {
                "success": False,
                "message": f"UNDO MOVE failed: {str(e)}",
                "entry": entry
            }
            self._log_result(result)
            return result

    def _undo_rename(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Undo a rename operation: restore file from new_name back to old_name.

        Args:
            entry: Rename undo entry with old_name and new_name

        Returns:
            Result dict with success status and message
        """
        try:
            # In rename, we store the full paths
            src = entry.get("src")  # This is the file with new name
            old_name = entry.get("old_name")
            new_name = entry.get("new_name")

            # Validate entry
            if not src or not old_name or not new_name:
                result = {
                    "success": False,
                    "message": "UNDO RENAME: Missing source, old_name, or new_name in entry",
                    "entry": entry
                }
                self._log_result(result)
                return result

            # src is the current path with the new name
            src = normalize_path(src)

            # Check if file with new name exists
            if not os.path.exists(src):
                result = {
                    "success": False,
                    "message": f"UNDO RENAME: File not found: {src}",
                    "entry": entry
                }
                self._log_result(result)
                return result

            # Get parent directory and construct original path
            parent_dir = os.path.dirname(src)
            original_path = os.path.join(parent_dir, old_name)
            original_path = normalize_path(original_path)

            # Handle collision: if original path now exists, use safe name
            restore_path = original_path
            collision_handled = False
            if os.path.exists(original_path):
                restore_path = _avoid_overwrite(original_path)
                collision_handled = True

            # Rename file back to original name
            os.rename(src, restore_path)

            message = f"UNDO RENAME: Restored {new_name} -> {old_name}"
            if collision_handled:
                message += " (collision avoided)"

            result = {
                "success": True,
                "message": message,
                "entry": entry,
                "restore_path": restore_path
            }
            self._log_result(result)
            return result

        except Exception as e:
            result = {
                "success": False,
                "message": f"UNDO RENAME failed: {str(e)}",
                "entry": entry
            }
            self._log_result(result)
            return result

    def _undo_copy(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Undo a copy operation: delete the copied file.

        Args:
            entry: Copy undo entry with dst path (the copied file)

        Returns:
            Result dict with success status and message
        """
        try:
            dst = entry.get("dst")

            # Validate entry
            if not dst:
                result = {
                    "success": False,
                    "message": "UNDO COPY: Missing destination path in entry",
                    "entry": entry
                }
                self._log_result(result)
                return result

            # Normalize path
            dst = normalize_path(dst)

            # Check if copied file exists
            if not os.path.exists(dst):
                result = {
                    "success": False,
                    "message": f"UNDO COPY: Copy not found at: {dst}",
                    "entry": entry
                }
                self._log_result(result)
                return result

            # Delete the copy
            if os.path.isfile(dst):
                os.remove(dst)
            else:
                result = {
                    "success": False,
                    "message": f"UNDO COPY: Path is not a file: {dst}",
                    "entry": entry
                }
                self._log_result(result)
                return result

            message = f"UNDO COPY: Deleted copy at {dst}"

            result = {
                "success": True,
                "message": message,
                "entry": entry
            }
            self._log_result(result)
            return result

        except Exception as e:
            result = {
                "success": False,
                "message": f"UNDO COPY failed: {str(e)}",
                "entry": entry
            }
            self._log_result(result)
            return result

    def _log_result(self, result: Dict[str, Any]) -> None:
        """
        Append the undo result to Activity Log.

        Args:
            result: Result dict with success and message
        """
        try:
            from folderfresh.activity_log import log_activity
            log_activity(result["message"])
        except ImportError:
            # Activity Log not available, silent fallback
            pass

    def __len__(self) -> int:
        """Return the number of entries in the undo stack."""
        return len(self.stack)


# Global singleton instance
UNDO_MANAGER = UndoManager()
