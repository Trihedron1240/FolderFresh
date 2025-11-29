import os

def get_fileinfo(path: str) -> dict:
    """Collect complete metadata for the rule engine.

    Returns:
        dict with keys:
            - path: absolute normalized path to file
            - name: filename with extension
            - ext: file extension (e.g., '.txt')
            - size: file size in bytes
            - stat: os.stat_result object (includes st_mtime, st_size, etc.)
    """
    # Normalize to absolute path
    abs_path = os.path.abspath(os.path.expanduser(path))

    # Get filename and extension
    name = os.path.basename(abs_path)
    ext = os.path.splitext(name)[1]

    # Get size and stat
    try:
        stat = os.stat(abs_path)
        size = stat.st_size
    except (FileNotFoundError, OSError):
        size = 0
        stat = None

    return {
        "path": abs_path,
        "name": name,
        "ext": ext,
        "size": size,
        "stat": stat,
    }
