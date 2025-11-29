"""
FolderFresh Qt Error Handler
Graceful error handling and user-friendly error reporting
"""

from typing import Callable, Optional
from PySide6.QtWidgets import QMessageBox
from folderfresh.logger_qt import log_error, log_warning, log_info, log_critical, log_debug


class QtErrorHandler:
    """Centralized error handling for PySide6 application"""

    @staticmethod
    def handle_file_operation_error(
        error: Exception,
        operation: str,
        file_path: str,
        parent=None,
        recovery_fn: Optional[Callable] = None
    ) -> bool:
        """
        Handle file operation errors with user feedback

        Args:
            error: Exception that occurred
            operation: Operation name (e.g., "organize", "move")
            file_path: File path involved
            parent: Parent widget
            recovery_fn: Optional recovery function to retry

        Returns:
            True if user chose to retry, False otherwise
        """
        error_msg = f"Error during {operation}:\n{file_path}\n\n{str(error)}"
        log_error(f"File operation failed: {operation} - {file_path}", exc_info=True)

        if recovery_fn:
            reply = QMessageBox.critical(
                parent,
                f"{operation.capitalize()} Failed",
                error_msg,
                QMessageBox.Retry | QMessageBox.Cancel
            )
            return reply == QMessageBox.Retry and recovery_fn()
        else:
            QMessageBox.critical(
                parent,
                f"{operation.capitalize()} Failed",
                error_msg,
                QMessageBox.Ok
            )
            return False

    @staticmethod
    def handle_rule_execution_error(
        error: Exception,
        rule_name: str,
        parent=None
    ) -> None:
        """
        Handle rule execution errors

        Args:
            error: Exception that occurred
            rule_name: Name of rule that failed
            parent: Parent widget
        """
        log_error(f"Rule execution failed: {rule_name}", exc_info=True)

        QMessageBox.warning(
            parent,
            "Rule Execution Failed",
            f"Rule '{rule_name}' failed:\n\n{str(error)}"
        )

    @staticmethod
    def handle_config_error(
        error: Exception,
        parent=None,
        recovery_fn: Optional[Callable] = None
    ) -> bool:
        """
        Handle configuration loading errors

        Args:
            error: Exception that occurred
            parent: Parent widget
            recovery_fn: Optional recovery function

        Returns:
            True if user chose to retry with recovery
        """
        log_error(f"Configuration error: {str(error)}", exc_info=True)

        if recovery_fn:
            reply = QMessageBox.critical(
                parent,
                "Configuration Error",
                f"Failed to load configuration:\n\n{str(error)}\n\nTry to recover?",
                QMessageBox.Yes | QMessageBox.No
            )
            return reply == QMessageBox.Yes and recovery_fn()
        else:
            QMessageBox.critical(
                parent,
                "Configuration Error",
                f"Failed to load configuration:\n\n{str(error)}"
            )
            return False

    @staticmethod
    def handle_folder_watch_error(
        error: Exception,
        folder_path: str,
        parent=None
    ) -> None:
        """
        Handle folder watching errors

        Args:
            error: Exception that occurred
            folder_path: Folder that couldn't be watched
            parent: Parent widget
        """
        log_warning(f"Failed to watch folder: {folder_path}", exc_info=True)

        QMessageBox.warning(
            parent,
            "Watch Error",
            f"Failed to watch folder:\n{folder_path}\n\n{str(error)}"
        )

    @staticmethod
    def handle_export_error(
        error: Exception,
        export_type: str,
        parent=None
    ) -> None:
        """
        Handle export operation errors

        Args:
            error: Exception that occurred
            export_type: Type of export (e.g., "log", "report")
            parent: Parent widget
        """
        log_error(f"Export failed ({export_type})", exc_info=True)

        QMessageBox.critical(
            parent,
            "Export Failed",
            f"Failed to export {export_type}:\n\n{str(error)}"
        )

    @staticmethod
    def handle_undo_error(
        error: Exception,
        parent=None
    ) -> None:
        """
        Handle undo operation errors

        Args:
            error: Exception that occurred
            parent: Parent widget
        """
        log_error("Undo operation failed", exc_info=True)

        QMessageBox.critical(
            parent,
            "Undo Failed",
            f"Failed to undo last action:\n\n{str(error)}\n\n"
            "Files may be in an inconsistent state."
        )

    @staticmethod
    def handle_validation_error(
        error: str,
        field_name: str,
        parent=None
    ) -> None:
        """
        Handle validation errors

        Args:
            error: Error message
            field_name: Name of field that failed validation
            parent: Parent widget
        """
        log_warning(f"Validation failed: {field_name} - {error}")

        QMessageBox.warning(
            parent,
            "Validation Error",
            f"Invalid {field_name}:\n\n{error}"
        )

    @staticmethod
    def handle_fatal_error(
        error: Exception,
        parent=None
    ) -> None:
        """
        Handle fatal/critical errors

        Args:
            error: Exception that occurred
            parent: Parent widget
        """
        log_critical(f"Fatal error: {str(error)}", exc_info=True)

        QMessageBox.critical(
            parent,
            "Fatal Error",
            f"A critical error occurred:\n\n{str(error)}\n\n"
            "The application will exit."
        )

    @staticmethod
    def show_info(
        title: str,
        message: str,
        parent=None
    ) -> None:
        """Show info message"""
        log_info(f"{title}: {message}")
        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_warning(
        title: str,
        message: str,
        parent=None
    ) -> None:
        """Show warning message"""
        log_warning(f"{title}: {message}")
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_error(
        title: str,
        message: str,
        parent=None
    ) -> None:
        """Show error message"""
        log_error(f"{title}: {message}")
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def ask_confirmation(
        title: str,
        message: str,
        parent=None
    ) -> bool:
        """
        Ask for user confirmation

        Returns:
            True if user confirmed
        """
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        return reply == QMessageBox.Yes


# Convenience functions
def handle_error(error: Exception, context: str = "Operation", parent=None) -> None:
    """Handle generic error"""
    QtErrorHandler.show_error(
        "Error",
        f"{context}:\n\n{str(error)}",
        parent
    )


def handle_exception_with_context(
    exception: Exception,
    context: str = "An error occurred",
    parent=None
) -> None:
    """Handle exception with context information"""
    log_error(f"{context}: {str(exception)}", exc_info=True)
    QtErrorHandler.show_error("Error", f"{context}:\n\n{str(exception)}", parent)
