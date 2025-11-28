# condition_editor.py

import customtkinter as ctk
from tkinter import messagebox
from folderfresh.rule_engine import (
    NameContainsCondition,
    ExtensionIsCondition,
    FileSizeGreaterThanCondition
)


CONDITION_TYPES = {
    "Name Contains": NameContainsCondition,
    "Extension Is": ExtensionIsCondition,
    "File Size > X bytes": FileSizeGreaterThanCondition,
}


class ConditionEditor(ctk.CTkToplevel):
    """
    Popup to create a new condition with improved UI and validation.
    """

    def __init__(self, master, callback=None):
        super().__init__(master)

        self.callback = callback
        self.title("Add Condition")
        self.geometry("400x700")
        self.resizable(False, False)

        self.lift()
        self.focus_force()
        self.grab_set()

        # =========================================================
        # Title
        # =========================================================
        title = ctk.CTkLabel(self, text="Create a New Condition", font=("Arial", 18, "bold"))
        title.pack(pady=(20, 15))

        # =========================================================
        # Condition type dropdown
        # =========================================================
        type_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray15"))
        type_frame.pack(fill="x", padx=20, pady=10)

        type_label = ctk.CTkLabel(
            type_frame,
            text="Condition Type:",
            font=("Arial", 12)
        )
        type_label.pack(anchor="w", padx=12, pady=(10, 0))

        self.type_menu = ctk.CTkOptionMenu(
            type_frame,
            values=list(CONDITION_TYPES.keys()),
            command=self.on_type_changed,
            font=("Arial", 11)
        )
        self.type_menu.set("Name Contains")
        self.type_menu.pack(fill="x", padx=12, pady=10)

        # =========================================================
        # Parameter input (text or size-based)
        # =========================================================
        self.param_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray15"))
        self.param_frame.pack(fill="x", padx=20, pady=10)

        self.param_label = ctk.CTkLabel(
            self.param_frame,
            text="Parameter:",
            font=("Arial", 12)
        )
        self.param_label.pack(anchor="w", padx=12, pady=(10, 0))

        # Text entry (for Name Contains and Extension Is)
        self.param_entry = ctk.CTkEntry(
            self.param_frame,
            placeholder_text="Enter value...",
            font=("Arial", 11)
        )
        self.param_entry.pack(fill="x", padx=12, pady=10)
        self.param_entry.focus()

        # File size entry (numeric + unit dropdown)
        self.size_input_frame = ctk.CTkFrame(self.param_frame, fg_color="transparent")
        self.size_input_frame.pack(fill="x", padx=0, pady=10)

        self.size_entry = ctk.CTkEntry(
            self.size_input_frame,
            placeholder_text="0.0",
            font=("Arial", 11),
            width=100
        )
        self.size_entry.pack(side="left", padx=(0, 8), fill="x", expand=True)

        self.size_unit = ctk.CTkOptionMenu(
            self.size_input_frame,
            values=["Bytes", "KB", "MB", "GB"],
            font=("Arial", 11),
            width=80
        )
        self.size_unit.set("MB")
        self.size_unit.pack(side="left", padx=0)

        # Hide size input by default
        self.size_input_frame.pack_forget()

        self.current_condition_type = "Name Contains"

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
        self.on_type_changed("Name Contains")

        # =========================================================
        # Buttons
        # =========================================================
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Add Condition",
            command=self.add_condition,
            font=("Arial", 12)
        )
        add_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color=("gray70", "gray30"),
            command=self.destroy,
            font=("Arial", 12)
        )
        cancel_btn.pack(side="left", padx=5)

    def on_type_changed(self, choice):
        """Update parameter label, input fields, and description based on selected type."""
        self.current_condition_type = choice

        descriptions = {
            "Name Contains": (
                "Parameter: Search substring (case-insensitive)\n\n"
                "Example: type 'backup' to match files with 'backup' in their name"
            ),
            "Extension Is": (
                "Parameter: File extension without dot\n\n"
                "Example: type 'pdf' to match PDF files\n"
                "(Don't include the dot)"
            ),
            "File Size > X bytes": (
                "Select a minimum file size using the size picker.\n\n"
                "Examples:\n"
                "  • 1 MB: minimum 1 megabyte\n"
                "  • 500 KB: minimum 500 kilobytes\n"
                "  • 0.5 GB: minimum 512 megabytes"
            ),
        }

        labels = {
            "Name Contains": "Text to search for:",
            "Extension Is": "File extension (e.g., pdf):",
            "File Size > X bytes": "Minimum file size:",
        }

        # Update label
        self.param_label.configure(text=labels.get(choice, "Parameter:"))

        # Show/hide appropriate input fields
        if choice == "File Size > X bytes":
            self.param_entry.pack_forget()
            self.size_input_frame.pack(fill="x", padx=0, pady=10)
            self.size_entry.focus()
        else:
            self.size_input_frame.pack_forget()
            self.param_entry.pack(fill="x", padx=12, pady=10)
            self.param_entry.focus()

        # Update description
        self.desc_text.configure(state="normal")
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", descriptions.get(choice, ""))
        self.desc_text.configure(state="disabled")

    def add_condition(self):
        """Create and add the condition with unit conversion for file size."""
        choice = self.type_menu.get()

        try:
            if choice == "File Size > X bytes":
                # File size condition with unit conversion
                size_str = self.size_entry.get().strip()
                if not size_str:
                    messagebox.showwarning("Missing Parameter", "Please enter a file size value.")
                    return

                try:
                    size_value = float(size_str)
                    if size_value < 0:
                        raise ValueError("Must be non-negative")
                except ValueError:
                    messagebox.showerror(
                        "Invalid Input",
                        "File size must be a valid number (e.g., 1, 0.5, 100)."
                    )
                    return

                # Convert to bytes based on selected unit
                unit = self.size_unit.get()
                param = self._convert_to_bytes(size_value, unit)
            else:
                # Text-based conditions
                param = self.param_entry.get().strip()
                if not param:
                    messagebox.showwarning("Missing Parameter", f"Please enter a value for '{choice}'.")
                    return

            ConditionClass = CONDITION_TYPES[choice]
            condition_obj = ConditionClass(param)

            if self.callback:
                self.callback(condition_obj)

            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create condition: {str(e)}")

    def _convert_to_bytes(self, value, unit):
        """Convert a value from the given unit to bytes."""
        multipliers = {
            "Bytes": 1,
            "KB": 1024,
            "MB": 1024 * 1024,
            "GB": 1024 * 1024 * 1024,
        }
        return int(value * multipliers.get(unit, 1))
