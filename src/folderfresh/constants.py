# constants.py
from pathlib import Path

APP_VERSION = (Path(__file__).resolve().parent / "VERSION").read_text().strip()
APP_TITLE = f"FolderFresh v{APP_VERSION}"

# Log file created inside the selected folder after organise/copy
LOG_FILENAME = ".folderfresh_moves_log.json"

# Name of user config file stored in home directory
CONFIG_FILENAME = ".folderfresh_config.json"

# Default categories (extension → folder)
CATEGORIES: dict[str, list[str]] = {
    "Images": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".heic"],
    "PDF": [".pdf"],
    "Documents": [".doc", ".docx", ".txt", ".rtf", ".odt", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".ipynb"],
    "Shortcuts": [".lnk", ".url"],
}

# Smart rules used by apply_rules()
RULES = {
    "keywords": {
        "invoice": "Finance",
        "assignment": "School",
        "screenshot": "Screenshots",
    },
    # "age_days": { 30: "Archive" },
}

CONFIG_PATH = Path.home() / CONFIG_FILENAME

# Top-level category folders to avoid infinite loops
DEFAULT_CATEGORIES = [
    "Images", "PDF", "Documents", "Videos", "Audio",
    "Archives", "Code", "Other"
]

# Smart mode categories that can be created
SMART_CATEGORIES = [
    "Screenshots", "Camera Photos", "Messaging Media", "Installers",
    "Large Archives", "Backups", "Game Assets", "Code Projects",
    "Android Packages", "Edited Videos", "Creative Assets", "Ebooks",
    "Finance", "School Work", "Misc Media"
]

# All possible top-level categories (default + smart)
ALL_CATEGORIES = list(set(DEFAULT_CATEGORIES + SMART_CATEGORIES))
