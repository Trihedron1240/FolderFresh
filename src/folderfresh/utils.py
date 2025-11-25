# utils.py
import time
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta

from .constants import LOG_FILENAME, DEFAULT_CATEGORIES


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
    files = []
    iterator = root.rglob("*") if include_sub else root.glob("*")

    for p in iterator:
        try:
            if p.suffix.lower() in ignore_set:
                continue
            if not p.is_file():
                continue
            if p.name == LOG_FILENAME:
                continue

            rel = p.relative_to(root)

            if skip_hidden and (
                any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)
            ):
                continue

            if skip_categories:
                if len(rel.parts) >= 2 and rel.parts[0] in DEFAULT_CATEGORIES:
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
