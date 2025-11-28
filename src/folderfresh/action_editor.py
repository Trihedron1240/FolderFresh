# action_editor.py

import customtkinter as ctk
from tkinter import messagebox
from folderfresh.rule_engine import (
    RenameAction,
    MoveAction,
    CopyAction,
)

ACTION_TYPES = {
    "Rename File": RenameAction,
    "Move to Folder": MoveAction,
    "Copy to Folder": CopyAction,
}


class ActionEditor(ctk.CTkToplevel):
    """
    Polished popup UI to create a new action for a rule with validation and help text.
    """

    def __init__(self, master, callback=None):
        super().__init__(master)

        self.callback = callback

        self.title("Add Action")
        self.geometry("450x600")
        self.resizable(False, False)

        self.lift()
        self.focus_force()
        self.grab_set()

        # =========================================================
        # Title
        # =========================================================
        title = ctk.CTkLabel(self, text="Create a New Action", font=("Arial", 18, "bold"))
        title.pack(pady=(20, 10))

        # =========================================================
        # Action type dropdown
        # =========================================================
        type_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray15"))
        type_frame.pack(fill="x", padx=20, pady=10)

        type_label = ctk.CTkLabel(
            type_frame,
            text="Action Type:",
            font=("Arial", 12)
        )
        type_label.pack(anchor="w", padx=12, pady=(10, 0))

        self.type_menu = ctk.CTkOptionMenu(
            type_frame,
            values=list(ACTION_TYPES.keys()),
            command=self._on_type_change,
            font=("Arial", 11)
        )
        self.type_menu.set("Rename File")
        self.type_menu.pack(fill="x", padx=12, pady=10)

        # =========================================================
        # Parameter entry
        # =========================================================
        param_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray15"))
        param_frame.pack(fill="x", padx=20, pady=10)

        self.param_label = ctk.CTkLabel(
            param_frame,
            text="New filename:",
            font=("Arial", 12)
        )
        self.param_label.pack(anchor="w", padx=12, pady=(10, 0))

        self.param_entry = ctk.CTkEntry(
            param_frame,
            placeholder_text="Enter value...",
            font=("Arial", 11)
        )
        self.param_entry.pack(fill="x", padx=12, pady=10)
        self.param_entry.focus()

        # =========================================================
        # Description area
        # =========================================================
        desc_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray20"))
        desc_frame.pack(fill="both", padx=20, pady=10, expand=True)

        desc_label = ctk.CTkLabel(
            desc_frame,
            text="Description:",
            font=("Arial", 12, "bold")
        )
        desc_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.desc_text = ctk.CTkTextbox(
            desc_frame,
            height=80,
            state="disabled",
            corner_radius=8
        )
        self.desc_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Set initial description
        self._on_type_change("Rename File")

        # =========================================================
        # Buttons
        # =========================================================
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        create_btn = ctk.CTkButton(
            btn_frame,
            text="Add Action",
            command=self._create_action,
            font=("Arial", 12)
        )
        create_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color=("gray70", "gray30"),
            command=self.destroy,
            font=("Arial", 12)
        )
        cancel_btn.pack(side="left", padx=5)

    # =========================================================
    # UI LOGIC
    # =========================================================
    def _on_type_change(self, choice):
        """Change parameter label and description based on selected action."""
        descriptions = {
            "Rename File": (
                "Action: Rename the matched file\n\n"
                "Parameter: The new filename (with extension)\n\n"
                "Example: 'backup_2024.pdf'"
            ),
            "Move to Folder": (
                "Action: Move the matched file to a folder\n\n"
                "Parameter: Target folder path\n\n"
                "Example: 'C:\\Backups' or '/home/user/documents'"
            ),
            "Copy to Folder": (
                "Action: Copy the matched file to a folder\n\n"
                "Parameter: Target folder path\n\n"
                "Example: 'C:\\Archive' or '/mnt/backup'"
            ),
        }

        labels = {
            "Rename File": "New filename (with extension):",
            "Move to Folder": "Target folder path:",
            "Copy to Folder": "Target folder path:",
        }

        # Update label
        self.param_label.configure(text=labels.get(choice, "Parameter:"))

        # Update description
        self.desc_text.configure(state="normal")
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", descriptions.get(choice, ""))
        self.desc_text.configure(state="disabled")

    def _create_action(self):
        """Construct action object with validation."""
        choice = self.type_menu.get()
        param = self.param_entry.get().strip()

        if not param:
            messagebox.showwarning("Missing Parameter", f"Please enter a value for '{choice}'.")
            return

        try:
            ActionClass = ACTION_TYPES[choice]

            # Create actual action object
            action_obj = ActionClass(param)

            if self.callback:
                self.callback(action_obj)

            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create action: {str(e)}")
