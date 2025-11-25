from pathlib import Path
import threading
import pystray
from PIL import Image, ImageDraw

from .config import save_config

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

    # --- Menu handlers --------------------------------------------------------
    def on_open(icon, item=None):
        app.after(0, app.show_window)

    def on_toggle_watch(icon, item=None):
        app.after(0, lambda: app.watch_mode.toggle())
        app.after(0, app.on_toggle_watch)

    def on_exit(icon, item=None):
        try:
            app.stop_watching()
        except Exception:
            pass
        try:
            if app.tray_icon:
                app.tray_icon.stop()
        except Exception:
            pass
        app.after(0, app.destroy)

    # --- Menu -----------------------------------------------------------------
    menu = pystray.Menu(
        pystray.MenuItem("Open FolderFresh", on_open),
        pystray.MenuItem(
            lambda item: (
                "Turn Auto-tidy OFF" if app.watch_mode.get() else "Turn Auto-tidy ON"
            ),
            on_toggle_watch
        ),
        pystray.MenuItem("Exit", on_exit)
    )

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