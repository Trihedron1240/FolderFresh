# rule_manager.py

import customtkinter as ctk
from tkinter import messagebox
from folderfresh.profile_store import ProfileStore, now_iso
from folderfresh.rule_editor_popup import RuleEditorPopup
from folderfresh.activity_log_window import ActivityLogWindow
from folderfresh.rule_engine.rule_store import rule_to_dict


class RuleManager(ctk.CTkToplevel):
    """
    Rule Manager window with a list of rules.

    When a rule is selected, it opens in a popup editor (RuleEditorPopup).
    """

    def __init__(self, master=None, profile_id=None):
        super().__init__(master)

        self.geometry("300x600")
        self.minsize(250, 400)

        self.lift()
        self.focus_force()
        self.grab_set()

        # Load the specified profile (or active profile if not specified)
        self.store = ProfileStore()
        self.doc = self.store.load()
        self.profile_id = profile_id or self.doc.get("active_profile_id")

        # Find the profile by ID
        self.profile = None
        for p in self.doc.get("profiles", []):
            if p["id"] == self.profile_id:
                self.profile = p
                break

        if not self.profile:
            # Fallback to active profile if specified profile not found
            self.profile = self.store.get_active_profile(self.doc)
            self.profile_id = self.profile.get("id")

        self.rules = self.store.get_rules(self.profile)

        # Set window title with profile name
        profile_name = self.profile.get("name", "Unknown")
        self.title(f"Rule Manager - {profile_name}")

        # Track selected rule
        self.selected_rule_index = None
        self.rule_buttons = []

        # =============================================
        # LAYOUT
        # =============================================
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # LEFT panel (sidebar) - centered, no right panel
        self.sidebar = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray95", "gray15"))
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=10, pady=10, ipadx=0, ipady=0)
        self.sidebar.grid_propagate(False)
        self.sidebar.configure(width=220)

        # =============================================
        # SIDEBAR CONTENT
        # =============================================

        title = ctk.CTkLabel(
            self.sidebar,
            text="Rules",
            font=("Arial", 18, "bold")
        )
        title.pack(pady=(12, 5))

        # Priority explanation
        priority_help = ctk.CTkLabel(
            self.sidebar,
            text="Rules run top to bottom.\nOrder = priority.",
            font=("Arial", 9),
            text_color=("gray60", "gray40"),
            justify="center"
        )
        priority_help.pack(pady=(0, 8))

        # Scrollable list of rules
        self.rule_list_frame = ctk.CTkScrollableFrame(self.sidebar, width=160, height=260)
        self.rule_list_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)


        # Buttons container
        self.button_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.button_container.pack(fill="x", pady=(0, 10), padx=8)

        self.add_btn = ctk.CTkButton(
            self.button_container,
            text="+ Add",
            command=self.add_rule,
            font=("Arial", 11)
        )
        self.add_btn.pack(fill="x", pady=3)

        self.del_btn = ctk.CTkButton(
            self.button_container,
            text="- Delete",
            command=self.delete_rule,
            fg_color=("#d73336", "#b83a3e"),
            font=("Arial", 11)
        )
        self.del_btn.pack(fill="x", pady=3)

        self.up_btn = ctk.CTkButton(
            self.button_container,
            text="↑ Up",
            command=self.move_rule_up,
            font=("Arial", 11)
        )
        self.up_btn.pack(fill="x", pady=3)

        self.down_btn = ctk.CTkButton(
            self.button_container,
            text="↓ Down",
            command=self.move_rule_down,
            font=("Arial", 11)
        )
        self.down_btn.pack(fill="x", pady=3)

        # Activity Log button (separated with spacing)
        ctk.CTkLabel(self.sidebar, text="", font=("Arial", 3)).pack()

        self.log_btn = ctk.CTkButton(
            self.button_container,
            text="📋 Activity Log",
            command=self.open_activity_log,
            fg_color=("#2a5f2e", "#4a8f4e"),
            font=("Arial", 11)
        )
        self.log_btn.pack(fill="x", pady=3)

        # =============================================
        # RIGHT PANEL CONTENT
        # =============================================
        self.editor_container = None

        # Fill rule list
        self.render_rule_list()

    # =============================================
    # FUNCTIONS
    # =============================================

    def render_rule_list(self):
        """Render the list of rules in the sidebar with visual selection."""
        # Clear old content
        for child in self.rule_list_frame.winfo_children():
            child.destroy()

        self.rule_buttons = []

        # Add new buttons
        for i, rule in enumerate(self.rules):
            btn = ctk.CTkButton(
                self.rule_list_frame,
                text=rule.name,
                width=140,
                fg_color=("#1f6aa5", "#0d47a1") if i != self.selected_rule_index else ("#0d47a1", "#1565c0"),
                text_color=("white", "white") if i != self.selected_rule_index else ("white", "white"),
                command=lambda idx=i: self.select_rule(idx),
                font=("Arial", 11),
                corner_radius=8
            )
            btn.pack(fill="x", pady=3, padx=4)
            self.rule_buttons.append(btn)

    def select_rule(self, index):
        """Select a rule and open it in a popup editor."""
        self.selected_rule_index = index

        # Open popup editor for the selected rule
        RuleEditorPopup(
            self,
            self.rules[index],
            save_callback=self.save_rules
        )

        # Re-render list to update visual selection
        self.render_rule_list()

    def add_rule(self):
        """Add a new rule (unsaved until it becomes valid)."""
        name = self.simple_prompt("New Rule", "Name your new rule:")
        if not name:
            return

        from folderfresh.rule_engine import Rule
        new_rule = Rule(name=name, conditions=[], actions=[])

        # Add to memory but DON'T save to disk yet
        # The rule will only be persisted once it becomes valid (has conditions or actions)
        self.rules.append(new_rule)
        self.render_rule_list()

        # Auto-select the new rule for editing
        self.select_rule(len(self.rules) - 1)

    def delete_rule(self):
        """Delete the selected rule."""
        index = self.selected_rule_index
        if index is None:
            messagebox.showwarning("Delete Rule", "Please select a rule first.")
            return

        rule = self.rules[index]
        if not messagebox.askyesno("Delete Rule", f"Delete rule '{rule.name}'?"):
            return

        self.rules.pop(index)
        self.save_rules()

        # Reset selection
        self.selected_rule_index = None
        self.render_rule_list()

    def move_rule_up(self):
        """Move selected rule up in the list."""
        index = self.selected_rule_index
        if index is None or index == 0:
            messagebox.showwarning("Move Up", "Cannot move the first rule up.")
            return

        self.rules[index-1], self.rules[index] = self.rules[index], self.rules[index-1]
        self.selected_rule_index = index - 1
        self.save_rules()
        self.render_rule_list()

    def move_rule_down(self):
        """Move selected rule down in the list."""
        index = self.selected_rule_index
        if index is None or index >= len(self.rules) - 1:
            messagebox.showwarning("Move Down", "Cannot move the last rule down.")
            return

        self.rules[index+1], self.rules[index] = self.rules[index], self.rules[index+1]
        self.selected_rule_index = index + 1
        self.save_rules()
        self.render_rule_list()

    def save_rules(self):
        """Save all rules to the selected profile (self.profile_id) and persist to disk."""
        # Reload the document to ensure we have the latest state
        self.doc = self.store.load()

        # Find the profile by ID and update its rules
        for p in self.doc.get("profiles", []):
            if p["id"] == self.profile_id:
                # Convert Rule objects to dicts and update
                p["rules"] = [rule_to_dict(r) for r in self.rules]
                p["updated_at"] = now_iso()
                break

        # Save the updated document
        self.store.save(self.doc)

    def open_activity_log(self):
        """Open the Activity Log window."""
        ActivityLogWindow(self)

    def simple_prompt(self, title, message):
        """Show a simple text input dialog."""
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("350x150")
        win.resizable(False, False)

        win.lift()
        win.focus_force()
        win.grab_set()

        label = ctk.CTkLabel(win, text=message, font=("Arial", 11))
        label.pack(pady=(15, 10))

        entry = ctk.CTkEntry(win, placeholder_text="Enter text...")
        entry.pack(pady=5, padx=20, fill="x")
        entry.focus()

        out = {"v": None}

        def ok():
            out["v"] = entry.get().strip()
            win.destroy()

        def on_key(event):
            if event.keysym == "Return":
                ok()

        entry.bind("<Return>", on_key)

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x", padx=20)

        ok_btn = ctk.CTkButton(btn_frame, text="OK", command=ok)
        ok_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color=("gray70", "gray30"),
            command=win.destroy
        )
        cancel_btn.pack(side="left", padx=5)

        win.wait_window()
        return out["v"]
