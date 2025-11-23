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
PARTIAL_EXTS = {".crdownload", ".part", ".partial", ".tmp", ".download"}

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
    "age_filter_days": 0
    }


def file_is_stable(path: Path, wait=0.5):
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

def scan_dir(root: Path, include_subfolders: bool, skip_hidden: bool) -> list[Path]:
    """Return list of files under root (optionally recursive).

    We deliberately skip:
      • Hidden files (dotfiles or Windows hidden) when requested
      • Our own log file
      • Files already inside top‑level category folders (to avoid re‑processing)
    """
    files: list[Path] = []
    iterator = root.rglob("*") if include_subfolders else root.glob("*")

    for p in iterator:
        try:
            

            if not p.is_file():
                continue
            if p.name == LOG_FILENAME:
                continue
            rel = p.relative_to(root)
            if skip_hidden and (any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)):
                continue
            if len(rel.parts) >= 2 and rel.parts[0] in TOP_LEVEL_CATS:
                # already organised into a top‑level category → skip
                continue
            files.append(p)
        except Exception:
            # Be tolerant of permission/TOCTOU issues
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


def plan_moves(files: list[Path], root: Path) -> list[dict]:
    moves: list[dict] = []
    for src in files:
        folder = pick_category(src.suffix, src_path=src)
        dst_dir = root / folder
        dst_dir.mkdir(parents=True, exist_ok=True)
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
        if self.watch_mode.get():
            self.stop_watching()
            self.start_watching()

        if self.watch_mode.get():
            self.stop_watching()
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

            files_all = scan_dir(self.selected_folder, self.include_sub.get(), self.skip_hidden.get())
            files = [f for f in files_all if file_is_old_enough(f, min_days)]

            moves = plan_moves(files, self.selected_folder)

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
        # ensure we have a plan; if not, compute quickly
        if not self.preview_moves:
            # Force no recursion when cleaning Desktop
            desktop = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
            if self.selected_folder == desktop:
                include_sub = False
            else:
                include_sub = self.include_sub.get()
 
            min_days = int(self.age_filter_entry.get() or 0)

            files_all = scan_dir(self.selected_folder, self.include_sub.get(), self.skip_hidden.get())
            files = [f for f in files_all if file_is_old_enough(f, min_days)]

            self.preview_moves = plan_moves(files, self.selected_folder)
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
            files = scan_dir(self.selected_folder, self.include_sub.get(), self.skip_hidden.get())
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
            def on_created(self, event):
                if event.is_directory:
                    return
                root = self.outer.selected_folder
                if not root:
                    return
                p = Path(event.src_path)
                if not p.exists() or not p.is_file():
                    return
                if not file_is_stable(p):
                    return

                # --- SKIP PARTIAL DOWNLOADS ---
                PARTIAL_EXTS = {".crdownload", ".part", ".partial", ".tmp", ".download"}
                if p.suffix.lower() in PARTIAL_EXTS:
                    return
                # hidden check
                try:
                    rel = p.relative_to(root)
                    if self.outer.skip_hidden.get() and (
                        any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)
                    ):
                        return
                except Exception:
                    pass
                # plan & act for this single file
                move_plan = plan_moves([p], root)
                if not move_plan:
                    return
                m = move_plan[0]
                try:
                    if self.outer.safe_mode.get():
                        Path(m["dst"]).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(m["src"], m["dst"])
                    else:
                        shutil.move(m["src"], m["dst"]) 
                    self.outer.after(0, lambda: self.outer.set_status(f"Auto‑tidy moved: {Path(m['dst']).name}"))
                except Exception as e:
                    self.outer.after(0, lambda: self.outer.set_status(f"Auto‑tidy error: {e}"))
            def on_moved(self, event):
                # When a partial download is renamed to a real file
                if event.is_directory:
                    return
                root = self.outer.selected_folder
                if not root:
                    return

                p = Path(event.dest_path)
                if not p.exists() or not p.is_file():
                    return

                # skip hidden
                try:
                    rel = p.relative_to(root)
                    if self.outer.skip_hidden.get() and (
                        any(part.startswith(".") for part in rel.parts) or is_hidden_win(p)
                    ):
                        return
                except Exception:
                    pass

                # skip partials
                PARTIAL_EXTS = {".crdownload", ".part", ".partial", ".tmp", ".download", ".opdownload"}
                if p.suffix.lower() in PARTIAL_EXTS:
                    return

                # stability check
                if not file_is_stable(p):
                    return

                # plan & act
                move_plan = plan_moves([p], root)
                if not move_plan:
                    return

                m = move_plan[0]
                try:
                    if self.outer.safe_mode.get():
                        Path(m["dst"]).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(m["src"], m["dst"])
                    else:
                        shutil.move(m["src"], m["dst"])
                    self.outer.after(0, lambda: self.outer.set_status(f"Auto-tidy moved: {Path(m['dst']).name}"))
                except Exception as e:
                    self.outer.after(0, lambda: self.outer.set_status(f"Auto-tidy error: {e}"))
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
            "This app tidies messy folders by sorting files into neat categories.\n\n"
            "How to use:\n"
            "1) Click ‘Choose Folder’.\n"
            "2) Click ‘Preview’ to see what will happen.\n"
            "3) Click ‘Organise Files’ to tidy up.\n\n"
            "Options:\n"
            "• Also tidy inside sub‑folders (Include subfolders).\n"
            "• Ignore hidden/system files (recommended).\n"
            "• Safe Mode — makes copies, keeps originals (safer, uses more space).\n"
            "• Auto‑tidy — automatically sort new files as they appear.\n"
            "• Run in background (tray) — keep FolderFresh active via system tray.\n\n"
            "Extras:\n"
            "• Find Duplicates — suggests duplicate groups (by size + partial hash).\n"
            "• Clean Desktop — instantly target your Desktop folder.\n\n"
            "Undo: If you moved files (Safe Mode off), use ‘Undo Last’ to restore."
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
