# rule_editor.py

import customtkinter as ctk
from folderfresh.rule_engine import Rule
from folderfresh.condition_editor import ConditionEditor
from folderfresh.action_editor import ActionEditor


class RuleEditor:
    """
    Reusable Rule Editor component for editing rules in embedded frames.

    Properties edited:
    - name
    - match_mode ("all" or "any")
    - stop_on_match (bool)
    - conditions (list)
    - actions (list)

    For popup editing, use RuleEditorPopup which wraps this component.
    """

    def __init__(self, master, rule: Rule, save_callback=None):
        """
        Initialize RuleEditor in embedded mode.

        Args:
            master: Parent frame widget
            rule: Rule object to edit
            save_callback: Called after any change (for live updates)
        """
        self.rule = rule
        self.save_callback = save_callback
        self.container = master
        self.main_widget = master

        # Track selected condition and action for deletion
        self.selected_condition_index = None
        self.condition_row_frames = []
        self.selected_action_index = None
        self.action_row_frames = []

        self._build_ui(master)

    def _build_ui(self, parent):
        """Build the UI components inside parent frame."""
        # Build directly in the provided parent (which may be a scrollable frame)
        content_parent = parent

        # Name field
        name_frame = ctk.CTkFrame(content_parent, corner_radius=10)
        name_frame.pack(fill="x", padx=15, pady=8)

        name_label = ctk.CTkLabel(
            name_frame,
            text="Rule Name:",
            font=("Arial", 12)
        )
        name_label.pack(anchor="w", padx=10, pady=(8, 0))

        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Enter rule name"
        )
        self.name_entry.insert(0, self.rule.name)
        self.name_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Bind to live update (both popup and embedded auto-save)
        self.name_entry.bind("<KeyRelease>", lambda _: self._on_field_change())

        # Match mode dropdown with explanation
        mode_frame = ctk.CTkFrame(content_parent, corner_radius=10)
        mode_frame.pack(fill="x", padx=15, pady=8)

        mode_label = ctk.CTkLabel(
            mode_frame,
            text="Match Mode:",
            font=("Arial", 12)
        )
        mode_label.pack(anchor="w", padx=10, pady=(8, 0))

        self.mode_option = ctk.CTkOptionMenu(
            mode_frame,
            values=["all", "any"],
            command=lambda _: self._on_field_change()
        )
        self.mode_option.set(self.rule.match_mode)
        self.mode_option.pack(fill="x", padx=10, pady=(0, 5))

        # Match mode explanation
        mode_help_text = (
            "ALL = Match ALL conditions (AND) - run actions only if every condition is true\n"
            "ANY = Match ANY condition (OR) - run actions if at least one condition is true"
        )
        mode_help = ctk.CTkLabel(
            mode_frame,
            text=mode_help_text,
            font=("Arial", 9),
            text_color=("gray60", "gray40"),
            justify="left"
        )
        mode_help.pack(anchor="w", padx=10, pady=(0, 10), fill="x")

        # Stop-on-match checkbox
        check_frame = ctk.CTkFrame(content_parent, corner_radius=10)
        check_frame.pack(fill="x", padx=15, pady=8)

        self.stop_var = ctk.BooleanVar(value=self.rule.stop_on_match)
        self.stop_check = ctk.CTkCheckBox(
            check_frame,
            text="Stop processing other rules when this rule matches",
            variable=self.stop_var,
            command=lambda: self._on_field_change(),
            font=("Arial", 11)
        )
        self.stop_check.pack(anchor="w", padx=10, pady=10)

        # Separator
        sep = ctk.CTkFrame(content_parent, height=1, fg_color=("gray70", "gray30"))
        sep.pack(fill="x", padx=15, pady=10)

        # Conditions Section
        cond_frame = ctk.CTkFrame(content_parent, corner_radius=10)
        cond_frame.pack(fill="both", padx=15, pady=8, expand=True)

        cond_label = ctk.CTkLabel(
            cond_frame,
            text="Conditions:",
            font=("Arial", 13, "bold")
        )
        cond_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Conditions list (scrollable container with interactive rows)
        self.cond_list_scroll = ctk.CTkScrollableFrame(
            cond_frame,
            corner_radius=8,
            fg_color=("gray90", "gray20")
        )
        self.cond_list_scroll.pack(fill="both", padx=10, pady=(0, 8), expand=True)

        # Will hold condition row frames
        self.cond_list_container = self.cond_list_scroll

        # Buttons for conditions
        cond_btn_frame = ctk.CTkFrame(cond_frame, fg_color="transparent")
        cond_btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.add_cond_btn = ctk.CTkButton(
            cond_btn_frame,
            text="+ Add Condition",
            command=self.add_condition,
            fg_color=("#3a7bd5", "#1f6aa5"),
            font=("Arial", 11)
        )
        self.add_cond_btn.pack(side="left", padx=5)

        self.del_cond_btn = ctk.CTkButton(
            cond_btn_frame,
            text="- Delete Condition",
            command=self.delete_condition,
            fg_color=("#d73336", "#b83a3e"),
            font=("Arial", 11)
        )
        self.del_cond_btn.pack(side="left", padx=5)

        # Actions Section
        action_frame = ctk.CTkFrame(content_parent, corner_radius=10)
        action_frame.pack(fill="both", padx=15, pady=8, expand=True)

        action_label = ctk.CTkLabel(
            action_frame,
            text="Actions:",
            font=("Arial", 13, "bold")
        )
        action_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Actions list (scrollable container with interactive rows)
        self.action_list_scroll = ctk.CTkScrollableFrame(
            action_frame,
            corner_radius=8,
            fg_color=("gray90", "gray20")
        )
        self.action_list_scroll.pack(fill="both", padx=10, pady=(0, 8), expand=True)

        # Will hold action row frames
        self.action_list_container = self.action_list_scroll

        # Buttons for actions
        action_btn_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        action_btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.add_action_btn = ctk.CTkButton(
            action_btn_frame,
            text="+ Add Action",
            command=self.add_action,
            fg_color=("#3a7bd5", "#1f6aa5"),
            font=("Arial", 11)
        )
        self.add_action_btn.pack(side="left", padx=5)

        self.del_action_btn = ctk.CTkButton(
            action_btn_frame,
            text="- Delete Action",
            command=self.delete_action,
            fg_color=("#d73336", "#b83a3e"),
            font=("Arial", 11)
        )
        self.del_action_btn.pack(side="left", padx=5)

        # Add simulator button for popup mode

        sim_btn = ctk.CTkButton(
            content_parent,
            text="Simulate Rule",
            command=self.simulate_rule,
            fg_color=("#2a5f2e", "#4a8f4e"),
            font=("Arial", 11)
            )
        sim_btn.pack(pady=(10, 0), padx=15)

        # Refresh list displays
        self.refresh_conditions()
        self.refresh_actions()

    def _on_field_change(self):
        """Called when any field changes. Saves if rule is valid."""
        self._apply_changes()
        # Only save if the rule is valid
        if RuleEditor.rule_is_valid(self.rule) and self.save_callback:
            self.save_callback()

    def _apply_changes(self):
        """Apply current UI values to the rule object."""
        self.rule.name = self.name_entry.get()
        self.rule.match_mode = self.mode_option.get()
        self.rule.stop_on_match = self.stop_var.get()

    def refresh(self):
        """Refresh all UI fields from current rule state. Used when switching between rules."""
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, self.rule.name)
        self.mode_option.set(self.rule.match_mode)
        self.stop_var.set(self.rule.stop_on_match)
        self.refresh_conditions()
        self.refresh_actions()

    def refresh_actions(self):
        """Update action list with interactive, selectable rows."""
        # Clear old action rows
        for child in self.action_list_container.winfo_children():
            child.destroy()

        self.action_row_frames = []

        if not self.rule.actions:
            # Show empty state
            empty_label = ctk.CTkLabel(
                self.action_list_container,
                text="(No actions yet)",
                font=("Arial", 10),
                text_color=("gray60", "gray40")
            )
            empty_label.pack(fill="x", padx=8, pady=8)
            return

        # Build interactive action rows
        for i, act in enumerate(self.rule.actions):
            action_type = act.__class__.__name__.replace("Action", "")
            params = ", ".join(f"{k}={v}" for k, v in act.__dict__.items())
            display_text = f"{i+1}. {action_type}({params})"

            # Create action row frame
            row = ctk.CTkFrame(
                self.action_list_container,
                corner_radius=6,
                fg_color=("gray85", "gray25") if i != self.selected_action_index else ("#2a4f7a", "#1d3a5a"),
                border_width=1 if i == self.selected_action_index else 0,
                border_color=("#3a7bd5", "#1f6aa5") if i == self.selected_action_index else None
            )
            row.pack(fill="x", padx=6, pady=4)

            # Create label inside row
            label = ctk.CTkLabel(
                row,
                text=display_text,
                font=("Courier", 10),
                text_color="white" if i == self.selected_action_index else ("black", "white"),
                anchor="w"
            )
            label.pack(fill="x", padx=10, pady=8)

            # Bind click events to select this action
            def make_click_handler(idx):
                return lambda e: self.select_action(idx)

            def make_hover_enter_handler(idx, row_ref):
                return lambda e: self.on_action_hover(idx, row_ref)

            def make_hover_leave_handler(idx, row_ref):
                return lambda e: self.on_action_leave(idx, row_ref)

            row.bind("<Button-1>", make_click_handler(i))
            label.bind("<Button-1>", make_click_handler(i))

            # Bind hover events (but only if not already selected)
            row.bind("<Enter>", make_hover_enter_handler(i, row))
            row.bind("<Leave>", make_hover_leave_handler(i, row))

            self.action_row_frames.append(row)

    def add_action(self):
        """Open ActionEditor popup to add a new action."""
        # Get the toplevel window for the popup
        parent_window = self.container.winfo_toplevel()
        ActionEditor(parent_window, callback=self.on_action_added)

    def on_action_added(self, action_obj):
        """Callback when a new action is added."""
        self.rule.actions.append(action_obj)
        self.refresh_actions()
        # Only save if the complete rule is now valid
        if RuleEditor.rule_is_valid(self.rule) and self.save_callback:
            self.save_callback()

    def select_action(self, index):
        """Select an action by index and highlight it."""
        self.selected_action_index = index
        self.refresh_actions()

    def on_action_hover(self, index, row):
        """Handle mouse hover on an action row."""
        if index != self.selected_action_index:
            row.configure(fg_color=("gray80", "gray35"))

    def on_action_leave(self, index, row):
        """Handle mouse leave on an action row."""
        if index != self.selected_action_index:
            row.configure(fg_color=("gray85", "gray25"))

    def delete_action(self):
        """Delete the selected action from the list."""
        if self.selected_action_index is None:
            from tkinter import messagebox
            messagebox.showinfo("No Selection", "Please select an action to delete.")
            return

        index = self.selected_action_index
        self.rule.actions.pop(index)
        self.selected_action_index = None
        self.refresh_actions()

        # Only save if the complete rule is still valid
        if RuleEditor.rule_is_valid(self.rule) and self.save_callback:
            self.save_callback()

    def refresh_conditions(self):
        """Update condition list with interactive, selectable rows."""
        # Clear old condition rows
        for child in self.cond_list_container.winfo_children():
            child.destroy()

        self.condition_row_frames = []

        if not self.rule.conditions:
            # Show empty state
            empty_label = ctk.CTkLabel(
                self.cond_list_container,
                text="(No conditions yet)",
                font=("Arial", 10),
                text_color=("gray60", "gray40")
            )
            empty_label.pack(fill="x", padx=8, pady=8)
            return

        # Build interactive condition rows
        for i, cond in enumerate(self.rule.conditions):
            cond_type = cond.__class__.__name__.replace("Condition", "")

            # Format the condition display text
            if cond_type == "FileSizeGreaterThan":
                display_text = self._format_file_size_condition(cond, i + 1)
            else:
                params = ", ".join(f"{k}={v}" for k, v in cond.__dict__.items())
                display_text = f"{i+1}. {cond_type}({params})"

            # Create condition row frame
            row = ctk.CTkFrame(
                self.cond_list_container,
                corner_radius=6,
                fg_color=("gray85", "gray25") if i != self.selected_condition_index else ("#2a4f7a", "#1d3a5a"),
                border_width=1 if i == self.selected_condition_index else 0,
                border_color=("#3a7bd5", "#1f6aa5") if i == self.selected_condition_index else None
            )
            row.pack(fill="x", padx=6, pady=4)

            # Create label inside row
            label = ctk.CTkLabel(
                row,
                text=display_text,
                font=("Courier", 10),
                text_color="white" if i == self.selected_condition_index else ("black", "white"),
                anchor="w"
            )
            label.pack(fill="x", padx=10, pady=8)

            # Bind click events to select this condition
            def make_click_handler(idx):
                return lambda e: self.select_condition(idx)

            def make_hover_enter_handler(idx, row_ref):
                return lambda e: self.on_condition_hover(idx, row_ref)

            def make_hover_leave_handler(idx, row_ref):
                return lambda e: self.on_condition_leave(idx, row_ref)

            row.bind("<Button-1>", make_click_handler(i))
            label.bind("<Button-1>", make_click_handler(i))

            # Bind hover events (but only if not already selected)
            row.bind("<Enter>", make_hover_enter_handler(i, row))
            row.bind("<Leave>", make_hover_leave_handler(i, row))

            self.condition_row_frames.append(row)

    def _format_file_size_condition(self, cond, index):
        """Format file size condition with human-readable units."""
        min_bytes = cond.min_bytes

        # Determine the best unit
        if min_bytes >= 1024 * 1024 * 1024:
            size_value = min_bytes / (1024 * 1024 * 1024)
            unit = "GB"
        elif min_bytes >= 1024 * 1024:
            size_value = min_bytes / (1024 * 1024)
            unit = "MB"
        elif min_bytes >= 1024:
            size_value = min_bytes / 1024
            unit = "KB"
        else:
            size_value = min_bytes
            unit = "Bytes"

        # Format with appropriate decimal places
        if size_value == int(size_value):
            display_value = int(size_value)
        else:
            display_value = f"{size_value:.1f}".rstrip('0').rstrip('.')

        return f"{index}. FileSizeGreaterThan({display_value} {unit})"

    @staticmethod
    def rule_is_valid(rule) -> bool:
        """
        Check if a rule is valid and can be saved.

        A rule is valid if:
        - Name is not empty
        - Match mode is "all" or "any"
        - All conditions are fully formed
        - All actions are fully formed
        - Has at least one condition or action

        Returns:
            bool: True if rule is valid, False otherwise
        """
        # Check name
        if not rule.name or not str(rule.name).strip():
            return False

        # Check match mode
        if rule.match_mode not in ("all", "any"):
            return False

        # Check that rule has at least one condition or action
        if not rule.conditions and not rule.actions:
            return False

        # Validate all conditions
        for cond in rule.conditions:
            if not RuleEditor._condition_is_valid(cond):
                return False

        # Validate all actions
        for action in rule.actions:
            if not RuleEditor._action_is_valid(action):
                return False

        return True

    @staticmethod
    def _condition_is_valid(cond) -> bool:
        """Check if a condition object is fully formed."""
        cond_type = cond.__class__.__name__

        if cond_type == "NameContainsCondition":
            return hasattr(cond, "substring") and bool(cond.substring)
        elif cond_type == "ExtensionIsCondition":
            return hasattr(cond, "extension") and bool(cond.extension)
        elif cond_type == "FileSizeGreaterThanCondition":
            return hasattr(cond, "min_bytes") and isinstance(cond.min_bytes, int) and cond.min_bytes >= 0
        else:
            # Unknown condition type - assume invalid
            return False

    @staticmethod
    def _action_is_valid(action) -> bool:
        """Check if an action object is fully formed."""
        action_type = action.__class__.__name__

        if action_type == "RenameAction":
            return hasattr(action, "new_name") and bool(action.new_name)
        elif action_type == "MoveAction":
            return hasattr(action, "target_dir") and bool(action.target_dir)
        elif action_type == "CopyAction":
            return hasattr(action, "target_dir") and bool(action.target_dir)
        else:
            # Unknown action type - assume invalid
            return False

    def add_condition(self):
        """Open ConditionEditor popup to add a new condition."""
        # Get the toplevel window for the popup
        parent_window = self.container.winfo_toplevel()
        ConditionEditor(parent_window, callback=self.on_condition_added)

    def on_condition_added(self, condition_obj):
        """Callback when a new condition is added."""
        self.rule.conditions.append(condition_obj)
        self.refresh_conditions()
        # Only save if the complete rule is now valid
        if RuleEditor.rule_is_valid(self.rule) and self.save_callback:
            self.save_callback()

    def select_condition(self, index):
        """Select a condition by index and highlight it."""
        self.selected_condition_index = index
        self.refresh_conditions()

    def on_condition_hover(self, index, row):
        """Handle mouse hover on a condition row."""
        if index != self.selected_condition_index:
            row.configure(fg_color=("gray80", "gray35"))

    def on_condition_leave(self, index, row):
        """Handle mouse leave on a condition row."""
        if index != self.selected_condition_index:
            row.configure(fg_color=("gray85", "gray25"))

    def delete_condition(self):
        """Delete the selected condition from the list."""
        if self.selected_condition_index is None:
            from tkinter import messagebox
            messagebox.showinfo("No Selection", "Please select a condition to delete.")
            return

        index = self.selected_condition_index
        self.rule.conditions.pop(index)
        self.selected_condition_index = None
        self.refresh_conditions()

        # Only save if the complete rule is still valid
        if RuleEditor.rule_is_valid(self.rule) and self.save_callback:
            self.save_callback()

    def simulate_rule(self):
        """Open a dialog to simulate this rule against a test file."""
        from folderfresh.rule_simulator import RuleSimulator
        RuleSimulator(self.container, self.rule)
