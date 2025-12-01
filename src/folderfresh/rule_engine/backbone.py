from dataclasses import dataclass
from typing import Any, List, Dict
import os
import shutil
import time
import re
import threading
from datetime import datetime
from pathlib import Path

# Import activity logging (optional import to avoid circular dependencies)
try:
    from folderfresh.activity_log import log_activity
except ImportError:
    # Fallback if activity_log not available
    def log_activity(msg: str):
        pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_path(path: str) -> str:
    """
    Normalize a file path for Windows compatibility.
    - Expands ~ to home directory
    - Normalizes slashes
    - Converts to absolute path

    Args:
        path: Raw path string

    Returns:
        Normalized absolute path
    """
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.abspath(path)
    return path


def ensure_directory_exists(target_dir: str) -> bool:
    """
    Ensure that a target directory exists, creating it if necessary.

    Args:
        target_dir: Path to the directory

    Returns:
        True if directory exists or was created, False if creation failed
    """
    try:
        target_dir = normalize_path(target_dir)
        os.makedirs(target_dir, exist_ok=True)
        return True
    except Exception:
        return False


def avoid_overwrite(dest_path: str) -> str:
    """
    If a file already exists at dest_path, generate a new path with a suffix.

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


def is_file_accessible(file_path: str) -> bool:
    """
    Check if a file exists and is accessible.

    Args:
        file_path: Path to the file

    Returns:
        True if file exists and is readable
    """
    try:
        return os.path.isfile(file_path) and os.access(file_path, os.R_OK)
    except Exception:
        return False


# ============================================================================
# CONDITIONS
# ============================================================================

class Condition:
    """
    Base class for all conditions.
    A condition evaluates to True/False based on file info.
    """

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate this condition against file info.

        Args:
            fileinfo: dict with keys like 'name', 'ext', 'path', 'size', etc.

        Returns:
            True if condition is met, False otherwise.
        """
        raise NotImplementedError


class NameContainsCondition(Condition):
    """Check if filename contains a substring."""

    def __init__(self, substring: str):
        self.substring = substring

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        filename = fileinfo.get("name", "")
        result = self.substring.lower() in filename.lower()
        print(f"  [CONDITION] NameContains '{self.substring}' in '{filename}' -> {result}")
        return result


class ExtensionIsCondition(Condition):
    """Check if file extension matches (case-insensitive)."""

    def __init__(self, extension: str):
        # Normalize: remove leading dot if present
        self.extension = extension.lstrip(".").lower()

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        file_ext = fileinfo.get("ext", "").lstrip(".").lower()
        result = file_ext == self.extension
        print(f"  [CONDITION] ExtensionIs '.{self.extension}' with '.{file_ext}' -> {result}")
        return result


class FileSizeGreaterThanCondition(Condition):
    """Check if file size exceeds a threshold (in bytes)."""

    def __init__(self, min_bytes: int):
        self.min_bytes = min_bytes

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        size = fileinfo.get("size", 0)
        result = size > self.min_bytes
        print(f"  [CONDITION] FileSizeGreaterThan {self.min_bytes} bytes with {size} bytes -> {result}")
        return result


class FileAgeGreaterThanCondition(Condition):
    """Check if file age exceeds a threshold (in days)."""

    def __init__(self, days: int):
        self.days = days

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if file is older than the specified number of days.

        Uses st_mtime from fileinfo['stat'] if available, falls back to os.path.getmtime.
        Negative days are treated as always False (invalid input).
        """
        if self.days < 0:
            return False

        try:
            # Try to get mtime from stat object first
            if "stat" in fileinfo and hasattr(fileinfo["stat"], "st_mtime"):
                mtime = fileinfo["stat"].st_mtime
            else:
                # Fallback to os.path.getmtime
                file_path = fileinfo.get("path")
                if not file_path:
                    return False
                mtime = os.path.getmtime(file_path)

            current_time = time.time()
            age_seconds = current_time - mtime
            threshold_seconds = self.days * 86400

            result = age_seconds > threshold_seconds

            # Format age as days for logging
            age_days = age_seconds / 86400
            print(f"  [CONDITION] FileAgeGreaterThan {self.days}d with age={age_days:.1f}d -> {result}")
            return result
        except Exception as e:
            print(f"  [CONDITION] FileAgeGreaterThan {self.days}d -> ERROR: {e}")
            return False


class LastModifiedBeforeCondition(Condition):
    """Check if file was last modified before a specific timestamp."""

    def __init__(self, timestamp: str):
        """
        Initialize with a timestamp.

        Args:
            timestamp: ISO8601 string (e.g., "2024-01-01" or "2024-01-01T10:00:00")
                      or datetime object
        """
        self.timestamp = timestamp if isinstance(timestamp, str) else str(timestamp)

    @staticmethod
    def _parse_iso_datetime(s: str) -> datetime:
        """
        Parse ISO8601 datetime string.

        Accepts:
        - "2024-01-01" (date only)
        - "2024-01-01T10:00:00" (full datetime)
        - datetime objects (passed through)

        Returns:
            datetime object or None if parsing fails
        """
        if isinstance(s, datetime):
            return s

        if not isinstance(s, str):
            return None

        # Try parsing date-only format
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            pass

        # Try other common formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue

        return None

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if file was last modified before the specified timestamp.

        Returns False if:
        - timestamp parsing failed
        - file mtime cannot be retrieved
        """
        parsed_timestamp = self._parse_iso_datetime(self.timestamp)
        if parsed_timestamp is None:
            print(f"  [CONDITION] LastModifiedBefore {self.timestamp} -> ERROR: Invalid timestamp format")
            return False

        try:
            # Try to get mtime from stat object first
            if "stat" in fileinfo and hasattr(fileinfo["stat"], "st_mtime"):
                mtime = fileinfo["stat"].st_mtime
            else:
                # Fallback to os.path.getmtime
                file_path = fileinfo.get("path")
                if not file_path:
                    return False
                mtime = os.path.getmtime(file_path)

            file_mtime_dt = datetime.fromtimestamp(mtime)
            result = file_mtime_dt < parsed_timestamp

            print(f"  [CONDITION] LastModifiedBefore {self.timestamp} -> {result}")
            return result
        except Exception as e:
            print(f"  [CONDITION] LastModifiedBefore {self.timestamp} -> ERROR: {e}")
            return False


class IsHiddenCondition(Condition):
    """Check if file is hidden (Unix-style dot prefix or Windows attribute)."""

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if file is hidden.

        Returns True if:
        - filename starts with "." (Unix convention)
        - OR file has Windows hidden attribute (if available)
        """
        try:
            # Check Unix-style hidden (dot prefix)
            filename = fileinfo.get("name", "")
            if filename.startswith("."):
                print(f"  [CONDITION] IsHidden '{filename}' -> True")
                return True

            # Check Windows hidden attribute if available
            if "stat" in fileinfo and hasattr(fileinfo["stat"], "st_file_attributes"):
                FILE_ATTRIBUTE_HIDDEN = 0x2
                attributes = fileinfo["stat"].st_file_attributes
                is_hidden = bool(attributes & FILE_ATTRIBUTE_HIDDEN)
                print(f"  [CONDITION] IsHidden '{filename}' (Windows attr) -> {is_hidden}")
                return is_hidden

            print(f"  [CONDITION] IsHidden '{filename}' -> False")
            return False
        except Exception as e:
            print(f"  [CONDITION] IsHidden -> ERROR: {e}")
            return False


class IsReadOnlyCondition(Condition):
    """Check if file is read-only (no write permissions)."""

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if file is read-only (cannot be written to).

        Returns True if:
        - os.access(path, os.W_OK) returns False (no write permission)
        - OR stat.st_mode indicates read-only
        """
        try:
            file_path = fileinfo.get("path")
            if not file_path:
                print(f"  [CONDITION] IsReadOnly -> False (no path)")
                return False

            # Try os.access first (most reliable)
            can_write = os.access(file_path, os.W_OK)
            is_readonly = not can_write

            print(f"  [CONDITION] IsReadOnly '{file_path}' -> {is_readonly}")
            return is_readonly
        except Exception as e:
            print(f"  [CONDITION] IsReadOnly -> ERROR: {e}")
            return False


class IsDirectoryCondition(Condition):
    """Check if path is a directory."""

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if the path is a directory.

        Returns True if os.path.isdir(path) is True.
        """
        try:
            file_path = fileinfo.get("path")
            if not file_path:
                print(f"  [CONDITION] IsDirectory -> False (no path)")
                return False

            is_dir = os.path.isdir(file_path)
            filename = fileinfo.get("name", "")
            print(f"  [CONDITION] IsDirectory '{filename}' -> {is_dir}")
            return is_dir
        except Exception as e:
            print(f"  [CONDITION] IsDirectory -> ERROR: {e}")
            return False


class NameStartsWithCondition(Condition):
    """Check if filename (without extension) starts with a prefix."""

    def __init__(self, prefix: str):
        self.prefix = prefix

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if filename starts with the prefix (case-insensitive).

        Uses filename without extension from fileinfo["name"].
        """
        try:
            filename = fileinfo.get("name", "")
            # Case-insensitive comparison
            result = filename.lower().startswith(self.prefix.lower())
            print(f"  [CONDITION] NameStartsWith '{self.prefix}' in '{filename}' -> {result}")
            return result
        except Exception as e:
            print(f"  [CONDITION] NameStartsWith '{self.prefix}' -> ERROR: {e}")
            return False


class NameEndsWithCondition(Condition):
    """Check if filename (without extension) ends with a suffix."""

    def __init__(self, suffix: str):
        self.suffix = suffix

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if filename (without extension) ends with the suffix (case-insensitive).

        Strips extension from fileinfo["name"] before comparison.
        """
        try:
            filename = fileinfo.get("name", "")
            # Remove extension from filename for comparison
            name_without_ext = os.path.splitext(filename)[0]
            # Case-insensitive comparison
            result = name_without_ext.lower().endswith(self.suffix.lower())
            print(f"  [CONDITION] NameEndsWith '{self.suffix}' in '{name_without_ext}' -> {result}")
            return result
        except Exception as e:
            print(f"  [CONDITION] NameEndsWith '{self.suffix}' -> ERROR: {e}")
            return False


class NameEqualsCondition(Condition):
    """Check if filename exactly equals a value."""

    def __init__(self, value: str, case_sensitive: bool = False):
        self.value = value
        self.case_sensitive = case_sensitive

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if filename (without extension) exactly equals the value.

        Args:
            fileinfo: File information dict

        Returns:
            True if filename matches exactly (respecting case_sensitive setting)
        """
        try:
            filename = fileinfo.get("name", "")
            # Remove extension from filename for comparison
            name_without_ext = os.path.splitext(filename)[0]

            if self.case_sensitive:
                result = name_without_ext == self.value
            else:
                result = name_without_ext.lower() == self.value.lower()

            case_str = "case-sensitive" if self.case_sensitive else "case-insensitive"
            print(f"  [CONDITION] NameEquals '{self.value}' with '{name_without_ext}' ({case_str}) -> {result}")
            return result
        except Exception as e:
            print(f"  [CONDITION] NameEquals '{self.value}' -> ERROR: {e}")
            return False


class RegexMatchCondition(Condition):
    """Check if filename matches a regex pattern with catastrophic backtracking protection."""

    # Timeout in seconds for regex evaluation (100ms)
    REGEX_TIMEOUT = 0.1

    def __init__(self, pattern: str, ignore_case: bool = False):
        # Strip leading/trailing whitespace from pattern (handles JSON/config newlines)
        self.pattern = pattern.strip() if isinstance(pattern, str) else pattern
        self.ignore_case = ignore_case
        self._compiled = None  # Private attribute, not serialized

        # Try to compile the regex pattern
        try:
            flags = re.IGNORECASE if ignore_case else 0
            self._compiled = re.compile(self.pattern, flags)
        except re.error as e:
            # Invalid regex pattern - log but don't crash
            print(f"  [CONDITION] RegexMatch: Invalid pattern '{self.pattern}': {e}")
            self._compiled = None

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if filename matches the regex pattern with timeout protection.

        Args:
            fileinfo: File information dict

        Returns:
            True if filename matches regex (or False if pattern invalid or times out)
        """
        # If pattern failed to compile, return False
        if self._compiled is None:
            filename = fileinfo.get("name", "")
            print(f"  [CONDITION] RegexMatch '{self.pattern}' in '{filename}' -> False (invalid pattern)")
            return False

        try:
            filename = fileinfo.get("name", "")
            if not filename:
                print(f"  [CONDITION] RegexMatch '{self.pattern}' in '' -> False (no filename)")
                return False

            # Use thread-based timeout to prevent catastrophic backtracking
            result_container = {"result": None, "completed": False}

            def match_with_timeout():
                try:
                    result_container["result"] = bool(self._compiled.search(filename))
                    result_container["completed"] = True
                except Exception:
                    # Catastrophic backtracking or other regex error
                    result_container["result"] = False
                    result_container["completed"] = True

            thread = threading.Thread(target=match_with_timeout, daemon=True)
            thread.start()
            thread.join(timeout=self.REGEX_TIMEOUT)

            # If thread didn't complete in time, it's a timeout (likely catastrophic backtracking)
            if not result_container["completed"]:
                print(f"  [CONDITION] RegexMatch '{self.pattern}' in '{filename}' -> False (timeout)")
                return False

            result = result_container["result"]
            case_str = "(ignore-case)" if self.ignore_case else ""
            print(f"  [CONDITION] RegexMatch '{self.pattern}' {case_str} in '{filename}' -> {result}")
            return result

        except Exception as e:
            filename = fileinfo.get("name", "")
            print(f"  [CONDITION] RegexMatch '{self.pattern}' in '{filename}' -> ERROR: {e}")
            return False


class ParentFolderContainsCondition(Condition):
    """Check if parent folder name contains a substring."""

    def __init__(self, substring: str):
        self.substring = substring

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if parent folder name contains the substring (case-insensitive).

        Args:
            fileinfo: File information dict with "path" key

        Returns:
            True if substring found in parent folder name
        """
        try:
            path = fileinfo.get("path", "")
            if not path:
                print(f"  [CONDITION] ParentFolderContains '{self.substring}' in '' -> False (no path)")
                return False

            # Extract parent folder name
            parent_name = Path(path).parent.name
            if not parent_name:
                print(f"  [CONDITION] ParentFolderContains '{self.substring}' in '' -> False (no parent)")
                return False

            # Case-insensitive substring search
            result = self.substring.lower() in parent_name.lower()
            print(f"  [CONDITION] ParentFolderContains '{self.substring}' in '{parent_name}' -> {result}")
            return result

        except Exception as e:
            path = fileinfo.get("path", "")
            print(f"  [CONDITION] ParentFolderContains '{self.substring}' in '{path}' -> ERROR: {e}")
            return False


class FileInFolderCondition(Condition):
    """Check if file's parent path contains a folder pattern."""

    def __init__(self, folder_pattern: str):
        self.folder_pattern = folder_pattern

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Evaluate if folder_pattern appears anywhere in the parent path (case-insensitive).

        Args:
            fileinfo: File information dict with "path" key

        Returns:
            True if folder_pattern found in parent path
        """
        try:
            path = fileinfo.get("path", "")
            if not path:
                print(f"  [CONDITION] FileInFolder '{self.folder_pattern}' in '' -> False (no path)")
                return False

            # Extract full parent path (not just the last segment)
            parent_path = str(Path(path).parent)
            if not parent_path:
                print(f"  [CONDITION] FileInFolder '{self.folder_pattern}' in '' -> False (no parent)")
                return False

            # Case-insensitive substring search in full parent path
            result = self.folder_pattern.lower() in parent_path.lower()
            print(f"  [CONDITION] FileInFolder '{self.folder_pattern}' in '{parent_path}' -> {result}")
            return result

        except Exception as e:
            path = fileinfo.get("path", "")
            print(f"  [CONDITION] FileInFolder '{self.folder_pattern}' in '{path}' -> ERROR: {e}")
            return False


# ============================================================================
# ACTIONS
# ============================================================================

class Action:
    """
    Base class for all actions.
    An action performs some operation on a file.
    """

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute this action on the file.

        Args:
            fileinfo: dict with file information (name, path, size, ext, etc.)
            config: dict with merged profile configuration (safe_mode, etc.)

        Returns:
            A dict with:
            {
                "ok": bool,              # True if action succeeded
                "log": str,              # Log message for Activity Log
                "meta": {
                    "type": str,         # "move", "rename", or "copy"
                    "src": str,          # Original file path
                    "dst": str,          # New file path (for move)
                    "old_name": str,     # Original name (for rename)
                    "new_name": str,     # New name (for rename)
                    "collision_handled": bool  # If safe_mode created different path
                }
            }
        """
        raise NotImplementedError("Subclasses must implement run()")


class RenameAction(Action):
    """Rename a file to a new name."""

    def __init__(self, new_name: str):
        self.new_name = new_name

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Rename a file to a new name with guaranteed collision avoidance.

        Args:
            fileinfo: File information dict with 'path' and 'name' keys
            config: Profile config with 'safe_mode' and 'dry_run' flags

        Returns:
            Dict with ok, log, and meta keys for undo support
        """
        config = config or {}
        old_path = fileinfo.get("path")
        old_name = fileinfo.get("name")
        dry_run = config.get("dry_run", False)

        # Validation
        if not old_path:
            message = f"ERROR: RENAME - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "rename", "src": None, "old_name": None, "new_name": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        if not is_file_accessible(old_path):
            message = f"ERROR: RENAME - source file not found or not accessible: {old_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "rename", "src": old_path, "old_name": old_name, "new_name": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        if not self.new_name or not str(self.new_name).strip():
            message = f"ERROR: RENAME - new name is empty"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "rename", "src": old_path, "old_name": old_name, "new_name": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        try:
            old_path = normalize_path(old_path)
            parent_dir = os.path.dirname(old_path)

            # Preserve extension from original file if new name doesn't have one
            new_name = str(self.new_name).strip()
            if new_name and not os.path.splitext(new_name)[1]:
                # New name has no extension, so append the original extension
                _, ext = os.path.splitext(old_name or os.path.basename(old_path))
                new_name = new_name + ext

            new_path = os.path.join(parent_dir, new_name)
            new_path = normalize_path(new_path)

            # SKIP CHECK: If old and new paths are identical, skip (idempotent)
            if os.path.normcase(os.path.abspath(old_path)) == os.path.normcase(os.path.abspath(new_path)):
                message = f"SKIP: RENAME - already named '{new_name}'"
                print(f"  [ACTION] {message}")
                return {
                    "ok": True,  # Not an error, just skipped
                    "log": message,
                    "meta": {
                        "type": "rename",
                        "src": old_path,
                        "old_name": old_name,
                        "new_name": new_name,
                        "collision_handled": False,
                        "skipped": True,
                        "was_dry_run": dry_run
                    }
                }

            # Track if collision was handled
            collision_handled = False

            # CRITICAL FIX: Use avoid_overwrite() to get a safe destination
            # This is now called BEFORE the actual rename, ensuring atomicity
            if config.get("safe_mode", True):
                new_path_safe = avoid_overwrite(new_path)
                collision_handled = (new_path_safe != new_path)
                new_path = new_path_safe

            if dry_run:
                message = f"DRY RUN: Would RENAME: {old_path} -> {new_path}"
            else:
                # Perform the rename operation
                # IMPORTANT: At this point, new_path is guaranteed to not exist
                # because avoid_overwrite() checked and adjusted it if needed
                os.rename(old_path, new_path)
                message = f"RENAME: {old_path} -> {new_path}"

            print(f"  [ACTION] {message}")
            return {
                "ok": True,
                "log": message,
                "meta": {
                    "type": "rename",
                    "src": new_path if not dry_run else old_path,  # Store where file is (or would be)
                    "old_name": old_name,
                    "new_name": new_name,  # Use the name with extension preserved
                    "collision_handled": collision_handled,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: RENAME failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "rename", "src": old_path, "old_name": old_name, "new_name": self.new_name, "collision_handled": False, "was_dry_run": dry_run}
            }


class MoveAction(Action):
    """Move a file to a new directory."""

    def __init__(self, target_dir: str):
        self.target_dir = target_dir

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Move a file to a new directory with guaranteed collision avoidance.

        Args:
            fileinfo: File information dict with 'path' and 'name' keys
            config: Profile config with 'safe_mode' and 'dry_run' flags

        Returns:
            Dict with ok, log, and meta keys for undo support
        """
        config = config or {}
        old_path = fileinfo.get("path")
        filename = fileinfo.get("name")
        dry_run = config.get("dry_run", False)

        # Validation
        if not old_path:
            message = f"ERROR: MOVE - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "move", "src": None, "dst": None, "collision_handled": False}
            }

        if not filename:
            message = f"ERROR: MOVE - filename missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "move", "src": old_path, "dst": None, "collision_handled": False}
            }

        if not is_file_accessible(old_path):
            message = f"ERROR: MOVE - source file not found or not accessible: {old_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "move", "src": old_path, "dst": None, "collision_handled": False}
            }

        if not self.target_dir or not str(self.target_dir).strip():
            message = f"ERROR: MOVE - target directory is empty"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "move", "src": old_path, "dst": None, "collision_handled": False}
            }

        try:
            old_path = normalize_path(old_path)

            # Expand tokens in target_dir if it contains any
            target_dir = self.target_dir
            if "<" in target_dir and ">" in target_dir:
                try:
                    from folderfresh.rule_engine.tier1_actions import expand_tokens
                    target_dir = expand_tokens(target_dir, fileinfo)
                except ImportError:
                    pass  # If tier1_actions not available, use raw target_dir

            # Only normalize if target_dir is not already an absolute path
            # If it's relative, it stays relative; if absolute, it gets normalized
            if not os.path.isabs(target_dir):
                target_dir = normalize_path(target_dir)
            else:
                target_dir = os.path.normpath(target_dir)

            # Ensure target directory exists (create if needed) - but only in real mode, not dry_run
            if not dry_run:
                if not ensure_directory_exists(target_dir):
                    message = f"ERROR: MOVE - failed to create target directory: {target_dir}"
                    print(f"  [ACTION] {message}")
                    return {
                        "ok": False,
                        "log": message,
                        "meta": {"type": "move", "src": old_path, "dst": target_dir, "collision_handled": False}
                    }

            new_path = os.path.join(target_dir, filename)
            new_path = normalize_path(new_path)

            # SKIP CHECK 1: If old and new paths are identical, skip (idempotent)
            old_path_normalized = os.path.normcase(os.path.abspath(old_path))
            new_path_normalized = os.path.normcase(os.path.abspath(new_path))

            if old_path_normalized == new_path_normalized:
                message = f"SKIP: MOVE - already in target location"
                print(f"  [ACTION] {message}")
                return {
                    "ok": True,  # Not an error, just skipped
                    "log": message,
                    "meta": {
                        "type": "move",
                        "src": old_path,
                        "dst": old_path,  # No actual move
                        "collision_handled": False,
                        "skipped": True,
                        "was_dry_run": dry_run
                    }
                }

            # SKIP CHECK 2: If files are in same parent directory, skip move but allow rename to happen
            old_parent = os.path.dirname(old_path_normalized)
            new_parent = os.path.dirname(new_path_normalized)

            if old_parent == new_parent:
                message = f"SKIP: MOVE - already in target folder (only rename, not move)"
                print(f"  [ACTION] {message}")
                return {
                    "ok": True,  # Not an error, just skipped
                    "log": message,
                    "meta": {
                        "type": "move",
                        "src": old_path,
                        "dst": old_path,  # No actual move
                        "collision_handled": False,
                        "skipped": True,
                        "was_dry_run": dry_run
                    }
                }

            # Track if collision was handled
            collision_handled = False

            # CRITICAL FIX: Use avoid_overwrite() to get a safe destination
            if config.get("safe_mode", True):
                new_path_safe = avoid_overwrite(new_path)
                collision_handled = (new_path_safe != new_path)
                new_path = new_path_safe

            if dry_run:
                message = f"DRY RUN: Would MOVE: {old_path} -> {new_path}"
            else:
                # Perform the move operation using shutil.move()
                # At this point, new_path is guaranteed to not exist
                shutil.move(old_path, new_path)
                message = f"MOVE: {old_path} -> {new_path}"

            print(f"  [ACTION] {message}")
            return {
                "ok": True,
                "log": message,
                "meta": {
                    "type": "move",
                    "src": old_path,  # Original location for undo
                    "dst": new_path if not dry_run else old_path,  # New location (or original if preview)
                    "collision_handled": collision_handled,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: MOVE failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "move", "src": old_path, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }


class CopyAction(Action):
    """Copy a file to a new directory."""

    def __init__(self, target_dir: str):
        self.target_dir = target_dir

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Copy a file to a new directory with guaranteed collision avoidance.

        Args:
            fileinfo: File information dict with 'path' and 'name' keys
            config: Profile config with 'safe_mode' and 'dry_run' flags

        Returns:
            Dict with ok, log, and meta keys for undo support
        """
        config = config or {}
        old_path = fileinfo.get("path")
        filename = fileinfo.get("name")
        dry_run = config.get("dry_run", False)

        # Validation
        if not old_path:
            message = f"ERROR: COPY - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "copy", "src": None, "dst": None, "collision_handled": False}
            }

        if not filename:
            message = f"ERROR: COPY - filename missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "copy", "src": old_path, "dst": None, "collision_handled": False}
            }

        if not is_file_accessible(old_path):
            message = f"ERROR: COPY - source file not found or not accessible: {old_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "copy", "src": old_path, "dst": None, "collision_handled": False}
            }

        if not self.target_dir or not str(self.target_dir).strip():
            message = f"ERROR: COPY - target directory is empty"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "copy", "src": old_path, "dst": None, "collision_handled": False}
            }

        try:
            old_path = normalize_path(old_path)

            # Expand tokens in target_dir if it contains any
            target_dir = self.target_dir
            if "<" in target_dir and ">" in target_dir:
                try:
                    from folderfresh.rule_engine.tier1_actions import expand_tokens
                    target_dir = expand_tokens(target_dir, fileinfo)
                except ImportError:
                    pass  # If tier1_actions not available, use raw target_dir

            # Only normalize if target_dir is not already an absolute path
            # If it's relative, it stays relative; if absolute, it gets normalized
            if not os.path.isabs(target_dir):
                target_dir = normalize_path(target_dir)
            else:
                target_dir = os.path.normpath(target_dir)

            # Ensure target directory exists (create if needed) - but only in real mode, not dry_run
            if not dry_run:
                if not ensure_directory_exists(target_dir):
                    message = f"ERROR: COPY - failed to create target directory: {target_dir}"
                    print(f"  [ACTION] {message}")
                    return {
                        "ok": False,
                        "log": message,
                        "meta": {"type": "copy", "src": old_path, "dst": target_dir, "collision_handled": False, "was_dry_run": dry_run}
                    }

            new_path = os.path.join(target_dir, filename)
            new_path = normalize_path(new_path)

            # SKIP CHECK 1: If old and new paths are identical, skip (idempotent)
            old_path_normalized = os.path.normcase(os.path.abspath(old_path))
            new_path_normalized = os.path.normcase(os.path.abspath(new_path))

            if old_path_normalized == new_path_normalized:
                message = f"SKIP: COPY - already in target location"
                print(f"  [ACTION] {message}")
                return {
                    "ok": True,  # Not an error, just skipped
                    "log": message,
                    "meta": {
                        "type": "copy",
                        "src": old_path,
                        "dst": old_path,  # No actual copy
                        "collision_handled": False,
                        "skipped": True,
                        "was_dry_run": dry_run
                    }
                }

            # Track if collision was handled
            collision_handled = False

            # CRITICAL FIX: Use avoid_overwrite() to get a safe destination
            if config.get("safe_mode", True):
                new_path_safe = avoid_overwrite(new_path)
                collision_handled = (new_path_safe != new_path)
                new_path = new_path_safe

            if dry_run:
                message = f"DRY RUN: Would COPY: {old_path} -> {new_path}"
            else:
                # Perform the copy operation using shutil.copy2() (preserves metadata)
                # At this point, new_path is guaranteed to not exist
                shutil.copy2(old_path, new_path)
                message = f"COPY: {old_path} -> {new_path}"

            print(f"  [ACTION] {message}")
            return {
                "ok": True,
                "log": message,
                "meta": {
                    "type": "copy",
                    "src": old_path,  # Original file (not modified)
                    "dst": new_path if not dry_run else old_path,  # Copy location (or original if preview)
                    "collision_handled": collision_handled,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: COPY failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "copy", "src": old_path, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }


class DeleteFileAction(Action):
    """Permanently delete a file."""

    def __init__(self):
        pass

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Delete a file permanently.

        Args:
            fileinfo: File information dict with 'path' key
            config: Profile config with 'safe_mode' and 'dry_run' flags

        Returns:
            Dict with ok, log, and meta keys for undo support
        """
        config = config or {}
        file_path = fileinfo.get("path")
        safe_mode = config.get("safe_mode", True)
        dry_run = config.get("dry_run", False)

        # Validation
        if not file_path:
            message = f"ERROR: DELETE - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "delete", "src": None, "temp_backup": None}
            }

        if not is_file_accessible(file_path):
            message = f"ERROR: DELETE - source file not found or not accessible: {file_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "delete", "src": file_path, "temp_backup": None}
            }

        try:
            file_path = normalize_path(file_path)

            # Safe mode: completely block delete action
            if safe_mode:
                message = f"SAFE MODE: DELETE blocked - cannot delete files in safe mode"
                print(f"  [ACTION] {message}")
                return {
                    "ok": False,
                    "log": message,
                    "meta": {"type": "delete", "src": file_path, "temp_backup": None}
                }

            if dry_run:
                message = f"DRY RUN: Would DELETE: {file_path}"
                temp_backup = None
            else:
                # Create a temporary backup before deleting
                import tempfile
                temp_dir = tempfile.gettempdir()
                filename = os.path.basename(file_path)
                temp_backup = os.path.join(temp_dir, f"folderfresh_delete_{int(time.time())}_{filename}")

                # Copy file to temp location as backup
                shutil.copy2(file_path, temp_backup)

                # Delete the original file
                os.remove(file_path)
                message = f"DELETE: {file_path}"

            print(f"  [ACTION] {message}")
            return {
                "ok": True,
                "log": message,
                "meta": {
                    "type": "delete",
                    "src": file_path,
                    "temp_backup": temp_backup
                }
            }

        except Exception as e:
            message = f"ERROR: DELETE failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "delete", "src": file_path, "temp_backup": None}
            }


# ============================================================================
# RULE
# ============================================================================

@dataclass
class Rule:
    """
    A rule that groups conditions and actions.

    Attributes:
        name: Human-readable rule name.
        conditions: List of Condition objects to evaluate.
        actions: List of Action objects to execute if conditions match.
        match_mode: "all" (AND) or "any" (OR) for conditions.
        stop_on_match: If True, stop processing further rules after this one matches.
    """
    name: str
    conditions: List[Condition]
    actions: List[Action]
    match_mode: str = "all"  # "all" = AND, "any" = OR
    stop_on_match: bool = False

    def matches(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Check if this rule's conditions match the given file.

        Args:
            fileinfo: dict with file information.

        Returns:
            True if conditions match according to match_mode, False otherwise.
        """
        if not self.conditions:
            # No conditions = always matches
            return True

        if self.match_mode == "all":
            # All conditions must be True (AND logic)
            return all(cond.evaluate(fileinfo) for cond in self.conditions)
        elif self.match_mode == "any":
            # At least one condition must be True (OR logic)
            return any(cond.evaluate(fileinfo) for cond in self.conditions)
        else:
            raise ValueError(f"Unknown match_mode: {self.match_mode}")


# ============================================================================
# EXECUTOR
# ============================================================================

class RuleExecutor:
    """
    Executes rules against file info objects.
    Processes rules in order, checks conditions, and runs matching actions.
    """

    def __init__(self):
        self.log: List[str] = []
        self.handled: bool = False
        self.actions_executed: List[Dict[str, Any]] = []

    def execute(self, rules: List[Rule], fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a file through a list of rules.

        Args:
            rules: List of Rule objects to evaluate.
            fileinfo: dict with file information (name, ext, path, size, etc.).
            config: dict with merged profile configuration (safe_mode, etc.).

        Returns:
            Dict with keys:
                - "matched_rule": str or None - name of matched rule (if any)
                - "final_dst": str or None - final destination path (if rule moved file)
                - "success": bool - True if rule executed successfully
                - "log": List[str] - log messages
                - "handled": bool - True if any rule matched and actions executed
                - "actions": List[Dict] - details of actions executed
        """
        config = config or {}
        self.log = []
        self.handled = False
        self.actions_executed = []
        safe_mode_delete_blocks = []  # Track files that couldn't be deleted due to safe mode
        matched_rule_name = None
        final_dst = None
        success = True

        filename = fileinfo.get("name", "unknown")
        self.log.append(f"\n=== Processing file: {filename} ===")

        for rule in rules:
            self.log.append(f"\n[RULE] '{rule.name}'")

            if rule.matches(fileinfo):
                self.log.append(f"  -> MATCHED!")

                # Execute all actions
                for action in rule.actions:
                    # Convert move actions to copy in safe mode
                    if config.get("safe_mode", False) and isinstance(action, MoveAction):
                        # Create a copy action with the same target directory
                        action = CopyAction(action.target_dir)

                    result = action.run(fileinfo, config)

                    # Handle new dict return format from actions
                    if isinstance(result, dict):
                        log_msg = result.get("log", "")
                        self.log.append(f"  -> {log_msg}")

                        # Track if action was successful
                        if result.get("ok", False):
                            self.handled = True
                            # 🔥 Update fileinfo path/name so next action sees the correct location
                            meta = result.get("meta", {})
                            new_location = meta.get("dst") or meta.get("src")
                            if new_location:
                                fileinfo["path"] = new_location
                                fileinfo["name"] = Path(new_location).name

                            matched_rule_name = rule.name
                            self.actions_executed.append({
                                "action": action.__class__.__name__,
                                "result": result
                            })

                            # Extract final destination from action meta
                            meta = result.get("meta", {})
                            if meta.get("type") == "move":
                                final_dst = meta.get("dst")
                            elif meta.get("type") == "rename":
                                final_dst = meta.get("src")
                            elif meta.get("type") == "copy":
                                final_dst = meta.get("dst")

                        else:
                            success = False
                            # Track if delete was blocked by safe mode
                            log_msg = result.get("log", "").upper()
                            if config.get("safe_mode", False) and "DELETE" in log_msg and "SAFE MODE" in log_msg:
                                safe_mode_delete_blocks.append(fileinfo.get("name", "unknown"))

                        # Record undo entry if action succeeded and not a dry run
                        # (dry_run actions should not be recorded in undo history)
                        if result.get("ok", False) and not config.get("dry_run", False):
                            try:
                                from folderfresh.undo_manager import UNDO_MANAGER
                                undo_entry = {
                                    "type": result.get("meta", {}).get("type", "unknown"),
                                    "src": result.get("meta", {}).get("src"),
                                    "dst": result.get("meta", {}).get("dst"),
                                    "old_name": result.get("meta", {}).get("old_name"),
                                    "new_name": result.get("meta", {}).get("new_name"),
                                    "collision_handled": result.get("meta", {}).get("collision_handled", False)
                                }
                                UNDO_MANAGER.record_action(undo_entry)
                            except ImportError:
                                pass  # Undo manager not available, continue anyway
                    else:
                        # Legacy string return (backward compatibility)
                        self.log.append(f"  -> {result}")
                        # Mark as handled even with legacy string returns
                        self.handled = True
                        matched_rule_name = rule.name

                # Stop processing if requested
                if rule.stop_on_match:
                    self.log.append(f"  -> stop_on_match=True, stopping here.")
                    break
            else:
                self.log.append(f"  -> No match, skipping actions.")

        # Forward all log entries to the activity log
        for line in self.log:
            log_activity(line)

        # Return unified result dictionary with required contract
        return {
            "matched_rule": matched_rule_name,
            "final_dst": final_dst,
            "success": success,
            "log": self.log,
            "handled": self.handled,
            "actions": self.actions_executed,
            "safe_mode_delete_blocks": safe_mode_delete_blocks
        }


# ============================================================================
# EXAMPLE / TESTING
# ============================================================================

if __name__ == "__main__":
    # Create a test rule: "Organize Screenshots"
    # Condition: filename contains "screenshot" AND extension is "png"
    # Actions: rename it and move it to a destination folder

    rule = Rule(
        name="Organize Screenshots",
        conditions=[
            NameContainsCondition("screenshot"),
            ExtensionIsCondition("png"),
        ],
        actions=[
            RenameAction("screenshot_organized.png"),
            MoveAction("C:/Users/tristan/Desktop/Screenshots"),
        ],
        match_mode="all",
        stop_on_match=True,
    )

    # Create a fake file info object
    fake_file = {
        "name": "screenshot_2024_11_28.png",
        "ext": ".png",
        "path": "C:/Users/tristan/Downloads/screenshot_2024_11_28.png",
        "size": 1024000,
    }

    # Execute the rule with a sample config
    executor = RuleExecutor()
    sample_config = {
        "safe_mode": True,  # Avoid overwriting files
    }
    result = executor.execute([rule], fake_file, sample_config)

    # Print the log
    print("\n" + "=" * 60)
    print("EXECUTION LOG:")
    print("=" * 60)
    for line in result["log"]:
        print(line)

    print("\n" + "=" * 60)
    print(f"HANDLED: {result['handled']}")
    print(f"ACTIONS EXECUTED: {len(result['actions'])}")
    print("=" * 60)
