from __future__ import annotations
import json
from datetime import datetime
from typing import Dict, Any
import customtkinter as ctk
from tkinter import simpledialog, messagebox
from .category_manager import CategoryManagerWindow
from .profile_store import ProfileStore
from .config import load_config

def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


class ProfileManagerWindow(ctk.CTkToplevel):
    """
    Clean, stable profile manager:
    - Sidebar list
    - Right pane editor
    - Simple load/save cycle (no recursion)
    """

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.store: ProfileStore = app.profile_store

        # Load once
        self.doc = self.store.load()
        self.selected_id = self.doc.get("active_profile_id")
        self.profiles = {p["id"]: p for p in self.doc.get("profiles", [])}
        self.title("Manage Profiles")
        self.geometry("900x580")
        self.grab_set()

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        # Sidebar ------------------------
        self.sidebar = ctk.CTkFrame(container, width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        btn_row = ctk.CTkFrame(self.sidebar)
        btn_row.pack(fill="x", pady=(6, 4), padx=6)

        ctk.CTkButton(btn_row, text="New", width=60,
                      command=self.create_new_profile).pack(side="left", padx=4)

        ctk.CTkButton(btn_row, text="Import", width=70,
                      command=self.import_profiles).pack(side="left", padx=4)

        ctk.CTkButton(btn_row, text="Export", width=70,
                      command=self.export_profile).pack(side="left", padx=4)

        self.list_frame = ctk.CTkScrollableFrame(self.sidebar)
        self.list_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # Right pane ---------------------
        self.right = ctk.CTkScrollableFrame(container)
        self.right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        self.build_editor()

        # Initial load
        self.refresh_list()
        if self.selected_id:
            self.load_editor(self.selected_id)

    # ------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------
    def refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        self.doc = self.store.load()   # reload from disk
        self.profiles = {p["id"]: p for p in self.doc.get("profiles", [])}
        active = self.doc.get("active_profile_id")

        for p in self.profiles.values():
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=3, padx=4)

            lbl = ctk.CTkLabel(row, text=p.get("name", "(unnamed)"), anchor="w")
            lbl.pack(side="left", padx=4)
            lbl.bind("<Button-1>", lambda e, pid=p["id"]: self.load_editor(pid))

            if p["id"] == active:
                ctk.CTkLabel(row, text="(active)", text_color="#60a5fa").pack(side="left", padx=4)

            # quick menu
            menu_btn = ctk.CTkButton(row, text="⋯", width=32,
                                     command=lambda pid=p["id"]: self.popup_menu(pid))
            menu_btn.pack(side="right", padx=3)

    def popup_menu(self, pid: str):
        menu = ctk.CTkToplevel(self)
        menu.overrideredirect(True)
        menu.attributes("-topmost", True)
        menu.configure(fg_color="#0f1720")

        # Position
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        menu.geometry(f"+{x}+{y}")

        # ------ Close behaviour ------
        def close_menu(event=None):
            try:
                self.unbind("<Button-1>", click_outside_id)
            except:
                pass
            try:
                menu.destroy()
            except:
                pass

        # Close on Escape
        menu.bind("<Escape>", close_menu)

        # Detect click outside (safe version)
        def check_click(event):
            # if click is NOT inside popup → close
            if not menu.winfo_exists():
                return
            # Check if click is inside the popup window
            widget = menu.winfo_containing(event.x_root, event.y_root)

            # If widget is None or not a child of menu → close
            if widget is None or not str(widget).startswith(str(menu)):
                close_menu()

        # Bind click-outside to parent window
        click_outside_id = self.bind("<Button-1>", check_click, add="+")

        # Cleanup when window closes (unbind safely)
        def cleanup(event):
            try:
                self.unbind("<Button-1>", click_outside_id)
            except:
                pass

        menu.bind("<Destroy>", cleanup)

        # Helper for actions
        def choose(action):
            close_menu()
            action()

        # ---- Menu item builder ----
        def add_btn(label, color=None, cmd=lambda: None):
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

        # ---- Items ----
        add_btn("Rename", cmd=lambda: self._rename_action(pid))
        add_btn("Duplicate", cmd=lambda: self.duplicate_profile(pid))

        if not self.profiles.get(pid, {}).get("is_builtin", False):
            add_btn("Delete", color="#8b0000",
                    cmd=lambda: self.delete_profile(pid))

        add_btn("Set Active", color="#2563eb",
                cmd=lambda: self.set_active_profile(pid))

        # Focus so Escape works
        menu.focus_set()



    def _rename_action(self, pid):
        new = simpledialog.askstring("Rename", "New name:",
                                    initialvalue=self.profiles[pid]["name"])
        if new:
            self.rename_profile(pid, new.strip())

    # ------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------
    def create_new_profile(self):
        base = self.profiles.get(self.doc.get("active_profile_id"), {})
        new_id = f"profile_{int(datetime.now().timestamp())}"
        new_prof = json.loads(json.dumps(base))

        now = _now_iso()
        new_prof.update({
            "id": new_id,
            "name": "New Profile",
            "description": "",
            "created_at": now,
            "updated_at": now,
            "is_builtin": False
        })

        self.doc["profiles"].append(new_prof)
        self.doc["active_profile_id"] = new_id

        self.store.save(self.doc)
        self.refresh_list()
        self.load_editor(new_id)

    def duplicate_profile(self, pid):
        src = self.profiles.get(pid)
        if not src:
            return

        new_id = f"profile_{int(datetime.now().timestamp())}"
        copy = json.loads(json.dumps(src))
        now = _now_iso()
        copy.update({
            "id": new_id,
            "name": f"{src['name']} (copy)",
            "created_at": now,
            "updated_at": now,
            "is_builtin": False  # ← IMPORTANT FIX
        })

        self.doc["profiles"].append(copy)
        self.store.save(self.doc)
        self.refresh_list()


    def delete_profile(self, pid):
        if self.profiles.get(pid, {}).get("is_builtin"):
            messagebox.showwarning("Protected", "Cannot delete built-in profile.")
            return

        self.doc["profiles"] = [p for p in self.doc["profiles"] if p["id"] != pid]

        # fix active if needed
        if self.doc.get("active_profile_id") == pid:
            if self.doc["profiles"]:
                self.doc["active_profile_id"] = self.doc["profiles"][0]["id"]
            else:
                self.doc["active_profile_id"] = None

        self.store.save(self.doc)
        self.refresh_list()

    def rename_profile(self, pid, new):
        p = self.profiles.get(pid)
        if not p:
            return
        p["name"] = new
        p["updated_at"] = _now_iso()
        self.store.save(self.doc)
        self.refresh_list()

    def set_active_profile(self, pid):
        self.doc["active_profile_id"] = pid
        self.store.save(self.doc)
        self.refresh_list()
        messagebox.showinfo("Active profile", "Active profile set.")
        try:
            self.app.reload_profile(pid)
        except:
            pass

    # ------------------------------------------------------------
    # Import/Export
    # ------------------------------------------------------------
    def import_profiles(self):
        from tkinter import filedialog
        p = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not p:
            return
        data = json.load(open(p, "r", encoding="utf-8"))
        if "profiles" not in data:
            messagebox.showerror("Import", "Invalid file.")
            return

        for pf in data["profiles"]:
            pf["id"] = f"profile_{int(datetime.now().timestamp())}"
            self.doc["profiles"].append(pf)

        self.store.save(self.doc)
        self.refresh_list()

    def export_profile(self):
        from tkinter import filedialog
        if not self.selected_id:
            return
        pf = self.profiles.get(self.selected_id)
        p = filedialog.asksaveasfilename(defaultextension=".json")
        if not p:
            return
        json.dump({"profiles": [pf]}, open(p, "w", encoding="utf-8"), indent=2)
        messagebox.showinfo("Export", "Exported.")

    # ------------------------------------------------------------
    # Editor (Right Pane)
    # ------------------------------------------------------------
    def build_editor(self):
        """Build blank editor widgets."""
        self.name_entry = ctk.CTkEntry(self.right, placeholder_text="Profile name")
        self.name_entry.pack(fill="x", padx=10, pady=(6, 4))

        self.desc = ctk.CTkTextbox(self.right, height=80)
        self.add_placeholder(self.desc, "Describe what this profile does…")
        self.desc.pack(fill="x", padx=10, pady=(4, 10))

        # settings
        self.include_sub = ctk.CTkCheckBox(self.right, text="Include subfolders")
        self.include_sub.pack(anchor="w", padx=14)

        self.skip_hidden = ctk.CTkCheckBox(self.right, text="Ignore hidden/system files")
        self.skip_hidden.pack(anchor="w", padx=14)

        self.safe_mode = ctk.CTkCheckBox(self.right, text="Safe Mode (copy)")
        self.safe_mode.pack(anchor="w", padx=14)

        self.smart_mode = ctk.CTkCheckBox(self.right, text="Smart Sorting")
        self.smart_mode.pack(anchor="w", padx=14)

        row = ctk.CTkFrame(self.right)
        row.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(row, text="Ignore types:").pack(side="left")
        self.ignore_exts = ctk.CTkEntry(row, width=200, placeholder_text="e.g. .exe;.tmp;.log")
        self.ignore_exts.pack(side="left", padx=6)

        row2 = ctk.CTkFrame(self.right)
        row2.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(row2, text="Age filter (only moves files older than x days):").pack(side="left")
        self.age_days = ctk.CTkEntry(row2, width=80, placeholder_text="0 = off")
        self.age_days.pack(side="left", padx=6)

        # ignore patterns
        ctk.CTkLabel(self.right, text="Ignore Patterns:").pack(anchor="w", padx=10, pady=(8, 2))
        self.ignore_patterns = ctk.CTkTextbox(self.right, height=80)
        self.add_placeholder(self.ignore_patterns, "Enter patterns to ignore (one per line)…")
        self.ignore_patterns.pack(fill="x", padx=10)

        # don't move
        ctk.CTkLabel(self.right, text="Don't move list:").pack(anchor="w", padx=10, pady=(8, 2))
        self.dont_move = ctk.CTkTextbox(self.right, height=80)
        self.dont_move.insert("1.0", "Files or paths to exclude from moving…\nOne per line.")
        self.dont_move.pack(fill="x", padx=10)
        # Category Manager shortcut
        ctk.CTkButton(
            self.right,
            text="Edit Categories…",
            width=180,
            fg_color="#374151",
            hover_color="#2b3740",
            command=self.open_category_editor_for_profile,
        ).pack(pady=(10, 6), padx=10, anchor="w")


        # Save
        ctk.CTkButton(self.right, text="Save Changes",
                      fg_color="#2563eb", command=self.save_editor).pack(pady=14)
    def add_placeholder(self, textbox, text):
        textbox.placeholder = text

        def on_focus_in(event):
            if textbox.get("1.0", "end").strip() == text:
                textbox.delete("1.0", "end")
                textbox.configure(text_color="#ffffff")

        def on_focus_out(event):
            if not textbox.get("1.0", "end").strip():
                textbox.insert("1.0", text)
                textbox.configure(text_color="#7a8696")  # muted placeholder color

        textbox.bind("<FocusIn>", on_focus_in)
        textbox.bind("<FocusOut>", on_focus_out)

        # Initialize placeholder
        textbox.insert("1.0", text)
        textbox.configure(text_color="#7a8696")
            
    def open_category_editor_for_profile(self):
        pid = self.selected_id
        if not pid:
            messagebox.showerror("Categories", "Select a profile first.")
            return

        # Load fresh profile
        self.doc = self.store.load()
        self.profiles = {p["id"]: p for p in self.doc.get("profiles", [])}
        prof = self.profiles.get(pid)
        if not prof:
            messagebox.showerror("Categories", "Profile not found.")
            return

        # Open isolated Category Manager window
        CategoryManagerWindow(self.app, self.selected_id)



    def load_editor(self, pid):
        self.selected_id = pid
        self.doc = self.store.load()
        self.profiles = {p["id"]: p for p in self.doc.get("profiles", [])}
        p = self.profiles.get(pid)
        if not p:
            return

        s = p.get("settings", {})

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, p.get("name", ""))

        desc_text = p.get("description", "")
        self.desc.delete("1.0", "end")

        if desc_text.strip():
            self.desc.insert("1.0", desc_text)
            self.desc.configure(text_color="#ffffff")
        else:
            self.desc.insert("1.0", self.desc.placeholder)
            self.desc.configure(text_color="#7a8696")


        # checkboxes
        self.include_sub.select() if s.get("include_sub", True) else self.include_sub.deselect()
        self.skip_hidden.select() if s.get("skip_hidden", True) else self.skip_hidden.deselect()
        self.safe_mode.select() if s.get("safe_mode", True) else self.safe_mode.deselect()
        self.smart_mode.select() if s.get("smart_mode", False) else self.smart_mode.deselect()

        self.ignore_exts.delete(0, "end")
        self.ignore_exts.insert(0, s.get("ignore_exts", ""))

        self.age_days.delete(0, "end")
        self.age_days.insert(0, str(s.get("age_filter_days", 0)))

        # patterns
        self.ignore_patterns.delete("1.0", "end")
        for pat in p.get("ignore_patterns", []):
            self.ignore_patterns.insert("end", pat.get("pattern", "") + "\n")

        # dont move list
        self.dont_move.delete("1.0", "end")
        for path in p.get("dont_move_list", []):
            self.dont_move.insert("end", path + "\n")

    def save_editor(self):
        """Save UI → doc → disk. Zero recursion."""
        pid = self.selected_id
        self.doc = self.store.load()
        profiles = self.doc.get("profiles", [])
        p = next((x for x in profiles if x["id"] == pid), None)
        if not p:
            return

        p["name"] = self.name_entry.get().strip()
        p["description"] = self.desc.get("1.0", "end").strip()
        p["updated_at"] = _now_iso()

        s = p.setdefault("settings", {})
        s["include_sub"] = bool(self.include_sub.get())
        s["skip_hidden"] = bool(self.skip_hidden.get())
        s["safe_mode"] = bool(self.safe_mode.get())
        s["smart_mode"] = bool(self.smart_mode.get())
        s["ignore_exts"] = self.ignore_exts.get().strip()

        try:
            s["age_filter_days"] = int(self.age_days.get() or 0)
        except:
            s["age_filter_days"] = 0

        # patterns
        ips = [line.strip() for line in self.ignore_patterns.get("1.0", "end").splitlines()
               if line.strip()]
        p["ignore_patterns"] = [{"pattern": x} for x in ips]

        # dont move
        donts = [line.strip() for line in self.dont_move.get("1.0", "end").splitlines()
                 if line.strip()]
        p["dont_move_list"] = donts

        self.store.save(self.doc)
        self.refresh_list()

        # update live config if active
        if self.doc.get("active_profile_id") == pid:
            try:
                self.app.reload_profile(pid)
            except:
                pass

        messagebox.showinfo("Saved", "Profile saved.")
