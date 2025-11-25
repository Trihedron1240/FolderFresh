import json
from pathlib import Path
from .constants import CONFIG_FILENAME
def load_config() -> dict:
    try:
        p = Path.home() / CONFIG_FILENAME
        if p.exists():
            return json.load(open(p, "r", encoding="utf-8"))
    except Exception:
        pass
    return {
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
    }

def save_config(cfg: dict) -> None:
    try:
        p = Path.home() / CONFIG_FILENAME
        json.dump(cfg, open(p, "w", encoding="utf-8"), indent=2)
    except Exception:
        pass
