"""
FolderFresh Qt Logging System
Centralized logging for PySide6 application with file and console output
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys


class QtLogger:
    """Singleton logger for FolderFresh PySide6 application"""

    _instance: Optional['QtLogger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, app_name: str = "folderfresh"):
        """Initialize Qt logger (called once)"""
        if self._logger is None:
            self._setup_logging(app_name)

    def _setup_logging(self, app_name: str) -> None:
        """Setup logging configuration"""
        # Create logger
        self._logger = logging.getLogger(app_name)
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False

        # Create log directory
        if sys.platform == 'win32':
            log_dir = Path.home() / "AppData" / "Local" / "FolderFresh" / "logs"
        else:
            log_dir = Path.home() / ".folderfresh" / "logs"

        log_dir.mkdir(exist_ok=True, parents=True)

        # Remove any existing handlers
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        # File handler with rotation (10MB, keep 5 backups)
        log_file = log_dir / "folderfresh.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)

        # Console handler (INFO level only)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        # Log startup
        self._logger.info("=" * 70)
        self._logger.info(f"FolderFresh PySide6 Application Started")
        self._logger.info("=" * 70)

    def get_logger(self) -> logging.Logger:
        """Get the logger instance"""
        return self._logger

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message"""
        if self._logger:
            self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message"""
        if self._logger:
            self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message"""
        if self._logger:
            self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, exc_info: bool = False, **kwargs) -> None:
        """Log error message"""
        if self._logger:
            self._logger.error(msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg: str, *args, exc_info: bool = False, **kwargs) -> None:
        """Log critical error"""
        if self._logger:
            self._logger.critical(msg, *args, exc_info=exc_info, **kwargs)

    @classmethod
    def get_instance(cls) -> 'QtLogger':
        """Get or create logger instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def shutdown(self) -> None:
        """Shutdown logging gracefully"""
        if self._logger:
            self._logger.info("=" * 70)
            self._logger.info("FolderFresh Application Shutdown")
            self._logger.info("=" * 70)

            # Flush and close all handlers
            for handler in self._logger.handlers[:]:
                handler.flush()
                handler.close()


# Convenience functions
def get_logger() -> logging.Logger:
    """Get the application logger"""
    return QtLogger.get_instance().get_logger()


def log_debug(msg: str, *args, **kwargs) -> None:
    QtLogger.get_instance().debug(msg, *args, **kwargs)


def log_info(msg: str, *args, **kwargs) -> None:
    QtLogger.get_instance().info(msg, *args, **kwargs)


def log_warning(msg: str, *args, **kwargs) -> None:
    QtLogger.get_instance().warning(msg, *args, **kwargs)


def log_error(msg: str, *args, exc_info: bool = False, **kwargs) -> None:
    QtLogger.get_instance().error(msg, *args, exc_info=exc_info, **kwargs)


def log_critical(msg: str, *args, exc_info: bool = False, **kwargs) -> None:
    QtLogger.get_instance().critical(msg, *args, exc_info=exc_info, **kwargs)


def shutdown_logger() -> None:
    """Shutdown logger"""
    QtLogger.get_instance().shutdown()
