from .constants import DEFAULT_CATEGORIES

def resolve_category(default_name: str, cfg: dict) -> str:
    overrides = cfg.get("custom_category_names", {})
    enabled = cfg.get("category_enabled", {})

    # If this category is disabled, return the original name
    # (so system avoids creating a renamed version of a disabled category)
    if not enabled.get(default_name, True):
        return default_name

    # Otherwise apply rename override
    return overrides.get(default_name, default_name)
