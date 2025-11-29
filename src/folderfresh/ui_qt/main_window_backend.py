"""
MainWindow Backend Integration
Connects MainWindow to UndoManager and file processing
"""

from typing import List, Optional, Dict
from pathlib import Path

from PySide6.QtCore import Signal, QTimer, QObject

from folderfresh.undo_manager import UNDO_MANAGER
from folderfresh.activity_log import log_activity
from folderfresh.ui_qt.dialogs import (
    show_confirmation_dialog,
    show_error_dialog,
    show_info_dialog
)
from folderfresh.logger_qt import log_info, log_error, log_warning


class MainWindowBackend(QObject):
    """
    Backend integration for MainWindow.
    Handles undo/redo operations and state management.
    """

    # Signals
    undo_state_changed = Signal(bool, str)  # enabled, button_text
    undo_history_updated = Signal(list)  # history
    preview_generated = Signal(list)  # preview results (list of moves)
    organize_completed = Signal(list)  # organize results (list of moves)

    def __init__(self, check_interval: int = 500):
        """
        Initialize MainWindow backend

        Args:
            check_interval: Interval to check undo state (ms)
        """
        super().__init__()
        self.undo_manager = UNDO_MANAGER
        self.last_history_count = 0

        # Setup state check timer
        self.state_check_timer = QTimer()
        self.state_check_timer.timeout.connect(self._check_undo_state)
        self.state_check_timer.start(check_interval)

        log_info("MainWindowBackend initialized")

    def get_undo_history(self) -> List[Dict]:
        """Get undo history (newest first)"""
        return self.undo_manager.get_history()

    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.undo_manager.get_history()) > 0

    def get_undo_button_state(self) -> tuple:
        """
        Get undo button state

        Returns:
            (enabled, text) tuple
        """
        history = self.get_undo_history()

        if history:
            last_action = history[0]
            action_type = last_action.get("type", "").capitalize()
            src = last_action.get("src", last_action.get("old_name", ""))

            button_text = f"Undo {action_type}"
            tooltip = f"Undo: {src}"

            return True, button_text, tooltip
        else:
            return False, "Undo Last", "No actions to undo"

    def _check_undo_state(self) -> None:
        """Check if undo state changed and emit signal"""
        history = self.get_undo_history()
        current_count = len(history)

        if current_count != self.last_history_count:
            self.last_history_count = current_count
            enabled, text, _ = self.get_undo_button_state()
            self.undo_state_changed.emit(enabled, text)
            self.undo_history_updated.emit(history)

    def perform_undo(self) -> bool:
        """
        Perform undo operation

        Returns:
            True if successful
        """
        try:
            history = self.get_undo_history()
            if not history:
                show_info_dialog(None, "No Actions", "No actions to undo")
                return False

            result = self.undo_manager.undo_last()

            if result.get("success"):
                action_type = result.get("type", "").capitalize()
                src = result.get("src", result.get("old_name", ""))
                dst = result.get("dst", result.get("new_name", ""))

                message = f"Undid {action_type}:\n{src}"
                if dst:
                    message += f"\n→ {dst}"

                show_info_dialog(None, "Undo Successful", message)
                log_activity(f"Undo: {action_type} - {src}")
                log_info(f"Undo successful: {result.get('status')}")

                # Update button state
                enabled, text, _ = self.get_undo_button_state()
                self.undo_state_changed.emit(enabled, text)

                return True
            else:
                error_msg = result.get("error", "Unknown error")
                show_error_dialog(None, "Undo Failed", f"Undo failed:\n{error_msg}")
                log_warning(f"Undo failed: {error_msg}")
                return False

        except Exception as e:
            log_error(f"Exception during undo: {e}")
            show_error_dialog(None, "Undo Error", f"Error during undo:\n{e}")
            return False

    def get_undo_description(self, history_index: int = 0) -> str:
        """
        Get description of undo action

        Args:
            history_index: Index in history (0 = most recent)

        Returns:
            Description string
        """
        history = self.get_undo_history()

        if history_index >= len(history):
            return "No actions to undo"

        action = history[history_index]
        action_type = action.get("type", "unknown").capitalize()
        src = action.get("src", action.get("old_name", "Unknown"))

        return f"{action_type}: {src}"

    def clear_undo_history(self) -> bool:
        """
        Clear undo history

        Returns:
            True if successful
        """
        try:
            if not show_confirmation_dialog(
                None,
                "Clear Undo History",
                "Clear all undo history?\nThis cannot be undone."
            ):
                return False

            self.undo_manager.clear_history()

            log_info("Undo history cleared")
            self.undo_history_updated.emit([])

            # Update button state
            enabled, text, _ = self.get_undo_button_state()
            self.undo_state_changed.emit(enabled, text)

            return True

        except Exception as e:
            log_error(f"Failed to clear undo history: {e}")
            show_error_dialog(None, "Clear History Failed", f"Failed to clear history:\n{e}")
            return False

    def record_operation(
        self,
        operation_type: str,
        src: str,
        dst: str = None,
        old_name: str = None,
        new_name: str = None
    ) -> bool:
        """
        Record an operation for undo

        Args:
            operation_type: "move", "rename", "copy", "delete"
            src: Source path
            dst: Destination path
            old_name: Old name (for rename)
            new_name: New name (for rename)

        Returns:
            True if recorded
        """
        try:
            entry = {
                "type": operation_type,
                "src": src,
                "dst": dst,
                "old_name": old_name,
                "new_name": new_name,
                "collision_handled": False,
                "was_dry_run": False,
                "status": "recorded"
            }

            self.undo_manager.record_action(entry)

            log_info(f"Operation recorded: {operation_type} - {src}")
            self._check_undo_state()

            return True

        except Exception as e:
            log_error(f"Failed to record operation: {e}")
            return False

    def get_undo_menu_items(self, max_items: int = 10) -> List[str]:
        """
        Get undo menu items

        Args:
            max_items: Maximum items to return

        Returns:
            List of undo descriptions
        """
        history = self.get_undo_history()
        items = []

        for i in range(min(max_items, len(history))):
            items.append(self.get_undo_description(i))

        return items

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.state_check_timer:
            self.state_check_timer.stop()
            log_info("MainWindowBackend cleanup complete")

    # ========== PREVIEW & ORGANIZE ==========

    def generate_preview(
        self,
        folder: Path,
        config_data: Dict,
        include_subfolders: bool = True,
        skip_hidden: bool = True,
        smart_mode: bool = False
    ) -> List[Dict]:
        """
        Generate preview of file organization moves.

        Args:
            folder: Folder to scan
            config_data: Configuration dictionary
            include_subfolders: Include subdirectories
            skip_hidden: Skip hidden files
            smart_mode: Use smart categorization

        Returns:
            List of move operations ({"src": str, "dst": str, "mode": str, ...})
        """
        try:
            from folderfresh.actions import do_preview

            # Create a simple object that mimics the old app structure
            class PreviewApp:
                def __init__(self, folder, config, include_sub, skip_hidden, smart):
                    self.selected_folder = folder
                    self.config_data = config
                    self.include_sub = type('obj', (object,), {'get': lambda self: include_sub})()
                    self.skip_hidden = type('obj', (object,), {'get': lambda self: skip_hidden})()
                    self.smart_mode = type('obj', (object,), {'get': lambda self: smart})()

            app = PreviewApp(folder, config_data, include_subfolders, skip_hidden, smart_mode)
            moves = do_preview(app)

            log_info(f"Preview generated: {len(moves)} moves")
            self.preview_generated.emit(moves)

            return moves

        except Exception as e:
            import traceback
            log_error(f"Failed to generate preview: {e}")
            log_error(f"Traceback: {traceback.format_exc()}")
            show_error_dialog(None, "Preview Error", f"Failed to generate preview:\n{str(e)}")
            return []

    def execute_organize(
        self,
        folder: Path,
        moves: List[Dict],
        config_data: Dict,
        safe_mode: bool = True,
        smart_mode: bool = False
    ) -> List[Dict]:
        """
        Execute file organization based on preview moves.

        Args:
            folder: Folder being organized
            moves: List of move operations from preview
            config_data: Configuration dictionary
            safe_mode: Use copy instead of move
            smart_mode: Use smart categorization

        Returns:
            List of completed operations with results
        """
        try:
            from folderfresh.actions import do_organise

            # Create a simple object that mimics the old app structure
            class OrganizeApp:
                def __init__(self, folder, config, safe, smart):
                    self.selected_folder = folder
                    self.config_data = config
                    self.safe_mode = type('obj', (object,), {'get': lambda self: safe})()
                    self.smart_mode = type('obj', (object,), {'get': lambda self: smart})()

            app = OrganizeApp(folder, config_data, safe_mode, smart_mode)
            results = do_organise(app, moves)

            log_info(f"Organization completed: {len(results)} operations")
            self.organize_completed.emit(results)

            # Record operations in undo manager
            for result in results:
                if result.get("mode") == "sort" and not result.get("skipped"):
                    self.undo_manager.record_action({
                        "type": "move" if not safe_mode else "copy",
                        "src": result.get("src", ""),
                        "dst": result.get("dst", ""),
                        "status": "completed" if not result.get("error") else "failed",
                        "error": result.get("error", "")
                    })

            return results

        except Exception as e:
            log_error(f"Failed to execute organize: {e}")
            show_error_dialog(None, "Organize Error", f"Failed to execute organize:\n{str(e)}")
            return []
