# rule_editor_popup.py

import customtkinter as ctk
from folderfresh.rule_engine import Rule
from folderfresh.rule_editor import RuleEditor


class RuleEditorPopup(ctk.CTkToplevel):
    """
    Standalone popup window for editing a rule.

    Wraps RuleEditor in a CTkToplevel window for a clean popup experience.
    """

    def __init__(self, master, rule: Rule, save_callback=None):
        """
        Initialize RuleEditorPopup.

        Args:
            master: Parent window
            rule: Rule object to edit
            save_callback: Called when rule is saved
        """
        super().__init__(master)

        self.rule = rule
        self.save_callback = save_callback

        # Configure window
        self.title(f"Edit Rule: {rule.name}")
        self.geometry("600x700")
        self.minsize(500, 600)

        self.lift()
        self.focus_force()
        self.grab_set()

        # Create scrollable content frame
        scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Create RuleEditor inside the popup
        self.rule_editor = RuleEditor(
            scroll_frame,
            rule=rule,
            save_callback=self._on_rule_saved
        )

        # Add buttons at the bottom
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(10, 15))

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save & Close",
            command=self._save_and_close,
            fg_color=("#2a5f2e", "#4a8f4e"),
            font=("Arial", 12)
        )
        save_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=("gray70", "gray30"),
            font=("Arial", 12)
        )
        cancel_btn.pack(side="left", padx=5)

    def _on_rule_saved(self):
        """Called when rule editor saves changes."""
        if self.save_callback:
            self.save_callback()

    def _save_and_close(self):
        """Validate, save, and close the popup."""
        # Apply any pending changes
        self.rule_editor._apply_changes()

        # Validate the rule
        if not RuleEditor.rule_is_valid(self.rule):
            from tkinter import messagebox
            messagebox.showwarning(
                "Invalid Rule",
                "Cannot save an incomplete rule. Please:\n"
                "1. Enter a rule name\n"
                "2. Add at least one condition or action\n"
                "3. Ensure all conditions and actions are fully configured"
            )
            return

        # Save and close
        if self.save_callback:
            self.save_callback()
        self.destroy()
