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
from .rule_engine.backbone import avoid_overwrite
from folderfresh.rule_engine import RuleExecutor
from folderfresh.fileinfo import get_fileinfo
from folderfresh.profile_store import ProfileStore
from folderfresh.activity_log import log_activity

# =====================================================================
# AutoTidyHandler — handler for a *single watched folder*
# Uses TEMPORARY per-folder profile configs (Hazel-style)
# =====================================================================
class AutoTidyHandler(FileSystemEventHandler):
    # Debounce / scheduler constants — tuneable
    _DEBOUNCE_DELAY = 1.0      # seconds of inactivity before starting processing
    _STABLE_WINDOW = 0.6       # seconds size must be unchanged
    _MIN_FILE_AGE = 0.4        # minimum age (seconds) since mtime to avoid immediate placeholders
    _CHECK_INTERVAL = 0.12     # loop sleep inside wait

    def __init__(self, app, root_folder):
        super().__init__()
        self.app = app
        self.root = Path(root_folder)

        # path -> threading.Timer
        self._timers = {}
        self._timers_lock = threading.Lock()

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
    # Robust stabilization
    # ---------------------------------------------------
    def _can_open_rw(self, p: Path) -> bool:
        """Try to open file read/write to detect an exclusive writer (Explorer rename often locks)."""
        try:
            # Try r+b/r+ to detect write locks. Close immediately.
            with open(p, "r+b"):
                return True
        except Exception:
            # r+b may fail if inaccessible; try r
            try:
                with open(p, "rb"):
                    return True
            except Exception:
                return False

    def wait_until_stable(self, p: Path, cfg=None, timeout=20.0) -> bool:
        """
        Wait until file:
         - exists
         - is older than MIN_FILE_AGE
         - can be opened (best-effort)
         - size hasn't changed for STABLE_WINDOW

        Returns True if stable, False on timeout or if file disappears.
        """
        start = time.time()
        last_size = -1
        last_change = time.time()

        while True:
            # Timeout guard
            if (time.time() - start) > timeout:
                log_activity(f"⚠️  WATCHER: wait_until_stable timeout for '{p.name}'")
                return False

            # If file vanished, stop
            if not p.exists():
                log_activity(f"ℹ️  WATCHER: {p.name} disappeared while waiting for stabilization")
                return False

            # min age to avoid immediate placeholder handling
            try:
                mtime = p.stat().st_mtime
            except Exception:
                time.sleep(self._CHECK_INTERVAL)
                continue

            if (time.time() - mtime) < self._MIN_FILE_AGE:
                # still very fresh; wait a bit
                time.sleep(self._CHECK_INTERVAL)
                continue

            # Try to see if we can open (best-effort lock probe)
            if not self._can_open_rw(p):
                # file likely still locked by writer (Explorer, another process)
                time.sleep(self._CHECK_INTERVAL)
                continue

            # Check size stability
            try:
                size = p.stat().st_size
            except Exception:
                time.sleep(self._CHECK_INTERVAL)
                continue

            if size != last_size:
                last_size = size
                last_change = time.time()

            if (time.time() - last_change) >= self._STABLE_WINDOW:
                return True

            time.sleep(self._CHECK_INTERVAL)

    # ---------------------------------------------------
    # Fallback to category sorting (ONLY if no rule matched)
    # ---------------------------------------------------
    def fallback_to_category_sort(self, p: Path, cfg):
        """
        Category sorting fallback - ONLY called if no rule matched.
        This is the same logic that was in handle_file(), but now
        only executes after rule engine has run.
        """
        root = self.root
        filename = p.name

        # Determine category
        if cfg.get("smart_mode", False):
            folder_name = pick_smart_category(p, cfg=cfg)
            if not folder_name:
                folder_name = pick_category(p.suffix, src_path=p, cfg=cfg)
        else:
            folder_name = pick_category(p.suffix, src_path=p, cfg=cfg)

        # No category → do nothing (leave file untouched)
        if not folder_name:
            log_activity(f"ℹ️  WATCHER: {filename} - no matching category found, leaving untouched")
            return

        # Apply rename overrides
        folder_name = resolve_category(folder_name, cfg)

        # Build destination
        dst_dir = root / folder_name
        dst = dst_dir / p.name

        try:
            dst_dir.mkdir(parents=True, exist_ok=True)

            # 🔥 ALWAYS enforce unique final filename — NEVER overwrite
            dst = Path(avoid_overwrite(str(dst)))

            if cfg.get("safe_mode", True):
                log_activity(f"ℹ️  WATCHER: {filename} - copying to {folder_name}/…")
                shutil.copy2(str(p), str(dst))
                log_activity(f"✓ WATCHER: {filename} copied to {folder_name}/")
            else:
                log_activity(f"ℹ️  WATCHER: {filename} - moving to {folder_name}/…")
                shutil.move(str(p), str(dst))
                log_activity(f"✓ WATCHER: {filename} moved to {folder_name}/")


        except FileNotFoundError as e:
            log_activity(f"✗ WATCHER: {filename} - source or destination path not found: {str(e)}")
        except PermissionError as e:
            log_activity(f"✗ WATCHER: {filename} - permission denied during sorting: {str(e)}")
        except OSError as e:
            log_activity(f"✗ WATCHER: {filename} - I/O error during sorting: {str(e)}")
        except Exception as e:
            log_activity(f"✗ WATCHER: {filename} - failed to sort: {type(e).__name__}: {str(e)}")

    # ---------------------------------------------------
    # Actual work entrypoint (unchanged logic, but invoked
    # after debounce/stabilization)
    # ---------------------------------------------------
    def delayed_handle(self, path):
        """
        Handle file event with RULE-FIRST execution order.
        Execution order:
        1. Wait until stable (writing completed & renamed finished)
        2. Apply ignore filters
        3. Execute rules first
        4. Fallback to category sorting
        """
        cfg = self.get_folder_config()

        p = Path(path)
        filename = p.name

        # Basic existence
        if not p.exists() or not p.is_file():
            log_activity(f"ℹ️  WATCHER: {filename} no longer exists, skipping")
            return

        log_activity(f"📝 WATCHER: Processing file: {filename}")

        # 2. Wait for stabilization (includes lock checks and quiet size window)
        if not self.wait_until_stable(p, cfg):
            log_activity(f"⚠️  WATCHER: {filename} skipped (timeout waiting for stabilization)")
            return

        log_activity(f"✓ WATCHER: {filename} stabilized")

        # 3. APPLY IGNORE FILTERS
        if is_onedrive_placeholder(p):
            log_activity(f"ℹ️  WATCHER: {filename} ignored (OneDrive placeholder)")
            return

        if self.should_ignore(p, cfg):
            log_activity(f"ℹ️  WATCHER: {filename} ignored (matched ignore rules)")
            return

        min_days = int(cfg.get("age_filter_days", 0))
        if min_days > 0 and not file_is_old_enough(p, min_days):
            log_activity(f"ℹ️  WATCHER: {filename} skipped (too new for age filter: {min_days}d)")
            return

        # 4. RULE-FIRST EXECUTION
        try:
            store = ProfileStore()
            doc = store.load()
            profile = store.get_active_profile(doc)
            rules = store.get_rules(profile)

            if rules:
                log_activity(f"ℹ️  WATCHER: {filename} - evaluating {len(rules)} rule(s)…")

                try:
                    fileinfo = get_fileinfo(path)
                except Exception as e:
                    log_activity(f"ERROR: Failed to read file info for '{path}': {str(e)}")
                    return

                try:
                    executor = RuleExecutor()
                    result = executor.execute(rules, fileinfo, cfg)

                    if result.get("matched") and result.get("success"):
                        log_activity(f"✓ WATCHER: {filename} handled by rule '{result.get('rule_name', 'unknown')}'")
                        return
                    elif result.get("matched") and not result.get("success"):
                        log_activity(f"✗ WATCHER: {filename} - rule matched but failed: {result.get('error', 'unknown error')}")
                        return
                    else:
                        log_activity(f"ℹ️  WATCHER: {filename} - no rules matched, falling back to category sorting")

                except Exception as e:
                    log_activity(f"ERROR: Rule engine error processing '{filename}': {str(e)}")
                    return
            else:
                log_activity(f"ℹ️  WATCHER: {filename} - no rules defined, using category sorting")

        except Exception as e:
            log_activity(f"✗ WATCHER: {filename} - processing error: {type(e).__name__}: {str(e)}")
            return

        # 5. FALLBACK TO CATEGORY SORTING
        self.fallback_to_category_sort(p, cfg)

    # ---------------------------------------------------
    # Debounce / scheduling helpers
    # ---------------------------------------------------
    def _schedule_for_path(self, path: str, delay=None):
        """Schedule delayed_handle(path) to run after a quiet period.
        If there's already a timer for this path, cancel and reschedule.
        """
        if delay is None:
            delay = self._DEBOUNCE_DELAY

        with self._timers_lock:
            # Cancel existing timer if present
            t = self._timers.get(path)
            if t and t.is_alive():
                try:
                    t.cancel()
                except Exception:
                    pass

            # Create a timer that will invoke the real worker in a separate thread
            def _run():
                # Remove timer record
                with self._timers_lock:
                    if path in self._timers:
                        del self._timers[path]

                try:
                    # Run the heavy handler on its own thread (so watchdog's thread isn't blocked)
                    threading.Thread(target=self.delayed_handle, args=(path,), daemon=False).start()
                except Exception as e:
                    log_activity(f"✗ WATCHER: failed to start worker for '{Path(path).name}': {e}")

            timer = threading.Timer(delay, _run)
            self._timers[path] = timer
            timer.daemon = True
            timer.start()

    # ---------------------------------------------------
    # Watchdog callbacks
    # ---------------------------------------------------
    def on_created(self, event):
        if event.is_directory:
            return
        # schedule processing after debounce window
        self._schedule_for_path(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        # destination is final name - schedule that path
        self._schedule_for_path(event.dest_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        # modifications often happen during writes; reschedule
        self._schedule_for_path(event.src_path)
