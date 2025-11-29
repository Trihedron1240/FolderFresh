import json
from pathlib import Path
from .constants import CONFIG_FILENAME
def load_config() -> dict:
    try:
        p = Path.home() / CONFIG_FILENAME
        if p.exists():
            cfg = json.load(open(p, "r", encoding="utf-8"))
        else:
            raise FileNotFoundError
    except Exception:
        # Fall back to defaults
        cfg = {
            "watched_folders": [],
            "folder_profile_map": {},          # ⭐ NEW
            "first_run": True,
            "appearance": "system",
            "tray_mode": False,
            "last_folder": None,
            "include_sub": True,
            "skip_hidden": True,
            "safe_mode": True,
            "watch_mode": False,
            "age_filter_days": 0,
            "ignore_exts": "",
            "smart_mode": False,
            "custom_category_names": {},
            "custom_categories": {},
            "category_enabled": {},
            # File stabilization settings
            "stabilization_timeout": 30.0,        # Max seconds to wait for file stability
            "stabilization_attempts": 10,        # Number of stability checks
            "stabilization_interval": 0.5,       # Seconds between checks
            "stabilization_min_age": 1.0,        # Minimum file age (seconds)
        }

    # --- Migration for older versions ---
    if "watched_folders" not in cfg:
        old = cfg.get("auto_tidy_folder")
        if old:
            cfg["watched_folders"] = [old]
        else:
            cfg["watched_folders"] = []

    # ⭐ Ensure folder → profile map exists even on older configs
    cfg.setdefault("folder_profile_map", {})

    # --- Ensure new v1.4 keys exist ---
    cfg.setdefault("custom_categories", {})
    cfg.setdefault("custom_category_names", {})
    cfg.setdefault("category_enabled", {})

    # --- Ensure file stabilization settings exist ---
    cfg.setdefault("stabilization_timeout", 30.0)
    cfg.setdefault("stabilization_attempts", 10)
    cfg.setdefault("stabilization_interval", 0.5)
    cfg.setdefault("stabilization_min_age", 1.0)

    return cfg






def save_config(cfg: dict) -> None:
    try:
        p = Path.home() / CONFIG_FILENAME
        json.dump(cfg, open(p, "w", encoding="utf-8"), indent=2)
    except Exception:
        pass
