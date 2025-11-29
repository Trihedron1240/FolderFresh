# condition_editor.py

import customtkinter as ctk
from tkinter import messagebox
from folderfresh.rule_engine import (
    NameContainsCondition,
    NameStartsWithCondition,
    NameEndsWithCondition,
    NameEqualsCondition,
    RegexMatchCondition,
    ParentFolderContainsCondition,
    FileInFolderCondition,
    ExtensionIsCondition,
    FileSizeGreaterThanCondition,
    FileAgeGreaterThanCondition,
    LastModifiedBeforeCondition,
    IsHiddenCondition,
    IsReadOnlyCondition,
    IsDirectoryCondition,
    # Tier-1 Conditions
    ContentContainsCondition,
    DatePatternCondition,
)

CONDITION_TYPES = {
    "Name Contains": NameContainsCondition,
    "Name Starts With": NameStartsWithCondition,
    "Name Ends With": NameEndsWithCondition,
    "Name Equals": NameEqualsCondition,
    "Regex Match": RegexMatchCondition,
    "Parent Folder Contains": ParentFolderContainsCondition,
    "File is in folder containing": FileInFolderCondition,
    "Extension Is": ExtensionIsCondition,
    "File Size > X bytes": FileSizeGreaterThanCondition,
    "File Age > X days": FileAgeGreaterThanCondition,
    "Last Modified Before": LastModifiedBeforeCondition,
    "Is Hidden": IsHiddenCondition,
    "Is Read-Only": IsReadOnlyCondition,
    "Is Directory": IsDirectoryCondition,
    # Tier-1 Conditions
    "Content Contains": ContentContainsCondition,
    "Date Pattern": DatePatternCondition,
}


class ConditionEditor(ctk.CTkToplevel):
    """
    Popup to create a new condition with improved UI and validation.
    """

    def __init__(self, master, callback=None):
        super().__init__(master)

        self.callback = callback
        self.title("Add Condition")
        self.geometry("450x700")
        self.resizable(False, False)

        self.lift()
        self.focus_force()
        self.grab_set()

        # =========================================================
        # Title
        # =========================================================
        title = ctk.CTkLabel(self, text="Create a New Condition", font=("Arial", 18, "bold"))
        title.pack(pady=(20, 10))

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

        # Store current selection
        self.current_condition_type = "Name Contains"

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
        self.size_input_frame.pack(fill="x", padx=12, pady=10)

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

        # Case sensitive checkbox (for NameEqualsCondition)
        self.case_sensitive_frame = ctk.CTkFrame(self.param_frame, fg_color="transparent")
        self.case_sensitive_frame.pack(fill="x", padx=12, pady=5)

        self.case_sensitive_var = ctk.BooleanVar(value=False)
        self.case_sensitive_checkbox = ctk.CTkCheckBox(
            self.case_sensitive_frame,
            text="Case Sensitive",
            variable=self.case_sensitive_var,
            font=("Arial", 10)
        )
        self.case_sensitive_checkbox.pack(anchor="w")

        # Hide case sensitive checkbox by default
        self.case_sensitive_frame.pack_forget()

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

        # Update the type menu selection
        self.type_menu.set(choice)

        descriptions = {
            "Name Contains": (
                "Parameter: Search substring (case-insensitive)\n\n"
                "Example: type 'backup' to match files with 'backup' in their name"
            ),
            "Name Starts With": (
                "Parameter: Prefix text (case-insensitive)\n\n"
                "Example: type 'draft' to match files starting with 'draft'\n"
                "(e.g., draft_report.txt, DRAFT_budget.xlsx)"
            ),
            "Name Ends With": (
                "Parameter: Suffix text (case-insensitive)\n\n"
                "Example: type 'backup' to match files ending with 'backup'\n"
                "(e.g., data_backup.zip, BACKUP)"
            ),
            "Name Equals": (
                "Parameter: Exact filename to match\n\n"
                "By default: case-insensitive\n"
                "Enable 'Case Sensitive' checkbox for exact case matching\n\n"
                "Example: type 'README.md' to match that specific filename"
            ),
            "Regex Match": (
                "Parameter: Regular expression pattern\n\n"
                "Enable 'Ignore Case' for case-insensitive matching.\n"
                "Invalid patterns will return False (safe).\n"
                "Catastrophic backtracking patterns timeout automatically.\n\n"
                "Examples:\n"
                "  • ^report_.*\\.txt$ matches 'report_2024.txt'\n"
                "  • .*backup.* matches any file with 'backup' in name"
            ),
            "Parent Folder Contains": (
                "Parameter: Substring to search in parent folder name (case-insensitive)\n\n"
                "Example: type 'Downloads' to match files in a parent folder\n"
                "containing 'downloads' in its name\n\n"
                "Matches: /home/user/Downloads/file.txt\n"
                "Also matches: /home/user/MyDownloads/file.txt (case-insensitive)"
            ),
            "File is in folder containing": (
                "Parameter: Folder pattern to search in full parent path (case-insensitive)\n\n"
                "Example: type 'screenshots' to match files in any folder path\n"
                "containing 'screenshots' (anywhere in the path)\n\n"
                "Matches: C:/Users/me/Pictures/Screenshots/photo.jpg\n"
                "Also matches: C:/Downloads/screenshots_archive/image.png"
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
            "File Age > X days": (
                "Parameter: File age in days (numeric)\n\n"
                "Example: type '7' to match files older than 7 days\n"
                "The condition checks file modification time"
            ),
            "Last Modified Before": (
                "Parameter: Date/timestamp in ISO format\n\n"
                "Examples:\n"
                "  • 2024-01-01 (date only)\n"
                "  • 2024-01-01T10:00:00 (full datetime)\n"
                "Files modified before this time will match"
            ),
            "Is Hidden": (
                "Matches hidden files:\n"
                "  • Files starting with '.' (Unix-style)\n"
                "  • Files with Windows hidden attribute\n\n"
                "No parameters needed. Click 'Add' to apply."
            ),
            "Is Read-Only": (
                "Matches files with read-only permissions.\n\n"
                "These files cannot be modified or deleted.\n"
                "No parameters needed. Click 'Add' to apply."
            ),
            "Is Directory": (
                "Matches directories (folders).\n\n"
                "Use this to target directories in your rules.\n"
                "No parameters needed. Click 'Add' to apply."
            ),
            "Content Contains": (
                "Matches files by their text/binary content.\n\n"
                "Parameter: Keyword to search for (case-insensitive)\n\n"
                "Supports: Text files, PDF, DOCX, XLSX\n"
                "Searches first 256 KB by default\n\n"
                "Example: type 'ERROR' to find log files with errors"
            ),
            "Date Pattern": (
                "Matches files by creation or modification date using wildcards.\n\n"
                "First parameter: Date type (created or modified)\n"
                "Second parameter: Pattern like '2025-*' or '*-12-25'\n\n"
                "Examples:\n"
                "  • '2025-*': files created in 2025\n"
                "  • '2025-11-*': files created in November 2025\n"
                "  • '*-12-25': Christmas files from any year"
            ),
        }

        labels = {
            "Name Contains": "Text to search for:",
            "Name Starts With": "Prefix text:",
            "Name Ends With": "Suffix text:",
            "Name Equals": "Filename to match:",
            "Regex Match": "Regex pattern:",
            "Parent Folder Contains": "Folder name substring:",
            "File is in folder containing": "Folder pattern in path:",
            "Extension Is": "File extension (e.g., pdf):",
            "File Size > X bytes": "Minimum file size:",
            "File Age > X days": "File age in days:",
            "Last Modified Before": "Date/timestamp (ISO format):",
            "Is Hidden": "(No parameters)",
            "Is Read-Only": "(No parameters)",
            "Is Directory": "(No parameters)",
            "Content Contains": "Keyword to search for:",
            "Date Pattern": "Date pattern (e.g., 2025-* or *-12-25):",
        }

        # Update label
        self.param_label.configure(text=labels.get(choice, "Parameter:"))

        # Show/hide appropriate input fields
        if choice == "File Size > X bytes":
            self.param_entry.pack_forget()
            self.size_input_frame.pack(fill="x", padx=0, pady=10)
            self.case_sensitive_frame.pack_forget()
            self.size_entry.focus()
        elif choice in ["Is Hidden", "Is Read-Only", "Is Directory"]:
            # File attribute conditions have no parameters
            self.param_entry.pack_forget()
            self.size_input_frame.pack_forget()
            self.case_sensitive_frame.pack_forget()
        elif choice == "Content Contains":
            # Content Contains condition with single text parameter
            self.size_input_frame.pack_forget()
            self.param_entry.pack(fill="x", padx=12, pady=10)
            self.case_sensitive_frame.pack_forget()
            self.param_entry.focus()
        elif choice == "Date Pattern":
            # Date Pattern condition with pattern text parameter
            self.size_input_frame.pack_forget()
            self.param_entry.pack(fill="x", padx=12, pady=10)
            self.case_sensitive_frame.pack_forget()
            self.param_entry.focus()
        elif choice == "Name Equals":
            # Name Equals condition with case sensitivity option
            self.size_input_frame.pack_forget()
            self.param_entry.pack(fill="x", padx=12, pady=10)
            self.case_sensitive_checkbox.configure(text="Case Sensitive")
            self.case_sensitive_var.set(False)
            self.case_sensitive_frame.pack(fill="x", padx=12, pady=5)
            self.param_entry.focus()
        elif choice == "Regex Match":
            # Regex Match condition with ignore case option
            self.size_input_frame.pack_forget()
            self.param_entry.pack(fill="x", padx=12, pady=10)
            self.case_sensitive_checkbox.configure(text="Ignore Case")
            self.case_sensitive_var.set(False)
            self.case_sensitive_frame.pack(fill="x", padx=12, pady=5)
            self.param_entry.focus()
        else:
            self.size_input_frame.pack_forget()
            self.case_sensitive_frame.pack_forget()
            self.param_entry.pack(fill="x", padx=12, pady=10)
            self.param_entry.focus()

        # Update description
        self.desc_text.configure(state="normal")
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", descriptions.get(choice, ""))
        self.desc_text.configure(state="disabled")

    def add_condition(self):
        """Create and add the condition with appropriate parameter conversion."""
        choice = self.current_condition_type

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
                ConditionClass = CONDITION_TYPES[choice]
                condition_obj = ConditionClass(param)

            elif choice == "File Age > X days":
                # File age condition - convert to integer days
                days_str = self.param_entry.get().strip()
                if not days_str:
                    messagebox.showwarning("Missing Parameter", "Please enter a number of days.")
                    return

                try:
                    param = int(days_str)
                    if param < 0:
                        raise ValueError("Must be non-negative")
                except ValueError:
                    messagebox.showerror(
                        "Invalid Input",
                        "Days must be a whole number (e.g., 7, 30, 365)."
                    )
                    return

                ConditionClass = CONDITION_TYPES[choice]
                condition_obj = ConditionClass(param)

            elif choice in ["Is Hidden", "Is Read-Only", "Is Directory"]:
                # File attribute conditions - no parameters needed
                ConditionClass = CONDITION_TYPES[choice]
                condition_obj = ConditionClass()

            elif choice == "Name Equals":
                # Name Equals condition with case_sensitive option
                param = self.param_entry.get().strip()
                if not param:
                    messagebox.showwarning("Missing Parameter", f"Please enter a value for '{choice}'.")
                    return

                case_sensitive = self.case_sensitive_var.get()
                ConditionClass = CONDITION_TYPES[choice]
                condition_obj = ConditionClass(param, case_sensitive=case_sensitive)

            elif choice == "Regex Match":
                # Regex Match condition with ignore_case option
                param = self.param_entry.get().strip()
                if not param:
                    messagebox.showwarning("Missing Parameter", "Please enter a regex pattern.")
                    return

                ignore_case = self.case_sensitive_var.get()
                ConditionClass = CONDITION_TYPES[choice]
                condition_obj = ConditionClass(param, ignore_case=ignore_case)

            elif choice == "Parent Folder Contains":
                # Parent Folder Contains condition
                param = self.param_entry.get().strip()
                if not param:
                    messagebox.showwarning("Missing Parameter", "Please enter a folder name substring.")
                    return

                ConditionClass = CONDITION_TYPES[choice]
                condition_obj = ConditionClass(param)

            elif choice == "File is in folder containing":
                # File is in folder containing condition
                param = self.param_entry.get().strip()
                if not param:
                    messagebox.showwarning("Missing Parameter", "Please enter a folder pattern.")
                    return

                ConditionClass = CONDITION_TYPES[choice]
                condition_obj = ConditionClass(param)

            elif choice == "Content Contains":
                # Content Contains condition
                param = self.param_entry.get().strip()
                if not param:
                    messagebox.showwarning("Missing Parameter", "Please enter a keyword to search for.")
                    return

                ConditionClass = CONDITION_TYPES[choice]
                condition_obj = ConditionClass(param)

            elif choice == "Date Pattern":
                # Date Pattern condition
                param = self.param_entry.get().strip()
                if not param:
                    messagebox.showwarning("Missing Parameter", "Please enter a date pattern (e.g., 2025-* or *-12-25).")
                    return

                ConditionClass = CONDITION_TYPES[choice]
                # DatePatternCondition takes date_type and pattern as arguments
                # For UI simplicity, we'll use "modified" as the default date type
                condition_obj = ConditionClass("modified", param)

            else:
                # Text-based conditions (Name Contains, Name Starts With, Name Ends With, Extension Is, Last Modified Before)
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
