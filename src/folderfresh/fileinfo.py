import os

def get_fileinfo(path: str) -> dict:
    """Collect metadata for the rule engine."""
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1]
    try:
        size = os.path.getsize(path)
    except FileNotFoundError:
        size = 0

    return {
        "path": path,
        "name": name,
        "ext": ext,
        "size": size,
    }
