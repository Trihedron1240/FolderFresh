from __future__ import annotations
import json
from datetime import datetime
from typing import Dict, Any
import customtkinter as ctk
from tkinter import simpledialog, messagebox
from .category_manager import CategoryManagerWindow
from .profile_store import ProfileStore
from .rule_manager import RuleManager

def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


class ProfileManagerWindow(ctk.CTkToplevel):
    """
    Profile manager window with sidebar list and editor pane.

    Features:
    - Sidebar: List of profiles with quick actions
    - Right pane: Detailed profile editor
    - Simple load/save cycle with no recursion
    """

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.store: ProfileStore = app.profile_store

        # Load profile data
        self.doc = self.store.load()
        self.selected_id = self.doc.get("active_profile_id")
        self.profiles = {p["id"]: p for p in self.doc.get("profiles", [])}

        # Configure window
        self.title("Manage Profiles")
        self.geometry("900x580")
        self.grab_set()

        # Create main container
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        # Create UI sections
        self._create_sidebar(container)
        self._create_editor_pane(container)

        # Initialize display
        self.refresh_list()
        if self.selected_id:
            self.load_editor(self.selected_id)

    def _create_sidebar(self, parent):
        """Create the sidebar with profile list and action buttons."""
        self.sidebar = ctk.CTkFrame(parent, width=260)
        self.sidebar.pack(side="left", fill="y", padx=(0, 8))
        self.sidebar.pack_propagate(False)

        # Action buttons row
        btn_row = ctk.CTkFrame(self.sidebar)
        btn_row.pack(fill="x", pady=(8, 6), padx=8)

        ctk.CTkButton(
            btn_row,
            text="New",
            width=60,
            corner_radius=8,
            command=self.create_new_profile
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_row,
            text="Import",
            width=70,
            corner_radius=8,
            command=self.import_profiles
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_row,
            text="Export",
            width=70,
            corner_radius=8,
            command=self.export_profile
        ).pack(side="left", padx=(4, 0))

        # Scrollable profile list
        self.list_frame = ctk.CTkScrollableFrame(self.sidebar)
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _create_editor_pane(self, parent):
        """Create the right editor pane."""
        self.right = ctk.CTkScrollableFrame(parent)
        self.right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.build_editor()

    # Sidebar management
    def refresh_list(self):
        """Reload and display the profile list from storage."""
        # Clear existing widgets
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Reload from disk
        self.doc = self.store.load()
        self.profiles = {p["id"]: p for p in self.doc.get("profiles", [])}
        active_id = self.doc.get("active_profile_id")

        # Create profile list items
        for profile in self.profiles.values():
            self._create_profile_list_item(profile, active_id)

    def _create_profile_list_item(self, profile, active_id):
        """Create a single profile list item with label and menu button."""
        row = ctk.CTkFrame(self.list_frame)
        row.pack(fill="x", pady=4, padx=4)

        # Profile name label (clickable)
        label = ctk.CTkLabel(row, text=profile.get("name", "(unnamed)"), anchor="w")
        label.pack(side="left", padx=6, pady=6)
        label.bind("<Button-1>", lambda e, pid=profile["id"]: self.load_editor(pid))

        # Active indicator
        if profile["id"] == active_id:
            ctk.CTkLabel(
                row,
                text="(active)",
                text_color="#60a5fa"
            ).pack(side="left", padx=4, pady=6)

        # Menu button
        menu_btn = ctk.CTkButton(
            row,
            text="⋯",
            width=32,
            corner_radius=6,
            command=lambda pid=profile["id"]: self.popup_menu(pid)
        )
        menu_btn.pack(side="right", padx=4, pady=4)

    def popup_menu(self, pid: str):
        """Display a context menu for profile actions."""
        menu = ctk.CTkToplevel(self)
        menu.overrideredirect(True)
        menu.attributes("-topmost", True)
        menu.configure(fg_color="#0f1720")

        # Position at mouse cursor
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        menu.geometry(f"+{x}+{y}")

        # Setup menu close behavior
        self._setup_menu_close_behavior(menu)

        # Add menu items
        self._add_menu_items(menu, pid)

        # Focus for keyboard interaction
        menu.focus_set()

    def _setup_menu_close_behavior(self, menu):
        """Setup close behavior for popup menu."""
        def close_menu(event=None):
            try:
                self.unbind("<Button-1>", click_outside_id)
            except:
                pass
            try:
                menu.destroy()
            except:
                pass

        # Close on Escape key
        menu.bind("<Escape>", close_menu)

        # Detect clicks outside menu
        def check_click(event):
            if not menu.winfo_exists():
                return

            # Check if click is inside the popup window
            widget = menu.winfo_containing(event.x_root, event.y_root)

            # Close if click is outside menu
            if widget is None or not str(widget).startswith(str(menu)):
                close_menu()

        # Bind click detection to parent window
        click_outside_id = self.bind("<Button-1>", check_click, add="+")

        # Cleanup on menu destruction
        def cleanup(event):
            try:
                self.unbind("<Button-1>", click_outside_id)
            except:
                pass

        menu.bind("<Destroy>", cleanup)

        # Store close function for menu items
        menu.close_menu = close_menu

        return click_outside_id

    def _add_menu_items(self, menu, pid):
        """Add action items to the popup menu."""
        def choose(action):
            menu.close_menu()
            action()

        def add_menu_button(label, cmd, color=None):
            """Helper to create menu button."""
            btn = ctk.CTkButton(
                menu,
                text=label,
                width=160,
                height=32,
                corner_radius=6,
                fg_color=color or "#1e293b",
                hover_color="#334155",
                command=lambda: choose(cmd)
            )
            btn.pack(fill="x", padx=4, pady=2)

        # Add menu options
        add_menu_button("Rename", lambda: self._rename_action(pid))
        add_menu_button("Duplicate", lambda: self.duplicate_profile(pid))

        # Only allow delete for non-builtin profiles
        if not self.profiles.get(pid, {}).get("is_builtin", False):
            add_menu_button("Delete", lambda: self.delete_profile(pid), color="#8b0000")

        add_menu_button("Set Active", lambda: self.set_active_profile(pid), color="#2563eb")

    def _rename_action(self, pid):
        """Prompt user to rename a profile."""
        new_name = simpledialog.askstring(
            "Rename",
            "New name:",
            initialvalue=self.profiles[pid]["name"]
        )
        if new_name:
            self.rename_profile(pid, new_name.strip())

    # Profile CRUD operations
    def create_new_profile(self):
        """Create a new profile based on the current active profile."""
        base_profile = self.profiles.get(self.doc.get("active_profile_id"), {})
        new_id = f"profile_{int(datetime.now().timestamp())}"

        # Deep copy base profile
        new_profile = json.loads(json.dumps(base_profile))

        # Set new profile metadata
        now = _now_iso()
        new_profile.update({
            "id": new_id,
            "name": "New Profile",
            "description": "",
            "created_at": now,
            "updated_at": now,
            "is_builtin": False
        })

        # Add to document and set as active
        self.doc["profiles"].append(new_profile)
        self.doc["active_profile_id"] = new_id

        # Save and refresh UI
        self.store.save(self.doc)
        self.refresh_list()
        self.load_editor(new_id)

    def duplicate_profile(self, pid):
        """Create a duplicate of an existing profile."""
        source = self.profiles.get(pid)
        if not source:
            return

        new_id = f"profile_{int(datetime.now().timestamp())}"

        # Deep copy source profile
        duplicate = json.loads(json.dumps(source))

        # Update metadata for duplicate
        now = _now_iso()
        duplicate.update({
            "id": new_id,
            "name": f"{source['name']} (copy)",
            "created_at": now,
            "updated_at": now,
            "is_builtin": False
        })

        # Add to document
        self.doc["profiles"].append(duplicate)
        self.store.save(self.doc)
        self.refresh_list()

    def delete_profile(self, pid):
        """Delete a profile (builtin profiles cannot be deleted)."""
        if self.profiles.get(pid, {}).get("is_builtin"):
            messagebox.showwarning("Protected", "Cannot delete built-in profile.")
            return

        # Remove profile from list
        self.doc["profiles"] = [p for p in self.doc["profiles"] if p["id"] != pid]

        # Update active profile if deleted profile was active
        if self.doc.get("active_profile_id") == pid:
            if self.doc["profiles"]:
                self.doc["active_profile_id"] = self.doc["profiles"][0]["id"]
            else:
                self.doc["active_profile_id"] = None

        # Save and refresh UI
        self.store.save(self.doc)
        self.refresh_list()

    def rename_profile(self, pid, new_name):
        """Rename a profile."""
        profile = self.profiles.get(pid)
        if not profile:
            return

        profile["name"] = new_name
        profile["updated_at"] = _now_iso()

        self.store.save(self.doc)
        self.refresh_list()

    def set_active_profile(self, pid):
        """Set a profile as the active profile."""
        self.doc["active_profile_id"] = pid
        self.store.save(self.doc)
        self.refresh_list()

        messagebox.showinfo("Active profile", "Active profile set.")

        # Reload profile in main app
        try:
            self.app.reload_profile(pid)
        except:
            pass

    # Import/Export operations
    def import_profiles(self):
        """Import profiles from a JSON file."""
        from tkinter import filedialog

        # Prompt for file
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path:
            return

        # Load and validate file
        data = json.load(open(file_path, "r", encoding="utf-8"))
        if "profiles" not in data:
            messagebox.showerror("Import", "Invalid file.")
            return

        # Import profiles with new IDs
        for profile in data["profiles"]:
            profile["id"] = f"profile_{int(datetime.now().timestamp())}"
            self.doc["profiles"].append(profile)

        # Save and refresh UI
        self.store.save(self.doc)
        self.refresh_list()

    def export_profile(self):
        """Export the currently selected profile to a JSON file."""
        from tkinter import filedialog

        if not self.selected_id:
            return

        profile = self.profiles.get(self.selected_id)

        # Prompt for save location
        file_path = filedialog.asksaveasfilename(defaultextension=".json")
        if not file_path:
            return

        # Save profile to file
        json.dump(
            {"profiles": [profile]},
            open(file_path, "w", encoding="utf-8"),
            indent=2
        )
        messagebox.showinfo("Export", "Exported.")

    # Editor (Right Pane)
    def build_editor(self):
        """Build the profile editor widgets."""
        # Profile name
        self.name_entry = ctk.CTkEntry(
            self.right,
            placeholder_text="Profile name",
            height=36,
            corner_radius=8
        )
        self.name_entry.pack(fill="x", padx=12, pady=(12, 8))

        # Description
        self.desc = ctk.CTkTextbox(self.right, height=80, corner_radius=8)
        self.add_placeholder(self.desc, "Describe what this profile does…")
        self.desc.pack(fill="x", padx=12, pady=(0, 12))

        # Basic settings section
        ctk.CTkLabel(
            self.right,
            text="Basic Settings",
            font=("Segoe UI Variable", 13, "bold")
        ).pack(anchor="w", padx=12, pady=(8, 6))

        # Basic settings checkboxes
        self.include_sub = ctk.CTkCheckBox(self.right, text="Include subfolders")
        self.include_sub.pack(anchor="w", padx=16, pady=4)

        self.skip_hidden = ctk.CTkCheckBox(self.right, text="Ignore hidden/system files")
        self.skip_hidden.pack(anchor="w", padx=16, pady=4)

        self.safe_mode = ctk.CTkCheckBox(self.right, text="Safe Mode (copy)")
        self.safe_mode.pack(anchor="w", padx=16, pady=4)

        self.dry_run = ctk.CTkCheckBox(
            self.right,
            text="Dry Run Mode (no real file changes)"
        )
        self.dry_run.pack(anchor="w", padx=16, pady=4)

        self.smart_mode = ctk.CTkCheckBox(self.right, text="Smart Sorting")
        self.smart_mode.pack(anchor="w", padx=16, pady=4)

        # Filters section
        ctk.CTkLabel(
            self.right,
            text="Filters",
            font=("Segoe UI Variable", 13, "bold")
        ).pack(anchor="w", padx=12, pady=(16, 6))

        # Ignore file types
        ignore_row = ctk.CTkFrame(self.right, fg_color="transparent")
        ignore_row.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(ignore_row, text="Ignore types:").pack(side="left", padx=(4, 8))
        self.ignore_exts = ctk.CTkEntry(
            ignore_row,
            width=300,
            placeholder_text="e.g. .exe;.tmp;.log",
            corner_radius=8
        )
        self.ignore_exts.pack(side="left", fill="x", expand=True)

        # Age filter
        age_row = ctk.CTkFrame(self.right, fg_color="transparent")
        age_row.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(
            age_row,
            text="Age filter (only moves files older than):"
        ).pack(side="left", padx=(4, 8))
        self.age_days = ctk.CTkEntry(
            age_row,
            width=80,
            placeholder_text="0 = off",
            corner_radius=8
        )
        self.age_days.pack(side="left", padx=(0, 4))
        ctk.CTkLabel(age_row, text="days").pack(side="left")

        # Advanced section
        ctk.CTkLabel(
            self.right,
            text="Advanced Patterns",
            font=("Segoe UI Variable", 13, "bold")
        ).pack(anchor="w", padx=12, pady=(16, 6))

        # Ignore patterns
        ctk.CTkLabel(
            self.right,
            text="Ignore Patterns (one per line):"
        ).pack(anchor="w", padx=12, pady=(4, 2))
        self.ignore_patterns = ctk.CTkTextbox(self.right, height=80, corner_radius=8)
        self.add_placeholder(self.ignore_patterns, "Enter filename patterns to ignore…\nExample: .tmp\nExample: backup_")
        self.ignore_patterns.pack(fill="x", padx=12, pady=(0, 8))

        # Don't move list
        ctk.CTkLabel(
            self.right,
            text="Don't Move List (one per line):"
        ).pack(anchor="w", padx=12, pady=(4, 2))
        self.dont_move = ctk.CTkTextbox(self.right, height=80, corner_radius=8)
        self.add_placeholder(self.dont_move, "Enter files or paths to exclude from moving…\nExample: important.txt\nExample: C:\\Temp\\keep_here")
        self.dont_move.pack(fill="x", padx=12, pady=(0, 12))

        # Category manager button
        ctk.CTkButton(
            self.right,
            text="Edit Categories…",
            width=180,
            corner_radius=8,
            fg_color="#374151",
            hover_color="#2b3740",
            command=self.open_category_editor_for_profile,
        ).pack(pady=(8, 6), padx=12, anchor="w")

        # Rule manager button
        ctk.CTkButton(
            self.right,
            text="Open Rule Manager",
            width=180,
            corner_radius=8,
            fg_color="#374151",
            hover_color="#2b3740",
            command=self.open_rule_manager,
            ).pack(pady=(0, 16), padx=12, anchor="w")

        # Save button
        ctk.CTkButton(
            self.right,
            text="Save Changes",
            height=36,
            corner_radius=8,
            fg_color="#2563eb",
            hover_color="#1e4fd8",
            command=self.save_editor
        ).pack(pady=16, padx=12, fill="x")

    def open_rule_manager(self):
        """Open the Rule Manager for the selected profile."""
        if not self.selected_id:
            messagebox.showerror("Rule Manager", "Select a profile first.")
            return
        RuleManager(self, profile_id=self.selected_id)

    def add_placeholder(self, textbox, placeholder_text):
        """Add placeholder text functionality to a textbox."""
        textbox.placeholder = placeholder_text

        def on_focus_in(event):
            if textbox.get("1.0", "end").strip() == placeholder_text:
                textbox.delete("1.0", "end")
                textbox.configure(text_color="#ffffff")

        def on_focus_out(event):
            if not textbox.get("1.0", "end").strip():
                textbox.insert("1.0", placeholder_text)
                textbox.configure(text_color="#7a8696")

        textbox.bind("<FocusIn>", on_focus_in)
        textbox.bind("<FocusOut>", on_focus_out)

        # Initialize with placeholder
        textbox.insert("1.0", placeholder_text)
        textbox.configure(text_color="#7a8696")

    def open_category_editor_for_profile(self):
        """Open the category editor for the selected profile."""
        profile_id = self.selected_id
        if not profile_id:
            messagebox.showerror("Categories", "Select a profile first.")
            return

        # Load fresh profile data
        self.doc = self.store.load()
        self.profiles = {p["id"]: p for p in self.doc.get("profiles", [])}
        profile = self.profiles.get(profile_id)

        if not profile:
            messagebox.showerror("Categories", "Profile not found.")
            return

        # Open category manager window
        CategoryManagerWindow(self.app, self.selected_id)



    def load_editor(self, pid):
        """Load a profile into the editor UI."""
        self.selected_id = pid

        # Reload profile data
        self.doc = self.store.load()
        self.profiles = {p["id"]: p for p in self.doc.get("profiles", [])}
        profile = self.profiles.get(pid)

        if not profile:
            return

        settings = profile.get("settings", {})

        # Load profile name
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, profile.get("name", ""))

        # Load description (with placeholder handling)
        desc_text = profile.get("description", "")
        self.desc.delete("1.0", "end")

        if desc_text.strip():
            self.desc.insert("1.0", desc_text)
            self.desc.configure(text_color="#ffffff")
        else:
            self.desc.insert("1.0", self.desc.placeholder)
            self.desc.configure(text_color="#7a8696")

        # Load checkboxes
        self._set_checkbox(self.include_sub, settings.get("include_sub", True))
        self._set_checkbox(self.skip_hidden, settings.get("skip_hidden", True))
        self._set_checkbox(self.safe_mode, settings.get("safe_mode", True))
        self._set_checkbox(self.dry_run, settings.get("dry_run", True))
        self._set_checkbox(self.smart_mode, settings.get("smart_mode", False))

        # Load ignore extensions
        self.ignore_exts.delete(0, "end")
        self.ignore_exts.insert(0, settings.get("ignore_exts", ""))

        # Load age filter
        self.age_days.delete(0, "end")
        self.age_days.insert(0, str(settings.get("age_filter_days", 0)))

        # Load ignore patterns (with placeholder handling)
        patterns = profile.get("ignore_patterns", [])
        self.ignore_patterns.delete("1.0", "end")

        if patterns:
            for pattern in patterns:
                self.ignore_patterns.insert("end", pattern.get("pattern", "") + "\n")
            self.ignore_patterns.configure(text_color="#ffffff")
        else:
            self.ignore_patterns.insert("1.0", self.ignore_patterns.placeholder)
            self.ignore_patterns.configure(text_color="#7a8696")

        # Load don't move list (with placeholder handling)
        dont_move = profile.get("dont_move_list", [])
        self.dont_move.delete("1.0", "end")

        if dont_move:
            for path in dont_move:
                self.dont_move.insert("end", path + "\n")
            self.dont_move.configure(text_color="#ffffff")
        else:
            self.dont_move.insert("1.0", self.dont_move.placeholder)
            self.dont_move.configure(text_color="#7a8696")

    def _set_checkbox(self, checkbox, value):
        """Helper to set checkbox state."""
        if value:
            checkbox.select()
        else:
            checkbox.deselect()

    def save_editor(self):
        """Save editor changes to profile storage."""
        profile_id = self.selected_id

        # Reload and find profile
        self.doc = self.store.load()
        profiles = self.doc.get("profiles", [])
        profile = next((p for p in profiles if p["id"] == profile_id), None)

        if not profile:
            return

        # Save basic information
        profile["name"] = self.name_entry.get().strip()

        # Save description (skip if it's the placeholder)
        desc_text = self.desc.get("1.0", "end").strip()
        if desc_text != self.desc.placeholder:
            profile["description"] = desc_text
        else:
            profile["description"] = ""

        profile["updated_at"] = _now_iso()

        # Save settings
        settings = profile.setdefault("settings", {})
        settings["include_sub"] = bool(self.include_sub.get())
        settings["skip_hidden"] = bool(self.skip_hidden.get())
        settings["safe_mode"] = bool(self.safe_mode.get())
        settings["dry_run"] = bool(self.dry_run.get())
        settings["smart_mode"] = bool(self.smart_mode.get())
        settings["ignore_exts"] = self.ignore_exts.get().strip()

        # Save age filter (with validation)
        try:
            settings["age_filter_days"] = int(self.age_days.get() or 0)
        except:
            settings["age_filter_days"] = 0

        # Save ignore patterns (skip placeholder text)
        pattern_text = self.ignore_patterns.get("1.0", "end").strip()
        pattern_lines = [
            line.strip()
            for line in pattern_text.splitlines()
            if line.strip() and not line.strip().startswith("Enter filename") and not line.strip().startswith("Example:")
        ]
        profile["ignore_patterns"] = [{"pattern": p} for p in pattern_lines]

        # Save don't move list (skip placeholder text)
        dont_move_text = self.dont_move.get("1.0", "end").strip()
        dont_move_lines = [
            line.strip()
            for line in dont_move_text.splitlines()
            if line.strip() and not line.strip().startswith("Enter files") and not line.strip().startswith("Example:")
        ]
        profile["dont_move_list"] = dont_move_lines

        # Persist changes
        self.store.save(self.doc)
        self.refresh_list()

        # Update live config if this is the active profile
        if self.doc.get("active_profile_id") == profile_id:
            try:
                self.app.reload_profile(profile_id)
            except:
                pass

        messagebox.showinfo("Saved", "Profile saved.")
