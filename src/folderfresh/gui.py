# gui.py (Windows-11-style, Option C with Smart + Auto-tidy in basic row, Tray in Advanced, Help as circular icon)
from __future__ import annotations

import os
import time
import threading
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox

from .config import load_config, save_config
from .constants import APP_TITLE, LOG_FILENAME
from . import actions
from . import watcher
from . import tray

# Optional local file path (uploaded earlier) — can be used for tray/icon if you replace with a real .ico/.png
ICON_PATH = "/mnt/data/FolderFresh.py"

# Theme colours tuned for a Windows-11 utility look
ACCENT = "#2563eb"
SUCCESS = "#16a34a"
PANEL_BG = "#0f1720"
CARD_BG = "#0b1220"
BORDER = "#1f2937"
TEXT = "#e6eef8"
MUTED = "#9aa6b2"


class FolderFreshApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # load config
        self.config_data = load_config()

        # appearance
        ctk.set_appearance_mode("Dark")
        self.config_data["appearance"] = "Dark"

        ctk.set_default_color_theme("blue")

        # window
        self.title(APP_TITLE)
        self.geometry("880x660")
        self.minsize(760, 520)

        # state
        self.selected_folder: Optional[Path] = None
        self.preview_moves: list[dict] = []
        self.observer = None
        self.tray_icon = None
        self.tray_thread = None
        self.advanced_visible = False

        # root background
        self.configure(fg_color=PANEL_BG)

        # header card
        header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        header.pack(fill="x", padx=16, pady=(16, 10))

        title_label = ctk.CTkLabel(
            header, text=APP_TITLE, font=("Segoe UI Variable", 18, "bold"), text_color=TEXT
        )
        title_label.pack(side="left", padx=(12, 12))

        self.path_entry = ctk.CTkEntry(
            header,
            placeholder_text="Choose a folder to tidy…",
            width=0,
            height=0,
            corner_radius=8,
            fg_color="#071018",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
        )
        self.path_entry.configure(state="disabled")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        choose_btn = ctk.CTkButton(
            header,
            text="Choose Folder",
            width=140,
            corner_radius=8,
            fg_color=ACCENT,
            hover_color="#1e4fd8",
            command=self.choose_folder,
        )
        choose_btn.pack(side="right", padx=(0, 12))

        # main card
        main_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        main_card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # basic options row
        opts = ctk.CTkFrame(main_card, fg_color=CARD_BG)
        opts.pack(fill="x", padx=12, pady=(12, 10))

        # Include sub / Skip hidden / Safe mode
        self.include_sub = ctk.CTkCheckBox(opts, text="Include subfolders", command=self.remember_options)
        self.include_sub.grid(row=0, column=0, sticky="w", padx=(6, 16))
        if self.config_data.get("include_sub", True):
            self.include_sub.select()
        else:
            self.include_sub.deselect()

        self.skip_hidden = ctk.CTkCheckBox(opts, text="Ignore hidden/system files", command=self.remember_options)
        self.skip_hidden.grid(row=0, column=1, sticky="w", padx=(0, 16))
        if self.config_data.get("skip_hidden", True):
            self.skip_hidden.select()
        else:
            self.skip_hidden.deselect()

        self.safe_mode = ctk.CTkCheckBox(opts, text="Safe Mode (copy)", command=self.remember_options)
        self.safe_mode.grid(row=0, column=2, sticky="w", padx=(0, 16))
        if self.config_data.get("safe_mode", True):
            self.safe_mode.select()
        else:
            self.safe_mode.deselect()

        # Smart Sorting + Auto-tidy in basic row (Option C)
        self.smart_mode = ctk.CTkCheckBox(opts, text="Smart Sorting (experimental)", command=self.remember_options)
        self.smart_mode.grid(row=0, column=3, sticky="w", padx=(0, 16))
        if self.config_data.get("smart_mode", False):
            self.smart_mode.select()
        else:
            self.smart_mode.deselect()

        self.watch_mode = ctk.CTkCheckBox(opts, text="Auto-tidy", command=self.on_toggle_watch)
        self.watch_mode.grid(row=0, column=4, sticky="w", padx=(0, 6))
        if self.config_data.get("watch_mode", False):
            self.watch_mode.select()
        else:
            self.watch_mode.deselect()

        # actions row
        btn_row = ctk.CTkFrame(main_card, fg_color=CARD_BG)
        btn_row.pack(fill="x", padx=12, pady=(0, 12))

        btn_pad = 8
        self.preview_btn = ctk.CTkButton(
            btn_row, text="Preview", width=140, corner_radius=10, fg_color=ACCENT, hover_color="#1e4fd8", command=self.on_preview
        )
        self.preview_btn.grid(row=0, column=0, padx=(btn_pad, 0), pady=6)

        self.organise_btn = ctk.CTkButton(
            btn_row,
            text="Organise Files",
            width=160,
            corner_radius=10,
            fg_color=SUCCESS,
            hover_color="#0f9a3a",
            command=self.on_organise,
        )
        self.organise_btn.grid(row=0, column=1, padx=(btn_pad, 0), pady=6)

        self.undo_btn = ctk.CTkButton(
            btn_row, text="Undo Last", width=140, corner_radius=10, fg_color="#334155", hover_color="#24313b", command=self.on_undo
        )
        self.undo_btn.grid(row=0, column=2, padx=(btn_pad, 0), pady=6)

        self.dupe_btn = ctk.CTkButton(
            btn_row,
            text="Find Duplicates",
            width=160,
            corner_radius=10,
            fg_color="#3b82f6",
            hover_color="#2f6fdc",
            command=self.on_find_dupes,
        )
        self.dupe_btn.grid(row=0, column=3, padx=(btn_pad, 0), pady=6)

        self.desktop_btn = ctk.CTkButton(
            btn_row, text="Clean Desktop", width=140, corner_radius=10, fg_color="#0ea5a4", hover_color="#0a8a88", command=self.clean_desktop
        )
        self.desktop_btn.grid(row=0, column=4, padx=(btn_pad, 8), pady=6)

        # preview label
        preview_label = ctk.CTkLabel(main_card, text="Preview", font=("Segoe UI Variable", 13, "bold"), text_color=TEXT)
        preview_label.pack(anchor="w", padx=12, pady=(4, 6))

        # preview box
        self.preview_box = ctk.CTkTextbox(
            main_card,
            wrap="word",
            corner_radius=10,
            width=0,
            height=0,
            fg_color="#071018",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
        )
        self.preview_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.preview_box.insert("end", "Select a folder and click Preview to see planned moves.")
        self.preview_box.configure(state="disabled", font=("Segoe UI", 11))

        # advanced toggle
        adv_frame = ctk.CTkFrame(main_card, fg_color=CARD_BG)
        adv_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.advanced_button = ctk.CTkButton(
            adv_frame, text="Advanced Options ▾", width=720, corner_radius=10, fg_color="#1f2937", hover_color="#16202a", command=self.toggle_advanced
        )
        self.advanced_button.pack(fill="x", padx=6)

        # advanced content (hidden initially)
        self.advanced_frame = ctk.CTkFrame(main_card, fg_color=CARD_BG, corner_radius=10)
        # advanced_frame is not packed -> hidden

        # advanced inner layout
        adv_inner = ctk.CTkFrame(self.advanced_frame, fg_color=CARD_BG)
        adv_inner.pack(fill="x", padx=8, pady=8)

        # age filter + ignore types + custom category names
        age_label = ctk.CTkLabel(adv_inner, text="Only move files older than (days):")
        age_label.grid(row=0, column=0, sticky="w", padx=(4, 8), pady=(4, 6))
        self.age_filter_entry = ctk.CTkEntry(
            adv_inner, width=100, corner_radius=8, fg_color="#071018", border_width=1, border_color=BORDER, text_color=TEXT
        )
        self.age_filter_entry.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=(4, 6))
        self.age_filter_entry.delete(0, "end")
        self.age_filter_entry.insert(0, str(self.config_data.get("age_filter_days", 0)))

        ignore_label = ctk.CTkLabel(adv_inner, text="Ignore types (e.g. .exe;.tmp):")
        ignore_label.grid(row=1, column=0, sticky="w", padx=(4, 8), pady=(0, 6))
        self.ignore_entry = ctk.CTkEntry(
            adv_inner, width=420, corner_radius=8, fg_color="#071018", border_width=1, border_color=BORDER, text_color=TEXT
        )
        self.ignore_entry.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=(0, 6))
        self.ignore_entry.delete(0, "end")
        self.ignore_entry.insert(0, self.config_data.get("ignore_exts", ""))
        self.ignore_entry.bind("<KeyRelease>", lambda e: self.remember_options())

        edit_names_row = ctk.CTkFrame(adv_inner, fg_color=CARD_BG)
        edit_names_row.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 6))

        self.edit_names_btn = ctk.CTkButton(
            edit_names_row,
            text="Edit Category Names",
            width=180,
            corner_radius=8,
            fg_color="#374151",
            hover_color="#2b3740",
            command=self.open_category_editor
        )
        self.edit_names_btn.pack(anchor="w", padx=(4, 0))
        # tray mode (in advanced)
        toggles = ctk.CTkFrame(self.advanced_frame, fg_color=CARD_BG)
        toggles.pack(fill="x", padx=8, pady=(6, 8))

        self.tray_mode = ctk.CTkCheckBox(toggles, text="Run in background (tray)", command=self.on_toggle_tray)
        self.tray_mode.pack(side="left", padx=(6, 12))
        if self.config_data.get("tray_mode", False):
            self.tray_mode.select()
        else:
            self.tray_mode.deselect()

        # help button (small circular icon button) - style B
        help_frame = ctk.CTkFrame(main_card, fg_color=CARD_BG)
        help_frame.pack(fill="x", padx=12, pady=(0, 6))
        # place help at right side
        help_container = ctk.CTkFrame(help_frame, fg_color=CARD_BG)
        help_container.pack(fill="both")
        self.help_btn = ctk.CTkButton(
            help_container,
            text="?",
            width=36,
            height=36,
            corner_radius=18,
            fg_color="#374151",
            hover_color="#2b3740",
            command=self.show_help,
        )
        # align to right
        self.help_btn.pack(anchor="e", padx=(0, 8))

        # bottom status strip
        bottom = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        bottom.pack(fill="x", padx=16, pady=(0, 16))

        self.progress = ctk.CTkProgressBar(bottom, corner_radius=8)
        self.progress.set(0)
        self.progress.pack(fill="x", side="left", expand=True, padx=(10, 12), pady=8)

        self.progress_label = ctk.CTkLabel(bottom, text="0/0")
        self.progress_label.pack(side="left", padx=(0, 12), pady=8)

        self.status = ctk.CTkLabel(bottom, text="Ready")
        self.status.pack(side="left", padx=(0, 8), pady=8)

        # protocol and bindings
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Control-o>", lambda e: self.choose_folder())
        self.bind("<Control-p>", lambda e: self.on_preview())
        self.bind("<Return>", lambda e: self.on_organise())

        # initial disable
        for b in (self.preview_btn, self.organise_btn, self.undo_btn, self.dupe_btn):
            b.configure(state="disabled")

        # first run
        if self.config_data.get("first_run", True):
            messagebox.showinfo(
                "Welcome",
                "Welcome to FolderFresh!\n\nUse Preview before organising. Safe Mode copies files."
            )
            self.config_data["first_run"] = False
            save_config(self.config_data)

        # restore last folder
        last = self.config_data.get("last_folder")
        if last and Path(last).exists():
            self.selected_folder = Path(last)
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, last)
            self.path_entry.configure(state="disabled")
            for b in (self.preview_btn, self.organise_btn, self.dupe_btn):
                b.configure(state="normal")

        # start watcher if needed
        if self.watch_mode.get() and self.selected_folder:
            watcher.start_watching(self)

    # UI helpers
    def set_status(self, msg: str):
        self.status.configure(text=msg)
        self.update_idletasks()

    def set_preview(self, text: str):
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("end", text)
        self.preview_box.configure(state="disabled")

    def toggle_advanced(self):
        if self.advanced_visible:
            self.advanced_frame.pack_forget()
            self.advanced_button.configure(text="Advanced Options ▾")
            self.advanced_visible = False
        else:
            self.advanced_frame.pack(fill="x", padx=12, pady=(0, 12))
            self.advanced_button.configure(text="Advanced Options ▴")
            self.advanced_visible = True
    def open_category_editor(self):
        win = ctk.CTkToplevel(self)
        win.title("Edit Category Names")
        win.geometry("380x460")
        win.minsize(360, 420)
        win.grab_set()  # modal behaviour

        ctk.CTkLabel(
            win, text="Rename Categories", font=("Segoe UI Variable", 16, "bold")
        ).pack(pady=(12, 6))

        from .constants import DEFAULT_CATEGORIES
        self.name_entries = {}

        # Field list
        for cat in DEFAULT_CATEGORIES:
            row = ctk.CTkFrame(win)
            row.pack(fill="x", padx=12, pady=4)

            ctk.CTkLabel(row, text=f"{cat} →", width=120).pack(side="left", padx=(0, 6))

            entry = ctk.CTkEntry(
                row,
                width=200,
                corner_radius=8,
                fg_color="#071018",
                border_width=1,
                border_color=BORDER,
                text_color=TEXT,
            )
            entry.pack(side="left", fill="x", expand=True)

            # Load saved override
            entry.insert(
                0,
                self.config_data.get("custom_category_names", {}).get(cat, "")
            )

            self.name_entries[cat] = entry

        def save_names():
            overrides = {}
            for cat, ent in self.name_entries.items():
                val = ent.get().strip()
                if val:
                    overrides[cat] = val

            self.config_data["custom_category_names"] = overrides
            save_config(self.config_data)
            win.destroy()

        save_btn = ctk.CTkButton(
            win, text="Save", fg_color=ACCENT, hover_color="#1e4fd8", command=save_names
        )
        save_btn.pack(pady=12)

    # folder selection
    def choose_folder(self):
        path = filedialog.askdirectory()
        if not path:
            return
        self.selected_folder = Path(path)
        self.config_data["last_folder"] = str(self.selected_folder)
        save_config(self.config_data)
        self.path_entry.configure(state="normal")
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, str(self.selected_folder))
        self.path_entry.configure(state="disabled")
        self.set_preview("Folder selected. Click Preview to see what will happen.")
        self.set_status("Folder ready")
        for b in (self.preview_btn, self.organise_btn, self.dupe_btn):
            b.configure(state="normal")
        watcher.stop_watching(self)
        if self.watch_mode.get():
            time.sleep(0.1)
            watcher.start_watching(self)

    # actions (delegate to actions.py)
    def remember_options(self):
        try:
            self.config_data["age_filter_days"] = int(self.age_filter_entry.get() or 0)
        except Exception:
            self.config_data["age_filter_days"] = 0
        self.config_data["include_sub"] = bool(self.include_sub.get())
        self.config_data["skip_hidden"] = bool(self.skip_hidden.get())
        self.config_data["safe_mode"] = bool(self.safe_mode.get())
        self.config_data["watch_mode"] = bool(self.watch_mode.get())
        self.config_data["ignore_exts"] = self.ignore_entry.get()
        self.config_data["smart_mode"] = bool(self.smart_mode.get())
        self.config_data["tray_mode"] = bool(self.tray_mode.get())
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

        self.remember_options()

        moves = actions.do_preview(self)
        self.preview_moves = moves

        if not moves:
            messagebox.showinfo("Organise", "There’s nothing to move. Your folder is tidy.")
            return

        if self.safe_mode.get() and self.preview_moves:
            try:
                total_bytes = sum(Path(m["src"]).stat().st_size for m in self.preview_moves if Path(m["src"]).exists())
                mb = total_bytes / (1024 * 1024)
                if mb > 500:
                    proceed = messagebox.askyesno(
                        "Large Copy Warning",
                        f"Safe Mode will create about {mb:.1f} MB of duplicate data. Continue?"
                    )
                    if not proceed:
                        return
            except Exception:
                pass

        proceed = messagebox.askyesno("Confirm", f"I found {len(self.preview_moves)} file(s) to organise. Continue?")
        if not proceed:
            return

        self.disable_buttons()
        self.progress.set(0)
        self.set_status("Organising… please wait…")

        def worker():
            moves_done = actions.do_organise(self, moves)
            total = len(moves)
            self.after(0, lambda: self.set_preview(self.finish_summary(moves_done)))
            self.after(0, lambda: self.set_status("All done"))
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

        self.config_data["last_sort_mode"] = None
        save_config(self.config_data)

        self.set_preview(f"Undo complete. Restored {result} file(s).")
        self.set_status(f"Undo complete ({result} restored).")

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
                    except Exception:
                        lines.append(f"  {p.name}")
            out = "No obvious duplicates found." if not lines else "\n".join(lines)
            self.after(0, lambda: self.set_preview(out))
            self.after(0, lambda: self.progress_label.configure(text=f"{total}/{total}" if total else "0/0"))
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
        self.set_status("Desktop ready")
        if self.watch_mode.get():
            watcher.stop_watching(self)
            watcher.start_watching(self)

    # watcher & tray wrappers
    def on_toggle_watch(self):
        self.remember_options()
        self.config_data["watch_mode"] = bool(self.watch_mode.get())
        save_config(self.config_data)
        if self.watch_mode.get():
            watcher.start_watching(self)
        else:
            watcher.stop_watching(self)

    def start_watching(self):
        watcher.start_watching(self)

    def stop_watching(self):
        watcher.stop_watching(self)

    def on_toggle_tray(self):
        tray.toggle_tray(self)

    def hide_to_tray(self):
        tray.hide_to_tray(self)

    def show_window(self):
        tray.show_window(self)

    # summaries
    def make_summary(self, moves: list[dict]) -> str:
        if not moves:
            return "Nothing to organise."
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
        msg = ["All done!\n"]
        if ok:
            msg.append(self.make_summary(ok))
        if errors:
            msg.append("\nSome files could not be moved:")
            for m in errors[:10]:
                msg.append(f"  - {Path(m['src']).name}: {m['error']}")
            if len(errors) > 10:
                msg.append(f"  …and {len(errors) - 10} more.")
        if self.safe_mode.get():
            msg.append("\nNote: Safe Mode was ON, so files were COPIED.")
        else:
            msg.append("\nTip: You can use Undo to put things back.")
        return "\n".join(msg)

    def disable_buttons(self):
        for b in (self.preview_btn, self.organise_btn, self.undo_btn, self.dupe_btn, self.desktop_btn):
            b.configure(state="disabled")

    def enable_buttons(self):
        for b in (self.preview_btn, self.organise_btn, self.undo_btn, self.dupe_btn, self.desktop_btn):
            b.configure(state="normal")

    def show_help(self):
        message = (
            "FolderFresh tidies folders by sorting files into categories.\n\n"
            "Use Preview to check changes before Organising.\n"
            "Safe Mode copies instead of moving.\n"
            "Advanced options include age filter, ignore types, smart sorting, and auto-tidy."
        )
        messagebox.showinfo("Help", message)


    def on_close(self):
        try:
            self.remember_options()
        except Exception:
            pass

        try:
            if getattr(self, "tray_mode", None) and self.tray_mode.get():
                self.hide_to_tray()
                return
        except Exception:
            pass

        try:
            watcher.stop_watching(self)
        except Exception:
            pass

        self.destroy()


