from pathlib import Path
import os
import shutil
import time
import json
import fnmatch
from datetime import datetime
from .config import save_config
from .utils import (
    scan_dir,
    file_is_old_enough,
    remove_empty_category_folders,
    group_duplicates,
    is_onedrive_placeholder,
)
from .sorting import pick_category, pick_smart_category
from .sorting import plan_moves
from .constants import LOG_FILENAME
from .naming import resolve_category
from .file_processor import process_file_with_rules
from .profile_store import ProfileStore
from .rule_engine.backbone import avoid_overwrite
from tkinter import messagebox


def _matches_any_pattern(target: str, patterns: list[str]) -> bool:
    """
    Check if target matches any pattern.
    Patterns containing *, ?, [, ] use fnmatch.
    Otherwise substring. Case-insensitive.
    """
    target = target.lower()

    for pat in patterns:
        if not pat:
            continue
        pat = pat.lower().strip()

        # glob pattern
        if any(ch in pat for ch in "*?[]"):
            if fnmatch.fnmatch(target, pat):
                return True
        else:
            # substring
            if pat in target:
                return True

    return False



def save_log(root: Path, moves: list[dict], mode: str) -> Path:
    log_path = root / LOG_FILENAME
    payload = {
        "when": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,  # "move" or "copy"
        "moves": moves,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return log_path


def load_log(root: Path) -> dict | None:
    log_path = root / LOG_FILENAME
    if not log_path.exists():
        return None
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# =============================================================================
# PREVIEW (with RULES-FIRST execution)
# =============================================================================

def do_preview(app):
    """
    Backend logic for the Preview button with RULES-FIRST execution.

    Execution order:
    1. For each file, run RuleExecutor first (if rules exist)
    2. If rule matched and action succeeded → show rule result + STOP
    3. If no rule matched → show what category sorting would do
    4. If no category → show nothing (file stays untouched)

    Returns a list of moves (showing both rule and sorting results).
    """
    folder = app.selected_folder
    if not folder or not folder.exists():
        return []

    # Respect Desktop special rule
    desktop = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
    include_sub = False if folder == desktop else bool(app.include_sub.get())

    # -------------------------
    # LOAD IGNORE SETTINGS
    # -------------------------

    # extensions (.exe; .tmp etc.)
    ignore_raw = app.config_data.get("ignore_exts", "")
    ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}

    # patterns (substring or wildcard filters)
    pattern_list = app.config_data.get("ignore_patterns", [])
    ignore_patterns = [p["pattern"] for p in pattern_list if p.get("pattern")]

    # dont_move_list (paths/filenames to never move)
    dont_move_list = [s.lower().strip() for s in app.config_data.get("dont_move_list", [])]

    # age filter
    min_days = int(app.config_data.get("age_filter_days", 0))

    last_mode = app.config_data.get("last_sort_mode", None)
    current_mode = "smart" if app.smart_mode.get() else "simple"
    skip_categories = (last_mode == current_mode)

    # Debug logging
    from folderfresh.logger_qt import log_info
    log_info(f"[do_preview] last_mode={last_mode}, current_mode={current_mode}, skip_categories={skip_categories}")

    files_all = scan_dir(
        folder,
        include_sub,
        app.skip_hidden.get(),
        ignore_set,
        skip_categories
    )

    # Debug logging
    log_info(f"[do_preview] scan_dir returned {len(files_all)} files")

    # -------------------------
    # APPLY FILTERS
    # -------------------------
    files = []
    for f in files_all:

        # age filter
        if not file_is_old_enough(f, min_days):
            continue

        # ignore extensions
        if f.suffix.lower() in ignore_set:
            continue

        # ignore patterns (wildcard or substring)
        name = f.name.lower()
        fullpath = str(f).lower()
        if _matches_any_pattern(name, ignore_patterns) or _matches_any_pattern(fullpath, ignore_patterns):
            continue

        # dont_move_list (substring + fullpath matching)
        name = f.name.lower()
        fullpath = str(f).lower()
        if name in dont_move_list:
            continue
        files.append(f)

    # Debug logging
    log_info(f"[do_preview] after filters: {len(files)} files")

    # -------------------------
    # LOAD RULES AND APPLY RULES-FIRST LOGIC
    # -------------------------
    moves = []

    try:
        # Load rules from active profile
        store = ProfileStore()
        doc = store.load()
        profile = store.get_active_profile(doc)
        rules = store.get_rules(profile)
    except Exception:
        # If rules can't be loaded, proceed with sorting only
        rules = []

    for p in files:
        # Skip OneDrive cloud-only placeholders
        if is_onedrive_placeholder(p):
            continue

        # =====================================================================
        # RULES-FIRST: Check if any rule handles this file
        # =====================================================================
        if rules:
            result = process_file_with_rules(
                str(p),
                rules,
                app.config_data,
                preview=True  # Use preview/dry-run mode
            )

            if result["matched"] and result["success"]:
                # A rule matched and handled this file successfully
                # Show the rule result and do NOT fall through to sorting
                moves.append({
                    "src": str(p),
                    "dst": result["dst"],
                    "mode": "rule",
                    "rule_name": result["rule_name"],
                })
                continue

        # =====================================================================
        # NO RULES MATCHED - FALL BACK TO CATEGORY SORTING
        # =====================================================================
        use_smart = app.smart_mode.get()

        # SMART category
        folder_name = pick_smart_category(p, cfg=app.config_data) if use_smart else None

        # fallback to standard category
        if not folder_name:
            folder_name = pick_category(
                p.suffix,
                src_path=p,
                cfg=app.config_data
            )

        # If no category found, skip this file (leave untouched)
        if not folder_name:
            continue

        # apply rename overrides
        folder_name = resolve_category(folder_name, app.config_data)

        dst = folder / folder_name / p.name

        # SKIP CHECK: If file is already in the destination folder, skip
        p_resolved = p.resolve()
        dst_resolved = dst.resolve()

        # Check if file is already in the correct destination folder
        if p_resolved.parent == dst_resolved.parent:
            # File is already in the correct folder, skip the move
            continue

        # COLLISION FIX: Check for existing file and apply unique naming if needed
        dst_str = str(dst)
        if os.path.exists(dst_str):
            dst_str = avoid_overwrite(dst_str)
            dst = Path(dst_str)

        # Only add to moves if destination is different from source
        if p != dst:
            moves.append({
                "src": str(p),
                "dst": str(dst),
                "mode": "sort",
                "category": folder_name,
            })

    return moves


# =============================================================================
# ORGANISE
# =============================================================================

def do_organise(app, moves):
    """
    SAFELY organise files using a RULE-FIRST processing pipeline.

    Correct behaviour:
    1. For each file in the preview moves list:
       a. Run the rule engine first
       b. If a rule matched AND succeeded → log it and STOP (don't sort)
       c. If no rule matched → attempt category sorting
       d. If category sorting succeeds → log it
       e. If no category → leave file untouched

    NEVER delete files unless DeleteAction is explicitly triggered by a rule.
    """

    folder = app.selected_folder

    # -------------------------
    # LOAD IGNORE SETTINGS
    # -------------------------
    ignore_raw = app.config_data.get("ignore_exts", "")
    ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}

    pattern_list = app.config_data.get("ignore_patterns", [])
    ignore_patterns = [p["pattern"] for p in pattern_list if p.get("pattern")]

    dont_move_list = [s.lower().strip() for s in app.config_data.get("dont_move_list", [])]

    min_days = int(app.config_data.get("age_filter_days", 0))

    moves_done = []

    # Load rules once (faster)
    store = ProfileStore()
    doc = store.load()
    profile = store.get_active_profile(doc)
    rules = store.get_rules(profile)

    for m in moves:
        src = m["src"]

        # Skip cloud placeholders
        if is_onedrive_placeholder(src):
            continue

        p = Path(src)

        # apply ignore filters again for safety
        if p.suffix.lower() in ignore_set:
            continue

        name = p.name.lower()
        fullpath = str(p).lower()

        if _matches_any_pattern(name, ignore_patterns) or _matches_any_pattern(fullpath, ignore_patterns):
            continue
        if name in dont_move_list:
            continue

        if not file_is_old_enough(p, min_days):
            continue

        # =====================================================================
        # 1. RULE-FIRST EXECUTION (always try rules first)
        # =====================================================================
        try:
            if rules:
                result = process_file_with_rules(
                    src=src,
                    rules=rules,
                    config=app.config_data,
                    preview=False  # Real execution, not dry-run
                )

                # Check if a rule matched and succeeded
                if result.get("matched") and result.get("success"):
                    # Rule handled the file - record and STOP here
                    moves_done.append({
                        "src": src,
                        "dst": result["dst"],
                        "rule_name": result["rule_name"],
                        "mode": "rule"
                    })
                    continue  # CRUCIAL: Do NOT fall through to category sorting

                elif result.get("matched") and not result.get("success"):
                    # Rule matched but failed
                    moves_done.append({
                        "src": src,
                        "dst": src,
                        "error": result.get("error", "Rule action failed"),
                        "mode": "rule"
                    })
                    continue  # CRUCIAL: Do NOT attempt fallback sorting

        except Exception as e:
            moves_done.append({
                "src": src,
                "dst": src,
                "error": str(e),
                "mode": "rule"
            })
            continue

        # =====================================================================
        # 2. CATEGORY SORTING (ONLY IF NO RULE MATCHED)
        # =====================================================================

        # Determine category
        if app.smart_mode.get():
            folder_name = pick_smart_category(p, cfg=app.config_data)
            if not folder_name:
                folder_name = pick_category(p.suffix, src_path=p, cfg=app.config_data)
        else:
            folder_name = pick_category(p.suffix, src_path=p, cfg=app.config_data)

        # No category → do nothing (leave file untouched)
        if not folder_name:
            continue

        # Apply rename overrides
        folder_name = resolve_category(folder_name, app.config_data)

        # Build destination
        new_dst = Path(app.selected_folder) / folder_name / p.name

        try:
            # SKIP CHECK: If file is already in the correct destination folder, skip
            src_path = Path(src).resolve()
            dst_path_initial = new_dst.resolve()

            # Check if file is already in the destination folder
            if src_path.parent == dst_path_initial.parent:
                # File is already in the correct folder, skip the move
                moves_done.append({
                    "src": src,
                    "dst": src,  # No move happened
                    "mode": "sort",
                    "skipped": True,
                    "reason": "Already in target folder"
                })
                continue

            new_dst.parent.mkdir(parents=True, exist_ok=True)

            # 🔥 ALWAYS make destination unique — NEVER overwrite
            new_dst = Path(avoid_overwrite(str(new_dst)))

            # Double-check after collision handling: if now in same folder as source, skip
            if src_path.parent == new_dst.resolve().parent:
                moves_done.append({
                    "src": src,
                    "dst": src,
                    "mode": "sort",
                    "skipped": True,
                    "reason": "Collision handling placed in same folder as source"
                })
                continue

            if app.safe_mode.get():
                shutil.copy2(src, new_dst)
            else:
                shutil.move(src, new_dst)

            moves_done.append({
                "src": src,
                "dst": str(new_dst),
                "mode": "sort"
            })

        except Exception as e:
            moves_done.append({
                "src": src,
                "dst": str(new_dst),
                "error": str(e),
                "mode": "sort"
            })

    # =====================================================================
    # LOG THE SESSION
    # =====================================================================
    mode = "copy" if app.safe_mode.get() else "move"
    save_log(Path(folder), moves_done, mode)

    # Save sort mode for next preview
    app.config_data["last_sort_mode"] = "smart" if app.smart_mode.get() else "simple"
    save_config(app.config_data)

    # Clean empty folders
    remove_empty_category_folders(folder)

    return moves_done


# =============================================================================
# UNDO
# =============================================================================

def do_undo(app):
    folder = app.selected_folder
    log_path = folder / LOG_FILENAME

    if not log_path.exists():
        return None

    data = json.load(open(log_path, "r", encoding="utf-8"))

    if data.get("mode") == "copy":
        return "copy_mode"

    moves = data.get("moves", [])
    success = 0

    for m in reversed(moves):
        src = Path(m["src"])
        dst = Path(m["dst"])
        try:
            if dst.exists():
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(src))
                success += 1
        except:
            pass

    try:
        log_path.unlink(missing_ok=True)
    except:
        pass

    remove_empty_category_folders(folder)

    # Reset last sort mode
    app.config_data["last_sort_mode"] = None
    save_config(app.config_data)
    return success


# =============================================================================
# DUPLICATES
# =============================================================================

def do_find_duplicates(app):
    folder = app.selected_folder

    ignore_raw = app.config_data.get("ignore_exts", "")
    ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}

    pattern_list = app.config_data.get("ignore_patterns", [])
    ignore_patterns = [p["pattern"] for p in pattern_list if p.get("pattern")]

    dont_move_list = [s.lower().strip() for s in app.config_data.get("dont_move_list", [])]

    files_all = scan_dir(
        folder,
        app.include_sub.get(),
        app.skip_hidden.get(),
        ignore_set,
        skip_categories=False
    )

    # apply ignore ext + pattern filters
    files = []
    for f in files_all:
        if f.suffix.lower() in ignore_set:
            continue

        # dont_move_list (substring + fullpath matching)
        name = f.name.lower()
        fullpath = str(f).lower()
        if _matches_any_pattern(name, ignore_patterns) or _matches_any_pattern(fullpath, ignore_patterns):
            continue

        if name in dont_move_list:
            continue
        files.append(f)

    groups = group_duplicates(files)
    return groups


# =============================================================================
# LOG FILE VIEW
# =============================================================================

def open_log_file(folder: Path) -> bool:
    logs = sorted(
        folder.glob(".folderfresh_moves_log*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not logs:
        return False

    try:
        os.startfile(logs[0])
        return True
    except Exception:
        return False


def view_log_file(self):
    if not self.selected_folder:
        messagebox.showerror("Log File", "Select a folder first.")
        return

    if not open_log_file(Path(self.selected_folder)):
        messagebox.showinfo("Log File", "No FolderFresh log file found in this folder.")
