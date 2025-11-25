from pathlib import Path
from datetime import datetime
from .constants import CATEGORIES, RULES
from .utils import unique_dest
from .utils import file_is_old_enough

def apply_rules(path: Path) -> str | None:
    name = path.name.lower()
    for kw, folder in RULES.get("keywords", {}).items():
        if kw.lower() in name:
            return folder
    # age‑based
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age = (datetime.now() - mtime).days
        for days, folder in RULES.get("age_days", {}).items():
            try:
                if age >= int(days):
                    return folder
            except Exception:
                continue
    except Exception:
        pass
    return None
# ---- Simple category picker ----------------------------------------------------------
def pick_category(ext: str, src_path: Path | None = None) -> str:
    # rules first (if we know the source path)
    if src_path is not None:
        folder = apply_rules(src_path)
        if folder:
            return folder
    # then by extension
    ext = ext.lower()
    for folder, exts in CATEGORIES.items():
        if ext in exts:
            return folder
    return "Other"

# ---- Smart category picker ----------------------------------------------------
def pick_smart_category(path: Path) -> str | None:
    """
    Advanced rule-based categoriser with metadata, filename patterns,
    filetype inference, project detection, and contextual heuristics.
    Returns a smart category or None if no confidently matching rule exists.
    """

    name = path.name.lower()
    stem = path.stem.lower()
    ext = path.suffix.lower()

    # --- Try to get file size early ---
    try:
        size = path.stat().st_size
    except Exception:
        size = None

    # --- Try EXIF for photos ---
    is_photo = False
    try:
        from PIL import Image
        img = Image.open(path)
        img.verify()
        is_photo = True
    except Exception:
        pass

    # =============================================================
    #  HIGH CONFIDENCE MATCHES  (Instant category assignment)
    # =============================================================

    # Screenshots
    if any(x in name for x in ("screenshot", "screen shot", "capture", "snip", "printscreen")):
        return "Screenshots"

    # Camera photos (file structure + EXIF confirmed)
    if is_photo:
        if stem.startswith(("img_", "pxl_", "dsc_", "mvimg_", "psx_", "pano_", "img-")):
            return "Camera Photos"
        if stem[:8].isdigit() and ("-" in stem or "_" in stem):
            return "Camera Photos"

    # Messaging media (WhatsApp, Telegram, Messenger)
    if any(x in name for x in ("whatsapp", "waimg", "telegram", "signal-", "messenger", "line_")):
        return "Messaging Media"

    # High-confidence Installers / Setup files
    if ext in (".exe", ".msi", ".bat") and any(
        x in name for x in ("setup", "installer", "install", "update", "patch")
    ):
        return "Installers"

    # Large compressed files → Archives
    if ext in (".zip", ".rar", ".7z", ".tar", ".gz") and size and size > 200_000_000:
        return "Large Archives"

    # Backup & version files
    if any(x in name for x in ("backup", "bak", "_old", "-old", "(old)", "(copy)", "copy(")):
        return "Backups"

    # =============================================================
    #  MEDIUM CONFIDENCE MATCHES  (Slightly more specific)
    # =============================================================

    # Game assets and save files
    if ext in (".dll", ".pak", ".sav", ".vdf", ".uasset", ".unitypackage") or \
       any(x in name for x in ("unity", "unreal", "godot", "shader", "texture")):
        return "Game Assets"

    # Developer / Project files
    if ext in (".py", ".js", ".ts", ".java", ".cpp", ".csproj", ".sln", ".go", ".rs") or \
       any(x in name for x in ("project", "config", "build", "node_modules")):
        return "Code Projects"

    # Android APKs
    if ext in (".apk", ".aab"):
        return "Android Packages"

    # Video exports / edits
    if ext in (".mp4", ".mov", ".avi", ".mkv") and any(
        x in name for x in ("render", "final", "edited", "export")
    ):
        return "Edited Videos"

    # Edited images / creative content
    if ext in (".psd", ".xcf", ".kra", ".svg") or \
       any(x in name for x in ("design", "banner", "thumbnail", "logo", "cover")):
        return "Creative Assets"

    # Ebooks
    if ext in (".epub", ".mobi", ".azw3", ".pdf") and \
       any(x in name for x in ("ebook", "novel", "chapter", "volume", "book")):
        return "Ebooks"

    # Finance docs
    if any(x in name for x in ("invoice", "receipt", "bank", "statement", "tax", "payment", "paystub")):
        return "Finance"

    # School / Educational content
    if any(x in name for x in ("assignment", "homework", "worksheet", "module", "lesson", "quiz", "exam")):
        return "School Work"

    # =============================================================
    #  LOW CONFIDENCE MATCHES  (Weak patterns, safe fallback)
    # =============================================================

    # Common project folders/images
    if ext in (".png", ".jpg", ".webp") and any(
        x in name for x in ("temp", "asset", "sprite", "icon", "preview")
    ):
        return "Misc Media"

    # Files frequently part of app downloads
    if ext in (".zip", ".rar") and "download" in name:
        return "Downloaded Archives"

    # If nothing matched:
    return None


def unique_dest(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        candidate = path.with_name(f"{stem}_{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1

def plan_moves_preview(files, root):
    #Same as plan_moves but does NOT create folders or write anything.
    moves = []
    for src in files:
        folder = pick_category(src.suffix)  # or smart category, handled outside
        dst_dir = root / folder
        dst = dst_dir / src.name  # DO NOT mkdir, DO NOT unique_dest
        if src != dst:
            moves.append({"src": str(src), "dst": str(dst)})
    return moves

def plan_moves(files: list[Path], root: Path) -> list[dict]:
    """
    Pure helper: plan moves based on extension / rules.
    Does NOT reference UI state (self) so it is safe to call from handlers.
    """
    moves: list[dict] = []
    for src in files:
        # rules first if we can (apply_rules uses path)
        folder = pick_category(src.suffix, src_path=src)
        # fallback to Other handled inside pick_category
        dst_dir = root / folder
        # ensure destination dir is created by the caller (organise/worker)
        # but here we will compute a unique destination name (caller must mkdir before move)
        dst = unique_dest(dst_dir / src.name)
        if src != dst:
            moves.append({"src": str(src), "dst": str(dst)})
    return moves