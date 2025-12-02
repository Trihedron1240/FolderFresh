from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from folderfresh.rule_engine.rule_store import rule_to_dict, dict_to_rule
from folderfresh.rule_engine import Rule
from .config import load_config, save_config

PROFILES_FILE = Path.home() / ".folderfresh_profiles.json"
BACKUP_DIR = Path.home() / ".folderfresh_backups"
SCHEMA_VERSION = "1.0"
APP_VERSION = "1.4.0"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def atomic_write(path: Path, data: bytes):
    """Write file safely using atomic replace."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def backup_existing(path: Path):
    """Backup current profile file if it exists."""
    try:
        if path.exists():
            BACKUP_DIR.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%dT%H%M%S")
            shutil.copy2(path, BACKUP_DIR / f"{path.name}.{ts}.bak")
    except Exception:
        pass


def default_profiles_doc() -> Dict[str, Any]:
    now = now_iso()
    return {
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": now,
            "app_version": APP_VERSION,
        },
        "active_profile_id": "profile_default",
        "profiles": [
            {
                "id": "profile_default",
                "name": "Default",
                "description": "Default auto-generated profile",
                "created_at": now,
                "updated_at": now,
                "is_builtin": True,
                "is_locked": False,
                "sort_order": 0,
                "settings": {
                    "smart_mode": False,
                    "safe_mode": True,
                    "include_sub": True,
                    "skip_hidden": True,
                    "ignore_exts": "",
                    "age_filter_days": 0,
                    "rule_fallback_to_sort": True,
                },
                "category_overrides": {},
                "custom_categories": {},
                "category_enabled": {},
                "ignore_patterns": [],
                "dont_move_list": [],
                "rules": []
            }
        ],
    }


class ProfileStore:
    def __init__(self, path: Path = PROFILES_FILE):
        self.path = path

    def ensure_profiles(self):
        """Create profiles file if missing or invalid."""
        if self.path.exists():
            try:
                _ = self.load()
                return
            except Exception:
                pass

        doc = default_profiles_doc()
        self.save(doc)

    def load(self) -> Dict[str, Any]:
        """Load profile document or create/recover if invalid."""
        if not self.path.exists():
            doc = default_profiles_doc()
            self.save(doc)
            return doc

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception:
            doc = self.restore_or_reset()

        if not isinstance(doc.get("profiles"), list):
            doc = self.restore_or_reset()

        if not doc["profiles"]:
            doc = default_profiles_doc()
            self.save(doc)

        ids = [p["id"] for p in doc["profiles"]]
        if doc.get("active_profile_id") not in ids:
            doc["active_profile_id"] = ids[0]

        return doc
    def list_profiles(self) -> list[Dict[str, Any]]:
        """Return the list of profiles."""
        doc = self.load()
        return doc.get("profiles", [])

    def save(self, doc: Dict[str, Any]):
        backup_existing(self.path)
        raw = json.dumps(doc, indent=2, ensure_ascii=False).encode("utf-8")
        atomic_write(self.path, raw)

    def restore_or_reset(self) -> Dict[str, Any]:
        backups = sorted(
            BACKUP_DIR.glob("*.bak"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for b in backups:
            try:
                shutil.copy2(b, self.path)
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue

        doc = default_profiles_doc()
        self.save(doc)
        return doc

    def get_active_profile(self, doc: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        doc = doc or self.load()
        active_id = doc.get("active_profile_id")
        for p in doc["profiles"]:
            if p["id"] == active_id:
                return p
        return doc["profiles"][0]

    def set_active_profile(self, profile_id: str):
        doc = self.load()
        doc["active_profile_id"] = profile_id
        self.save(doc)

    def merge_profile_into_config(self, profile: Dict[str, Any], global_cfg: Dict[str, Any]) -> Dict[str, Any]:
        cfg = dict(global_cfg)
        settings = profile.get("settings", {})

        for k in (
            "smart_mode",
            "safe_mode",
            "include_sub",
            "skip_hidden",
            "ignore_exts",
            "age_filter_days",
            "rule_fallback_to_sort",
            "auto_tidy",
        ):
            if k in settings:
                cfg[k] = settings[k]

        cfg["custom_categories"] = profile.get("custom_categories", {})

        # Transform category_overrides to custom_category_names format
        # Profile format: {"cat_name": {"name": "Display Name", "extensions": [...]}}
        # Config format: {"cat_name": "Display Name"}
        category_overrides = profile.get("category_overrides", {})
        custom_category_names = {}
        for cat_name, override_data in category_overrides.items():
            if isinstance(override_data, dict) and "name" in override_data:
                custom_category_names[cat_name] = override_data["name"]
            elif isinstance(override_data, str):
                # Handle old-style string overrides for backward compatibility
                custom_category_names[cat_name] = override_data

        cfg["custom_category_names"] = custom_category_names
        cfg["category_enabled"] = profile.get("category_enabled", {})
        cfg["ignore_patterns"] = profile.get("ignore_patterns", [])
        cfg["dont_move_list"] = profile.get("dont_move_list", [])

        for k in ("watched_folders", "tray_mode", "appearance", "startup", "first_run"):
            cfg[k] = global_cfg.get(k, cfg.get(k))

        return cfg
    # ========================================================
    # RULE ENGINE INTEGRATION
    # ========================================================

    def get_rules(self, profile: Dict[str, Any]) -> list[Rule]:
        """
        Convert the stored 'rules' list (JSON) into Rule objects.
        Returns an empty list if profile has no rules yet.
        """
        entries = profile.get("rules", [])
        return [dict_to_rule(entry) for entry in entries]

    def get_rules_for_profile_id(self, profile_id: str) -> list[Dict[str, Any]]:
        """
        Get raw rules (as dicts) for a specific profile by ID.
        Returns an empty list if profile not found or has no rules.
        """
        doc = self.load()
        for p in doc["profiles"]:
            if p["id"] == profile_id:
                return p.get("rules", [])
        return []

    def set_rules(self, rules: list[Rule], profile_id: str = None):
        """
        Convert a list of Rule objects into JSON-serializable dicts
        and store them inside a profile. Then save the entire
        profiles.json file to persist changes.

        Args:
            rules: List of Rule objects to store (or raw dicts if coming from UI)
            profile_id: Optional specific profile ID to update. If not provided, updates active profile.
        """
        # Load the full document to ensure we save the correct state
        doc = self.load()

        # Determine which profile to update
        if profile_id:
            # Update specific profile by ID
            target_id = profile_id
        else:
            # Fall back to active profile for backward compatibility
            target_id = doc.get("active_profile_id")

        # Convert rules to dicts - handle both Rule objects and raw dicts
        rules_as_dicts = []
        for rule in rules:
            if isinstance(rule, dict):
                # Already a dict (from UI), just use as-is
                rules_as_dicts.append(rule)
            else:
                # Rule object, convert to dict
                rules_as_dicts.append(rule_to_dict(rule))

        # Find and update the target profile
        for p in doc["profiles"]:
            if p["id"] == target_id:
                p["rules"] = rules_as_dicts
                p["updated_at"] = now_iso()
                break

        # Save the updated document
        self.save(doc)
