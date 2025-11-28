from dataclasses import dataclass
from typing import Any, List, Dict
import os
import shutil
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
            config: dict with merged profile configuration (safe_mode, dry_run, etc.)

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
                    "collision_handled": bool,  # If safe_mode created different path
                    "was_dry_run": bool  # True if action was only a preview
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
        Rename a file to a new name.

        Args:
            fileinfo: File information dict with 'path' and 'name' keys
            config: Profile config with 'dry_run' and 'safe_mode' flags

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
            new_path = os.path.join(parent_dir, self.new_name)
            new_path = normalize_path(new_path)

            # Track if collision was handled
            collision_handled = False
            # Handle collision avoidance
            if config.get("safe_mode", True):
                new_path_before = new_path
                new_path = avoid_overwrite(new_path)
                collision_handled = (new_path != new_path_before)

            if dry_run:
                message = f"DRY RUN: Would RENAME: {old_path} -> {new_path}"
                ok = True
            else:
                # Perform the rename operation
                os.rename(old_path, new_path)
                message = f"RENAME: {old_path} -> {new_path}"
                ok = True

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "rename",
                    "src": new_path,  # Store where the file ended up (for undo)
                    "old_name": old_name,
                    "new_name": self.new_name,
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
        Move a file to a new directory.

        Args:
            fileinfo: File information dict with 'path' and 'name' keys
            config: Profile config with 'dry_run' and 'safe_mode' flags

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
                "meta": {"type": "move", "src": None, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        if not filename:
            message = f"ERROR: MOVE - filename missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "move", "src": old_path, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        if not is_file_accessible(old_path):
            message = f"ERROR: MOVE - source file not found or not accessible: {old_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "move", "src": old_path, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        if not self.target_dir or not str(self.target_dir).strip():
            message = f"ERROR: MOVE - target directory is empty"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "move", "src": old_path, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        try:
            old_path = normalize_path(old_path)
            target_dir = normalize_path(self.target_dir)

            # Ensure target directory exists (create if needed)
            if not dry_run:
                if not ensure_directory_exists(target_dir):
                    message = f"ERROR: MOVE - failed to create target directory: {target_dir}"
                    print(f"  [ACTION] {message}")
                    return {
                        "ok": False,
                        "log": message,
                        "meta": {"type": "move", "src": old_path, "dst": target_dir, "collision_handled": False, "was_dry_run": dry_run}
                    }

            new_path = os.path.join(target_dir, filename)
            new_path = normalize_path(new_path)

            # Track if collision was handled
            collision_handled = False
            # Handle collision avoidance
            if config.get("safe_mode", True):
                new_path_before = new_path
                new_path = avoid_overwrite(new_path)
                collision_handled = (new_path != new_path_before)

            if dry_run:
                message = f"DRY RUN: Would MOVE: {old_path} -> {new_path}"
                ok = True
            else:
                # Perform the move operation using shutil.move()
                shutil.move(old_path, new_path)
                message = f"MOVE: {old_path} -> {new_path}"
                ok = True

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "move",
                    "src": old_path,  # Original location for undo
                    "dst": new_path,  # New location
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
        Copy a file to a new directory.

        Args:
            fileinfo: File information dict with 'path' and 'name' keys
            config: Profile config with 'dry_run' and 'safe_mode' flags

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
                "meta": {"type": "copy", "src": None, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        if not filename:
            message = f"ERROR: COPY - filename missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "copy", "src": old_path, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        if not is_file_accessible(old_path):
            message = f"ERROR: COPY - source file not found or not accessible: {old_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "copy", "src": old_path, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        if not self.target_dir or not str(self.target_dir).strip():
            message = f"ERROR: COPY - target directory is empty"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "copy", "src": old_path, "dst": None, "collision_handled": False, "was_dry_run": dry_run}
            }

        try:
            old_path = normalize_path(old_path)
            target_dir = normalize_path(self.target_dir)

            # Ensure target directory exists (create if needed)
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

            # Track if collision was handled
            collision_handled = False
            # Handle collision avoidance
            if config.get("safe_mode", True):
                new_path_before = new_path
                new_path = avoid_overwrite(new_path)
                collision_handled = (new_path != new_path_before)

            if dry_run:
                message = f"DRY RUN: Would COPY: {old_path} -> {new_path}"
                ok = True
            else:
                # Perform the copy operation using shutil.copy2() (preserves metadata)
                shutil.copy2(old_path, new_path)
                message = f"COPY: {old_path} -> {new_path}"
                ok = True

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "copy",
                    "src": old_path,  # Original file (not modified)
                    "dst": new_path,  # Copy location
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

    def execute(self, rules: List[Rule], fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> List[str]:
        """
        Process a file through a list of rules.

        Args:
            rules: List of Rule objects to evaluate.
            fileinfo: dict with file information (name, ext, path, size, etc.).
            config: dict with merged profile configuration (safe_mode, dry_run, etc.).

        Returns:
            List of log messages describing what happened.
        """
        config = config or {}
        self.log = []
        filename = fileinfo.get("name", "unknown")
        self.log.append(f"\n=== Processing file: {filename} ===")

        for rule in rules:
            self.log.append(f"\n[RULE] '{rule.name}'")

            if rule.matches(fileinfo):
                self.log.append(f"  -> MATCHED!")

                # Execute all actions
                for action in rule.actions:
                    result = action.run(fileinfo, config)

                    # Handle new dict return format from actions
                    if isinstance(result, dict):
                        log_msg = result.get("log", "")
                        self.log.append(f"  -> {log_msg}")

                        # Record undo entry if action succeeded and wasn't a dry run
                        if result.get("ok", False) and not result.get("meta", {}).get("was_dry_run", False):
                            try:
                                from folderfresh.undo_manager import UNDO_MANAGER
                                undo_entry = {
                                    "type": result.get("meta", {}).get("type", "unknown"),
                                    "src": result.get("meta", {}).get("src"),
                                    "dst": result.get("meta", {}).get("dst"),
                                    "old_name": result.get("meta", {}).get("old_name"),
                                    "new_name": result.get("meta", {}).get("new_name"),
                                    "collision_handled": result.get("meta", {}).get("collision_handled", False),
                                    "was_dry_run": False
                                }
                                UNDO_MANAGER.record_action(undo_entry)
                            except ImportError:
                                pass  # Undo manager not available, continue anyway
                    else:
                        # Legacy string return (backward compatibility)
                        self.log.append(f"  -> {result}")

                # Stop processing if requested
                if rule.stop_on_match:
                    self.log.append(f"  -> stop_on_match=True, stopping here.")
                    break
            else:
                self.log.append(f"  -> No match, skipping actions.")

        # Forward all log entries to the activity log
        for line in self.log:
            log_activity(line)

        return self.log


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
        "dry_run": True,  # Don't actually move files
        "safe_mode": True,  # Avoid overwriting files
    }
    log = executor.execute([rule], fake_file, sample_config)

    # Print the log
    print("\n" + "=" * 60)
    print("EXECUTION LOG:")
    print("=" * 60)
    for line in log:
        print(line)
