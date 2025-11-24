# FolderFresh – Student File Organiser (All‑in‑One)
# -------------------------------------------------
# • Friendly GUI for non‑tech users (CustomTkinter)
# • Preview → Confirm → Organise → Undo
# • Options: Include subfolders, Skip hidden, Safe Mode (copy), Auto‑tidy (watch folder)
# • Extras: Clean Desktop button, Duplicate finder, Live status, Progress bar
# • Optional dep: watchdog (for Auto‑tidy). App works without it.
#
# How to run:
#   python -m pip install customtkinter  # if pip works
#   python app.py
#
# Optional (Auto‑tidy):
#   python -m pip install watchdog  # optional; app runs without it
#
# Build a Windows .exe (optional):
#   python -m pip install pyinstaller
#   pyinstaller --onefile --windowed --name "FolderFresh" app.py

from __future__ import annotations

import os
import sys
import json
import shutil
import threading
import hashlib
from pathlib import Path
from datetime import datetime
from datetime import timedelta
import time
# --- Optional watchdog for Auto‑tidy ------------------------------------------
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except Exception:  # pragma: no cover
    WATCHDOG_AVAILABLE = False
# Temporary/incomplete download extensions to ignore
PARTIAL_EXTS = {".crdownload", ".part", ".partial", ".download"}

# --- Optional system tray for background mode ---------------------------------
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except Exception:  # pragma: no cover
    TRAY_AVAILABLE = False

import customtkinter as ctk
from tkinter import filedialog, messagebox

APP_TITLE = "FolderFresh – Student File Organiser"
LOG_FILENAME = ".folderfresh_moves_log.json"  # saved inside chosen folder
# App config (UX prefs) saved in user home
CONFIG_FILENAME = ".folderfresh_config.json"

# ---- File categories (editable) ----------------------------------------------
CATEGORIES: dict[str, list[str]] = {
    "Images": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".heic"],
    "PDF": [".pdf"],
    "Docs": [".doc", ".docx", ".txt", ".rtf", ".odt", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".ipynb"],
    "Shortcuts": [".lnk", ".url"],

}

# Extra smart rules (editable). These run BEFORE extension categories.
RULES = {
    "keywords": {  # name contains keyword (case‑insensitive) → folder
        "invoice": "Finance",
        "assignment": "School",
        "screenshot": "Screenshots",
    },
    #"age_days": {  # if file is at least N days old → folder
    #    30: "Archive",
    
}

CONFIG_PATH = Path.home() / ".folderfresh_config.json"

TOP_LEVEL_CATS = set(CATEGORIES.keys()) | {"Other"}

# ---- Platform helpers ---------------------------------------------------------
if sys.platform.startswith("win"):
    import ctypes
    FILE_ATTRIBUTE_HIDDEN = 0x2

    def is_hidden_win(path: Path) -> bool:
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            return attrs != -1 and bool(attrs & FILE_ATTRIBUTE_HIDDEN)
        except Exception:
            return False
else:
    def is_hidden_win(path: Path) -> bool:  # type: ignore
        return False

# ---- Core helpers -------------------------------------------------------------

def load_config() -> dict:
    try:
        p = Path.home() / CONFIG_FILENAME
        if p.exists():
            return json.load(open(p, "r", encoding="utf-8"))
    except Exception:
        pass
    return {
    "first_run": True,
    "appearance": "system",
    "tray_mode": False,
    "last_folder": None,
    "include_sub": True,
    "skip_hidden": True,
    "safe_mode": True,
    "watch_mode": False,
    "age_filter_days": 0,
    "ignore_exts": "",
    "smart_mode": False
    }


def file_is_stable(path: Path, wait=1.0):
    try:
        size1 = path.stat().st_size
        time.sleep(wait)
        size2 = path.stat().st_size
        return size1 == size2
    except Exception:
        return False
    
def save_config(cfg: dict) -> None:
    try:
        p = Path.home() / CONFIG_FILENAME
        json.dump(cfg, open(p, "w", encoding="utf-8"), indent=2)
    except Exception:
        pass

def file_is_old_enough(path: Path, min_days: int):
    if min_days <= 0:
         return True  # no filter

    cutoff = datetime.now() - timedelta(days=min_days)
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return mtime < cutoff

def scan_dir(
    root: Path,
    include_subfolders: bool,
    skip_hidden: bool,
    ignore_set: set[str],
    skip_categories: bool
) -> list[Path]:

    files: list[Path] = []
    iterator = root.rglob("*") if include_subfolders else root.glob("*")

    for p in iterator:
        try:
            # Ignore user-specified extensions
            if p.suffix.lower() in ignore_set:
                continue
            if not p.is_file():
                continue
            if p.name == LOG_FILENAME:
                continue

            rel = p.relative_to(root)

            # Skip hidden/system files
            if skip_hidden and (
                any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)
            ):
                continue

            # NEW RULE: Skip category folders only if last_mode == current_mode
            if skip_categories:
                if len(rel.parts) >= 2 and rel.parts[0] in TOP_LEVEL_CATS:
                    continue

            files.append(p)

        except Exception:
            # Be tolerant of permission / TOCTOU issues
            continue

    return files



def apply_rules(path: Path) -> str | None:
    name = path.name.lower()
    for kw, folder in RULES.get("keywords", {}).items():
        if kw.lower() in name:
            return folder
    # age‑based
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age = (datetime.now() - mtime).days
        for days, folder in RULES.get("age_days", {}).items():
            try:
                if age >= int(days):
                    return folder
            except Exception:
                continue
    except Exception:
        pass
    return None
# ---- Smart category picker ----------------------------------------------------
def pick_smart_category(path: Path) -> str | None:
    """
    Advanced rule-based categoriser with metadata, filename patterns,
    filetype inference, project detection, and contextual heuristics.
    Returns a smart category or None if no confidently matching rule exists.
    """

    name = path.name.lower()
    stem = path.stem.lower()
    ext = path.suffix.lower()

    # --- Try to get file size early ---
    try:
        size = path.stat().st_size
    except Exception:
        size = None

    # --- Try EXIF for photos ---
    is_photo = False
    try:
        from PIL import Image
        img = Image.open(path)
        img.verify()
        is_photo = True
    except Exception:
        pass

    # =============================================================
    #  HIGH CONFIDENCE MATCHES  (Instant category assignment)
    # =============================================================

    # Screenshots
    if any(x in name for x in ("screenshot", "screen shot", "capture", "snip", "printscreen")):
        return "Screenshots"

    # Camera photos (file structure + EXIF confirmed)
    if is_photo:
        if stem.startswith(("img_", "pxl_", "dsc_", "mvimg_", "psx_", "pano_", "img-")):
            return "Camera Photos"
        if stem[:8].isdigit() and ("-" in stem or "_" in stem):
            return "Camera Photos"

    # Messaging media (WhatsApp, Telegram, Messenger)
    if any(x in name for x in ("whatsapp", "waimg", "telegram", "signal-", "messenger", "line_")):
        return "Messaging Media"

    # High-confidence Installers / Setup files
    if ext in (".exe", ".msi", ".bat") and any(
        x in name for x in ("setup", "installer", "install", "update", "patch")
    ):
        return "Installers"

    # Large compressed files → Archives
    if ext in (".zip", ".rar", ".7z", ".tar", ".gz") and size and size > 200_000_000:
        return "Large Archives"

    # Backup & version files
    if any(x in name for x in ("backup", "bak", "_old", "-old", "(old)", "(copy)", "copy(")):
        return "Backups"

    # =============================================================
    #  MEDIUM CONFIDENCE MATCHES  (Slightly more specific)
    # =============================================================

    # Game assets and save files
    if ext in (".dll", ".pak", ".sav", ".vdf", ".uasset", ".unitypackage") or \
       any(x in name for x in ("unity", "unreal", "godot", "shader", "texture")):
        return "Game Assets"

    # Developer / Project files
    if ext in (".py", ".js", ".ts", ".java", ".cpp", ".csproj", ".sln", ".go", ".rs") or \
       any(x in name for x in ("project", "config", "build", "node_modules")):
        return "Code Projects"

    # Android APKs
    if ext in (".apk", ".aab"):
        return "Android Packages"

    # Video exports / edits
    if ext in (".mp4", ".mov", ".avi", ".mkv") and any(
        x in name for x in ("render", "final", "edited", "export")
    ):
        return "Edited Videos"

    # Edited images / creative content
    if ext in (".psd", ".xcf", ".kra", ".svg") or \
       any(x in name for x in ("design", "banner", "thumbnail", "logo", "cover")):
        return "Creative Assets"

    # Ebooks
    if ext in (".epub", ".mobi", ".azw3", ".pdf") and \
       any(x in name for x in ("ebook", "novel", "chapter", "volume", "book")):
        return "Ebooks"

    # Finance docs
    if any(x in name for x in ("invoice", "receipt", "bank", "statement", "tax", "payment", "paystub")):
        return "Finance"

    # School / Educational content
    if any(x in name for x in ("assignment", "homework", "worksheet", "module", "lesson", "quiz", "exam")):
        return "School Work"

    # =============================================================
    #  LOW CONFIDENCE MATCHES  (Weak patterns, safe fallback)
    # =============================================================

    # Common project folders/images
    if ext in (".png", ".jpg", ".webp") and any(
        x in name for x in ("temp", "asset", "sprite", "icon", "preview")
    ):
        return "Misc Media"

    # Files frequently part of app downloads
    if ext in (".zip", ".rar") and "download" in name:
        return "Downloaded Archives"

    # If nothing matched:
    return None


def pick_category(ext: str, src_path: Path | None = None) -> str:
    # rules first (if we know the source path)
    if src_path is not None:
        folder = apply_rules(src_path)
        if folder:
            return folder
    # then by extension
    ext = ext.lower()
    for folder, exts in CATEGORIES.items():
        if ext in exts:
            return folder
    return "Other"


def unique_dest(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        candidate = path.with_name(f"{stem}_{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1

def plan_moves_preview(files, root):
    #Same as plan_moves but does NOT create folders or write anything.
    moves = []
    for src in files:
        folder = pick_category(src.suffix)  # or smart category, handled outside
        dst_dir = root / folder
        dst = dst_dir / src.name  # DO NOT mkdir, DO NOT unique_dest
        if src != dst:
            moves.append({"src": str(src), "dst": str(dst)})
    return moves

def plan_moves(files: list[Path], root: Path) -> list[dict]:
    """
    Pure helper: plan moves based on extension / rules.
    Does NOT reference UI state (self) so it is safe to call from handlers.
    """
    moves: list[dict] = []
    for src in files:
        # rules first if we can (apply_rules uses path)
        folder = pick_category(src.suffix, src_path=src)
        # fallback to Other handled inside pick_category
        dst_dir = root / folder
        # ensure destination dir is created by the caller (organise/worker)
        # but here we will compute a unique destination name (caller must mkdir before move)
        dst = unique_dest(dst_dir / src.name)
        if src != dst:
            moves.append({"src": str(src), "dst": str(dst)})
    return moves



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
def remove_empty_category_folders(root: Path):
    """Remove empty category folders after undoing moves."""
    try:
        for item in root.iterdir():
            if item.is_dir():
                # Delete ONLY if the folder is empty
                try:
                    next(item.iterdir())  # raises StopIteration if empty
                except StopIteration:
                    # Folder is empty → safe to delete
                    item.rmdir()
    except Exception:
        pass

# ---- Duplicate finder ---------------------------------------------------------

def quick_hash(path: Path, bytes_to_read: int = 1024 * 64):
    try:
        h = hashlib.md5()
        size = path.stat().st_size
        with open(path, "rb") as f:
            chunk = f.read(bytes_to_read)
            h.update(chunk)
            if size > bytes_to_read:
                try:
                    f.seek(max(0, size - bytes_to_read))
                    h.update(f.read(bytes_to_read))
                except Exception:
                    pass
        return (size, h.hexdigest())
    except Exception:
        return None


def group_duplicates(paths: list[Path]) -> list[list[Path]]:
    table: dict[tuple[int, str], list[Path]] = {}
    for p in paths:
        sig = quick_hash(p)
        if not sig:
            continue
        table.setdefault(sig, []).append(p)
    return [grp for grp in table.values() if len(grp) > 1]

# ---- UI App -------------------------------------------------------------------

class FolderFreshApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()

        
        
        # Auto-load last used folder if it still exists
        last = self.config_data.get("last_folder")
        
        ctk.set_appearance_mode(self.config_data.get("appearance", "Dark"))  # "light" | "dark" | "system"
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("860x620")
        self.minsize(760, 560)

        # state
        self.selected_folder: Path | None = None
        self.preview_moves: list[dict] = []
        self.observer: Observer | None = None
        self.tray_icon = None  # pystray.Icon or None
        self.tray_thread = None

        # top bar
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=(12, 6))

        self.path_entry = ctk.CTkEntry(top, placeholder_text="Choose a folder to tidy…", width=620)
        self.path_entry.configure(state="disabled")
        self.path_entry.pack(side="left", padx=(6, 8), pady=8, expand=True, fill="x")

        self.choose_btn = ctk.CTkButton(top, text="📁 Choose Folder", command=self.choose_folder)
        self.choose_btn.pack(side="left", padx=(0, 6), pady=6)
        if last and Path(last).exists():
            self.selected_folder = Path(last)
            # set entry field
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, last)
            self.path_entry.configure(state="disabled")
        
        # options bar
        opts = ctk.CTkFrame(self)
        opts.pack(fill="x", padx=12, pady=6)

        # Configure columns so they don't squish
        opts.grid_columnconfigure((0,1,2,3,4,5,6,7), weight=0)
        opts.grid_rowconfigure(0, weight=1)

        # Row 0 = everything in one neat aligned line
        self.include_sub = ctk.CTkCheckBox(
            opts,
            text="Include subfolders",
            checkbox_width=18,
            checkbox_height=18,
            command=self.remember_options
            )
        self.include_sub.grid(row=0, column=0, padx=8, pady=6, sticky="w")
        if self.config_data.get("include_sub", True):
            self.include_sub.select()
        else:
            self.include_sub.deselect()

        self.skip_hidden = ctk.CTkCheckBox(opts, text="Ignore hidden/system files", checkbox_width=18, checkbox_height=18, command=self.remember_options)
        self.skip_hidden.grid(row=0, column=1, padx=8, pady=6, sticky="w")
        if self.config_data.get("skip_hidden", True):
            self.skip_hidden.select()
        else:
            self.skip_hidden.deselect()
        self.safe_mode = ctk.CTkCheckBox(opts, text="Safe Mode (make copies, keep originals)", command=self.remember_options)
        self.safe_mode.grid(row=0, column=2, padx=8, pady=6, sticky="w")
        if self.config_data.get("safe_mode", True):
            self.safe_mode.select()
        else:
            self.safe_mode.deselect()
        self.watch_mode = ctk.CTkCheckBox(opts, text="Auto-tidy (watch folder)", command=self.on_toggle_watch)
        self.watch_mode.grid(row=0, column=3, padx=8, pady=6, sticky="w")
        if self.config_data.get("watch_mode", False):
            self.watch_mode.select()
        else:
            self.watch_mode.deselect()
        # Age filter controls
        self.age_filter_label = ctk.CTkLabel(opts, text="Only move files older than:")
        self.age_filter_label.grid(row=1, column=0, padx=8, sticky="w")

        self.age_filter_entry = ctk.CTkEntry(opts, width=60, placeholder_text="0 days")
        self.age_filter_entry.grid(row=1, column=1, padx=4, sticky="w")
        self.age_filter_entry.delete(0, "end")
        self.age_filter_entry.insert(0, str(self.config_data.get("age_filter_days", 0)))
        # --- Ignore File Types ---
        self.ignore_label = ctk.CTkLabel(opts, text="Ignore types (e.g. .exe;.dll):")
        self.ignore_label.grid(row=2, column=0, padx=8, pady=6, sticky="w")

        self.ignore_entry = ctk.CTkEntry(opts, width=160, placeholder_text=".exe;.dll")
        self.ignore_entry.grid(row=2, column=1, padx=4, pady=6, sticky="w")

        # Load saved value
        self.ignore_entry.delete(0, "end")
        self.ignore_entry.insert(0, self.config_data.get("ignore_exts", ""))

        # Save on typing
        self.ignore_entry.bind("<KeyRelease>", lambda e: self.remember_options())

        # --- Smart Mode ---
        self.smart_mode = ctk.CTkCheckBox(
            opts,
            text="Smart Sorting (experimental)",
            command=self.remember_options
        )
        self.smart_mode.grid(row=3, column=0, padx=8, pady=6, sticky="w")
        if self.config_data.get("smart_mode", False):
            self.smart_mode.select()
        else:
            self.smart_mode.deselect()



        # center: preview + actions
        center = ctk.CTkFrame(self)
        center.pack(fill="both", expand=True, padx=12, pady=6)

        left = ctk.CTkFrame(center)
        left.pack(side="left", fill="both", expand=True, padx=(6, 3), pady=6)

        right = ctk.CTkFrame(center, width=240)
        right.pack(side="left", fill="y", padx=(3, 6), pady=6)

        # Section header
        actions_label = ctk.CTkLabel(right, text="Actions", font=("Segoe UI", 15, "bold"))
        actions_label.pack(pady=(10, 2))

        self.preview_box = ctk.CTkTextbox(left, wrap="word")
        self.preview_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.preview_box.configure(font=("Segoe UI", 12))
        self.preview_box.insert(
            "end",
            "📂 FolderFresh — Smart Student File Organiser "
            "Welcome!\n"
            "1) Click ‘Choose Folder’\n"
            "2) Click ‘Preview’ to see where files will go\n"
            "3) Click ‘Organise Files’ to tidy up\n"
            "Tip: Safe Mode makes copies (keeps originals)."
        )
        self.preview_box.configure(state="disabled")

        # actions right panel
        self.preview_btn = ctk.CTkButton(right, text="🔍 Preview", command=self.on_preview)
        self.preview_btn.pack(fill="x", padx=12, pady=(14, 8))

        self.organise_btn = ctk.CTkButton(right, text="✅ Organise Files", command=self.on_organise)
        self.organise_btn.pack(fill="x", padx=12, pady=8)

        self.undo_btn = ctk.CTkButton(right, text="⏪ Undo Last", command=self.on_undo)
        self.undo_btn.pack(fill="x", padx=12, pady=8)

        self.dupe_btn = ctk.CTkButton(right, text="🔁 Find Duplicates", command=self.on_find_dupes)
        self.dupe_btn.pack(fill="x", padx=12, pady=8)

        self.desktop_btn = ctk.CTkButton(right, text="🧼 Clean Desktop", command=self.clean_desktop)
        self.desktop_btn.pack(fill="x", padx=12, pady=8)

        self.tray_mode = ctk.CTkCheckBox(right, text="Run in background (tray)", command=self.on_toggle_tray)
        self.tray_mode.pack(fill="x", padx=12, pady=6)

        if self.config_data.get("tray_mode", False):
            self.tray_mode.select()
        else:
            self.tray_mode.deselect()

        self.tray_mode.pack(side="left", padx=8, pady=6)
        # Theme toggle & help
        self.theme_btn = ctk.CTkButton(right, text="🌓 Toggle Dark Mode", command=self.toggle_theme)
        self.theme_btn.pack(fill="x", padx=12, pady=6)

        self.help_btn = ctk.CTkButton(right, text="❓ Help", command=self.show_help, fg_color="gray")
        self.help_btn.pack(fill="x", padx=12, pady=(6, 12))

        # bottom bar: progress + status
        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=12, pady=(0, 12))

        self.progress = ctk.CTkProgressBar(bottom)
        self.progress.set(0)
        self.progress.pack(fill="x", side="left", expand=True, padx=(10, 8), pady=10)

        # Progress counter label (new)
        self.progress_label = ctk.CTkLabel(bottom, text="0/0", font=("Segoe UI", 11))
        self.progress_label.pack(side="left", padx=(0,8))

        self.status = ctk.CTkLabel(bottom, text="Ready ✨", font=("Segoe UI", 12))
        self.status.pack(side="left", padx=8)

        # graceful shutdown for watcher thread
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Button emphasis & initial states
        self.organise_btn.configure(fg_color="#22c55e")  # green
        self.preview_btn.configure(fg_color="#3b82f6")   # blue
        self.desktop_btn.configure(fg_color="#0ea5e9")   # cyan

        # Disable main actions until a folder is chosen
        for b in (self.preview_btn, self.organise_btn, self.undo_btn, self.dupe_btn):
            b.configure(state="disabled")

        # Keyboard shortcuts
        self.bind("<Control-o>", lambda e: self.choose_folder())
        self.bind("<Control-p>", lambda e: self.on_preview())
        self.bind("<Return>", lambda e: self.on_organise())

        # First-run friendly popup
        if self.config_data.get("first_run", True):
            messagebox.showinfo(
                "Welcome!",
                "Welcome to FolderFresh! 👋"
                "• You can Preview before anything changes."
                "• Safe Mode keeps originals."
                "• Undo is always available."
            )
            self.config_data["first_run"] = False
            save_config(self.config_data)
        self.enable_buttons()
        # Start Auto-tidy automatically if enabled and folder restored
        if self.watch_mode.get() and self.selected_folder:
            self.start_watching()
        
    # ---- UI helpers ------------------------------------------------------------

    def set_status(self, msg: str):
        self.status.configure(text=msg)
        self.update_idletasks()

    def set_preview(self, text: str):
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("end", text)
        self.preview_box.configure(state="disabled")

    def choose_folder(self):
        path = filedialog.askdirectory()
        if not path:
            return
        self.selected_folder = Path(path)
        # Save last folder to config
        self.config_data["last_folder"] = str(self.selected_folder)
        save_config(self.config_data)
        self.path_entry.configure(state="normal")
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, str(self.selected_folder))
        self.path_entry.configure(state="disabled")
        self.set_preview("Folder selected. Click ‘Preview’ to see what will happen.")
        self.set_status("Folder ready ✅")
        # Enable actions now that a folder is chosen
        for b in (self.preview_btn, self.organise_btn, self.dupe_btn):
            b.configure(state="normal")
        # keep Undo disabled until a move happens
        # Kill current watcher if any
        self.stop_watching()

        # Restart with new folder if watch mode is enabled
        if self.watch_mode.get():
            time.sleep(0.1)
            self.start_watching()

    # ---- Actions ---------------------------------------------------------------
    def remember_options(self):
        self.config_data["include_sub"] = bool(self.include_sub.get())
        self.config_data["skip_hidden"] = bool(self.skip_hidden.get())
        self.config_data["safe_mode"] = bool(self.safe_mode.get())
        self.config_data["watch_mode"] = bool(self.watch_mode.get())
        try:
            self.config_data["age_filter_days"] = int(self.age_filter_entry.get() or 0)
        except:
            self.config_data["age_filter_days"] = 0
        self.config_data["ignore_exts"] = self.ignore_entry.get()
        self.config_data["smart_mode"] = bool(self.smart_mode.get())
        save_config(self.config_data)

    def on_preview(self):
        # Save current settings
        self.config_data["include_sub"] = bool(self.include_sub.get())
        self.config_data["skip_hidden"] = bool(self.skip_hidden.get())
        self.config_data["safe_mode"] = bool(self.safe_mode.get())
        self.config_data["watch_mode"] = bool(self.watch_mode.get())
        self.config_data["age_filter_days"] = int(self.age_filter_entry.get() or 0)
        save_config(self.config_data)
        if not self.selected_folder or not self.selected_folder.exists():
            messagebox.showerror("Choose Folder", "Please choose a valid folder first.")
            return
        self.disable_buttons()
        self.set_status("Scanning…")
        self.progress.set(0)

        def worker():
            # Force no recursion when cleaning Desktop
            desktop = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
            if self.selected_folder == desktop:
                include_sub = False
            else:
                include_sub = self.include_sub.get()

            min_days = int(self.age_filter_entry.get() or 0)

            ignore_raw = self.config_data.get("ignore_exts", "")
            ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}

            last_mode = self.config_data.get("last_sort_mode", None)
            current_mode = "smart" if self.smart_mode.get() else "simple"
            skip_categories = (last_mode == current_mode)

            files_all = scan_dir(self.selected_folder, self.include_sub.get(), self.skip_hidden.get(), ignore_set, skip_categories)

            # apply age + ignore filter
            files = [
                f for f in files_all
                if file_is_old_enough(f, min_days)
                and f.suffix.lower() not in ignore_set
            ]

            moves = []
            use_smart = self.smart_mode.get()

            for p in files:
                # Smart or fallback
                folder = pick_smart_category(p) if use_smart else None
                if not folder:
                    folder = pick_category(p.suffix)

                # PREVIEW MODE: DO NOT create folders, DO NOT use unique_dest
                dst = self.selected_folder / folder / p.name

                if p != dst:
                    moves.append({"src": str(p), "dst": str(dst)})

            self.preview_moves = moves
            summary = self.make_summary(moves)
            self.after(0, lambda: self.set_preview(summary))
            # show counter: 0 / N -> then N / N
            self.after(0, lambda: self.progress_label.configure(text=f"0/{len(moves)}"))
            self.after(0, lambda: self.set_status(f"Preview ready: {len(moves)} file(s)."))
            self.after(0, self.enable_buttons)
            self.after(0, lambda: self.progress.set(1.0))
            self.after(0, lambda: self.progress_label.configure(text=f"{len(moves)}/{len(moves)}"))

        threading.Thread(target=worker, daemon=True).start()

    def on_organise(self):
        # Save current settings
        self.config_data["include_sub"] = bool(self.include_sub.get())
        self.config_data["skip_hidden"] = bool(self.skip_hidden.get())
        self.config_data["safe_mode"] = bool(self.safe_mode.get())
        self.config_data["watch_mode"] = bool(self.watch_mode.get())
        self.config_data["age_filter_days"] = int(self.age_filter_entry.get() or 0)
        save_config(self.config_data)
        if not self.selected_folder or not self.selected_folder.exists():
            messagebox.showerror("Choose Folder", "Please choose a valid folder first.")
            return
        # ALWAYS regenerate moves fresh (preview is optional)
        self.preview_moves = []

        # Force no recursion when cleaning Desktop
        desktop = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
        if self.selected_folder == desktop:
            include_sub = False
        else:
            include_sub = self.include_sub.get()

        min_days = int(self.age_filter_entry.get() or 0)

        ignore_raw = self.config_data.get("ignore_exts", "")
        ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}

        last_mode = self.config_data.get("last_sort_mode", None)
        current_mode = "smart" if self.smart_mode.get() else "simple"
        skip_categories = (last_mode == current_mode)

        files_all = scan_dir(
            self.selected_folder,
            self.include_sub.get(),
            self.skip_hidden.get(),
            ignore_set,
            skip_categories
        )

        # apply age + ignore filter
        files = [
            f for f in files_all
            if file_is_old_enough(f, min_days)
            and f.suffix.lower() not in ignore_set
        ]

        moves = []
        use_smart = self.smart_mode.get()

        for p in files:
            folder = pick_smart_category(p) if use_smart else None
            if not folder:
                folder = pick_category(p.suffix)

            dest_dir = self.selected_folder / folder
            dest_dir.mkdir(parents=True, exist_ok=True)
            dst = dest_dir / p.name

            if p != dst:
                moves.append({"src": str(p), "dst": str(dst)})

        self.preview_moves = moves

        if not self.preview_moves:
            messagebox.showinfo("Organise", "There’s nothing to move. Nice and tidy already! ✨")
            return
        # --- Space impact estimator when Safe Mode ON ---
        if self.safe_mode.get() and self.preview_moves:
            try:
                total_bytes = sum(
                    Path(m["src"]).stat().st_size
                    for m in self.preview_moves
                    if Path(m["src"]).exists()
                )
                mb = total_bytes / (1024 * 1024)

                if mb > 500:  # 500MB threshold
                    proceed = messagebox.askyesno(
                        "Large Copy Warning",
                        f"Safe Mode will create about {mb:.1f} MB of duplicate data.\n"
                        "This can fill storage.\n\n"
                        "You might want to switch off safe mode\n"
                        "Continue with Safe Mode?"
                    )
                    if not proceed:
                        return
            except Exception:
                pass
        proceed = messagebox.askyesno(
            "Confirm",
            (
                f"I found {len(self.preview_moves)} file(s) to organise.\n\n"
                "Images → Images/\nPDFs → PDF/\nDocuments → Docs/\nVideos → Videos/\n"
                "Audio → Audio/\nArchives → Archives/\nCode → Code/\nOther types → Other/\n\n"
                "Do you want to continue?"
            ),
        )
        if not proceed:
            return

        self.disable_buttons()
        self.progress.set(0)
        self.set_status("Organising… please wait…")

        def worker():
            moves_done: list[dict] = []
            total = len(self.preview_moves)
            for i, m in enumerate(self.preview_moves, start=1):
                try:
                    Path(m["dst"]).parent.mkdir(parents=True, exist_ok=True)
                    if self.safe_mode.get():
                        # COPY instead of MOVE
                        Path(m["dst"]).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(m["src"], m["dst"])  # preserve metadata
                    else:
                        shutil.move(m["src"], m["dst"])  # faster
                    moves_done.append(m)
                except Exception as e:
                    # record error line in preview/status but keep going
                    moves_done.append({"src": m["src"], "dst": m["dst"], "error": str(e)})
                finally:
                    # update progress bar (fraction) and counter "i / total"
                    self.after(0, lambda val=i/total: self.progress.set(val))
                    self.after(0, lambda i=i, total=total: self.progress_label.configure(text=f"{i}/{total}"))

            # log only if not safe_mode (because originals still exist when copying)
            if not self.safe_mode.get():
                save_log(self.selected_folder, moves_done, mode="move")
            else:
                # optional: record copy sessions too (not used by undo)
                try:
                    save_log(self.selected_folder, moves_done, mode="copy")
                except Exception:
                    pass
            # Save last used sorting mode
            self.config_data["last_sort_mode"] = "smart" if self.smart_mode.get() else "simple"
            save_config(self.config_data)
            
            # Cleanup: remove now-empty category folders
            remove_empty_category_folders(self.selected_folder)
            
            self.after(0, lambda: self.set_status("All done ✔️"))

            self.after(0, lambda: self.set_preview(self.finish_summary(moves_done)))
            self.after(0, self.enable_buttons)
            self.after(0, lambda: self.progress_label.configure(text=f"{total}/{total}"))
        threading.Thread(target=worker, daemon=True).start()

    def on_undo(self):
        if not self.selected_folder or not self.selected_folder.exists():
            messagebox.showerror("Choose Folder", "Please choose the same folder you organised before.")
            return
        data = load_log(self.selected_folder)
        if not data:
            messagebox.showinfo("Undo", "You don’t have anything to undo yet.")
            return
        if data.get("mode") == "copy":
            messagebox.showinfo(
                "Undo",
                "The last action was in Safe Mode (COPY). Originals were not moved, so there is nothing to undo.",
            )
            return
        if not messagebox.askyesno("Undo", "Put everything back the way it was?"):
            return

        self.disable_buttons()
        self.progress.set(0)
        self.set_status("Restoring…")

        def worker():
            moves = data.get("moves", [])
            total = len(moves) if moves else 1
            success = 0
            for i, m in enumerate(reversed(moves), start=1):
                src, dst = Path(m["src"]), Path(m["dst"])  # we moved src → dst; now move back
                try:
                    if dst.exists():
                        src.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(dst), str(src))
                        success += 1
                except Exception:
                    pass
                finally:
                    self.after(0, lambda val=i/total: self.progress.set(val))
                    self.after(0, lambda i=i, total=total: self.progress_label.configure(text=f"{i}/{total}"))

            # remove log
            try:
                (self.selected_folder / LOG_FILENAME).unlink(missing_ok=True)
            except Exception:
                pass
            # Remove now-empty category folders
            remove_empty_category_folders(self.selected_folder)

            self.after(0, lambda: self.set_status(f"Undo complete (restored {success} file(s))."))
            self.after(0, lambda: self.set_preview(f"⏪ Undo complete. Restored {success} file(s)."))
            self.after(0, self.enable_buttons)
            self.after(0, lambda: self.progress_label.configure(text=f"{success}/{total}"))

        threading.Thread(target=worker, daemon=True).start()

    def on_find_dupes(self):
        if not self.selected_folder or not self.selected_folder.exists():
            messagebox.showerror("Duplicates", "Choose a folder first.")
            return
        self.disable_buttons()
        self.set_status("Scanning for duplicates…")
        self.progress.set(0)

        def worker():
            ignore_raw = self.config_data.get("ignore_exts", "")
            ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}

            last_mode = self.config_data.get("last_sort_mode", None)
            current_mode = "smart" if self.smart_mode.get() else "simple"
            skip_categories = (last_mode == current_mode)

            files_all = scan_dir(self.selected_folder, self.include_sub.get(), self.skip_hidden.get(), ignore_set, skip_categories)
            files = [f for f in files_all if f.suffix.lower() not in ignore_set]
            groups = group_duplicates(files)
            lines: list[str] = []
            total = sum(len(g) for g in groups)
            for g in groups:
                lines.append("— Potential duplicates —")
                for p in g:
                    try:
                        lines.append(f"  {p.name}   ({p.stat().st_size} B) → {p.parent}")
                    except Exception:
                        lines.append(f"  {p.name}")
            if not lines:
                out = "No obvious duplicates found. 🎉"
            else:
                out = "\n".join(lines) + "\n\nTip: Delete manually the ones you don't need."
            self.after(0, lambda: self.progress_label.configure(text=f"{total}/{total}" if total else "0/0"))
            self.after(0, lambda: self.set_preview(out))
            self.after(0, lambda: self.set_status(f"Duplicate scan done ({total} files in groups)."))
            self.after(0, self.enable_buttons)

        threading.Thread(target=worker, daemon=True).start()

    def clean_desktop(self):
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            messagebox.showerror("Desktop", "Could not find your Desktop folder.")
            return
        self.selected_folder = desktop
        self.path_entry.configure(state="normal")
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, str(desktop))
        self.path_entry.configure(state="disabled")
        self.set_preview("Desktop selected. Click ‘Preview’ then ‘Organise Files’.")
        self.enable_buttons()
        self.set_status("Desktop ready 🧼")
        if self.watch_mode.get():
            self.stop_watching()
            self.start_watching()

    # ---- Auto‑tidy (watch folder) ---------------------------------------------

    def on_toggle_watch(self):
        self.remember_options()   # forces writing safe_mode state
        self.config_data["watch_mode"] = bool(self.watch_mode.get())
        save_config(self.config_data)

        if not self.selected_folder:
            if self.watch_mode.get():
                messagebox.showinfo("Auto‑tidy", "Choose a folder first.")
                self.watch_mode.deselect()
            return 
        if self.watch_mode.get():
            self.start_watching()
        else:
            self.stop_watching()

    def start_watching(self):
        if not self.selected_folder:
            return
        if not WATCHDOG_AVAILABLE:
            messagebox.showwarning("Auto‑tidy", "Install 'watchdog' to enable Auto‑tidy.")
            self.watch_mode.deselect()
            return
        if self.observer:
            return

        class Handler(FileSystemEventHandler):
            def __init__(self, outer: "FolderFreshApp"):
                self.outer = outer

            # ----------- Helper: should Auto-tidy ignore this file? -----------
            def should_ignore(self, p: Path, root: Path) -> bool:
                # Skip category folders (prevents endless loops)
                try:
                    rel = p.relative_to(root)
                    if rel.parts and rel.parts[0] in TOP_LEVEL_CATS:
                        return True
                except Exception:
                    pass

                # Ignore user-ignored extensions
                ignore_raw = self.outer.config_data.get("ignore_exts", "")
                ignore_set = {ext.strip().lower() for ext in ignore_raw.split(";") if ext.strip()}
                if p.suffix.lower() in ignore_set:
                    return True

                # Skip partial download extensions (DO NOT include .tmp)
                PARTIALS = {".crdownload", ".part", ".partial", ".download", ".opdownload"}
                if p.suffix.lower() in PARTIALS:
                    return True

                # Skip hidden/system files
                try:
                    rel = p.relative_to(root)
                    if self.outer.skip_hidden.get() and (
                        any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)
                    ):
                        return True
                except Exception:
                    pass

                return False

            # ----------- Helper: wait for file stability -----------
            def wait_until_stable(self, p: Path, attempts=4, delay=0.25) -> bool:
                """Try multiple times because Explorer holds file locks after drag/drop."""
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

            # ----------- Main: handle file arrival -----------
            def handle_file(self, p: Path, root: Path):
                # ensure file exists
                if not p.exists() or not p.is_file():
                    return

                # skip logic
                if self.should_ignore(p, root):
                    return

                # wait for stability
                if not self.wait_until_stable(p):
                    return
                # --- AGE FILTER (ensure auto-tidy respects it) ---
                try:
                    min_days = int(self.outer.age_filter_entry.get() or 0)
                except:
                    min_days = 0

                if min_days > 0:
                    if not file_is_old_enough(p, min_days):
                        return  # too new → do not auto-move it

                # SMART override
                if self.outer.smart_mode.get():
                    smart_folder = pick_smart_category(p)
                    if smart_folder:
                        dest_dir = root / smart_folder
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dst = dest_dir / p.name
                        try:
                            if self.outer.safe_mode.get():
                                shutil.copy2(p, dst)
                            else:
                                shutil.move(str(p), str(dst))
                        except Exception as e:
                            self.outer.after(0, lambda e=e: self.outer.set_status(f"Auto-tidy error: {e}"))
                        return  # stop here

                # NORMAL rules
                move_plan = plan_moves([p], root)
                if not move_plan:
                    return

                m = move_plan[0]
                try:
                    Path(m["dst"]).parent.mkdir(parents=True, exist_ok=True)
                    if self.outer.safe_mode.get():
                        shutil.copy2(m["src"], m["dst"])
                    else:
                        shutil.move(m["src"], m["dst"])
                except Exception as e:
                    self.outer.after(0, lambda e=e: self.outer.set_status(f"Auto-tidy error: {e}"))

            # ----------- Events -----------

            def on_created(self, event):
                
                if event.is_directory:
                    return
                root = self.outer.selected_folder
                if not root:
                    return
                self.handle_file(Path(event.src_path), root)

            def on_moved(self, event):
                
                if event.is_directory:
                    return
                root = self.outer.selected_folder
                if not root:
                    return
                self.handle_file(Path(event.dest_path), root)

        self.observer = Observer()
        try:
            self.observer.schedule(Handler(self), str(self.selected_folder), recursive=self.include_sub.get())
            self.observer.start()
            self.set_status("Auto‑tidy watching…")
            

        except Exception as e:
            self.observer = None
            self.watch_mode.deselect()
            messagebox.showerror("Auto‑tidy", f"Could not start watcher: {e}")

    def stop_watching(self):
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2)
            except Exception:
                pass
            self.observer = None
            self.set_status("Auto‑tidy stopped")

    # ---- Misc -----------------------------------------------------------------

    def make_summary(self, moves: list[dict]) -> str:
        if not moves:
            return "Nothing to organise. Your folder is already neat. ✨"
        counts: dict[str, int] = {}
        lines: list[str] = []
        for m in moves:
            dst_folder = Path(m["dst"]).parent.name
            counts[dst_folder] = counts.get(dst_folder, 0) + 1
            lines.append(f"• {Path(m['src']).name}  →  {dst_folder}/")
        lines.append("\nSummary:")
        for k in sorted(counts):
            v = counts[k]
            lines.append(f"  - {k}: {v} file(s)")
        return "\n".join(lines)

    def finish_summary(self, moves_done: list[dict]) -> str:
        errors = [m for m in moves_done if m.get("error")]
        ok = [m for m in moves_done if not m.get("error")]
        msg = ["✅ All done! Your folder is organised.\n"]
        if ok:
            msg.append(self.make_summary(ok))
        if errors:
            msg.append("\nSome files could not be moved:")
            for m in errors[:10]:
                msg.append(f"  - {Path(m['src']).name}: {m['error']}")
            if len(errors) > 10:
                msg.append(f"  …and {len(errors) - 10} more.")
        if self.safe_mode.get():
            msg.append("\nNote: Safe Mode was ON, so files were COPIED. Originals are still in place.")
        else:
            msg.append("\nTip: You can use ⏪ Undo to put things back the way they were.")
        return "\n".join(msg)

    def disable_buttons(self):
        for b in (self.preview_btn, self.organise_btn, self.undo_btn, self.choose_btn, self.dupe_btn, self.desktop_btn):
            b.configure(state="disabled")

    def enable_buttons(self):
        for b in (self.preview_btn, self.organise_btn, self.undo_btn, self.choose_btn, self.dupe_btn, self.desktop_btn):
            b.configure(state="normal")

    def show_help(self):
        message = (
        "This app tidies messy folders by sorting files into simple categories.\n\n"
        "How to use:\n"
        "1) Click ‘Choose Folder’.\n"
        "2) Click ‘Preview’ to see where files will go.\n"
        "3) Click ‘Organise Files’ to tidy the folder.\n\n"
        "Options:\n"
        "• Include subfolders — tidy files inside sub-folders.\n"
        "• Ignore hidden/system files — skip hidden or dot-prefixed items.\n"
        "• Safe Mode — makes copies instead of moving (originals stay in place).\n"
        "• Auto-tidy — automatically sort new files when they appear.\n"
        "• Smart Sorting — recognises screenshots, invoices, assignments, photos, etc.\n"
        "• Ignore types — skip certain extensions (e.g. .exe;.tmp).\n"
        "• Age filter — only move files older than a chosen number of days.\n\n"
        "Extras:\n"
        "• Find Duplicates — shows groups of similar files.\n"
        "• Clean Desktop — quickly tidy your Desktop.\n\n"
        "Undo:\n"
        "If Safe Mode was OFF, you can use ‘Undo Last’ to restore moved files."

        )
        messagebox.showinfo("Help", message)

    def toggle_theme(self):
        # Toggle between Light and Dark, remember choice
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        self.config_data["appearance"] = new_mode
        save_config(self.config_data)

    # === Tray Mode Implementation ==============================================
    def on_toggle_tray(self):
        if self.tray_mode.get() and not TRAY_AVAILABLE:
            messagebox.showwarning("Tray Mode", "Install 'pystray' and 'Pillow' to enable tray mode.\n\npip install pystray pillow")
            self.tray_mode.deselect()
            return
        # persist
        self.config_data["tray_mode"] = bool(self.tray_mode.get())
        save_config(self.config_data)

    def build_tray_image(self, size=64):
        # Simple generated icon (blue circle folder-ish)
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((4, 4, size-4, size-4), fill=(14, 165, 233, 255))
        d.rectangle((10, size*0.45, size-10, size-10), fill=(34, 197, 94, 255))
        return img

    def hide_to_tray(self):
        if not TRAY_AVAILABLE:
            self.withdraw()  # fallback: just hide
            return
        if self.tray_icon is not None:
            # Already running; just hide
            self.withdraw()
            self.set_status("Running in tray…")
            return
        self.withdraw()
        self.set_status("Running in tray…")

        def on_open(icon, item=None):
            self.after(0, self.show_window)
        def on_toggle_watch(icon, item=None):
            self.after(0, lambda: self.watch_mode.toggle())
            self.after(0, self.on_toggle_watch)
        def on_exit(icon, item=None):
            try:
                self.stop_watching()
            except Exception:
                pass
            if self.tray_icon:
                try:
                    self.tray_icon.stop()
                except Exception:
                    pass
            self.after(0, self.destroy)

        menu = pystray.Menu(
            pystray.MenuItem("Open FolderFresh", on_open),
            pystray.MenuItem(lambda item: "Turn Auto‑tidy OFF" if self.watch_mode.get() else "Turn Auto‑tidy ON", on_toggle_watch),
            pystray.MenuItem("Exit", on_exit)
        )
        icon_img = self.build_tray_image()
        self.tray_icon = pystray.Icon("FolderFresh", icon_img, "FolderFresh", menu)

        def run_tray():
            try:
                self.tray_icon.run()
            except Exception:
                pass
        self.tray_thread = threading.Thread(target=run_tray, daemon=True)
        self.tray_thread.start()

    def show_window(self):
        try:
            if self.tray_icon:
                try:
                    self.tray_icon.stop()
                except Exception:
                    pass
                self.tray_icon = None
        except Exception:
            pass
        self.deiconify()
        self.lift()
        self.focus_force()
        self.set_status("Ready ✨")



    def on_close(self):
        # If tray mode is enabled and available, hide instead of exit
        if getattr(self, "tray_mode", None) and self.tray_mode.get() and TRAY_AVAILABLE:
            self.hide_to_tray()
            return
        try:
            self.stop_watching()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = FolderFreshApp()
    app.mainloop()
