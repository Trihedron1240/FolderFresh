# watcher.py
import os
import time
import shutil
import threading
from pathlib import Path
from watchdog.events import FileSystemEventHandler

from .utils import file_is_old_enough, is_hidden_win, is_onedrive_placeholder
from .sorting import pick_smart_category, pick_category
from .constants import DEFAULT_CATEGORIES
from .naming import resolve_category

from folderfresh.rule_engine import RuleExecutor
from folderfresh.fileinfo import get_fileinfo
from folderfresh.profile_store import ProfileStore
from folderfresh.activity_log import log_activity

# =====================================================================
# AutoTidyHandler — handler for a *single watched folder*
# Uses TEMPORARY per-folder profile configs (Hazel-style)
# =====================================================================
class AutoTidyHandler(FileSystemEventHandler):
    def __init__(self, app, root_folder):
        super().__init__()
        self.app = app
        self.root = Path(root_folder)

    # ====================================================
    # Build a *temporary* config for THIS watched folder
    # ====================================================
    def get_folder_config(self) -> dict:
        from .config import load_config  # avoid circular import

        folder_map = self.app.config_data.get("folder_profile_map", {})
        folder_key = str(self.root)

        profile_name = folder_map.get(folder_key)

        # No mapping → use the *current* active config_data
        if not profile_name:
            return self.app.config_data

        # Load profile storage file
        doc = self.app.profile_store.load()

        # Search for profile by name
        profile_obj = None
        for p in doc["profiles"]:
            if p["name"].lower() == profile_name.lower():
                profile_obj = p
                break

        # Missing profile → fall back
        if profile_obj is None:
            print(f"[Watcher] WARNING: No such profile '{profile_name}'. Using active profile.")
            return self.app.config_data

        # Load global baseline config
        base_cfg = load_config()

        # Merge the profile’s settings into a fresh copy
        merged_cfg = self.app.profile_store.merge_profile_into_config(
            profile_obj,
            base_cfg
        )

        # Safety: merge should produce a dict
        if not isinstance(merged_cfg, dict):
            print(f"[Watcher] ERROR: merge_profile_into_config returned invalid data for {profile_name}")
            return self.app.config_data

        return merged_cfg

    # ---------------------------------------------------
    # Ignore logic (now uses cfg)
    # ---------------------------------------------------
    def should_ignore(self, p: Path, cfg) -> bool:
        root = self.root

        overrides = cfg.get("custom_category_names", {})
        enabled_map = cfg.get("category_enabled", {})
        custom = cfg.get("custom_categories", {})

        # Skip cloud placeholders
        if is_onedrive_placeholder(p):
            return True

        # Allowed categories
        allowed = {c for c in DEFAULT_CATEGORIES if enabled_map.get(c, True)}
        allowed |= {c for c in custom if enabled_map.get(c, True)}
        allowed |= set(overrides.values())

        # Skip category folders
        try:
            rel = p.relative_to(root)
            first = rel.parts[0] if rel.parts else ""
            if first in allowed:
                return True
        except:
            pass

        # Ignore extensions
        ignore_raw = cfg.get("ignore_exts", "")
        ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}
        if p.suffix.lower() in ignore_set:
            return True

        # Skip partial downloads
        PARTIALS = {".crdownload", ".part", ".partial", ".download", ".opdownload"}
        if p.suffix.lower() in PARTIALS:
            return True

        # Skip hidden files
        try:
            rel = p.relative_to(root)
            if cfg.get("skip_hidden", True) and (
                any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)
            ):
                return True
        except:
            pass

        return False

    # ---------------------------------------------------
    # Wait until file stops changing
    # ---------------------------------------------------
    def wait_until_stable(self, p: Path, attempts=4, delay=0.25) -> bool:
        for _ in range(attempts):
            try:
                size1 = p.stat().st_size
                time.sleep(delay)
                size2 = p.stat().st_size
                if size1 == size2:
                    return True
            except:
                pass
        return False

    # ---------------------------------------------------
    # Main sorting (patched to use cfg everywhere)
    # ---------------------------------------------------
    def handle_file(self, p: Path, cfg):
        root = self.root

        if not p.exists() or not p.is_file():
            return

        # Ignore newly modified files
        try:
            if time.time() - p.stat().st_mtime < 1.0:
                return
        except:
            return

        if self.should_ignore(p, cfg):
            return

        if not self.wait_until_stable(p):
            return

        # Age filter
        min_days = int(cfg.get("age_filter_days", 0))
        if min_days > 0 and not file_is_old_enough(p, min_days):
            return

        # SMART SORTING
        if cfg.get("smart_mode", False):
            smart_folder = pick_smart_category(p, cfg=cfg)
            if smart_folder:
                smart_folder = resolve_category(smart_folder, cfg)
                dst_dir = root / smart_folder
                dst_dir.mkdir(parents=True, exist_ok=True)

                dst = dst_dir / p.name
                try:
                    if cfg.get("safe_mode", True):
                        shutil.copy2(p, dst)
                    else:
                        shutil.move(str(p), str(dst))
                except Exception as e:
                    self.app.after(0, lambda e=e: self.app.set_status(f"Auto-tidy error: {e}"))
                return

        # STANDARD
        folder_name = pick_category(
            p.suffix,
            src_path=p,
            cfg=cfg
        )
        folder_name = resolve_category(folder_name, cfg)

        dst = root / folder_name / p.name
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if cfg.get("safe_mode", True):
                shutil.copy2(p, dst)
            else:
                shutil.move(str(p), dst)
        except Exception as e:
            self.app.after(0, lambda e=e: self.app.set_status(f"Auto-tidy error: {e}"))

    # ---------------------------------------------------
    # Delayed execution wrapper
    # ---------------------------------------------------
    def delayed_handle(self, path):
        """
        Handle file event: run auto-tidy first, then execute rules.
        All output is logged to ActivityLog for real-time monitoring.
        """
        cfg = self.get_folder_config()
        time.sleep(0.6)
        self.handle_file(Path(path), cfg)

        # ====================================================
        # RULE ENGINE EXECUTION WITH ACTIVITY LOG
        # ====================================================
        try:
            # Verify file still exists
            if not os.path.exists(path) or not os.path.isfile(path):
                log_activity(f"INFO: File no longer exists: {path}")
                return

            # Load profile storage
            store = ProfileStore()
            doc = store.load()
            profile = store.get_active_profile(doc)

            # Get rules attached to active profile
            rules = store.get_rules(profile)

            # Skip if profile has no rules
            if not rules:
                return

            # Build complete fileinfo dictionary
            try:
                fileinfo = get_fileinfo(path)
            except Exception as e:
                log_activity(f"ERROR: Failed to read file info for '{path}': {str(e)}")
                return

            # Get merged config with profile settings
            merged_cfg = cfg

            # Run rule executor with merged config
            executor = RuleExecutor()
            log_lines = executor.execute(rules, fileinfo, merged_cfg)

            # All log lines are already forwarded to ActivityLog by RuleExecutor
            # (see rule_engine/backbone.py execute() method)
            # Optional: print to console for debugging
            for line in log_lines:
                if line.strip():
                    print("[WATCHER RULE]", line)

        except Exception as e:
            error_msg = f"ERROR: Rule engine error processing '{os.path.basename(path)}': {str(e)}"
            print("[WATCHER ERROR]", error_msg)
            log_activity(error_msg)
    # ---------------------------------------------------
    # Watchdog callbacks
    # ---------------------------------------------------
    def on_created(self, event):

        if event.is_directory:
            return
        threading.Thread(
            target=lambda: self.delayed_handle(event.src_path),
            daemon=False
        ).start()

    def on_moved(self, event):

        if event.is_directory:
            return
        threading.Thread(
            target=lambda: self.delayed_handle(event.dest_path),
            daemon=False
        ).start()

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        threading.Thread(
            target=lambda: self.delayed_handle(event.src_path),
            daemon=False
        ).start()
