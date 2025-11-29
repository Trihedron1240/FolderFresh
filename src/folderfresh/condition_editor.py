# condition_editor.py
# Hazel-style dynamic condition builder UI

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
    # Tier-2 Conditions
    ColorIsCondition,
    HasTagCondition,
    MetadataContainsCondition,
    MetadataFieldEqualsCondition,
    IsDuplicateCondition,
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
    # Tier-2 Conditions
    "Color Is": ColorIsCondition,
    "Has Tag": HasTagCondition,
    "Metadata Contains": MetadataContainsCondition,
    "Metadata Field Equals": MetadataFieldEqualsCondition,
    "Is Duplicate": IsDuplicateCondition,
}

# ========================================================================
# HAZEL-STYLE UI SCHEMA: Maps condition types to their parameter fields
# ========================================================================
# Field type options:
#   "text" → single-line text input (CTkEntry)
#   "numeric" → numeric input (validated as int)
#   "size" → numeric with unit dropdown (Bytes, KB, MB, GB)
#   "date" → date text input (ISO format)
#   "dropdown" → choice from predefined options (CTkOptionMenu)
#   "checkbox" → boolean flag (CTkCheckBox)
#   "none" → no input required
# ========================================================================

UI_SCHEMA = {
    # Basic Name Conditions (1 text parameter each)
    "Name Contains": [
        {"label": "Text to search for:", "type": "text", "placeholder": "e.g., backup"},
    ],
    "Name Starts With": [
        {"label": "Prefix text:", "type": "text", "placeholder": "e.g., draft"},
    ],
    "Name Ends With": [
        {"label": "Suffix text:", "type": "text", "placeholder": "e.g., backup"},
    ],
    "Name Equals": [
        {"label": "Filename to match:", "type": "text", "placeholder": "e.g., README.md"},
        {"label": "Case sensitive:", "type": "checkbox", "default": False},
    ],

    # Regex
    "Regex Match": [
        {"label": "Regex pattern:", "type": "text", "placeholder": "e.g., ^report_.*\\.txt$"},
        {"label": "Ignore case:", "type": "checkbox", "default": False},
    ],

    # File Path Conditions (1 text parameter each)
    "Parent Folder Contains": [
        {"label": "Folder name substring:", "type": "text", "placeholder": "e.g., Downloads"},
    ],
    "File is in folder containing": [
        {"label": "Folder pattern in path:", "type": "text", "placeholder": "e.g., screenshots"},
    ],

    # File Properties
    "Extension Is": [
        {"label": "File extension (e.g., pdf):", "type": "text", "placeholder": "pdf"},
    ],
    "File Size > X bytes": [
        {"label": "Minimum file size:", "type": "size", "default": 1, "unit": "MB"},
    ],
    "File Age > X days": [
        {"label": "File age in days:", "type": "numeric", "placeholder": "7"},
    ],
    "Last Modified Before": [
        {"label": "Date/timestamp (ISO format):", "type": "text", "placeholder": "2024-01-01"},
    ],

    # File Attributes (no parameters)
    "Is Hidden": [
        {"label": "No parameters required", "type": "none"},
    ],
    "Is Read-Only": [
        {"label": "No parameters required", "type": "none"},
    ],
    "Is Directory": [
        {"label": "No parameters required", "type": "none"},
    ],

    # Tier-1 Content & Patterns
    "Content Contains": [
        {"label": "Keyword to search for:", "type": "text", "placeholder": "e.g., ERROR"},
    ],
    "Date Pattern": [
        {"label": "Date type:", "type": "dropdown", "options": ["created", "modified"], "default": "modified"},
        {"label": "Pattern (e.g., 2025-* or *-12-25):", "type": "text", "placeholder": "2025-*"},
    ],

    # Tier-2 Metadata & Tags
    "Color Is": [
        {"label": "Color name:", "type": "dropdown", "options": ["red", "blue", "green", "yellow", "orange", "purple"], "default": "red"},
    ],
    "Has Tag": [
        {"label": "Tag name:", "type": "text", "placeholder": "e.g., important"},
    ],
    "Metadata Contains": [
        {"label": "Field name (e.g., author, exif.CameraModel):", "type": "text", "placeholder": "author"},
        {"label": "Keyword to search for:", "type": "text", "placeholder": "John"},
    ],
    "Metadata Field Equals": [
        {"label": "Field name (e.g., status, pdf_pages):", "type": "text", "placeholder": "status"},
        {"label": "Exact value to match:", "type": "text", "placeholder": "completed"},
    ],
    "Is Duplicate": [
        {"label": "Match type:", "type": "dropdown", "options": ["quick", "full"], "default": "quick"},
    ],
}

DESCRIPTIONS = {
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
    # Tier-2 Conditions
    "Color Is": (
        "Matches files with a specific color label.\n\n"
        "Parameter: Color name (red, blue, green, yellow, orange, purple)\n\n"
        "Example: type 'red' to match all red-labeled files\n\n"
        "Use 'Set Color Label' action to apply colors"
    ),
    "Has Tag": (
        "Matches files that have a specific tag.\n\n"
        "Parameter: Tag name (any string)\n\n"
        "Examples: 'important', 'urgent', 'review', 'archived'\n\n"
        "Use 'Add Tag' action to apply tags"
    ),
    "Metadata Contains": (
        "Matches files by metadata content (case-insensitive).\n\n"
        "Parameter 1: Field name (e.g., 'author', 'exif.CameraModel')\n"
        "Parameter 2: Keyword to search for\n\n"
        "Supports nested fields with dot notation\n"
        "Extracted from EXIF, PDF, Office, etc."
    ),
    "Metadata Field Equals": (
        "Matches files by exact metadata field value.\n\n"
        "Parameter 1: Field name (e.g., 'status', 'pdf_pages')\n"
        "Parameter 2: Exact value to match\n\n"
        "Case-insensitive matching\n"
        "Supports nested fields with dot notation"
    ),
    "Is Duplicate": (
        "Matches files detected as duplicates by hash.\n\n"
        "Parameter: Match type (quick or full)\n"
        "  • 'quick': compares first 1MB hash (fast)\n"
        "  • 'full': compares entire file hash (slow)\n\n"
        "Use 'Mark as Duplicate' action to tag duplicates"
    ),
}


class ConditionEditor(ctk.CTkToplevel):
    """
    Hazel-style dynamic condition builder.
    Renders different parameter fields based on condition type.
    """

    def __init__(self, master, callback=None):
        super().__init__(master)

        self.callback = callback
        self.title("Add Condition")
        self.geometry("500x750")
        self.resizable(False, False)

        self.lift()
        self.focus_force()
        self.grab_set()

        # Track current condition and field widgets
        self.current_condition_type = "Name Contains"
        self.field_widgets = {}  # {field_key: widget_object}

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

        # =========================================================
        # Dynamic parameter fields container
        # =========================================================
        self.param_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray15"))
        self.param_frame.pack(fill="x", padx=20, pady=10)

        self.param_inner = ctk.CTkFrame(self.param_frame, fg_color="transparent")
        self.param_inner.pack(fill="both", expand=True, padx=12, pady=12)

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

        # Initialize UI for default condition type
        self.on_type_changed("Name Contains")

    def on_type_changed(self, choice):
        """Rebuild parameter fields dynamically based on selected condition type."""
        self.current_condition_type = choice
        self.type_menu.set(choice)

        # Clear existing field widgets
        self._clear_fields()

        # Get schema for this condition
        schema = UI_SCHEMA.get(choice, [])

        # Build new fields
        for field_spec in schema:
            field_type = field_spec.get("type", "text")
            label = field_spec.get("label", "")

            if field_type == "none":
                # No parameter input needed
                pass
            elif field_type == "text":
                self._create_text_field(label, field_spec)
            elif field_type == "numeric":
                self._create_numeric_field(label, field_spec)
            elif field_type == "size":
                self._create_size_field(label, field_spec)
            elif field_type == "date":
                self._create_text_field(label, field_spec)
            elif field_type == "dropdown":
                self._create_dropdown_field(label, field_spec)
            elif field_type == "checkbox":
                self._create_checkbox_field(label, field_spec)

        # Update description
        self._update_description(choice)

    def _clear_fields(self):
        """Destroy all dynamically created field widgets."""
        for widget in self.field_widgets.values():
            try:
                widget.destroy()
            except Exception:
                pass
        self.field_widgets = {}

    def _create_text_field(self, label, spec):
        """Create a text entry field."""
        # Label
        label_widget = ctk.CTkLabel(
            self.param_inner,
            text=label,
            font=("Arial", 11),
            text_color=("gray10", "gray90")
        )
        label_widget.pack(anchor="w", pady=(8, 2))
        self.field_widgets[f"{label}_label"] = label_widget

        # Entry
        placeholder = spec.get("placeholder", "Enter value...")
        entry = ctk.CTkEntry(
            self.param_inner,
            placeholder_text=placeholder,
            font=("Arial", 10),
            height=32
        )
        entry.pack(fill="x", pady=(0, 8))
        self.field_widgets[label] = entry

    def _create_numeric_field(self, label, spec):
        """Create a numeric entry field."""
        label_widget = ctk.CTkLabel(
            self.param_inner,
            text=label,
            font=("Arial", 11),
            text_color=("gray10", "gray90")
        )
        label_widget.pack(anchor="w", pady=(8, 2))
        self.field_widgets[f"{label}_label"] = label_widget

        entry = ctk.CTkEntry(
            self.param_inner,
            placeholder_text="0",
            font=("Arial", 10),
            height=32
        )
        entry.pack(fill="x", pady=(0, 8))
        self.field_widgets[label] = entry

    def _create_size_field(self, label, spec):
        """Create a size entry with unit dropdown."""
        label_widget = ctk.CTkLabel(
            self.param_inner,
            text=label,
            font=("Arial", 11),
            text_color=("gray10", "gray90")
        )
        label_widget.pack(anchor="w", pady=(8, 2))
        self.field_widgets[f"{label}_label"] = label_widget

        # Container for entry and unit
        container = ctk.CTkFrame(self.param_inner, fg_color="transparent")
        container.pack(fill="x", pady=(0, 8))

        entry = ctk.CTkEntry(
            container,
            placeholder_text="1",
            font=("Arial", 10),
            height=32
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        unit_menu = ctk.CTkOptionMenu(
            container,
            values=["Bytes", "KB", "MB", "GB"],
            font=("Arial", 10),
            width=80
        )
        unit_menu.set(spec.get("unit", "MB"))
        unit_menu.pack(side="left")

        self.field_widgets[f"{label}_value"] = entry
        self.field_widgets[f"{label}_unit"] = unit_menu

    def _create_dropdown_field(self, label, spec):
        """Create a dropdown field."""
        label_widget = ctk.CTkLabel(
            self.param_inner,
            text=label,
            font=("Arial", 11),
            text_color=("gray10", "gray90")
        )
        label_widget.pack(anchor="w", pady=(8, 2))
        self.field_widgets[f"{label}_label"] = label_widget

        options = spec.get("options", [])
        default = spec.get("default", options[0] if options else "")

        menu = ctk.CTkOptionMenu(
            self.param_inner,
            values=options,
            font=("Arial", 10),
            height=32
        )
        menu.set(default)
        menu.pack(fill="x", pady=(0, 8))
        self.field_widgets[label] = menu

    def _create_checkbox_field(self, label, spec):
        """Create a checkbox field."""
        default = spec.get("default", False)
        var = ctk.BooleanVar(value=default)

        checkbox = ctk.CTkCheckBox(
            self.param_inner,
            text=label,
            variable=var,
            font=("Arial", 10)
        )
        checkbox.pack(anchor="w", pady=(8, 8))
        self.field_widgets[label] = checkbox
        # Store the variable reference for later retrieval
        self.field_widgets[f"{label}_var"] = var

    def _update_description(self, condition_type):
        """Update the description panel."""
        description = DESCRIPTIONS.get(condition_type, "")
        self.desc_text.configure(state="normal")
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", description)
        self.desc_text.configure(state="disabled")

    def _get_field_value(self, label):
        """Retrieve the value from a field widget."""
        widget = self.field_widgets.get(label)
        if widget is None:
            return None

        if isinstance(widget, ctk.CTkEntry):
            return widget.get().strip()
        elif isinstance(widget, ctk.CTkOptionMenu):
            return widget.get()
        elif isinstance(widget, ctk.CTkCheckBox):
            var = self.field_widgets.get(f"{label}_var")
            if var:
                return var.get()
            return widget.get()
        return None

    def add_condition(self):
        """Construct and add the condition object."""
        choice = self.current_condition_type
        schema = UI_SCHEMA.get(choice, [])

        try:
            # Collect parameters based on condition type and schema
            params = self._collect_parameters(choice, schema)

            # Create condition object
            ConditionClass = CONDITION_TYPES[choice]
            condition_obj = self._instantiate_condition(ConditionClass, choice, params)

            if self.callback:
                self.callback(condition_obj)

            self.destroy()

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create condition: {str(e)}")

    def _collect_parameters(self, condition_type, schema):
        """Collect parameter values from the dynamically built form."""
        params = {}

        for field_spec in schema:
            field_type = field_spec.get("type", "text")
            label = field_spec.get("label", "")

            if field_type == "none":
                continue

            if field_type == "checkbox":
                params[label] = self._get_field_value(label)
            elif field_type == "size":
                value_str = self.field_widgets.get(f"{label}_value")
                unit_menu = self.field_widgets.get(f"{label}_unit")

                if not value_str or not unit_menu:
                    raise ValueError(f"Missing size parameter: {label}")

                try:
                    size_val = float(value_str.get().strip())
                    if size_val < 0:
                        raise ValueError("Size must be non-negative")
                except ValueError:
                    raise ValueError(f"Invalid size value for '{label}'. Must be a number.")

                unit = unit_menu.get()
                size_bytes = self._convert_to_bytes(size_val, unit)
                params[label] = size_bytes
            else:
                value = self._get_field_value(label)
                if not value and field_type in ["text", "numeric", "date"]:
                    # Optional: Allow empty for some conditions, error for others
                    raise ValueError(f"Please enter a value for '{label}'.")
                params[label] = value

        return params

    def _instantiate_condition(self, ConditionClass, condition_type, params):
        """Create a condition instance with the collected parameters."""

        # Map condition types to constructor signatures
        if condition_type == "Is Hidden" or condition_type == "Is Read-Only" or condition_type == "Is Directory":
            return ConditionClass()

        elif condition_type == "Name Equals":
            filename = params.get("Filename to match:", "")
            case_sensitive = params.get("Case sensitive:", False)
            return ConditionClass(filename, case_sensitive=case_sensitive)

        elif condition_type == "Regex Match":
            pattern = params.get("Regex pattern:", "")
            ignore_case = params.get("Ignore case:", False)
            return ConditionClass(pattern, ignore_case=ignore_case)

        elif condition_type == "File Size > X bytes":
            size_bytes = params.get("Minimum file size:", 0)
            return ConditionClass(size_bytes)

        elif condition_type == "File Age > X days":
            days_str = params.get("File age in days:", "0")
            try:
                days = int(days_str)
            except ValueError:
                raise ValueError("Days must be a whole number.")
            return ConditionClass(days)

        elif condition_type == "Date Pattern":
            date_type = params.get("Date type:", "modified")
            pattern = params.get("Pattern (e.g., 2025-* or *-12-25):", "")
            return ConditionClass(date_type, pattern)

        elif condition_type == "Metadata Contains":
            field_name = params.get("Field name (e.g., author, exif.CameraModel):", "")
            keyword = params.get("Keyword to search for:", "")
            return ConditionClass(field_name, keyword)

        elif condition_type == "Metadata Field Equals":
            field_name = params.get("Field name (e.g., status, pdf_pages):", "")
            value = params.get("Exact value to match:", "")
            return ConditionClass(field_name, value)

        elif condition_type == "Is Duplicate":
            match_type = params.get("Match type:", "quick")
            return ConditionClass(match_type)

        else:
            # Generic single-parameter conditions
            # Extract the first text parameter (works for Name Contains, Extension Is, etc.)
            for label, value in params.items():
                if label not in ["Case sensitive:", "Ignore case:"]:
                    return ConditionClass(value)
            return ConditionClass("")

    def _convert_to_bytes(self, value, unit):
        """Convert a value from the given unit to bytes."""
        multipliers = {
            "Bytes": 1,
            "KB": 1024,
            "MB": 1024 * 1024,
            "GB": 1024 * 1024 * 1024,
        }
        return int(value * multipliers.get(unit, 1))
