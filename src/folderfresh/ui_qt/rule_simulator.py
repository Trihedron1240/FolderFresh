"""
PySide6 rule simulator dialog for FolderFresh.
Test rules on sample files before executing them.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal

from .styles import Colors, Fonts
from .base_widgets import (
    StyledButton,
    StyledLabel,
    StyledTextEdit,
    HeadingLabel,
    MutedLabel,
    VerticalFrame,
    HorizontalFrame,
    CardFrame,
)
from .dialogs import browse_file_dialog

# Import rule engine components
from folderfresh.rule_engine.rule_store import ACTION_MAP, CONDITION_MAP, ACTION_DISPLAY_NAME_TO_INTERNAL
from folderfresh.rule_engine.tier1_actions import expand_tokens


class RuleSimulator(QDialog):
    """Dialog for simulating rule execution on test files."""

    # Signals
    closed = Signal()

    def __init__(self, parent=None, rule_name: str = "Rule"):
        """
        Initialize rule simulator.

        Args:
            parent: Parent widget
            rule_name: Name of the rule being simulated
        """
        super().__init__(parent)
        self.setWindowTitle(f"Simulate: {rule_name}")
        self.setGeometry(200, 200, 700, 600)
        self.setMinimumSize(600, 500)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.PANEL_BG}; }}")
        self.setModal(True)

        self.rule_name = rule_name
        self.test_file_path: Optional[Path] = None
        self.rule_data: Optional[Dict[str, Any]] = None

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = HeadingLabel(f"Simulate: {self.rule_name}")
        main_layout.addWidget(title)

        # File selection section
        file_frame = VerticalFrame(spacing=8)
        file_label = StyledLabel("Test File:", font_size=Fonts.SIZE_NORMAL, bold=True)
        file_frame.add_widget(file_label)

        file_row = HorizontalFrame(spacing=8)
        self.file_display = StyledLabel(
            "(No file selected)",
            font_size=Fonts.SIZE_NORMAL,
        )
        self.file_display.setWordWrap(True)
        file_row.add_widget(self.file_display, 1)

        browse_btn = StyledButton("Browse...", bg_color=Colors.ACCENT)
        browse_btn.setMaximumWidth(100)
        browse_btn.clicked.connect(self._on_browse_file)
        file_row.add_widget(browse_btn)

        file_frame.add_widget(file_row)
        main_layout.addWidget(file_frame)

        # Rule info section
        info_frame = VerticalFrame(spacing=8)
        info_label = StyledLabel("Rule Info:", font_size=Fonts.SIZE_NORMAL, bold=True)
        info_frame.add_widget(info_label)

        self.info_display = MutedLabel("(Rule information will appear here)")
        self.info_display.setWordWrap(True)
        info_frame.add_widget(self.info_display)

        main_layout.addWidget(info_frame)

        # Results section
        results_frame = VerticalFrame(spacing=8)
        results_label = StyledLabel("Simulation Results:", font_size=Fonts.SIZE_NORMAL, bold=True)
        results_frame.add_widget(results_label)

        self.results_text = StyledTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlainText("(No simulation run yet)\n\nSelect a file and click 'Run Simulation' to test the rule.")
        self.results_text.setMinimumHeight(200)
        results_frame.add_widget(self.results_text)

        main_layout.addWidget(results_frame)

        # Buttons
        button_frame = HorizontalFrame(spacing=8)

        simulate_btn = StyledButton("Run Simulation", bg_color=Colors.SUCCESS)
        simulate_btn.clicked.connect(self._on_run_simulation)
        button_frame.add_widget(simulate_btn)

        button_frame.add_stretch()

        close_btn = StyledButton("Close", bg_color=Colors.BORDER_LIGHT)
        close_btn.clicked.connect(self.accept)
        button_frame.add_widget(close_btn)

        main_layout.addWidget(button_frame)

    def _on_browse_file(self) -> None:
        """Open file browser dialog."""
        file_path = browse_file_dialog(
            self,
            title="Select File for Simulation",
        )

        if file_path:
            self.test_file_path = file_path
            self.file_display.setText(str(file_path))

    def _on_run_simulation(self) -> None:
        """Run simulation on selected file."""
        if not self.test_file_path:
            self.results_text.setPlainText("ERROR: No file selected. Please browse for a file first.")
            return

        # Simulate rule execution
        results = self._simulate_rule_on_file(self.test_file_path)
        self.results_text.setPlainText(results)

    def _simulate_rule_on_file(self, file_path: Path) -> str:
        """
        Simulate rule execution on a file.

        Args:
            file_path: File to simulate on

        Returns:
            Simulation results text
        """
        if not self.rule_data:
            return "ERROR: No rule data available for simulation."

        try:
            results_lines = []

            # File info header
            try:
                stat_info = file_path.stat()
                size_bytes = stat_info.st_size
                size_readable = self._format_size(size_bytes)
            except Exception as e:
                return f"ERROR: Could not read file information:\n{e}"

            results_lines.append(f"File: {file_path.name}")
            results_lines.append(f"Path: {file_path}")
            results_lines.append(f"Size: {size_readable} ({size_bytes} bytes)")
            results_lines.append("")

            # Build fileinfo dict from the file
            fileinfo = self._build_fileinfo(file_path)

            # Evaluate conditions
            results_lines.append("Condition Matches:")
            conditions = self.rule_data.get("conditions", [])
            match_mode = self.rule_data.get("match_mode", "all")

            matched_conditions = []
            for i, condition_data in enumerate(conditions):
                cond_type = condition_data.get("type", "Unknown")
                cond_args = condition_data.get("args", {})

                try:
                    # Get the condition class and evaluate
                    if cond_type in CONDITION_MAP:
                        condition_class = CONDITION_MAP[cond_type]
                        condition = condition_class(**cond_args)
                        matches = condition.evaluate(fileinfo)
                        matched_conditions.append(matches)

                        # Format condition display
                        cond_display = self._format_condition_display(cond_type, cond_args)
                        symbol = "✓" if matches else "✗"
                        results_lines.append(f"  {symbol} {cond_display}")
                    else:
                        results_lines.append(f"  ? {cond_type} (unknown)")
                except Exception as e:
                    results_lines.append(f"  ? {cond_type} (error: {str(e)[:40]})")

            # Check if rule applies based on match_mode
            if match_mode == "all":
                rule_applies = all(matched_conditions) if matched_conditions else False
            elif match_mode == "any":
                rule_applies = any(matched_conditions) if matched_conditions else False
            else:
                rule_applies = False

            results_lines.append("")

            # Show actions if rule applies
            if rule_applies:
                results_lines.append("Actions to Execute:")
                actions = self.rule_data.get("actions", [])

                for i, action_data in enumerate(actions, 1):
                    action_type = action_data.get("type", "Unknown")
                    action_args = action_data.get("args", {})

                    try:
                        # Get the action class and simulate
                        if action_type in ACTION_MAP:
                            action_class = ACTION_MAP[action_type]
                            action = action_class(**action_args)

                            # Format action display with simulation
                            action_display = self._format_action_display(action_type, action_args, fileinfo)
                            results_lines.append(f"  {i}. {action_display}")
                        else:
                            results_lines.append(f"  {i}. {action_type} (unknown)")
                    except Exception as e:
                        results_lines.append(f"  {i}. {action_type} (error: {str(e)[:40]})")

                results_lines.append("")
                results_lines.append("Summary:")
                results_lines.append("  ✓ Rule APPLIES to this file")
                results_lines.append("  ℹ This is a dry-run simulation (no files will be modified)")
            else:
                results_lines.append("Summary:")
                results_lines.append("  ✗ Rule does NOT apply to this file")
                results_lines.append(f"  Match mode is '{match_mode}' but conditions do not match")

            return "\n".join(results_lines)

        except Exception as e:
            return f"ERROR: Simulation failed:\n{str(e)}"

    def _build_fileinfo(self, file_path: Path) -> Dict[str, Any]:
        """Build fileinfo dict from a file path."""
        try:
            stat_info = file_path.stat()
            filename = file_path.name
            name_without_ext = file_path.stem
            extension = file_path.suffix  # includes the dot

            from datetime import datetime
            created_time = datetime.fromtimestamp(stat_info.st_ctime)
            modified_time = datetime.fromtimestamp(stat_info.st_mtime)

            return {
                "name": filename,
                "path": str(file_path),
                "ext": extension,
                "size": stat_info.st_size,
                "created_at": created_time.isoformat(),
                "modified_at": modified_time.isoformat(),
                "stat": stat_info,
            }
        except Exception:
            return {
                "name": file_path.name,
                "path": str(file_path),
                "ext": file_path.suffix,
                "size": 0,
            }

    def _format_condition_display(self, cond_type: str, args: Dict[str, Any]) -> str:
        """Format condition for display."""
        if cond_type == "NameContains":
            return f"Name Contains '{args.get('substring', '')}'"
        elif cond_type == "NameStartsWith":
            return f"Name Starts With '{args.get('prefix', '')}'"
        elif cond_type == "NameEndsWith":
            return f"Name Ends With '{args.get('suffix', '')}'"
        elif cond_type == "NameEquals":
            return f"Name Equals '{args.get('name', '')}'"
        elif cond_type == "ExtensionIs":
            return f"Extension Is '{args.get('extension', '')}'"
        elif cond_type == "FileSizeGreaterThan":
            size = args.get('size_bytes', 0)
            return f"File Size > {self._format_size(size)}"
        elif cond_type == "FileAgeGreaterThan":
            days = args.get('days', 0)
            return f"File Age > {days} days"
        elif cond_type == "IsHidden":
            return "Is Hidden"
        elif cond_type == "IsReadOnly":
            return "Is Read-Only"
        elif cond_type == "IsDirectory":
            return "Is Directory"
        else:
            return cond_type

    def _format_action_display(self, action_type: str, args: Dict[str, Any], fileinfo: Dict[str, Any]) -> str:
        """Format action for display with simulated output."""
        try:
            if action_type == "Rename":
                new_name = args.get("new_name", "")
                return f"Rename File to: {new_name}"

            elif action_type == "TokenRename":
                pattern = args.get("name_pattern", "")
                expanded = expand_tokens(pattern, fileinfo)
                return f"Rename with Tokens: {pattern} → {expanded}"

            elif action_type == "Move":
                target_dir = args.get("target_dir", "")
                # Expand tokens if present
                if "<" in target_dir and ">" in target_dir:
                    expanded_dir = expand_tokens(target_dir, fileinfo)
                    return f"Move to Folder: {target_dir} → {expanded_dir}"
                else:
                    return f"Move to Folder: {target_dir}"

            elif action_type == "Copy":
                target_dir = args.get("target_dir", "")
                # Expand tokens if present
                if "<" in target_dir and ">" in target_dir:
                    expanded_dir = expand_tokens(target_dir, fileinfo)
                    return f"Copy to Folder: {target_dir} → {expanded_dir}"
                else:
                    return f"Copy to Folder: {target_dir}"

            elif action_type == "Delete":
                return "Delete File (PERMANENT)"

            elif action_type == "DeleteToTrash":
                return "Delete to Trash"

            elif action_type == "RunCommand":
                command = args.get("command", "")
                # Expand the command with actual file values for preview
                expanded_command = expand_tokens(command, fileinfo) if "<" in command else command

                # Replace curly brace placeholders for display preview
                file_path = fileinfo.get("path", "")
                if file_path:
                    from pathlib import Path
                    file_path_obj = Path(file_path)
                    expanded_command = expanded_command.replace("{file}", str(file_path))
                    expanded_command = expanded_command.replace("{dir}", str(file_path_obj.parent))
                    expanded_command = expanded_command.replace("{name}", file_path_obj.stem)
                    expanded_command = expanded_command.replace("{ext}", file_path_obj.suffix)
                    expanded_command = expanded_command.replace("{basename}", file_path_obj.name)

                # Truncate for display if too long
                if len(expanded_command) > 80:
                    display_command = expanded_command[:80] + "..."
                else:
                    display_command = expanded_command

                return f"Run Command: {display_command}\n  Supported placeholders: {{file}}, {{dir}}, {{name}}, {{ext}}, {{basename}}"

            elif action_type == "Archive":
                archive_path = args.get("archive_path", "")
                return f"Archive to ZIP: {archive_path}"

            elif action_type == "Extract":
                extract_path = args.get("extract_path", "")
                return f"Extract Archive to: {extract_path}"

            elif action_type == "CreateFolder":
                folder_name = args.get("folder_name", "")
                expanded = expand_tokens(folder_name, fileinfo)
                return f"Create Folder: {expanded}"

            elif action_type == "AddTag":
                tag = args.get("tag", "")
                return f"Add Tag: {tag}"

            elif action_type == "RemoveTag":
                tag = args.get("tag", "")
                return f"Remove Tag: {tag}"

            elif action_type == "ColorLabel":
                color = args.get("color", "")
                return f"Set Color Label: {color}"

            elif action_type == "MarkAsDuplicate":
                method = args.get("method", "")
                return f"Mark as Duplicate: {method}"

            else:
                return action_type
        except Exception as e:
            return f"{action_type} (error: {str(e)[:30]})"

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}".rstrip("0").rstrip(".")
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def set_rule_info(self, rule_data: Dict[str, Any]) -> None:
        """
        Set rule information for display.

        Args:
            rule_data: Rule data dictionary
        """
        self.rule_data = rule_data
        conditions_count = len(rule_data.get("conditions", []))
        actions_count = len(rule_data.get("actions", []))
        match_mode = rule_data.get("match_mode", "all")

        info_text = (
            f"Conditions: {conditions_count} (match mode: {match_mode})\n"
            f"Actions: {actions_count}"
        )

        self.info_display.setText(info_text)

    def closeEvent(self, event):
        """Handle window close event."""
        self.closed.emit()
        self.accept()
        event.accept()
