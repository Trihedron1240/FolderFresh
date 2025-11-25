from .constants import DEFAULT_CATEGORIES

def resolve_category(default_name: str, cfg: dict) -> str:
    overrides = cfg.get("custom_category_names", {})
    return overrides.get(default_name, default_name)