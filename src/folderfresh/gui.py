from __future__ import annotations

import os
import sys
import time
import threading
import webbrowser
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox
from .config import load_config, save_config
from .constants import APP_TITLE, LOG_FILENAME, APP_VERSION
from .watcher_manager import WatcherManager
from datetime import datetime
from . import actions
from . import tray
from .profile_store import ProfileStore
from .profile_manager import ProfileManagerWindow

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

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None

        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25

        self.tip_window = tw = ctk.CTkToplevel(self.widget)
        tw.overrideredirect(True)
        tw.geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(
            tw,
            text=self.text,
            bg_color="#000000",
            text_color="#ffffff",
            corner_radius=6,
            fg_color="#000000",
            padx=6,
            pady=4,
        )
        label.pack()
    
    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class FolderFreshApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Load configuration and profiles
        self._initialize_config_and_profiles()

        # Initialize multi-folder watcher manager
        self.watcher_manager = WatcherManager(self)

        # Set appearance and theme
        self._initialize_appearance()

        # Configure window
        self._configure_window()

        # Initialize application state
        self._initialize_state()

        # Set root background
        self.configure(fg_color=PANEL_BG)

        # Create UI sections
        self._create_header_section()
        self._create_main_card()
        self._create_footer()
        self._create_status_bar()

        # Setup event handlers and initialization
        self._setup_event_handlers()
        self._initialize_button_states()
        self._handle_first_run()
        self._restore_last_folder()
        self._start_watched_folders()
        # ------------------------------------------------------------
        # Force Auto-Tidy to reinitialize properly if it was ON
        # ------------------------------------------------------------
        if self.config_data.get("watch_mode", False):
            # Temporarily disable
            self.watch_mode.deselect()
            self.on_toggle_watch()

            # Re-enable (this runs the full correct logic)
            self.watch_mode.select()
            self.on_toggle_watch()
             
    def _initialize_config_and_profiles(self):
        """Load configuration and profile data."""
        from .profile_store import ProfileStore
        global_cfg = load_config()
        store = ProfileStore()
        store.ensure_profiles()
        profiles_doc = store.load()
        active_profile = store.get_active_profile(profiles_doc)
        self.config_data = store.merge_profile_into_config(active_profile, global_cfg)

        # Keep references to the store for later saves
        self.profile_store = store
        self.profiles_doc = profiles_doc
        self.active_profile = active_profile

    def _initialize_appearance(self):
        """Configure application appearance and theme."""
        ctk.set_appearance_mode("Dark")
        self.config_data["appearance"] = "Dark"
        ctk.set_default_color_theme("blue")

    def _configure_window(self):
        """Set up window properties."""
        self.title(APP_TITLE)
        self.geometry("880x660")
        self.minsize(760, 520)

    def _initialize_state(self):
        """Initialize application state variables."""
        self.selected_folder: Optional[Path] = None
        self.preview_moves: list[dict] = []
        self.observer = None
        self.tray_icon = None
        self.tray_thread = None
        self.advanced_visible = False

    def _create_header_section(self):
        """Create the header card with title and folder selection."""
        header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        header.pack(fill="x", padx=16, pady=(16, 10))

        # Application title
        title_label = ctk.CTkLabel(
            header,
            text=APP_TITLE,
            font=("Segoe UI Variable", 18, "bold"),
            text_color=TEXT
        )
        title_label.pack(side="left", padx=(12, 12))

        # Folder path display
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

        # Folder selection buttons
        open_btn = ctk.CTkButton(
            header,
            text="Open Folder",
            width=140,
            corner_radius=8,
            fg_color=ACCENT,
            hover_color="#1e4fd8",
            command=self.open_folder,
        )
        open_btn.pack(side="right", padx=(1, 12))

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

    def _create_main_card(self):
        """Create the main content card with options and controls."""
        main_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        main_card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self._create_basic_options(main_card)
        self._create_action_buttons(main_card)
        self._create_preview_section(main_card)
        self._create_advanced_section(main_card)
        self._create_help_button(main_card)

    def _create_basic_options(self, parent):
        """Create the basic options checkboxes."""
        opts = ctk.CTkFrame(parent, fg_color=CARD_BG)
        opts.pack(fill="x", padx=12, pady=(12, 10))

        # Configure grid columns for equal spacing
        for i in range(5):
            opts.grid_columnconfigure(i, weight=1)

        # Include subfolders checkbox
        self.include_sub = ctk.CTkCheckBox(
            opts,
            text="Include subfolders",
            command=self.remember_options
        )
        self.include_sub.grid(row=0, column=0, sticky="w", padx=8, pady=4)
        if self.config_data.get("include_sub", True):
            self.include_sub.select()
        else:
            self.include_sub.deselect()

        # Skip hidden files checkbox
        self.skip_hidden = ctk.CTkCheckBox(
            opts,
            text="Ignore hidden/system files",
            command=self.remember_options
        )
        self.skip_hidden.grid(row=0, column=1, sticky="w", padx=8, pady=4)
        if self.config_data.get("skip_hidden", True):
            self.skip_hidden.select()
        else:
            self.skip_hidden.deselect()

        # Safe mode checkbox
        self.safe_mode = ctk.CTkCheckBox(
            opts,
            text="Safe Mode (copy)",
            command=self.remember_options
        )
        self.safe_mode.grid(row=0, column=2, sticky="w", padx=8, pady=4)
        if self.config_data.get("safe_mode", True):
            self.safe_mode.select()
        else:
            self.safe_mode.deselect()

        # Smart sorting checkbox with tooltip
        self.smart_mode = ctk.CTkCheckBox(
            opts,
            text="Smart Sorting",
            command=self.remember_options
        )
        Tooltip(
            self.smart_mode,
            "Uses advanced rules to detect screenshots, assignments,\nphotos, invoices, messaging media and more."
        )
        self.smart_mode.grid(row=0, column=3, sticky="w", padx=8, pady=4)
        if self.config_data.get("smart_mode", False):
            self.smart_mode.select()
        else:
            self.smart_mode.deselect()

        # Auto-tidy checkbox
        self.watch_mode = ctk.CTkCheckBox(
            opts,
            text="Auto-tidy",
            command=self.on_toggle_watch
        )
        self.watch_mode.grid(row=0, column=4, sticky="w", padx=8, pady=4)
        if self.config_data.get("watch_mode", False):
            self.watch_mode.select()
        else:
            self.watch_mode.deselect()

    def _create_action_buttons(self, parent):
        """Create the action buttons row."""
        btn_row = ctk.CTkFrame(parent, fg_color=CARD_BG)
        btn_row.pack(fill="x", padx=12, pady=(0, 12))

        # Configure grid columns for equal spacing
        for i in range(5):
            btn_row.grid_columnconfigure(i, weight=1)

        # Preview button
        self.preview_btn = ctk.CTkButton(
            btn_row,
            text="Preview",
            width=140,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color="#1e4fd8",
            command=self.on_preview
        )
        self.preview_btn.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        # Organize button
        self.organise_btn = ctk.CTkButton(
            btn_row,
            text="Organise Files",
            width=160,
            corner_radius=10,
            fg_color=SUCCESS,
            hover_color="#0f9a3a",
            command=self.on_organise,
        )
        self.organise_btn.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        # Undo button
        self.undo_btn = ctk.CTkButton(
            btn_row,
            text="Undo Last",
            width=140,
            corner_radius=10,
            fg_color="#334155",
            hover_color="#24313b",
            command=self.on_undo
        )
        self.undo_btn.grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        # Find duplicates button
        self.dupe_btn = ctk.CTkButton(
            btn_row,
            text="Find Duplicates",
            width=160,
            corner_radius=10,
            fg_color="#3b82f6",
            hover_color="#2f6fdc",
            command=self.on_find_dupes,
        )
        self.dupe_btn.grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        # Clean desktop button
        self.desktop_btn = ctk.CTkButton(
            btn_row,
            text="Clean Desktop",
            width=140,
            corner_radius=10,
            fg_color="#0ea5a4",
            hover_color="#0a8a88",
            command=self.clean_desktop
        )
        self.desktop_btn.grid(row=0, column=4, padx=6, pady=6, sticky="ew")

    def _create_preview_section(self, parent):
        """Create the preview text box section."""
        # Preview label
        preview_label = ctk.CTkLabel(
            parent,
            text="Preview",
            font=("Segoe UI Variable", 13, "bold"),
            text_color=TEXT
        )
        preview_label.pack(anchor="w", padx=12, pady=(4, 6))

        # Preview text box
        self.preview_box = ctk.CTkTextbox(
            parent,
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

    def _create_advanced_section(self, parent):
        """Create the advanced options section (initially hidden)."""
        # Advanced toggle button
        adv_frame = ctk.CTkFrame(parent, fg_color=CARD_BG)
        adv_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.advanced_button = ctk.CTkButton(
            adv_frame,
            text="Advanced Options ▾",
            width=720,
            corner_radius=10,
            fg_color="#1f2937",
            hover_color="#16202a",
            command=self.toggle_advanced
        )
        self.advanced_button.pack(fill="x", padx=6, pady=4)

        # Advanced content frame (hidden initially)
        self.advanced_frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=10)

        # Advanced inner layout
        adv_inner = ctk.CTkFrame(self.advanced_frame, fg_color=CARD_BG)
        adv_inner.pack(fill="x", padx=12, pady=12)

        # Manage Profiles button
        self.manage_profiles_btn = ctk.CTkButton(
            adv_inner,
            text="Manage Profiles",
            width=220,
            corner_radius=8,
            fg_color="#374151",
            hover_color="#2b3740",
            command=self.open_profile_manager
        )
        self.manage_profiles_btn.grid(row=0, column=0, sticky="w", padx=4, pady=6)

        # Manage Watched Folders button
        self.manage_wf_btn = ctk.CTkButton(
            adv_inner,
            text="Manage Watched Folders…",
            width=220,
            corner_radius=8,
            fg_color="#374151",
            hover_color="#2b3740",
            command=self.open_watched_folders_window
        )
        self.manage_wf_btn.grid(row=1, column=0, sticky="w", padx=4, pady=6)

        # Startup checkbox
        self.startup_checkbox = ctk.CTkCheckBox(
            adv_inner,
            text="Run FolderFresh at Windows startup",
            command=self.toggle_startup
        )
        self.startup_checkbox.grid(row=2, column=0, sticky="w", padx=4, pady=6)
        if self.config_data.get("startup", False):
            self.startup_checkbox.select()

        # Tray mode checkbox
        self.tray_mode = ctk.CTkCheckBox(
            adv_inner,
            text="Run in background (tray)",
            command=self.on_toggle_tray
        )
        self.tray_mode.grid(row=3, column=0, sticky="w", padx=4, pady=6)
        if self.config_data.get("tray_mode", False):
            self.tray_mode.select()

    def _create_help_button(self, parent):
        """Create the help button (circular icon)."""
        help_frame = ctk.CTkFrame(parent, fg_color=CARD_BG)
        help_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.help_btn = ctk.CTkButton(
            help_frame,
            text="?",
            width=36,
            height=36,
            corner_radius=18,
            fg_color="#374151",
            hover_color="#2b3740",
            command=self.show_help,
        )
        self.help_btn.pack(anchor="e", padx=8, pady=4)

    def _create_footer(self):
        """Create the footer with credits and links."""
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 0))

        # Left zone - credits
        left_zone = ctk.CTkFrame(footer, fg_color="transparent")
        left_zone.pack(side="left")

        self.credit_label = ctk.CTkLabel(
            left_zone,
            text="By Tristan Neale github.com/Trihedron1240/FolderFresh",
            font=("Segoe UI", 11),
            text_color="#8c8c8c",
            cursor="hand2"
        )
        self.credit_label.pack(side="left", padx=(8, 0))
        self.credit_label.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://trihedron1240.github.io/FolderFresh/")
        )

        # Right zone - version and bug report
        right_zone = ctk.CTkFrame(footer, fg_color="transparent")
        right_zone.pack(side="right")

        self.version_label = ctk.CTkLabel(
            right_zone,
            text=f"v{APP_VERSION}",
            font=("Segoe UI", 11),
            text_color="#8c8c8c",
        )
        self.version_label.pack(side="left", padx=(0, 6))

        self.bug_label = ctk.CTkLabel(
            right_zone,
            text="Report Bug",
            font=("Segoe UI", 11, "underline"),
            text_color="#60a5fa",
            cursor="hand2"
        )
        self.bug_label.pack(side="left")
        self.bug_label.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://github.com/Trihedron1240/FolderFresh/issues/new/choose")
        )

    def _create_status_bar(self):
        """Create the bottom status bar with progress indicator."""
        bottom = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        bottom.pack(fill="x", padx=16, pady=(0, 16))

        self.progress = ctk.CTkProgressBar(bottom, corner_radius=8)
        self.progress.set(0)
        self.progress.pack(fill="x", side="left", expand=True, padx=(12, 8), pady=10)

        self.progress_label = ctk.CTkLabel(bottom, text="0/0")
        self.progress_label.pack(side="left", padx=(8, 8), pady=10)

        self.status = ctk.CTkLabel(bottom, text="Ready")
        self.status.pack(side="left", padx=(8, 12), pady=10)

    def _setup_event_handlers(self):
        """Set up window protocols and keyboard bindings."""
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Control-o>", lambda e: self.choose_folder())
        self.bind("<Control-p>", lambda e: self.on_preview())
        self.bind("<Return>", lambda e: self.on_organise())

    def _initialize_button_states(self):
        """Set initial button states (disabled until folder selected)."""
        for button in (self.preview_btn, self.organise_btn, self.undo_btn, self.dupe_btn):
            button.configure(state="disabled")

    def _handle_first_run(self):
        """Show welcome message on first run."""
        if self.config_data.get("first_run", True):
            messagebox.showinfo(
                "Welcome",
                "Welcome to FolderFresh!\n\nUse Preview before organising. Safe Mode copies files."
            )
            self.config_data["first_run"] = False
            save_config(self.config_data)

    def _restore_last_folder(self):
        """Restore the last selected folder from config."""
        last = self.config_data.get("last_folder")
        if last and Path(last).exists():
            self.selected_folder = Path(last)
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, last)
            self.path_entry.configure(state="disabled")
            for button in (self.preview_btn, self.organise_btn, self.dupe_btn):
                button.configure(state="normal")

    def _start_watched_folders(self):
        """Start multi-folder watchers at launch."""
        for folder in self.config_data.get("watched_folders", []):
            if Path(folder).exists():
                self.watcher_manager.watch_folder(folder)






    def open_watched_folders_window(self):
        win = ctk.CTkToplevel(self)
        win.title("Watched Folders")
        win.geometry("600x420")
        win.grab_set()

        title = ctk.CTkLabel(win, text="Watched Folders", font=("Segoe UI Variable", 16, "bold"))
        title.pack(pady=12)

        list_frame = ctk.CTkScrollableFrame(
            win, width=560, height=280, corner_radius=10, fg_color="#0b1220"
        )
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Load existing mapping
        folder_map = self.config_data.setdefault("folder_profile_map", {})

        # Get available profiles
        profile_names = [p["name"] for p in self.profile_store.list_profiles()]
        if "Default" not in profile_names:
            profile_names.insert(0, "Default")

        # Store dropdown widgets for saving
        self._folder_profile_dropdowns = {}

        def refresh_list():
            for child in list_frame.winfo_children():
                child.destroy()

            folders = self.config_data.get("watched_folders", [])

            for folder in folders:
                row = ctk.CTkFrame(list_frame, fg_color="#0b1220")
                row.pack(fill="x", pady=4, padx=4)

                # Folder label
                ctk.CTkLabel(row, text=folder, anchor="w", text_color="#ffffff").pack(
                    side="left", padx=8, pady=6
                )

                # Assigned profile
                assigned_profile = folder_map.get(folder, "Default")
                if assigned_profile not in profile_names:
                    assigned_profile = "Default"

                dropdown = ctk.CTkComboBox(
                    row,
                    values=profile_names,
                    width=140,
                    command=lambda p, f=folder: assign_folder_profile(f, p)
                )
                dropdown.set(assigned_profile)
                dropdown.pack(side="right", padx=10, pady=6)

                self._folder_profile_dropdowns[folder] = dropdown

                # Status
                status = "🟢 Watching" if self.watch_mode.get() else "⚪ Disabled"
                color = "#16a34a" if self.watch_mode.get() else "#94a3b8"
                ctk.CTkLabel(row, text=status, text_color=color).pack(
                    side="right", padx=10, pady=6
                )

        def assign_folder_profile(folder, profile_name):
            folder_map[folder] = profile_name
            save_config(self.config_data)

        refresh_list()

        # Buttons row
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=8)

        def add_folder():
            folder = filedialog.askdirectory()
            if not folder:
                return
            folder = str(Path(folder))
            if folder not in self.config_data["watched_folders"]:
                self.config_data["watched_folders"].append(folder)
                save_config(self.config_data)
                folder_map.setdefault(folder, "Default")
                if self.watch_mode.get():
                    self.watcher_manager.watch_folder(folder)
                refresh_list()

        def remove_folder():
            folder = filedialog.askdirectory(title="Select folder to remove")
            if not folder:
                return
            folder = str(Path(folder))
            if folder in self.config_data["watched_folders"]:
                self.config_data["watched_folders"].remove(folder)
                folder_map.pop(folder, None)
                save_config(self.config_data)
                self.watcher_manager.unwatch_folder(folder)
                refresh_list()

        ctk.CTkButton(btn_row, text="Add Folder", fg_color="#2563eb", hover_color="#1e4fd8",
                    corner_radius=8, command=add_folder).pack(side="left", padx=(0, 6), pady=4)

        ctk.CTkButton(btn_row, text="Remove Folder", fg_color="#374151", hover_color="#2b3740",
                    corner_radius=8, command=remove_folder).pack(side="left", padx=6, pady=4)

        ctk.CTkButton(btn_row, text="Close", fg_color="#475569", hover_color="#334155",
                    corner_radius=8, command=win.destroy).pack(side="right", padx=(6, 0), pady=4)


    # Profile management
    def open_profile_manager(self):
        """Open the profile manager window."""
        try:
            from .profile_manager import ProfileManagerWindow
            win = ProfileManagerWindow(self)

            # When the window closes → reload profile
            def on_close_reload():
                self.reload_profile()   # THIS is the missing piece

            win.protocol("WM_DELETE_WINDOW", lambda: (win.destroy(), on_close_reload()))

        except Exception as e:
            messagebox.showerror("Profiles", f"Could not open Profile Manager: {e}")


    def reload_profile(self, profile_id: str | None = None):
        """
        Reload profiles from storage and apply to UI.

        Args:
            profile_id: Optional profile ID to switch to. If None, uses current active profile.
        """
        try:
            # Reload profiles from file
            self.profiles_doc = self.profile_store.load()

            # Switch to requested profile if specified
            if profile_id:
                self.profiles_doc["active_profile_id"] = profile_id
                self.profile_store.save(self.profiles_doc)

            # Get the active profile object
            self.active_profile = self.profile_store.get_active_profile(self.profiles_doc)

            # Merge active profile with global config
            global_cfg = load_config()
            self.config_data = self.profile_store.merge_profile_into_config(
                self.active_profile,
                global_cfg
            )

            # Update UI to reflect profile settings
            self.apply_profile_to_ui()

        except Exception as e:
            print("Reload error:", e)

    def apply_profile_to_ui(self):
        """
        Apply currently active_profile values into UI and into self.config_data
        """
        self.freeze_profile_events(True)
        try:
            # Make sure the main app config_data contains the merged profile
            try:
                # prefer using already-merged config if present
                if hasattr(self, "config_data") and isinstance(self.config_data, dict) and self.config_data:
                    merged = self.config_data
                else:
                    # merge active_profile into global config as a fallback
                    merged = self.profile_store.merge_profile_into_config(
                        self.active_profile,
                        load_config()
                    )
                # Ensure the app's active config is the merged profile
                self.config_data = merged
            except Exception as e:
                print("ERROR merging/applying profile into config_data:", e)

            settings = self.active_profile.get("settings", {}) if self.active_profile else {}

            # Update checkboxes (existing behavior)
            self._set_checkbox_state(self.include_sub, settings.get("include_sub", True))
            self._set_checkbox_state(self.skip_hidden, settings.get("skip_hidden", True))
            self._set_checkbox_state(self.safe_mode, settings.get("safe_mode", True))
            self._set_checkbox_state(self.smart_mode, settings.get("smart_mode", False))

            # >>> Ensure ignore lists are present on the active config_data
            self.config_data["ignore_patterns"] = settings.get("ignore_patterns", self.config_data.get("ignore_patterns", []))
            self.config_data["dont_move_list"] = settings.get("dont_move_list", self.config_data.get("dont_move_list", []))

        finally:
            self.freeze_profile_events(False)

    def _set_checkbox_state(self, checkbox, enabled: bool):
        """Helper to set checkbox state based on boolean value."""
        if enabled:
            checkbox.select()
        else:
            checkbox.deselect()

    def _set_entry_value(self, entry, value: str):
        """Helper to set entry widget value."""
        entry.delete(0, "end")
        entry.insert(0, value)

    def save_active_profile(self):
        """
        Save the currently loaded profiles document.

        Note: This updates the stored profiles data so UI and backend stay synchronized.
        """
        try:
            self.profile_store.save(self.profiles_doc)
            self.save_active_profile()

        except Exception as e:
            print("Profile save error:", e)

    # UI state helpers
    def set_status(self, msg: str):
        """Update the status label text."""
        self.status.configure(text=msg)
        self.update_idletasks()

    def set_preview(self, text: str):
        """Update the preview text box with new content."""
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("end", text)
        self.preview_box.configure(state="disabled")

    def toggle_advanced(self):
        """Toggle the visibility of the advanced options panel."""
        if self.advanced_visible:
            self.advanced_frame.pack_forget()
            self.advanced_button.configure(text="Advanced Options ▾")
            self.advanced_visible = False
        else:
            self.advanced_frame.pack(fill="x", padx=12, pady=(0, 12))
            self.advanced_button.configure(text="Advanced Options ▴")
            self.advanced_visible = True

    # Settings management
    def toggle_startup(self):
        """Enable or disable running FolderFresh at Windows startup."""
        from folderfresh.utils import enable_startup, disable_startup

        exe_path = sys.executable
        app_name = "FolderFresh"

        is_enabled = bool(self.startup_checkbox.get())
        if is_enabled:
            enable_startup(app_name, exe_path)
        else:
            disable_startup(app_name)

        # Save preference
        self.config_data["startup"] = is_enabled
        save_config(self.config_data)

    def open_folder(self):
        """Open the currently selected folder in File Explorer."""
        path = self.config_data.get("last_folder")
        try:
            os.startfile(path)
        except Exception:
            messagebox.showerror(
                "Open Folder",
                "No valid folder is selected or the folder no longer exists."
            )

    def choose_folder(self):
        """Prompt user to select a folder to organize."""
        path = filedialog.askdirectory()
        if not path:
            return

        self.selected_folder = Path(path)
        self.config_data["last_folder"] = str(self.selected_folder)
        save_config(self.config_data)

        # Update UI
        self.path_entry.configure(state="normal")
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, str(self.selected_folder))
        self.path_entry.configure(state="disabled")

        self.set_preview("Folder selected. Click Preview to see what will happen.")
        self.set_status("Folder ready")

        # Enable action buttons
        for button in (self.preview_btn, self.organise_btn, self.dupe_btn):
            button.configure(state="normal")

    def save_profile_setting(self, key, value):
        """Save a single setting to the active profile."""
        if getattr(self, "closing", False):
            return  # Ignore saves during shutdown

        self.active_profile.setdefault("settings", {})[key] = value
        self.profiles_doc["meta"]["generated_at"] = datetime.now().isoformat(timespec="seconds")
        self.profile_store.save(self.profiles_doc)
        self.config_data[key] = value

    def freeze_profile_events(self, freeze=True):
        """Enable or disable profile event handling to prevent recursion."""
        self._profile_freeze = freeze

    def remember_options(self):
        """Save current UI option states to profile and global config."""
        # Prevent recursion during profile reloads
        if getattr(self, "_profile_freeze", False):
            return

        # Save profile-specific settings
        self.save_profile_setting("include_sub", bool(self.include_sub.get()))
        self.save_profile_setting("skip_hidden", bool(self.skip_hidden.get()))
        self.save_profile_setting("safe_mode", bool(self.safe_mode.get()))
        self.save_profile_setting("smart_mode", bool(self.smart_mode.get()))

        # Save global settings
        global_cfg = load_config()
        global_cfg["watch_mode"] = bool(self.watch_mode.get())
        global_cfg["tray_mode"] = bool(self.tray_mode.get())
        save_config(global_cfg)

    # Action handlers
    def on_preview(self):
        """Generate and display a preview of planned file moves."""
        self.disable_buttons()
        self.set_status("Scanning…")
        self.progress.set(0)

        def worker():
            moves = actions.do_preview(self)
            self.preview_moves = moves
            summary = self.make_summary(moves)

            # Update UI from main thread
            self.after(0, lambda: self.set_preview(summary))
            self.after(0, lambda: self.progress_label.configure(text=f"{len(moves)}/{len(moves)}"))
            self.after(0, lambda: self.progress.set(1))
            self.after(0, lambda: self.set_status(f"Preview ready: {len(moves)} file(s)."))
            self.after(0, self.enable_buttons)

        threading.Thread(target=worker, daemon=True).start()

    def on_organise(self):
        """Execute the file organization with user confirmation."""
        # Validate folder selection
        if not self.selected_folder or not self.selected_folder.exists():
            messagebox.showerror("Choose Folder", "Please choose a valid folder first.")
            return

        self.remember_options()

        # Generate preview of moves
        moves = actions.do_preview(self)
        self.preview_moves = moves

        if not moves:
            messagebox.showinfo("Organise", "There's nothing to move. Your folder is tidy.")
            return

        # Check for large copy operations in safe mode
        if self.safe_mode.get() and self.preview_moves:
            if not self._check_safe_mode_size():
                return

        # Confirm with user
        proceed = messagebox.askyesno(
            "Confirm",
            f"I found {len(self.preview_moves)} file(s) to organise. Continue?"
        )
        if not proceed:
            return

        # Execute organization
        self.disable_buttons()
        self.progress.set(0)
        self.set_status("Organising… please wait…")

        def worker():
            moves_done = actions.do_organise(self, moves)
            total = len(moves)

            # Update UI from main thread
            self.after(0, lambda: self.set_preview(self.finish_summary(moves_done)))
            self.after(0, lambda: self.set_status("All done"))
            self.after(0, lambda: self.progress_label.configure(text=f"{total}/{total}"))
            self.after(0, self.enable_buttons)

        threading.Thread(target=worker, daemon=True).start()

    def _check_safe_mode_size(self) -> bool:
        """
        Check if safe mode copy operation is too large and confirm with user.

        Returns:
            True if should proceed, False if user cancelled.
        """
        try:
            total_bytes = sum(
                Path(m["src"]).stat().st_size
                for m in self.preview_moves
                if Path(m["src"]).exists()
            )
            mb = total_bytes / (1024 * 1024)

            if mb > 500:
                proceed = messagebox.askyesno(
                    "Large Copy Warning",
                    f"Safe Mode will create about {mb:.1f} MB of duplicate data. Continue?"
                )
                return proceed

        except Exception:
            pass

        return True

    def on_undo(self):
        """Undo the last file organization operation."""
        result = actions.do_undo(self)

        if result is None:
            messagebox.showinfo("Undo", "You don't have anything to undo yet.")
            return

        if result == "copy_mode":
            messagebox.showinfo("Undo", "Last action was Safe Mode COPY — nothing to undo.")
            return

        # Clear last sort mode
        self.config_data["last_sort_mode"] = None
        save_config(self.config_data)

        self.set_preview(f"Undo complete. Restored {result} file(s).")
        self.set_status(f"Undo complete ({result} restored).")

    def on_find_dupes(self):
        """Scan for and display duplicate files."""
        self.disable_buttons()
        self.set_status("Scanning for duplicates…")
        self.progress.set(0)

        def worker():
            groups = actions.do_find_duplicates(self)
            lines = []
            total = sum(len(g) for g in groups)

            # Format duplicate groups
            for g in groups:
                lines.append("— Potential duplicates —")
                for p in g:
                    try:
                        lines.append(f"  {p.name} ({p.stat().st_size} B) → {p.parent}")
                    except Exception:
                        lines.append(f"  {p.name}")

            output = "No obvious duplicates found." if not lines else "\n".join(lines)

            # Update UI from main thread
            self.after(0, lambda: self.set_preview(output))
            self.after(0, lambda: self.progress_label.configure(
                text=f"{total}/{total}" if total else "0/0"
            ))
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

    def on_toggle_watch(self):
        """
        Toggle Auto-Tidy watch mode with proper state management.

        Prevents race conditions and ensures config is always synchronized.
        """
        enabled = bool(self.watch_mode.get())

        # Only process if state actually changed
        current_state = self.config_data.get("watch_mode", False)
        if enabled == current_state:
            # No change needed
            return

        # Update config and save
        self.config_data["watch_mode"] = enabled
        save_config(self.config_data)

        if enabled:
            # Start watching all folders
            folders_to_watch = [f for f in self.config_data.get("watched_folders", [])
                               if Path(f).exists()]

            if folders_to_watch:
                for folder in folders_to_watch:
                    try:
                        self.watcher_manager.watch_folder(folder)
                    except Exception as e:
                        print(f"[WATCHER ERROR] Failed to watch {folder}: {e}")

                self.set_status(f"✓ Auto-tidy enabled ({len(folders_to_watch)} folder(s))")
            else:
                self.set_status("⚠️  Auto-tidy: No watched folders found")
        else:
            # Stop ALL watchers
            try:
                self.watcher_manager.stop_all()
            except Exception as e:
                print(f"[WATCHER ERROR] Failed to stop watchers: {e}")
            self.set_status("⏸ Auto-tidy paused")


    def on_toggle_tray(self):

        tray.toggle_tray(self)

    def hide_to_tray(self):
        tray.hide_to_tray(self)
        # ------------------------------------------------------------
        # Auto-reinitialize Auto-Tidy when entering tray mode
        # ------------------------------------------------------------
        if self.watch_mode.get():
            self.watch_mode.deselect()
            self.on_toggle_watch()
            self.watch_mode.select()
            self.on_toggle_watch()

    def show_window(self):
        tray.show_window(self)

    # summaries
    def make_summary(self, moves: list[dict]) -> str:
        """
        Generate a preview summary showing both rule-handled and sorting-fallback files.

        Distinguishes between:
        - Rule-handled files (mode="rule") - handled by custom rules
        - Sorting-fallback files (mode="sort") - handled by standard sorting
        """
        if not moves:
            return "Nothing to organise."

        # Separate rule-handled vs sorting moves
        rule_moves = [m for m in moves if m.get("mode") == "rule"]
        sort_moves = [m for m in moves if m.get("mode") == "sort"]

        lines: list[str] = []

        # =====================================================================
        # RULE-HANDLED FILES (rules matched)
        # =====================================================================
        if rule_moves:
            lines.append("🎯 FILES HANDLED BY RULES:")
            rule_counts: dict[str, int] = {}

            for m in rule_moves:
                rule_name = m.get("rule_name", "Unknown Rule")
                filename = Path(m["src"]).name

                # Group by rule
                rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
                lines.append(f"  ✓ {filename}  [Rule: {rule_name}]")

            lines.append("\n  Rule Summary:")
            for rule_name in sorted(rule_counts):
                count = rule_counts[rule_name]
                lines.append(f"    - {rule_name}: {count} file(s)")

        # =====================================================================
        # SORTING-HANDLED FILES (fallback to standard sorting)
        # =====================================================================
        if sort_moves:
            if rule_moves:
                lines.append("\n" + "—" * 50)
            lines.append("📁 FILES SORTED BY CATEGORY:")
            sort_counts: dict[str, int] = {}

            for m in sort_moves:
                dst_folder = Path(m["dst"]).parent.name
                filename = Path(m["src"]).name

                # Group by category
                sort_counts[dst_folder] = sort_counts.get(dst_folder, 0) + 1
                lines.append(f"  • {filename}  →  {dst_folder}/")

            lines.append("\n  Sort Summary:")
            for k in sorted(sort_counts):
                v = sort_counts[k]
                lines.append(f"    - {k}: {v} file(s)")

        # =====================================================================
        # OVERALL SUMMARY
        # =====================================================================
        total_rule = len(rule_moves)
        total_sort = len(sort_moves)
        total = total_rule + total_sort

        lines.append("\n" + "=" * 50)
        if total_rule > 0 and total_sort > 0:
            lines.append(f"Total: {total} file(s) [{total_rule} by rules, {total_sort} by sorting]")
        elif total_rule > 0:
            lines.append(f"Total: {total_rule} file(s) [All handled by rules]")
        else:
            lines.append(f"Total: {total_sort} file(s) [All sorted by category]")

        return "\n".join(lines)

    def finish_summary(self, moves_done: list[dict]) -> str:
        """Show completion summary with rule vs sorting breakdown."""
        errors = [m for m in moves_done if m.get("error")]
        ok = [m for m in moves_done if not m.get("error")]

        msg = ["✅ All done!\n"]
        if ok:
            msg.append(self.make_summary(ok))
        if errors:
            msg.append("\n⚠️  Some files could not be processed:")
            for m in errors[:10]:
                msg.append(f"  - {Path(m['src']).name}: {m['error']}")
            if len(errors) > 10:
                msg.append(f"  …and {len(errors) - 10} more.")

        if self.safe_mode.get():
            msg.append("\nℹ️  Safe Mode was ON, so files were COPIED.")
        else:
            msg.append("\n💡 Tip: You can use Undo to put things back.")

        return "\n".join(msg)

    def disable_buttons(self):
        for b in (self.preview_btn, self.organise_btn, self.undo_btn, self.dupe_btn, self.desktop_btn):
            b.configure(state="disabled")

    def enable_buttons(self):
        for b in (self.preview_btn, self.organise_btn, self.undo_btn, self.dupe_btn, self.desktop_btn):
            b.configure(state="normal")
    def view_log_file(self):
        if not self.selected_folder:
            messagebox.showerror("Log File", "Select a folder first.")
            return

        if not actions.open_log_file(Path(self.selected_folder)):
            messagebox.showinfo("Log File", "No FolderFresh log file found in this folder.")
    def show_help(self):
        help_win = ctk.CTkToplevel(self)
        help_win.title("Help")
        help_win.geometry("420x480")
        help_win.grab_set()

        text = (
            "FolderFresh helps you tidy folders quickly.\n\n"
            "Features:\n"
            "• Preview mode\n"
            "• Safe Mode\n"
            "• Smart Sorting\n"
            "• Auto-tidy\n"
            "• Undo\n"
            "• Duplicate finder\n"
            "• Age & ignore filters\n\n"
            "This tool never deletes files.\n"
            "All actions are reversible.\n"
        )

        txt = ctk.CTkLabel(help_win, text=text, justify="left", wraplength=380)
        txt.pack(padx=16, pady=16)

        view_log_btn = ctk.CTkButton(help_win, text="View Log File", command=lambda: actions.open_log_file(self.selected_folder))
        view_log_btn.pack(pady=6)

        report_btn = ctk.CTkButton(help_win, text="Report Bug", command=lambda: webbrowser.open("https://github.com/Trihedron1240/FolderFresh/issues/new/choose"))
        report_btn.pack(pady=6)


    def on_close(self):
        
        self.closing = True

        
        try:
            self.watcher_manager.stop_all()
        except Exception:
            pass

        
        try:
            if getattr(self, "tray_mode", None) and self.tray_mode.get():
                self.hide_to_tray()
                return
        except Exception:
            pass

        self.destroy()


