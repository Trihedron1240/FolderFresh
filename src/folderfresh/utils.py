# utils.py
import os
import time
import hashlib
import json
import winreg
import re
from pathlib import Path
from datetime import datetime, timedelta
import ctypes
from ctypes import wintypes
from .constants import LOG_FILENAME, ALL_CATEGORIES

# OneDrive Cloud Reparse Tag
IO_REPARSE_TAG_CLOUD = 0x9000001A

def is_onedrive_placeholder(path: Path) -> bool:
    """
    Returns True if the file is a OneDrive cloud-only placeholder.
    """
    # Only applies on Windows
    if os.name != "nt":
        return False

    try:
        # Check reparse tag
        FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))

        if attrs == -1:
            return False

        # If not a reparse point → not a placeholder
        if not (attrs & FILE_ATTRIBUTE_REPARSE_POINT):
            return False

        # Query reparse data
        # Use CreateFile + DeviceIoControl to read the tag
        FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
        FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
        GENERIC_READ = 0x80000000

        handle = ctypes.windll.kernel32.CreateFileW(
            str(path),
            GENERIC_READ,
            0,
            None,
            3,  # OPEN_EXISTING
            FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS,
            None
        )

        if handle == -1:
            return False

        # Structure to receive reparse info
        REPARSE_DATA_BUFFER_SIZE = 16384
        buf = ctypes.create_string_buffer(REPARSE_DATA_BUFFER_SIZE)
        bytes_returned = wintypes.DWORD()

        FSCTL_GET_REPARSE_POINT = 0x000900A8
        ok = ctypes.windll.kernel32.DeviceIoControl(
            handle,
            FSCTL_GET_REPARSE_POINT,
            None,
            0,
            buf,
            REPARSE_DATA_BUFFER_SIZE,
            ctypes.byref(bytes_returned),
            None
        )
        ctypes.windll.kernel32.CloseHandle(handle)

        if not ok:
            return False

        # First 4 bytes after ReparseTag are the tag value
        tag = ctypes.cast(buf, ctypes.POINTER(ctypes.c_ulong)).contents.value

        return tag == IO_REPARSE_TAG_CLOUD

    except Exception:
        return False
# ----------------------------- HIDDEN FILE CHECK ------------------------------

def is_hidden_win(path: Path) -> bool:
    """
    Windows hidden file detection. Other OS return False.
    """
    import sys
    if not sys.platform.startswith("win"):
        return False

    try:
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x2
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        return attrs != -1 and bool(attrs & FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        return False


def is_placeholder_file(path: Path) -> bool:
    """
    Detect default/placeholder filenames created by Windows, Office, and creative tools.

    Returns True if the file appears to be an auto-generated placeholder that the user
    has not renamed yet. These should be skipped during watcher processing and manual sorting.

    Detects patterns like:
    - "New Text Document.txt"
    - "New Text Document (2).txt"
    - "Untitled.txt", "Untitled-1.png"
    - "Document1.docx", "Document123.xlsx"
    - "Presentation1.pptx", "Presentation (1).pptx"
    - "Book1.xlsx"
    - Any file starting with "New "

    Args:
        path: Path object to the file

    Returns:
        True if file matches placeholder patterns, False otherwise
    """
    if not path.is_file():
        return False

    filename = path.name
    name_without_ext = path.stem  # filename without extension

    # Normalize for case-insensitive matching
    name_lower = name_without_ext.lower()

    # === PATTERN 1: "New *" files (Windows/Explorer default) ===
    # Matches: "New Text Document.txt", "New Folder.lnk", "New File.txt"
    # But NOT: "New Year Party Photos.zip" (has meaningful words after the type)
    if name_lower.startswith("new "):
        # Allow ONLY if it's "New [generic type]" without additional meaningful words
        # Generic patterns: "New Text Document", "New Folder", "New File", "New Bitmap", etc.
        remainder = name_lower[4:].strip()  # Skip "new "

        # These are the generic Windows defaults - single words or two-word templates
        generic_new_patterns = [
            r'^text\s+document$',
            r'^bitmap\s+image$',
            r'^document$',
            r'^folder$',
            r'^file$',
            r'^shortcut$',
            r'^compressed\s+\(zipped\)\s+folder$',
        ]

        for pattern in generic_new_patterns:
            if re.match(pattern, remainder):
                return True

        # If it doesn't match a known Windows generic, it's probably user-meaningful
        # e.g., "New Year Party Photos" is intentional naming

    # === PATTERN 2: "Untitled" variants ===
    # Matches: "Untitled.txt", "Untitled-1.psd", "Untitled (1).png"
    # But NOT: "Untitled Love Story.docx" (has text after number/variant)
    if name_lower.startswith("untitled"):
        # Allow ONLY pure "Untitled" or "Untitled-N" or "Untitled (N)" or "Untitled N"
        remainder = name_lower[len("untitled"):].strip()

        # Pure "Untitled" with no suffix
        if not remainder:
            return True

        # "Untitled" followed by number variant: "-1", "(1)", or " 1"
        if re.match(r'^[\s\-\(]?\d+[\)]?$', remainder):
            return True

    # === PATTERN 3: Office "DocumentN", "PresentationN", "BookN" ===
    # Matches: "Document1.docx", "Presentation2.pptx", "Book1.xlsx"
    # These are generic Office defaults with incremental numbers
    office_generics = [
        (r'^document\d+$', 'Document'),  # Document1, Document123
        (r'^presentation\d+$', 'Presentation'),  # Presentation1
        (r'^book\d+$', 'Book'),  # Book1
        (r'^sheet\d+$', 'Sheet'),  # Sheet1
        (r'^workbook\d+$', 'Workbook'),  # Workbook1
    ]

    for pattern, label in office_generics:
        if re.match(pattern, name_lower):
            return True

    # === PATTERN 4: "Word, Powerpoint, Excel" auto-recovery names ===
    # Matches: "AutoRecovery save of Document1.asd"
    if re.match(r'^autorecovery\s+save\s+of\s+', name_lower):
        return True

    # === PATTERN 5: Numbered variants with parentheses ===
    # Matches: "Document (1).docx", "Presentation (2).pptx"
    # But only if the base name is a generic Office template
    if re.search(r'\s\(\d+\)$', name_without_ext):
        base_without_number = re.sub(r'\s\(\d+\)$', '', name_without_ext).lower()

        # Check if base is a generic Office name
        if base_without_number in ['document', 'presentation', 'book', 'sheet', 'workbook', 'untitled']:
            return True

    # Not a placeholder
    return False


# ------------------------------- AGE CHECK ------------------------------------

def file_is_old_enough(path: Path, min_days: int):
    if min_days <= 0:
        return True
    cutoff = datetime.now() - timedelta(days=min_days)
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return mtime < cutoff


# ----------------------------- FILE STABILITY ---------------------------------

def file_is_stable(path: Path, wait=1.0):
    """
    Checks whether file has stopped changing size.
    """
    try:
        size1 = path.stat().st_size
        time.sleep(wait)
        size2 = path.stat().st_size
        return size1 == size2
    except Exception:
        return False


# ----------------------------- DIRECTORY SCAN ---------------------------------

def scan_dir(
    root: Path,
    include_sub: bool,
    skip_hidden: bool,
    ignore_set: set[str],
    skip_categories: bool
):
    from folderfresh.logger_qt import log_info
    log_info(f"[scan_dir] skip_categories={skip_categories}, include_sub={include_sub}, ALL_CATEGORIES={ALL_CATEGORIES}")

    files = []
    iterator = root.rglob("*") if include_sub else root.glob("*")

    for p in iterator:
        try:
            if is_onedrive_placeholder(p):
                continue

            if p.suffix.lower() in ignore_set:
                continue
            if not p.is_file():
                continue
            if p.name == LOG_FILENAME:
                continue

            rel = p.relative_to(root)

            # Debug: log files found
            if skip_categories == False and len(rel.parts) >= 2:
                log_info(f"[scan_dir] File in subfolder: {rel}, parts={rel.parts}")

            if skip_hidden and (
                any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)
            ):
                continue

            if skip_categories:
                if len(rel.parts) >= 2 and rel.parts[0] in ALL_CATEGORIES:
                    continue

            files.append(p)

        except Exception:
            continue

    return files


# ------------------------------ UNIQUE DEST -----------------------------------

def unique_dest(path: Path) -> Path:
    """
    Appends _1, _2, ... to avoid overwriting.
    """
    if not path.exists():
        return path

    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        candidate = path.with_name(f"{stem}_{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1


# ------------------------------ DUPLICATE FINDER ------------------------------

def quick_hash(path: Path, bytes_to_read: int = 1024 * 64):
    try:
        h = hashlib.md5()
        size = path.stat().st_size
        with open(path, "rb") as f:
            chunk = f.read(bytes_to_read)
            h.update(chunk)
            if size > bytes_to_read:
                f.seek(max(0, size - bytes_to_read))
                h.update(f.read(bytes_to_read))
        return (size, h.hexdigest())
    except Exception:
        return None


def group_duplicates(paths: list[Path]) -> list[list[Path]]:
    table = {}
    for p in paths:
        sig = quick_hash(p)
        if not sig:
            continue
        table.setdefault(sig, []).append(p)
    return [grp for grp in table.values() if len(grp) > 1]


# ------------------------------ EMPTY FOLDER CLEANUP --------------------------

def remove_empty_category_folders(root: Path):
    """
    Deletes category folders that become empty.
    """
    try:
        for item in root.iterdir():
            if item.is_dir():
                try:
                    next(item.iterdir())
                except StopIteration:
                    item.rmdir()
    except Exception:
        pass


# ------------------------------ LOG SAVE/LOAD ---------------------------------

def save_log(root: Path, moves: list[dict], mode: str):
    """
    Save move or copy log.
    """
    log_path = root / LOG_FILENAME
    payload = {
        "when": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "moves": moves,
    }
    json.dump(payload, open(log_path, "w", encoding="utf-8"), indent=2)
    return log_path


def load_log(root: Path):
    log_path = root / LOG_FILENAME
    if not log_path.exists():
        return None

    try:
        return json.load(open(log_path, "r", encoding="utf-8"))
    except Exception:
        return None

def enable_startup(app_name: str, exe_path: str):
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
    winreg.CloseKey(key)


def disable_startup(app_name: str):
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, app_name)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass
