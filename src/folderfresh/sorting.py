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
def pick_custom_category(ext, cfg):
    custom = cfg.get("custom_categories", {})
    for cat, exts in custom.items():
        if ext.lower() in exts:
            if cfg.get("category_enabled", {}).get(cat, True):
                return cat
    return None

# ---- Simple category picker ----------------------------------------------------------
def pick_category(ext: str, src_path=None, cfg=None) -> str:
    ext = ext.lower()

    custom_map = cfg.get("custom_categories", {}) if cfg else {}
    enabled_map = cfg.get("category_enabled", {}) if cfg else {}

    # -----------------------------------------------
    # 1) CUSTOM CATEGORIES (including overrides to defaults)
    # -----------------------------------------------
    # If a category appears in custom_categories, its extension list overrides the default.
    for cat, exts in custom_map.items():
        if not enabled_map.get(cat, True):
            continue
        # Ensure exts is a list (skip if it's a dict or other type)
        if not isinstance(exts, list):
            continue
        if ext in exts:
            return cat

    # -----------------------------------------------
    # 2) KEYWORD / SMART RULES
    # -----------------------------------------------
    if src_path is not None:
        folder = apply_rules(src_path)
        if folder and enabled_map.get(folder, True):
            return folder

    # -----------------------------------------------
    # 3) DEFAULT CATEGORIES (only if NOT overridden)
    # -----------------------------------------------
    for cat, default_exts in CATEGORIES.items():
        if not enabled_map.get(cat, True):
            continue

        # Skip this default category if the user provided a custom override
        if cat in custom_map:
            continue

        if ext in default_exts:
            return cat

    # -----------------------------------------------
    # 4) FALLBACK
    # -----------------------------------------------
    return "Other"



# ---- Smart category picker ----------------------------------------------------
def pick_smart_category(path: Path, cfg=None) -> str | None:
    """
    Smart category detection with full support for:
    - disabled categories (category_enabled)
    - renamed categories (handled later by resolve_category)
    - custom categories do NOT apply here (smart mode overrides them)
    """
    name = path.name.lower()
    stem = path.stem.lower()
    ext = path.suffix.lower()

    # Retrieve enabled/disabled map
    enabled = cfg.get("category_enabled", {}) if cfg else {}

    def allow(cat: str) -> bool:
        """Check if category is enabled."""
        return enabled.get(cat, True)

    # Try to get file size
    try:
        size = path.stat().st_size
    except Exception:
        size = None

    # EXIF photo detection
    is_photo = False
    try:
        from PIL import Image
        img = Image.open(path)
        img.verify()
        is_photo = True
    except Exception:
        pass

    # =============================================================
    #  HIGH CONFIDENCE CATEGORIES
    # =============================================================

    # Screenshots
    if any(x in name for x in ("screenshot", "screen shot", "capture", "snip", "printscreen")):
        return "Screenshots" if allow("Screenshots") else None

    # Camera photos
    if is_photo:
        if stem.startswith(("img_", "pxl_", "dsc_", "mvimg_", "psx_", "pano_", "img-")):
            return "Camera Photos" if allow("Camera Photos") else None
        if stem[:8].isdigit() and ("-" in stem or "_" in stem):
            return "Camera Photos" if allow("Camera Photos") else None

    # Messaging media
    if any(x in name for x in ("whatsapp", "waimg", "telegram", "signal-", "messenger", "line_")):
        return "Messaging Media" if allow("Messaging Media") else None

    # Installers
    if ext in (".exe", ".msi", ".bat") and any(
        x in name for x in ("setup", "installer", "install", "update", "patch")
    ):
        return "Installers" if allow("Installers") else None

    # Large archives
    if ext in (".zip", ".rar", ".7z", ".tar", ".gz") and size and size > 200_000_000:
        return "Large Archives" if allow("Large Archives") else None

    # Backups
    if any(x in name for x in ("backup", "bak", "_old", "-old", "(old)", "(copy)", "copy(")):
        return "Backups" if allow("Backups") else None

    # =============================================================
    #  MEDIUM CONFIDENCE CATEGORIES
    # =============================================================

    # Game assets
    if ext in (".dll", ".pak", ".sav", ".vdf", ".uasset", ".unitypackage") or \
       any(x in name for x in ("unity", "unreal", "godot", "shader", "texture")):
        return "Game Assets" if allow("Game Assets") else None

    # Developer / project files
    if ext in (".py", ".js", ".ts", ".java", ".cpp", ".csproj", ".sln", ".go", ".rs") or \
       any(x in name for x in ("project", "config", "build", "node_modules")):
        return "Code Projects" if allow("Code Projects") else None

    # APKs
    if ext in (".apk", ".aab"):
        return "Android Packages" if allow("Android Packages") else None

    # Video exports
    if ext in (".mp4", ".mov", ".avi", ".mkv") and any(
        x in name for x in ("render", "final", "edited", "export")
    ):
        return "Edited Videos" if allow("Edited Videos") else None

    # Creative images
    if ext in (".psd", ".xcf", ".kra", ".svg") or \
       any(x in name for x in ("design", "banner", "thumbnail", "logo", "cover")):
        return "Creative Assets" if allow("Creative Assets") else None

    # Ebooks
    if ext in (".epub", ".mobi", ".azw3", ".pdf") and \
       any(x in name for x in ("ebook", "novel", "chapter", "volume", "book")):
        return "Ebooks" if allow("Ebooks") else None

    # Finance
    if any(x in name for x in ("invoice", "receipt", "bank", "statement", "tax", "payment", "paystub")):
        return "Finance" if allow("Finance") else None

    # School work
    if any(x in name for x in ("assignment", "homework", "worksheet", "module", "lesson", "quiz", "exam")):
        return "School Work" if allow("School Work") else None

    # =============================================================
    #  LOW CONFIDENCE CATEGORIES
    # =============================================================

    if ext in (".png", ".jpg", ".webp") and any(
        x in name for x in ("temp", "asset", "sprite", "icon", "preview")
    ):
        return "Misc Media" if allow("Misc Media") else None

    if ext in (".zip", ".rar") and "download" in name:
        return "Downloaded Archives" if allow("Downloaded Archives") else None

    # Nothing matched
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
