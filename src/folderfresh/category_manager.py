from __future__ import annotations
import json
from typing import Dict, Any
import copy
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from .profile_store import ProfileStore
from .constants import CATEGORIES


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class CategoryManagerWindow(ctk.CTkToplevel):
    
    def __init__(self, app, profile_id):
        super().__init__(app)
        self.app = app
        self.profile_store: ProfileStore = app.profile_store
        self.active_profile_id = profile_id

        # Load full document ONCE
        full_doc = self.profile_store.load()

        # Extract active profile safely
        original = next(
            (p for p in full_doc.get("profiles", []) if p["id"] == profile_id),
            None
        )
        if not original:
            messagebox.showerror("Error", "Profile not found.")
            self.destroy()
            return

        # Work only on a deep copy
        self.working_profile = copy.deepcopy(original)

        self.full_doc = full_doc  # kept only for save patching

        # ------------------------------
        # UI
        # ------------------------------
        self.title("Manage Categories")
        self.geometry("750x700")
        self.grab_set()

        ctk.CTkLabel(self, text="Category Manager",
                     font=("Segoe UI Variable", 18, "bold")).pack(pady=10)

        self.frame = ctk.CTkScrollableFrame(self, width=720, height=520)
        self.frame.pack(padx=12, pady=8, fill="both", expand=True)

        btn_row = ctk.CTkFrame(self)
        btn_row.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkButton(
            btn_row,
            text="Restore Default Categories",
            fg_color="#ef4444",
            hover_color="#c72f2f",
            command=self._restore_defaults_popup
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row,
            text="Close",
            fg_color="#475569",
            hover_color="#334155",
            command=self.destroy
        ).pack(side="right", padx=6)

        self._render()

    # ------------------------------------------------------------
    # Save handling (critical logic)
    # ------------------------------------------------------------
    def _commit_profile_changes(self):
        """
        Writes ONLY the working profile back into the full document.
        """
        # reload fresh document in case other profiles changed
        doc = self.profile_store.load()
        profiles = doc.get("profiles", [])

        for i, p in enumerate(profiles):
            if p["id"] == self.active_profile_id:
                self.working_profile["updated_at"] = _now_iso()
                doc["profiles"][i] = self.working_profile
                break

        self.profile_store.save(doc)
        self.full_doc = doc

        # update app's copy (safe — no merges or reloads)
        try:
            self.app.profiles_doc = doc
        except:
            pass

    # ------------------------------------------------------------
    # Render UI
    # ------------------------------------------------------------
    def _render(self):
        for w in self.frame.winfo_children():
            w.destroy()

        p = self.working_profile
        overrides = p.get("category_overrides", {}) or {}
        ext_map = p.get("custom_categories", {}) or {}
        enabled_map = p.get("category_enabled", {}) or {}

        # ----------------------------
        # Default categories
        # ----------------------------
        ctk.CTkLabel(self.frame, text="Default Categories",
                     font=("Segoe UI Variable", 16, "bold")).pack(anchor="w", padx=6, pady=(6, 8))

        for cat in CATEGORIES.keys():
            row = ctk.CTkFrame(self.frame)
            row.pack(fill="x", pady=4, padx=6)

            var = ctk.BooleanVar(value=bool(enabled_map.get(cat, True)))
            ctk.CTkCheckBox(
                row, text="Enabled", variable=var,
                command=lambda c=cat, v=var: self._toggle_enabled(c, v.get())
            ).pack(side="left", padx=(0, 8))

            ctk.CTkLabel(row, text=cat, width=120).pack(side="left")

            rename = ctk.CTkEntry(row, width=180, placeholder_text="New name")
            rename.pack(side="left", padx=8)
            if cat in overrides:
                rename.insert(0, overrides[cat])

            # extensions
            exts = ext_map.get(cat, CATEGORIES.get(cat, []))
            ext_entry = ctk.CTkEntry(row, width=200)
            ext_entry.pack(side="left", padx=6)
            ext_entry.insert(0, ";".join(exts))

            ctk.CTkButton(
                row, text="Save", width=60,
                command=lambda c=cat, r=rename, e=ext_entry:
                    self._save_default(c, r.get().strip(), e.get().strip())
            ).pack(side="left", padx=6)

        # ----------------------------
        # Custom categories
        # ----------------------------
        ctk.CTkLabel(self.frame, text="Custom Categories",
                     font=("Segoe UI Variable", 16, "bold")).pack(anchor="w", padx=6, pady=(12, 8))

        for cat, exts in list(ext_map.items()):
            if cat in CATEGORIES:
                continue

            row = ctk.CTkFrame(self.frame)
            row.pack(fill="x", pady=4, padx=6)

            var = ctk.BooleanVar(value=bool(enabled_map.get(cat, True)))
            ctk.CTkCheckBox(
                row, text="Enabled", variable=var,
                command=lambda c=cat, v=var: self._toggle_enabled(c, v.get())
            ).pack(side="left", padx=(0, 8))

            name_entry = ctk.CTkEntry(row, width=160)
            name_entry.pack(side="left", padx=6)
            name_entry.insert(0, cat)

            ext_entry = ctk.CTkEntry(row, width=200)
            ext_entry.pack(side="left", padx=6)
            ext_entry.insert(0, ";".join(exts))

            ctk.CTkButton(
                row, text="Save", width=60,
                command=lambda old=cat, n=name_entry, e=ext_entry:
                    self._save_custom(old, n.get().strip(), e.get().strip())
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                row, text="✕", width=36,
                fg_color="#8b0000", hover_color="#b30000",
                command=lambda x=cat: self._delete_custom(x)
            ).pack(side="left", padx=6)

        # ----------------------------
        # Add new custom
        # ----------------------------
        ctk.CTkLabel(self.frame, text="Add New Category",
                     font=("Segoe UI Variable", 16, "bold")).pack(anchor="w", padx=6, pady=(12, 6))

        add_row = ctk.CTkFrame(self.frame)
        add_row.pack(fill="x", padx=6, pady=6)

        self.new_name = ctk.CTkEntry(add_row, width=180, placeholder_text="Category name")
        self.new_name.pack(side="left", padx=6)

        self.new_exts = ctk.CTkEntry(add_row, width=240, placeholder_text=".ext1;.ext2")
        self.new_exts.pack(side="left", padx=6)

        ctk.CTkButton(
            add_row, text="Add", width=80,
            fg_color="#2563eb", hover_color="#1e4fd8",
            command=self._add_custom
        ).pack(side="left", padx=6)

    # ------------------------------------------------------------
    # Action callbacks
    # ------------------------------------------------------------
    def _toggle_enabled(self, cat, val):
        p = self.working_profile
        p.setdefault("category_enabled", {})[cat] = bool(val)
        self._commit_profile_changes()
        self._render()

    def _save_default(self, cat, new_name, raw_exts):
        p = self.working_profile
        cc = p.setdefault("custom_categories", {})
        co = p.setdefault("category_overrides", {})

        exts = [x.strip().lower() for x in raw_exts.split(";") if x.strip()]
        cc[cat] = exts

        if new_name:
            co[cat] = new_name
        else:
            co.pop(cat, None)

        self._commit_profile_changes()
        messagebox.showinfo("Saved", f"Category '{cat}' updated.")
        self._render()

    def _save_custom(self, old, new, raw_exts):
        if not new:
            messagebox.showwarning("Error", "Name cannot be empty.")
            return

        p = self.working_profile
        cc = p.setdefault("custom_categories", {})
        ce = p.setdefault("category_enabled", {})

        exts = [x.strip().lower() for x in raw_exts.split(";") if x.strip()]

        # rename logic
        old_enabled = ce.pop(old, True)
        cc.pop(old, None)

        cc[new] = exts
        ce[new] = old_enabled

        self._commit_profile_changes()
        messagebox.showinfo("Saved", f"Custom category '{new}' saved.")
        self._render()

    def _delete_custom(self, cat):
        p = self.working_profile
        p.setdefault("custom_categories", {}).pop(cat, None)
        p.setdefault("category_enabled", {}).pop(cat, None)

        self._commit_profile_changes()
        messagebox.showinfo("Deleted", f"Custom category '{cat}' removed.")
        self._render()

    def _add_custom(self):
        name = self.new_name.get().strip()
        raw = self.new_exts.get().strip()

        if not name:
            messagebox.showwarning("Add Category", "Please provide a category name.")
            return

        exts = [x.strip().lower() for x in raw.split(";") if x.strip()]

        p = self.working_profile
        p.setdefault("custom_categories", {})[name] = exts
        p.setdefault("category_enabled", {})[name] = True

        self._commit_profile_changes()
        messagebox.showinfo("Added", f"Category '{name}' added.")

        self.new_name.delete(0, "end")
        self.new_exts.delete(0, "end")
        self._render()

    # Restore defaults -------------------------------------------
    def _restore_defaults_popup(self):
        if messagebox.askyesno("Restore Defaults",
                               "Restore default categories only for this profile?"):
            self._restore_defaults()

    def _restore_defaults(self):
        p = self.working_profile
        p["custom_categories"] = {}
        p["category_overrides"] = {}
        p["category_enabled"] = {}

        self._commit_profile_changes()
        messagebox.showinfo("Restored", "Defaults restored for this profile.")
        self.destroy()
