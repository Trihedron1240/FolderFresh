from __future__ import annotations

import os
import time
import threading
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox

from .config import load_config, save_config
from .constants import APP_TITLE, LOG_FILENAME
from . import actions
from . import watcher
from . import tray

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
        self.observer = None
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
        opts.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=0)
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

        self.skip_hidden = ctk.CTkCheckBox(
            opts,
            text="Ignore hidden/system files",
            checkbox_width=18,
            checkbox_height=18,
            command=self.remember_options
        )
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
        self.progress_label.pack(side="left", padx=(0, 8))

        self.status = ctk.CTkLabel(bottom, text="Ready ✨", font=("Segoe UI", 12))
        self.status.pack(side="left", padx=8)

        # graceful shutdown for watcher thread
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Button emphasis & initial states
        self.organise_btn.configure(fg_color="#22c55e")  # green
        self.preview_btn.configure(fg_color="#3b82f6")  # blue
        self.desktop_btn.configure(fg_color="#0ea5e9")  # cyan

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
        watcher.stop_watching(self)

        # Restart with new folder if watch mode is enabled
        if self.watch_mode.get():
            time.sleep(0.1)
            watcher.start_watching(self)

    # ---- Actions (delegating to actions.py) -----------------------------------

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
        self.disable_buttons()
        self.set_status("Scanning…")
        self.progress.set(0)

        def worker():
            moves = actions.do_preview(self)
            self.preview_moves = moves

            summary = self.make_summary(moves)

            self.after(0, lambda: self.set_preview(summary))
            self.after(0, lambda: self.progress_label.configure(text=f"{len(moves)}/{len(moves)}"))
            self.after(0, lambda: self.progress.set(1))
            self.after(0, lambda: self.set_status(f"Preview ready: {len(moves)} file(s)."))
            self.after(0, self.enable_buttons)

        threading.Thread(target=worker, daemon=True).start()

    def on_organise(self):
        if not self.selected_folder or not self.selected_folder.exists():
            messagebox.showerror("Choose Folder", "Please choose a valid folder first.")
            return

        moves = actions.do_preview(self)
        self.preview_moves = moves

        if not moves:
            messagebox.showinfo("Organise", "There’s nothing to move. Nice and tidy already! ✨")
            return

        proceed = messagebox.askyesno(
            "Confirm",
            f"I found {len(self.preview_moves)} file(s) to organise.\n\n"
            "Images → Images/\nPDFs → PDF/\nDocuments → Docs/\nVideos → Videos/\n"
            "Audio → Audio/\nArchives → Archives/\nCode → Code/\nOther types → Other/\n\n"
            "Do you want to continue?"
        )
        if not proceed:
            return

        self.disable_buttons()
        self.progress.set(0)
        self.set_status("Organising… please wait…")

        def worker():
            moves_done = actions.do_organise(self, moves)
            total = len(moves)

            self.after(0, lambda: self.set_preview(self.finish_summary(moves_done)))
            self.after(0, lambda: self.set_status("All done ✔️"))
            self.after(0, lambda: self.progress_label.configure(text=f"{total}/{total}"))
            self.after(0, self.enable_buttons)

        threading.Thread(target=worker, daemon=True).start()

    def on_undo(self):
        result = actions.do_undo(self)

        if result is None:
            messagebox.showinfo("Undo", "You don’t have anything to undo yet.")
            return

        if result == "copy_mode":
            messagebox.showinfo("Undo", "Last action was Safe Mode COPY — nothing to undo.")
            return

        self.set_preview(f"⏪ Undo complete. Restored {result} file(s).")
        self.set_status(f"Undo complete ({result} file(s) restored).")

    def on_find_dupes(self):
        self.disable_buttons()
        self.set_status("Scanning for duplicates…")
        self.progress.set(0)

        def worker():
            groups = actions.do_find_duplicates(self)

            lines = []
            total = sum(len(g) for g in groups)

            for g in groups:
                lines.append("— Potential duplicates —")
                for p in g:
                    try:
                        lines.append(f"  {p.name} ({p.stat().st_size} B) → {p.parent}")
                    except:
                        lines.append(f"  {p.name}")

            out = "No obvious duplicates found. 🎉" if not lines else "\n".join(lines)

            self.after(0, lambda: self.set_preview(out))
            self.after(0, lambda: self.progress_label.configure(text=f"{total}/{total}"))
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
            watcher.stop_watching(self)
            watcher.start_watching(self)

    # ---- Auto-tidy (watch folder) ---------------------------------------------

    def on_toggle_watch(self):
        # persist options first
        self.remember_options()
        self.config_data["watch_mode"] = bool(self.watch_mode.get())
        save_config(self.config_data)

        # delegate to watcher module
        if self.watch_mode.get():
            watcher.start_watching(self)
        else:
            watcher.stop_watching(self)

    def start_watching(self):
        watcher.start_watching(self)

    def stop_watching(self):
        watcher.stop_watching(self)

    # ---- Misc helper methods --------------------------------------------------

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

    # === Tray Mode wrappers (delegate to tray.py) ==============================

    def on_toggle_tray(self):
        tray.toggle_tray(self)

    def build_tray_image(self, size=64):
        # Keep an in-GUI building helper for backward compatibility (calls tray.build_tray_image)
        return tray.build_tray_image(size=size)

    def hide_to_tray(self):
        tray.hide_to_tray(self)

    def show_window(self):
        tray.show_window(self)

    def on_close(self):
        self.remember_options()
        # If tray mode is enabled, delegate tray handling; else stop watcher and exit
        try:
            if getattr(self, "tray_mode", None) and self.tray_mode.get():
                # delegate hiding logic to tray module
                self.hide_to_tray()
                return
        except Exception:
            pass

        try:
            watcher.stop_watching(self)
        except Exception:
            pass
        self.destroy()


