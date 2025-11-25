# watcher.py
import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .utils import file_is_old_enough, is_hidden_win
from .sorting import pick_smart_category
from .sorting import plan_moves
from .constants import DEFAULT_CATEGORIES
from .naming import resolve_category
# ========== INTERNAL HANDLER CLASS ===========================================

class AutoTidyHandler(FileSystemEventHandler):
    """
    This class mirrors the inner Handler class inside FolderFreshApp,
    but extracted into a standalone module.
    """

    def __init__(self, app):
        super().__init__()
        self.app = app
        
    # -------------------------------------------------------------
    # Should ignore file?
    # -------------------------------------------------------------
    def should_ignore(self, p: Path, root: Path) -> bool:
        # Skip category folders
        try:
            rel = p.relative_to(root)
            if rel.parts and rel.parts[0] in DEFAULT_CATEGORIES:
                return True
        except Exception:
            pass

        # User-ignored extensions
        ignore_raw = self.app.config_data.get("ignore_exts", "")
        ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}
        if p.suffix.lower() in ignore_set:
            return True

        # Skip partial download files
        PARTIALS = {".crdownload", ".part", ".partial", ".download", ".opdownload"}
        if p.suffix.lower() in PARTIALS:
            return True

        # Skip hidden/system files
        try:
            rel = p.relative_to(root)
            if self.app.skip_hidden.get() and (
                any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)
            ):
                return True
        except Exception:
            pass

        return False

    # -------------------------------------------------------------
    # Wait until file stops being written
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # Main file handling
    # -------------------------------------------------------------
    def handle_file(self, p: Path, root: Path):
        if not p.exists() or not p.is_file():
            return

        if self.should_ignore(p, root):
            return

        if not self.wait_until_stable(p):
            return

        # AGE FILTER
        try:
            min_days = int(self.app.age_filter_entry.get() or 0)
        except:
            min_days = 0

        if min_days > 0 and not file_is_old_enough(p, min_days):
            return

        # SMART SORTING
        if self.app.smart_mode.get():
            smart_folder = pick_smart_category(p)
            if smart_folder:
                # APPLY USER-DEFINED CATEGORY NAME
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

        # STANDARD SORTING
        move_plan = plan_moves([p], root)
        if not move_plan:
            return

        m = move_plan[0]
        # Extract default category name
        dst_path = Path(m["dst"])
        default_cat = dst_path.parent.name

        # APPLY USER-DEFINED CATEGORY NAME
        new_cat = resolve_category(default_cat, self.app.config_data)

        # Rebuild dst with new category
        new_dst = root / new_cat / dst_path.name
        m["dst"] = str(new_dst)
        try:
            Path(m["dst"]).parent.mkdir(parents=True, exist_ok=True)
            if self.app.safe_mode.get():
                shutil.copy2(m["src"], m["dst"])
            else:
                shutil.move(m["src"], m["dst"])
        except Exception as e:
            self.app.after(0, lambda e=e: self.app.set_status(f"Auto-tidy error: {e}"))

    # -------------------------------------------------------------
    # Watchdog Events
    # -------------------------------------------------------------
    def on_created(self, event):
        if event.is_directory:
            return
        root = self.app.selected_folder
        if root:
            self.handle_file(Path(event.src_path), root)

    def on_moved(self, event):
        if event.is_directory:
            return
        root = self.app.selected_folder
        if root:
            self.handle_file(Path(event.dest_path), root)



# ========== PUBLIC API FUNCTIONS =============================================

def start_watching(app):
    """
    Starts folder watching for auto-tidy.
    Mirrors FolderFreshApp.start_watching logic.
    """
    if not app.selected_folder:
        return

    # Create observer only once
    if app.observer:
        return

    app.observer = Observer()
    handler = AutoTidyHandler(app)

    try:
        app.observer.schedule(
            handler,
            str(app.selected_folder),
            recursive=app.include_sub.get()
        )
        app.observer.start()
        app.set_status("Auto-tidy watching…")
    except Exception as e:
        app.observer = None
        app.watch_mode.deselect()
        from tkinter import messagebox
        messagebox.showerror("Auto-tidy", f"Could not start watcher: {e}")


def stop_watching(app):
    """
    Stops folder watching.
    Mirrors FolderFreshApp.stop_watching logic.
    """
    if app.observer:
        try:
            app.observer.stop()
            app.observer.join(timeout=2)
        except Exception:
            pass

        app.observer = None
        app.set_status("Auto-tidy stopped")
