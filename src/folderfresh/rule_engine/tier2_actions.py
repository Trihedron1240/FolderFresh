"""
Tier-2 Hazel-advanced actions for FolderFresh.

Includes:
- ColorLabelAction: Apply color labels to files
- AddTagAction / RemoveTagAction: Add/remove tags
- DeleteToTrashAction: Safe delete to recycle bin
- MarkAsDuplicateAction: Mark files as duplicates

All actions follow FolderFresh patterns:
- Inherit from Action base class
- Return dict with ok, log, meta
- Support safe_mode, dry_run, undo
- Implement idempotency (skip if no change)
"""

import os
import shutil
import time
import tempfile
from typing import Dict, Any
from .backbone import Action, normalize_path
from .tier2_metadata import METADATA_DB, calculate_quick_hash, calculate_full_hash


class ColorLabelAction(Action):
    """Apply a color label to a file."""

    def __init__(self, color: str):
        """
        Args:
            color: Color name (red, blue, green, yellow, orange, purple)
        """
        self.color = color.lower()

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Apply color label to file (idempotent).

        Args:
            fileinfo: File information dict
            config: Profile config with dry_run, safe_mode flags

        Returns:
            Dict with ok, log, meta for undo support
        """
        config = config or {}
        dry_run = config.get("dry_run", False)
        file_path = fileinfo.get("path")
        file_name = fileinfo.get("name", "unknown")

        # Validation
        if not file_path:
            message = "ERROR: COLOR_LABEL - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "color_label", "src": None, "color": None, "was_dry_run": dry_run}
            }

        if not os.path.exists(file_path):
            message = f"ERROR: COLOR_LABEL - file not found: {file_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "color_label", "src": file_path, "color": None, "was_dry_run": dry_run}
            }

        try:
            file_path = normalize_path(file_path)

            # SKIP CHECK: If file already has this color, skip (idempotent)
            current_color = METADATA_DB.get_color(file_path)
            if current_color and current_color.lower() == self.color:
                message = f"SKIP: COLOR_LABEL - already labeled '{self.color}'"
                print(f"  [ACTION] {message}")
                return {
                    "ok": True,
                    "log": message,
                    "meta": {
                        "type": "color_label",
                        "src": file_path,
                        "color": self.color,
                        "was_dry_run": dry_run,
                        "skipped": True
                    }
                }

            # Store old color for undo
            old_color = current_color

            if dry_run:
                message = f"DRY RUN: Would COLOR_LABEL: {file_name} -> {self.color}"
                ok = True
            else:
                # Apply color label
                if METADATA_DB.set_color(file_path, self.color):
                    message = f"COLOR_LABEL: {file_name} -> {self.color}"
                    ok = True
                else:
                    message = f"ERROR: COLOR_LABEL - could not set color"
                    ok = False

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "color_label",
                    "src": file_path,
                    "color": self.color,
                    "old_color": old_color,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: COLOR_LABEL failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "color_label", "src": file_path, "color": self.color, "was_dry_run": dry_run}
            }


class AddTagAction(Action):
    """Add a tag to a file."""

    def __init__(self, tag: str):
        """
        Args:
            tag: Tag string to add
        """
        self.tag = tag

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add tag to file (idempotent).

        Args:
            fileinfo: File information dict
            config: Profile config

        Returns:
            Dict with ok, log, meta for undo support
        """
        config = config or {}
        dry_run = config.get("dry_run", False)
        file_path = fileinfo.get("path")
        file_name = fileinfo.get("name", "unknown")

        # Validation
        if not file_path:
            message = "ERROR: ADD_TAG - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "add_tag", "src": None, "tag": None, "was_dry_run": dry_run}
            }

        if not os.path.exists(file_path):
            message = f"ERROR: ADD_TAG - file not found: {file_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "add_tag", "src": file_path, "tag": None, "was_dry_run": dry_run}
            }

        try:
            file_path = normalize_path(file_path)

            # SKIP CHECK: If tag already exists, skip (idempotent)
            if METADATA_DB.has_tag(file_path, self.tag):
                message = f"SKIP: ADD_TAG - tag '{self.tag}' already exists"
                print(f"  [ACTION] {message}")
                return {
                    "ok": True,
                    "log": message,
                    "meta": {
                        "type": "add_tag",
                        "src": file_path,
                        "tag": self.tag,
                        "was_dry_run": dry_run,
                        "skipped": True
                    }
                }

            if dry_run:
                message = f"DRY RUN: Would ADD_TAG: {file_name} -> {self.tag}"
                ok = True
            else:
                # Add tag
                if METADATA_DB.add_tag(file_path, self.tag):
                    message = f"ADD_TAG: {file_name} -> {self.tag}"
                    ok = True
                else:
                    message = f"ERROR: ADD_TAG - could not add tag"
                    ok = False

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "add_tag",
                    "src": file_path,
                    "tag": self.tag,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: ADD_TAG failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "add_tag", "src": file_path, "tag": self.tag, "was_dry_run": dry_run}
            }


class RemoveTagAction(Action):
    """Remove a tag from a file."""

    def __init__(self, tag: str):
        """
        Args:
            tag: Tag string to remove
        """
        self.tag = tag

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Remove tag from file (idempotent).

        Args:
            fileinfo: File information dict
            config: Profile config

        Returns:
            Dict with ok, log, meta for undo support
        """
        config = config or {}
        dry_run = config.get("dry_run", False)
        file_path = fileinfo.get("path")
        file_name = fileinfo.get("name", "unknown")

        # Validation
        if not file_path:
            message = "ERROR: REMOVE_TAG - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "remove_tag", "src": None, "tag": None, "was_dry_run": dry_run}
            }

        if not os.path.exists(file_path):
            message = f"ERROR: REMOVE_TAG - file not found: {file_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "remove_tag", "src": file_path, "tag": None, "was_dry_run": dry_run}
            }

        try:
            file_path = normalize_path(file_path)

            # SKIP CHECK: If tag doesn't exist, skip (idempotent)
            if not METADATA_DB.has_tag(file_path, self.tag):
                message = f"SKIP: REMOVE_TAG - tag '{self.tag}' not found"
                print(f"  [ACTION] {message}")
                return {
                    "ok": True,
                    "log": message,
                    "meta": {
                        "type": "remove_tag",
                        "src": file_path,
                        "tag": self.tag,
                        "was_dry_run": dry_run,
                        "skipped": True
                    }
                }

            if dry_run:
                message = f"DRY RUN: Would REMOVE_TAG: {file_name} <- {self.tag}"
                ok = True
            else:
                # Remove tag
                if METADATA_DB.remove_tag(file_path, self.tag):
                    message = f"REMOVE_TAG: {file_name} <- {self.tag}"
                    ok = True
                else:
                    message = f"ERROR: REMOVE_TAG - could not remove tag"
                    ok = False

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "remove_tag",
                    "src": file_path,
                    "tag": self.tag,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: REMOVE_TAG failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "remove_tag", "src": file_path, "tag": self.tag, "was_dry_run": dry_run}
            }


class DeleteToTrashAction(Action):
    """
    Safe delete to recycle bin using send2trash.
    Honors safe_mode (skips deletion in safe mode).
    """

    def __init__(self):
        pass

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Delete file to recycle bin (safe delete).

        Safe mode: Skips deletion (returns SKIP)
        Dry run: Preview only

        Args:
            fileinfo: File information dict
            config: Profile config with safe_mode, dry_run flags

        Returns:
            Dict with ok, log, meta for undo support
        """
        config = config or {}
        dry_run = config.get("dry_run", False)
        safe_mode = config.get("safe_mode", False)
        file_path = fileinfo.get("path")
        file_name = fileinfo.get("name", "unknown")

        # Validation
        if not file_path:
            message = "ERROR: DELETE_TO_TRASH - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "delete_to_trash", "src": None, "temp_backup": None, "was_dry_run": dry_run}
            }

        if not os.path.exists(file_path):
            message = f"ERROR: DELETE_TO_TRASH - file not found: {file_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "delete_to_trash", "src": file_path, "temp_backup": None, "was_dry_run": dry_run}
            }

        try:
            file_path = normalize_path(file_path)

            # SAFE MODE CHECK: Don't delete in safe mode
            if safe_mode:
                message = f"SAFE MODE: DELETE_TO_TRASH blocked - cannot delete files in safe mode"
                print(f"  [ACTION] {message}")
                return {
                    "ok": False,
                    "log": message,
                    "meta": {
                        "type": "delete_to_trash",
                        "src": file_path,
                        "temp_backup": None,
                        "was_dry_run": dry_run
                    }
                }

            temp_backup = None

            if dry_run:
                message = f"DRY RUN: Would DELETE_TO_TRASH: {file_name}"
                ok = True
            else:
                # Create temporary backup for undo support
                try:
                    temp_dir = tempfile.gettempdir()
                    filename = os.path.basename(file_path)
                    temp_backup = os.path.join(temp_dir, f"folderfresh_trash_{int(time.time())}_{filename}")
                    shutil.copy2(file_path, temp_backup)
                except Exception:
                    # If backup fails, continue with deletion but without undo support
                    temp_backup = None

                # Try to use send2trash for safe deletion
                try:
                    import send2trash
                    send2trash.send2trash(file_path)
                    message = f"DELETE_TO_TRASH: {file_name} -> Recycle Bin"
                    ok = True
                except ImportError:
                    # Fallback: use os.remove if send2trash not available
                    # (less safe, but better than nothing)
                    os.remove(file_path)
                    message = f"DELETE_TO_TRASH: {file_name} (permanent, send2trash not available)"
                    ok = True

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "delete_to_trash",
                    "src": file_path,
                    "temp_backup": temp_backup,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: DELETE_TO_TRASH failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "delete_to_trash", "src": file_path, "temp_backup": None, "was_dry_run": dry_run}
            }


class MarkAsDuplicateAction(Action):
    """Mark a file as a duplicate."""

    def __init__(self, tag: str = "duplicate", method: str = None):
        """
        Args:
            tag: Tag to apply to duplicates (default: "duplicate")
            method: Legacy parameter name (accepted for backwards compatibility, ignored)
        """
        # Support legacy 'method' parameter name for backwards compatibility
        if method is not None and tag == "duplicate":
            tag = method

        # Strip surrounding quotes if present
        self.tag = tag.strip('"') if isinstance(tag, str) else tag

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Mark file as duplicate (by adding a tag).

        Args:
            fileinfo: File information dict
            config: Profile config

        Returns:
            Dict with ok, log, meta for undo support
        """
        config = config or {}
        dry_run = config.get("dry_run", False)
        file_path = fileinfo.get("path")
        file_name = fileinfo.get("name", "unknown")

        # Validation
        if not file_path:
            message = "ERROR: MARK_DUPLICATE - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "mark_duplicate", "src": None, "was_dry_run": dry_run}
            }

        if not os.path.exists(file_path):
            message = f"ERROR: MARK_DUPLICATE - file not found: {file_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "mark_duplicate", "src": file_path, "was_dry_run": dry_run}
            }

        try:
            file_path = normalize_path(file_path)

            # Calculate quick hash and store for future duplicate detection
            try:
                file_size = os.path.getsize(file_path)
                hash_quick = calculate_quick_hash(file_path)
                METADATA_DB.set_hash(file_path, file_size, hash_quick)
            except Exception:
                pass

            # SKIP CHECK: If already marked as duplicate, skip
            if METADATA_DB.has_tag(file_path, self.tag):
                message = f"SKIP: MARK_DUPLICATE - already marked"
                print(f"  [ACTION] {message}")
                return {
                    "ok": True,
                    "log": message,
                    "meta": {
                        "type": "mark_duplicate",
                        "src": file_path,
                        "was_dry_run": dry_run,
                        "skipped": True
                    }
                }

            if dry_run:
                message = f"DRY RUN: Would MARK_DUPLICATE: {file_name}"
                ok = True
            else:
                # Add duplicate tag
                if METADATA_DB.add_tag(file_path, self.tag):
                    message = f"MARK_DUPLICATE: {file_name} tagged as '{self.tag}'"
                    ok = True
                else:
                    message = f"ERROR: MARK_DUPLICATE - could not tag file"
                    ok = False

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "mark_duplicate",
                    "src": file_path,
                    "tag": self.tag,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: MARK_DUPLICATE failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "mark_duplicate", "src": file_path, "was_dry_run": dry_run}
            }
