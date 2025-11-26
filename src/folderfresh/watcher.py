# watcher.py
import time
import shutil
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .utils import file_is_old_enough, is_hidden_win
from .sorting import pick_smart_category, plan_moves
from .constants import DEFAULT_CATEGORIES
from .naming import resolve_category
from .sorting import pick_smart_category, plan_moves, pick_category


# =====================================================================
# AutoTidyHandler — handler for a **single watched folder**
# =====================================================================
class AutoTidyHandler(FileSystemEventHandler):
    def __init__(self, app, root_folder):
        super().__init__()
        self.app = app
        self.root = Path(root_folder)

    # ---------------------------------------------------
    # Ignore logic
    # ---------------------------------------------------
    def should_ignore(self, p: Path) -> bool:
        root = self.root
        overrides = self.app.config_data.get("custom_category_names", {})
        enabled_map = self.app.config_data.get("category_enabled", {})
        custom = self.app.config_data.get("custom_categories", {})
        overrides = self.app.config_data.get("custom_category_names", {})

        # Default categories that are enabled
        allowed_cats = {c for c in DEFAULT_CATEGORIES if enabled_map.get(c, True)}

        # Custom categories that are enabled
        allowed_cats |= {c for c in custom if enabled_map.get(c, True)}

        # Renamed categories need to be allowed by name
        allowed_cats |= set(overrides.values())

        # Ignore category folders
        try:
            rel = p.relative_to(root)
            first = rel.parts[0] if rel.parts else ""
            if first in allowed_cats:
                return True
        except Exception:
            pass

        # Ignore extensions
        ignore_raw = self.app.config_data.get("ignore_exts", "")
        ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}
        if p.suffix.lower() in ignore_set:
            return True

        # Partial downloads
        PARTIALS = {".crdownload", ".part", ".partial", ".download", ".opdownload"}
        if p.suffix.lower() in PARTIALS:
            return True

        # Hidden/system
        try:
            rel = p.relative_to(root)
            if self.app.skip_hidden.get() and (
                any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)
            ):
                return True
        except Exception:
            pass

        return False

    # ---------------------------------------------------
    # Ensure file is done writing
    # ---------------------------------------------------
    def wait_until_stable(self, p: Path, attempts=4, delay=0.25) -> bool:
        for _ in range(attempts):
            try:
                s1 = p.stat().st_size
                time.sleep(delay)
                s2 = p.stat().st_size
                if s1 == s2:
                    return True
            except Exception:
                pass
        return False

    # ---------------------------------------------------
    # Main move logic
    # ---------------------------------------------------
    def handle_file(self, p: Path):
        root = self.root
        
        if not p.exists() or not p.is_file():
            return
        # If the file was edited/renamed in the last second, ignore it
        try:
            if time.time() - p.stat().st_mtime < 1.0:
                return
        except:
            return
        if self.should_ignore(p):
            return

        if not self.wait_until_stable(p):
            return

        # Age filter
        try:
            min_days = int(self.app.age_filter_entry.get() or 0)
        except:
            min_days = 0
        if min_days > 0 and not file_is_old_enough(p, min_days):
            return

        # SMART SORTING
        if self.app.smart_mode.get():
            smart_folder = pick_smart_category(p, cfg=self.app.config_data)
            if smart_folder:
                smart_folder = resolve_category(smart_folder, self.app.config_data)
                dest_dir = root / smart_folder
                dest_dir.mkdir(parents=True, exist_ok=True)
                dst = dest_dir / p.name
                try:
                    if self.app.safe_mode.get():
                        shutil.copy2(p, dst)
                    else:
                        shutil.move(str(p), str(dst))
                except Exception as e:
                    self.app.after(0, lambda e=e: self.app.set_status(f"Auto-tidy error: {e}"))
                return

        # STANDARD SORTING with config support
        from .sorting import pick_category  # ensure imported

        folder_name = pick_category(
            p.suffix,
            src_path=p,
            cfg=self.app.config_data
        )

        folder_name = resolve_category(folder_name, self.app.config_data)

        new_dst = root / folder_name / p.name

        try:
            new_dst.parent.mkdir(parents=True, exist_ok=True)
            if self.app.safe_mode.get():
                shutil.copy2(p, new_dst)
            else:
                shutil.move(str(p), new_dst)
        except Exception as e:
            self.app.after(0, lambda e=e: self.app.set_status(f"Auto-tidy error: {e}"))


    # ---------------------------------------------------
    # Event handling — uses delay
    # ---------------------------------------------------
    def delayed_handle(self, path):
        time.sleep(0.6)   # grace period
        self.handle_file(Path(path))

    def on_created(self, event):
        if event.is_directory:
            return
        threading.Thread(
            target=lambda: self.delayed_handle(event.src_path),
            daemon=True,
        ).start()

    def on_moved(self, event):
        if event.is_directory:
            return
        threading.Thread(
            target=lambda: self.delayed_handle(event.dest_path),
            daemon=True,
        ).start()
