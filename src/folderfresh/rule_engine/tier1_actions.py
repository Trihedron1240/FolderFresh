"""
Tier-1 Hazel-style automation actions for FolderFresh.

Includes:
- TokenRenameAction: Rename with token expansion
- RunCommandAction: Execute scripts/commands
- ArchiveAction: Zip files
- ExtractAction: Unzip/extract archives
- CreateFolderAction: Create folders with tokens

All actions follow FolderFresh patterns:
- Return dict with ok, log, meta
- Support safe_mode, dry_run, undo
- Use avoid_overwrite() for collision prevention
- Idempotent (skip if already done)
"""

import os
import shutil
import time
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .backbone import normalize_path, avoid_overwrite, is_file_accessible, Action


# ============================================================================
# TOKEN EXPANSION UTILITIES
# ============================================================================

def expand_tokens(template: str, fileinfo: Dict[str, Any]) -> str:
    """
    Expand tokens in a template string using file info.

    Supported tokens:
    - <name>: filename without extension
    - <extension>: file extension (with dot)
    - <date_created>: file creation date (YYYY-MM-DD)
    - <date_modified>: file modification date (YYYY-MM-DD)
    - <year>: current year
    - <month>: current month (zero-padded)
    - <day>: current day (zero-padded)
    - <hour>: current hour (zero-padded)
    - <minute>: current minute (zero-padded)
    - <date_created_year>, <date_modified_month>, etc.

    Args:
        template: String with tokens like "Documents/<year>/<month>/<name>.pdf"
        fileinfo: File info dict with 'path', 'name', 'ext'

    Returns:
        Expanded string with all tokens replaced
    """
    result = template

    # Get file timestamps
    try:
        file_path = fileinfo.get("path", "")
        if file_path and os.path.exists(file_path):
            stat_info = os.stat(file_path)
            created_time = datetime.fromtimestamp(stat_info.st_birthtime if hasattr(stat_info, 'st_birthtime') else stat_info.st_ctime)
            modified_time = datetime.fromtimestamp(stat_info.st_mtime)
        else:
            created_time = modified_time = datetime.now()
    except Exception:
        created_time = modified_time = datetime.now()

    now = datetime.now()

    # Extract filename components
    full_name = fileinfo.get("name", "")
    name_without_ext = os.path.splitext(full_name)[0]
    extension = os.path.splitext(full_name)[1]  # includes dot

    # Replace tokens
    replacements = {
        "<name>": name_without_ext,
        "<extension>": extension,
        "<date_created>": created_time.strftime("%Y-%m-%d"),
        "<date_modified>": modified_time.strftime("%Y-%m-%d"),
        "<date_created_year>": created_time.strftime("%Y"),
        "<date_created_month>": created_time.strftime("%m"),
        "<date_created_day>": created_time.strftime("%d"),
        "<date_modified_year>": modified_time.strftime("%Y"),
        "<date_modified_month>": modified_time.strftime("%m"),
        "<date_modified_day>": modified_time.strftime("%d"),
        "<year>": now.strftime("%Y"),
        "<month>": now.strftime("%m"),
        "<day>": now.strftime("%d"),
        "<hour>": now.strftime("%H"),
        "<minute>": now.strftime("%M"),
    }

    for token, value in replacements.items():
        result = result.replace(token, value)

    return result


# ============================================================================
# 1. TOKEN RENAME ACTION
# ============================================================================

class TokenRenameAction(Action):
    """Rename a file using token expansion (e.g., '<date_modified>_<name>')."""

    def __init__(self, name_pattern: str):
        """
        Args:
            name_pattern: Filename pattern with tokens, e.g., "<date_modified>_<name><extension>"
        """
        self.name_pattern = name_pattern

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Rename file using token expansion.

        Returns idempotently if filename already matches the token pattern.
        """
        config = config or {}
        old_path = fileinfo.get("path")
        old_name = fileinfo.get("name")
        dry_run = config.get("dry_run", False)
        safe_mode = config.get("safe_mode", True)

        # Validation
        if not old_path:
            message = "ERROR: TOKEN_RENAME - source file path missing"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "rename", "src": None, "old_name": old_name, "new_name": None, "was_dry_run": dry_run}
            }

        if not is_file_accessible(old_path):
            message = f"ERROR: TOKEN_RENAME - source file not found: {old_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "rename", "src": old_path, "old_name": old_name, "new_name": None, "was_dry_run": dry_run}
            }

        try:
            old_path = normalize_path(old_path)
            parent_dir = os.path.dirname(old_path)

            # Expand tokens to get new name
            new_name = expand_tokens(self.name_pattern, fileinfo)
            new_path = os.path.join(parent_dir, new_name)
            new_path = normalize_path(new_path)

            # SKIP CHECK: If paths are identical, skip (idempotent)
            if os.path.normcase(os.path.abspath(old_path)) == os.path.normcase(os.path.abspath(new_path)):
                message = f"SKIP: TOKEN_RENAME - already named '{new_name}'"
                print(f"  [ACTION] {message}")
                return {
                    "ok": True,
                    "log": message,
                    "meta": {
                        "type": "rename",
                        "src": old_path,
                        "old_name": old_name,
                        "new_name": new_name,
                        "collision_handled": False,
                        "was_dry_run": dry_run,
                        "skipped": True
                    }
                }

            # Collision avoidance
            collision_handled = False
            if safe_mode:
                new_path_safe = avoid_overwrite(new_path)
                collision_handled = (new_path_safe != new_path)
                new_path = new_path_safe
                new_name = os.path.basename(new_path)

            if dry_run:
                message = f"DRY RUN: Would TOKEN_RENAME: {old_path} -> {new_path}"
                ok = True
            else:
                os.rename(old_path, new_path)
                message = f"TOKEN_RENAME: {old_path} -> {new_path}"
                ok = True

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "rename",
                    "src": old_path,
                    "dst": new_path,
                    "old_name": old_name,
                    "new_name": new_name,
                    "collision_handled": collision_handled,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: TOKEN_RENAME failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "rename", "src": old_path, "old_name": old_name, "new_name": None, "was_dry_run": dry_run}
            }


# ============================================================================
# 2. RUN COMMAND ACTION
# ============================================================================

class RunCommandAction(Action):
    """Execute a command or script."""

    def __init__(self, command: str):
        """
        Args:
            command: Command to execute (e.g., "powershell -command ...", "cmd /c ...", or script path)
        """
        self.command = command

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the command.

        In dry_run or safe_mode: Don't execute, only preview.

        Supported placeholders:
        - {file} → full path
        - {dir} → parent directory
        - {name} → filename without extension
        - {ext} → extension (including dot)
        - {basename} → filename with extension
        """
        config = config or {}
        file_path = fileinfo.get("path", "")
        dry_run = config.get("dry_run", False)
        safe_mode = config.get("safe_mode", True)

        # Expand tokens in command (angle bracket tokens like <name>, <extension>)
        command = expand_tokens(self.command, fileinfo)

        # Replace curly brace placeholders for RunCommand
        file_path_obj = Path(file_path) if file_path else None
        if file_path_obj:
            parent_dir = str(file_path_obj.parent)
            name_without_ext = file_path_obj.stem
            extension = file_path_obj.suffix  # includes dot
            basename = file_path_obj.name

            command = command.replace("{file}", file_path)
            command = command.replace("{dir}", parent_dir)
            command = command.replace("{name}", name_without_ext)
            command = command.replace("{ext}", extension)
            command = command.replace("{basename}", basename)

        if dry_run or safe_mode:
            message = f"DRY RUN: Would execute: {command}"
            print(f"  [ACTION] {message}")
            return {
                "ok": True,
                "log": message,
                "meta": {
                    "type": "run_command",
                    "src": file_path,
                    "command": command,
                    "was_dry_run": True
                }
            }

        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout + result.stderr
            if result.returncode == 0:
                message = f"RUN_COMMAND succeeded: {command}\n{output[:200]}"
                ok = True
            else:
                message = f"RUN_COMMAND failed (code {result.returncode}): {command}\n{output[:200]}"
                ok = False

            print(f"  [ACTION] {message[:100]}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "run_command",
                    "src": file_path,
                    "command": command,
                    "return_code": result.returncode,
                    "was_dry_run": False
                }
            }

        except subprocess.TimeoutExpired:
            message = f"ERROR: RUN_COMMAND timeout (30s): {command}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "run_command", "src": file_path, "was_dry_run": False}
            }
        except Exception as e:
            message = f"ERROR: RUN_COMMAND failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "run_command", "src": file_path, "was_dry_run": False}
            }


# ============================================================================
# 3. ARCHIVE ACTION (ZIP)
# ============================================================================

class ArchiveAction(Action):
    """Zip a file to a destination folder."""

    def __init__(self, target_dir: str):
        """
        Args:
            target_dir: Directory to zip file into (can include tokens)
        """
        self.target_dir = target_dir

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Zip the file to target directory.
        """
        config = config or {}
        file_path = fileinfo.get("path", "")
        file_name = fileinfo.get("name", "")
        dry_run = config.get("dry_run", False)
        safe_mode = config.get("safe_mode", True)

        # Validation
        if not file_path or not is_file_accessible(file_path):
            message = f"ERROR: ARCHIVE - source file not found: {file_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "archive", "src": file_path, "dst": None, "was_dry_run": dry_run}
            }

        try:
            file_path = normalize_path(file_path)
            target_dir = expand_tokens(self.target_dir, fileinfo)
            target_dir = normalize_path(target_dir)

            # Create target directory if needed
            if not dry_run:
                os.makedirs(target_dir, exist_ok=True)

            # Generate zip filename
            name_without_ext = os.path.splitext(file_name)[0]
            zip_path = os.path.join(target_dir, f"{name_without_ext}.zip")
            zip_path = normalize_path(zip_path)

            # Collision avoidance
            if not dry_run:
                zip_path = avoid_overwrite(zip_path)

            if dry_run:
                message = f"DRY RUN: Would ZIP: {file_path} -> {zip_path}"
                ok = True
            else:
                # Create zip with single file
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(file_path, arcname=file_name)
                message = f"ARCHIVE: {file_path} -> {zip_path}"
                ok = True

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "archive",
                    "src": file_path,
                    "dst": zip_path,
                    "collision_handled": (zip_path != os.path.join(target_dir, f"{name_without_ext}.zip")),
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: ARCHIVE failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "archive", "src": file_path, "dst": None, "was_dry_run": dry_run}
            }


# ============================================================================
# 4. EXTRACT ACTION
# ============================================================================

class ExtractAction(Action):
    """Extract an archive (zip, rar, 7z) to a destination folder."""

    def __init__(self, target_dir: str):
        """
        Args:
            target_dir: Directory to extract into (can include tokens)
        """
        self.target_dir = target_dir

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract archive to target directory.
        """
        config = config or {}
        file_path = fileinfo.get("path", "")
        file_name = fileinfo.get("name", "")
        dry_run = config.get("dry_run", False)

        # Validation
        if not file_path or not is_file_accessible(file_path):
            message = f"ERROR: EXTRACT - source archive not found: {file_path}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "extract", "src": file_path, "dst": None, "was_dry_run": dry_run}
            }

        # Check file type
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.zip', '.rar', '.7z']:
            message = f"ERROR: EXTRACT - unsupported format: {ext}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "extract", "src": file_path, "was_dry_run": dry_run}
            }

        try:
            file_path = normalize_path(file_path)
            target_dir = expand_tokens(self.target_dir, fileinfo)
            target_dir = normalize_path(target_dir)

            # Create target directory
            if not dry_run:
                os.makedirs(target_dir, exist_ok=True)

            if dry_run:
                message = f"DRY RUN: Would EXTRACT: {file_path} -> {target_dir}"
                ok = True
            else:
                if ext == '.zip':
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        zf.extractall(target_dir)
                else:
                    # rar/7z not supported without external tools
                    message = f"ERROR: EXTRACT - {ext} not supported (install 7-Zip or WinRAR)"
                    print(f"  [ACTION] {message}")
                    return {
                        "ok": False,
                        "log": message,
                        "meta": {"type": "extract", "src": file_path, "was_dry_run": dry_run}
                    }

                message = f"EXTRACT: {file_path} -> {target_dir}"
                ok = True

            print(f"  [ACTION] {message}")
            return {
                "ok": ok,
                "log": message,
                "meta": {
                    "type": "extract",
                    "src": file_path,
                    "dst": target_dir,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: EXTRACT failed - {str(e)}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "extract", "src": file_path, "was_dry_run": dry_run}
            }


# ============================================================================
# 5. CREATE FOLDER ACTION
# ============================================================================

class CreateFolderAction(Action):
    """Create a folder using the same normalization and token logic as MoveAction."""

    def __init__(self, folder_path: str):
        self.target_dir = folder_path

    def run(self, fileinfo: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        config = config or {}
        dry_run = config.get("dry_run", False)

        # We keep fileinfo just in case tokens require file context
        old_path = fileinfo.get("path")

        # Expand tokens IN THE DIRECTORY
        target_dir = self.target_dir

        try:
            # Use the SAME token rule as MoveAction
            if "<" in target_dir and ">" in target_dir:
                from folderfresh.rule_engine.tier1_actions import expand_tokens
                target_dir = expand_tokens(target_dir, fileinfo)
        except Exception as e:
            message = f"ERROR: CREATE_FOLDER token expansion failed - {e}"
            print(f"  [ACTION] {message}")
            return {"ok": False, "log": message, "meta": {"type": "create_folder"}}

        # Normalize EXACTLY the same as MoveAction
        if not os.path.isabs(target_dir):
            target_dir = normalize_path(target_dir)
        else:
            target_dir = os.path.normpath(target_dir)

        # SKIP if directory already exists
        if os.path.isdir(target_dir):
            message = f"SKIP: CREATE_FOLDER - already exists: {target_dir}"
            print(f"  [ACTION] {message}")
            return {
                "ok": True,
                "log": message,
                "meta": {
                    "type": "create_folder",
                    "dst": target_dir,
                    "skipped": True,
                    "was_dry_run": dry_run
                }
            }

        # Create ONLY the folder (no move)
        try:
            if dry_run:
                message = f"DRY RUN: Would CREATE_FOLDER: {target_dir}"
            else:
                from folderfresh.rule_engine.backbone import ensure_directory_exists
                if not ensure_directory_exists(target_dir):
                    raise RuntimeError("ensure_directory_exists returned False")
                message = f"CREATE_FOLDER: {target_dir}"

            print(f"  [ACTION] {message}")

            return {
                "ok": True,
                "log": message,
                "meta": {
                    "type": "create_folder",
                    "dst": target_dir,
                    "was_dry_run": dry_run
                }
            }

        except Exception as e:
            message = f"ERROR: CREATE_FOLDER failed - {e}"
            print(f"  [ACTION] {message}")
            return {
                "ok": False,
                "log": message,
                "meta": {"type": "create_folder", "dst": None, "was_dry_run": dry_run}
            }
