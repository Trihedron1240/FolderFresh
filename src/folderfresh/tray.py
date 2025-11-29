from pathlib import Path
import os
import threading
import pystray
from PIL import Image, ImageDraw

from .config import save_config

# ========== CI ENVIRONMENT DETECTION ================================================
# Force dummy backend in headless CI environments (no display server)
if os.getenv("CI") == "true":
    os.environ["PYSTRAY_BACKEND"] = "dummy"

# ========== TRAY IMAGE ========================================================

def build_tray_image(size=64):
    """
    Recreates the generated tray icon exactly like in your app.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, size-4, size-4), fill=(14, 165, 233, 255))
    d.rectangle((10, size*0.45, size-10, size-10), fill=(34, 197, 94, 255))
    return img


# ========== TOGGLE TRAY MODE ==================================================

def toggle_tray(app):
    """
    This handles clicking the checkbox in the GUI.
    Mirrors app.on_toggle_tray behavior.
    """
    # If tray is turned ON but pystray not available, GUI will already warn.
    app.config_data["tray_mode"] = bool(app.tray_mode.get())
    save_config(app.config_data)


# ========== TRAY HIDING =======================================================

def _build_tray_menu(app):
    """
    Build the tray menu dynamically based on current app state.
    This is called each time we need to update the menu.
    """
    # --- Menu handlers --------------------------------------------------------
    def on_open(icon, item=None):
        app.after(0, app.show_window)

    def on_toggle_watch(icon, item=None):
        """
        Handle Auto-Tidy toggle from tray menu.
        Uses the canonical auto_tidy_enabled state to avoid races.
        """
        # Determine desired state (opposite of current)
        desired_state = not app.auto_tidy_enabled

        # Update UI toggle to match desired state
        if desired_state:
            app.watch_mode.select()
        else:
            app.watch_mode.deselect()

        # Call handler to process the toggle
        # (by this point, both UI and canonical state will be synced)
        app.after(0, app.on_toggle_watch)

    def on_exit(icon, item=None):
        try:
            app.watcher_manager.stop_all()
        except Exception:
            pass
        try:
            if app.tray_icon:
                app.tray_icon.stop()
        except Exception:
            pass
        app.after(0, app.destroy)

    # --- Build menu with current state ----------------------------------------
    # Auto-Tidy label reflects CURRENT canonical state
    auto_tidy_label = "Turn Auto-tidy OFF" if app.auto_tidy_enabled else "Turn Auto-tidy ON"

    menu = pystray.Menu(
        pystray.MenuItem("Open FolderFresh", on_open),
        pystray.MenuItem(auto_tidy_label, on_toggle_watch),
        pystray.MenuItem("Exit", on_exit)
    )

    return menu


def hide_to_tray(app):
    """
    Hides the window and creates the tray icon, matching your original code.
    """
    # Fallback hide if pystray somehow unavailable (rare)
    if "pystray" not in globals():
        app.withdraw()
        return

    # Already running → just hide window
    if app.tray_icon is not None:
        app.withdraw()
        app.set_status("Running in tray…")
        return

    app.withdraw()
    app.set_status("Running in tray…")

    # Build initial menu
    menu = _build_tray_menu(app)

    # Build & attach tray icon
    icon_img = build_tray_image()
    app.tray_icon = pystray.Icon("FolderFresh", icon_img, "FolderFresh", menu)

    # Run in background thread
    def run_tray():
        try:
            app.tray_icon.run()
        except Exception:
            pass

    app.tray_thread = threading.Thread(target=run_tray, daemon=True)
    app.tray_thread.start()


# ========== SHOW WINDOW FROM TRAY ============================================

def show_window(app):
    """
    Restores the GUI window and cleans up the tray icon.
    """
    try:
        if app.tray_icon:
            try:
                app.tray_icon.stop()
            except Exception:
                pass
            app.tray_icon = None
    except Exception:
        pass

    app.deiconify()
    app.lift()
    app.focus_force()
    app.set_status("Ready ✨")
