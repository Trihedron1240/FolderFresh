"""
PySide6 system tray integration for FolderFresh.
Adapter for pystray integration with Qt application.
"""

import os
import threading
from typing import Optional, Callable

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

# Force dummy backend in CI environments
if os.getenv("CI") == "true":
    os.environ["PYSTRAY_BACKEND"] = "dummy"


class TrayIcon:
    """System tray icon manager for PySide6 application."""

    def __init__(self, app_name: str = "FolderFresh"):
        """
        Initialize tray icon.

        Args:
            app_name: Application name for tray
        """
        self.app_name = app_name
        self.icon: Optional[pystray.Icon] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False

    def _build_tray_image(self, size: int = 64) -> Image.Image:
        """
        Build tray icon image.

        Args:
            size: Icon size in pixels

        Returns:
            PIL Image object
        """
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Blue circle (main icon)
        draw.ellipse((4, 4, size - 4, size - 4), fill=(14, 165, 233, 255))

        # Green rectangle (folder indicator)
        draw.rectangle((10, size * 0.45, size - 10, size - 10), fill=(34, 197, 94, 255))

        return img

    def create(
        self,
        on_open: Callable,
        on_toggle_watch: Callable,
        on_exit: Callable,
        auto_tidy_enabled: bool = False,
    ) -> bool:
        """
        Create and setup tray icon.

        Args:
            on_open: Callback for "Open" action
            on_toggle_watch: Callback for toggle watch action
            on_exit: Callback for exit action
            auto_tidy_enabled: Current auto-tidy state

        Returns:
            True if successful, False otherwise
        """
        if not PYSTRAY_AVAILABLE:
            return False

        if self.icon is not None:
            return True  # Already created

        try:
            # Build menu
            auto_tidy_label = "Turn Auto-tidy OFF" if auto_tidy_enabled else "Turn Auto-tidy ON"

            menu = pystray.Menu(
                pystray.MenuItem("Open FolderFresh", on_open),
                pystray.MenuItem(auto_tidy_label, on_toggle_watch),
                pystray.MenuItem("Exit", on_exit),
            )

            # Build icon
            img = self._build_tray_image()
            self.icon = pystray.Icon(
                self.app_name,
                img,
                self.app_name,
                menu,
            )

            return True
        except Exception:
            return False

    def show(self) -> bool:
        """
        Show tray icon and run in background thread.

        Returns:
            True if successful, False otherwise
        """
        if not self.icon:
            return False

        if self.is_running:
            return True  # Already running

        try:
            self.is_running = True

            def run_tray():
                try:
                    self.icon.run()
                except Exception:
                    pass
                finally:
                    self.is_running = False

            self.thread = threading.Thread(target=run_tray, daemon=True)
            self.thread.start()

            return True
        except Exception:
            self.is_running = False
            return False

    def update_menu(
        self,
        on_open: Callable,
        on_toggle_watch: Callable,
        on_exit: Callable,
        auto_tidy_enabled: bool = False,
    ) -> bool:
        """
        Update tray menu items.

        Args:
            on_open: Callback for "Open" action
            on_toggle_watch: Callback for toggle watch action
            on_exit: Callback for exit action
            auto_tidy_enabled: Current auto-tidy state

        Returns:
            True if successful, False otherwise
        """
        if not self.icon:
            return False

        try:
            auto_tidy_label = "Turn Auto-tidy OFF" if auto_tidy_enabled else "Turn Auto-tidy ON"

            menu = pystray.Menu(
                pystray.MenuItem("Open FolderFresh", on_open),
                pystray.MenuItem(auto_tidy_label, on_toggle_watch),
                pystray.MenuItem("Exit", on_exit),
            )

            self.icon.menu = menu
            return True
        except Exception:
            return False

    def hide(self) -> bool:
        """
        Hide tray icon and stop running.

        Returns:
            True if successful, False otherwise
        """
        if not self.icon:
            return True  # Not running

        try:
            self.icon.stop()
            self.icon = None
            self.is_running = False

            # Wait for thread to finish
            if self.thread:
                self.thread.join(timeout=2)

            return True
        except Exception:
            return False

    def is_visible(self) -> bool:
        """Check if tray icon is visible."""
        return self.icon is not None and self.is_running


# Module-level helper functions for simplified API

_global_tray: Optional[TrayIcon] = None


def create_tray(
    app_name: str = "FolderFresh",
    on_open: Optional[Callable] = None,
    on_toggle_watch: Optional[Callable] = None,
    on_exit: Optional[Callable] = None,
    auto_tidy_enabled: bool = False,
) -> bool:
    """
    Create global tray icon.

    Args:
        app_name: Application name
        on_open: Open callback
        on_toggle_watch: Toggle watch callback
        on_exit: Exit callback
        auto_tidy_enabled: Auto-tidy state

    Returns:
        True if successful
    """
    global _global_tray

    if not PYSTRAY_AVAILABLE:
        return False

    _global_tray = TrayIcon(app_name)

    success = _global_tray.create(
        on_open or (lambda i, m: None),
        on_toggle_watch or (lambda i, m: None),
        on_exit or (lambda i, m: None),
        auto_tidy_enabled,
    )

    if success:
        success = _global_tray.show()

    return success


def hide_tray() -> bool:
    """Hide global tray icon."""
    global _global_tray

    if _global_tray:
        return _global_tray.hide()

    return True


def is_tray_visible() -> bool:
    """Check if tray is visible."""
    global _global_tray

    if _global_tray:
        return _global_tray.is_visible()

    return False


def update_tray_menu(
    on_open: Callable,
    on_toggle_watch: Callable,
    on_exit: Callable,
    auto_tidy_enabled: bool = False,
) -> bool:
    """Update tray menu."""
    global _global_tray

    if _global_tray:
        return _global_tray.update_menu(on_open, on_toggle_watch, on_exit, auto_tidy_enabled)

    return False
