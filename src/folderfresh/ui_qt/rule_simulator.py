"""
PySide6 rule simulator dialog for FolderFresh.
Test rules on sample files before executing them.
"""

from pathlib import Path
from typing import Optional, Dict, Any

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
        # TODO: Integrate with actual rule engine for real simulation
        # For now, return placeholder results

        results_lines = [
            f"File: {file_path.name}",
            f"Path: {file_path}",
            f"Size: {file_path.stat().st_size} bytes",
            "",
            "Condition Matches:",
            "  ✓ Name Contains 'test'",
            "  ✓ File Size > 1MB",
            "  ✓ File Age > 7 days",
            "",
            "Actions to Execute:",
            "  1. Move to Folder: C:\\Archive\\Old Files",
            "  2. Add Tag: archived",
            "",
            "Summary:",
            "  File would be MOVED to C:\\Archive\\Old Files",
            "  This is a SAFE operation (file will be moved, not deleted)",
        ]

        return "\n".join(results_lines)

    def set_rule_info(self, rule_data: Dict[str, Any]) -> None:
        """
        Set rule information for display.

        Args:
            rule_data: Rule data dictionary
        """
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
