"""
Tier-2 metadata storage layer for FolderFresh.

Manages:
- Color labels (file -> color mapping)
- File tags (file -> tag list mapping)
- Metadata cache (EXIF, PDF, Office, etc.)
- Duplicate detection (hash-based)

Uses SQLite for persistent metadata storage with cross-platform compatibility.
"""

import os
import json
import sqlite3
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from threading import Lock
from .backbone import normalize_path


class MetadataDB:
    """
    SQLite-based metadata storage for file labels, tags, and cached metadata.
    Thread-safe with lock-based synchronization.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize metadata database.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.folderfresh/metadata.db
        """
        if db_path is None:
            home = Path.home()
            db_dir = home / ".folderfresh"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "metadata.db")

        self.db_path = db_path
        self._lock = Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database tables if they don't exist."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Color labels: absolute_path -> color_name
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS color_labels (
                    id INTEGER PRIMARY KEY,
                    file_path TEXT UNIQUE NOT NULL,
                    color TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # File tags: file_path -> comma-separated tags
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_tags (
                    id INTEGER PRIMARY KEY,
                    file_path TEXT UNIQUE NOT NULL,
                    tags TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Metadata cache: file_path -> JSON metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata_cache (
                    id INTEGER PRIMARY KEY,
                    file_path TEXT UNIQUE NOT NULL,
                    metadata TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # File hashes: file_path -> hash value
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_hashes (
                    id INTEGER PRIMARY KEY,
                    file_path TEXT UNIQUE NOT NULL,
                    file_size INTEGER NOT NULL,
                    hash_quick TEXT,
                    hash_full TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()

    def set_color(self, file_path: str, color: str) -> bool:
        """
        Set color label for a file.

        Args:
            file_path: Absolute file path
            color: Color name (e.g., "red", "blue", "green")

        Returns:
            True if successful
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO color_labels (file_path, color)
                    VALUES (?, ?)
                """, (file_path, color))

                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"Error setting color label: {e}")
            return False

    def get_color(self, file_path: str) -> Optional[str]:
        """
        Get color label for a file.

        Args:
            file_path: Absolute file path

        Returns:
            Color name or None if not set
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT color FROM color_labels WHERE file_path = ?", (file_path,))
                row = cursor.fetchone()
                conn.close()

                return row[0] if row else None
        except Exception as e:
            print(f"Error getting color label: {e}")
            return None

    def remove_color(self, file_path: str) -> bool:
        """Remove color label from a file."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("DELETE FROM color_labels WHERE file_path = ?", (file_path,))

                conn.commit()
                conn.close()
                return True
        except Exception:
            return False

    def add_tag(self, file_path: str, tag: str) -> bool:
        """
        Add a tag to a file (idempotent).

        Args:
            file_path: Absolute file path
            tag: Tag string

        Returns:
            True if successful or already existed
        """
        try:
            file_path = normalize_path(file_path)
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT tags FROM file_tags WHERE file_path = ?", (file_path,))
                row = cursor.fetchone()

                if row:
                    tags_list = row[0].split(";")
                    if tag not in tags_list:
                        tags_list.append(tag)
                        new_tags = ";".join(tags_list)
                        cursor.execute(
                            "UPDATE file_tags SET tags = ? WHERE file_path = ?",
                            (new_tags, file_path)
                        )
                        conn.commit()
                else:
                    cursor.execute(
                        "INSERT INTO file_tags (file_path, tags) VALUES (?, ?)",
                        (file_path, tag)
                    )
                    conn.commit()

                conn.close()
                return True
        except Exception as e:
            print(f"Error adding tag: {e}")
            return False

    def remove_tag(self, file_path: str, tag: str) -> bool:
        """
        Remove a tag from a file.

        Args:
            file_path: Absolute file path
            tag: Tag to remove

        Returns:
            True if successful
        """
        try:
            file_path = normalize_path(file_path)
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT tags FROM file_tags WHERE file_path = ?", (file_path,))
                row = cursor.fetchone()

                if row:
                    tags_list = row[0].split(";")
                    if tag in tags_list:
                        tags_list.remove(tag)

                        if tags_list:
                            new_tags = ";".join(tags_list)
                            cursor.execute(
                                "UPDATE file_tags SET tags = ? WHERE file_path = ?",
                                (new_tags, file_path)
                            )
                        else:
                            cursor.execute("DELETE FROM file_tags WHERE file_path = ?", (file_path,))

                        conn.commit()

                conn.close()
                return True
        except Exception:
            return False

    def get_tags(self, file_path: str) -> List[str]:
        """
        Get all tags for a file.

        Args:
            file_path: Absolute file path

        Returns:
            List of tag strings
        """
        try:
            file_path = normalize_path(file_path)
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT tags FROM file_tags WHERE file_path = ?", (file_path,))
                row = cursor.fetchone()
                conn.close()

                return row[0].split(";") if row else []
        except Exception:
            return []

    def has_tag(self, file_path: str, tag: str) -> bool:
        """Check if file has a specific tag."""
        return tag in self.get_tags(file_path)

    def set_metadata(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Cache metadata for a file.

        Args:
            file_path: Absolute file path
            metadata: Dictionary of metadata

        Returns:
            True if successful
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                metadata_json = json.dumps(metadata)
                cursor.execute("""
                    INSERT OR REPLACE INTO metadata_cache (file_path, metadata)
                    VALUES (?, ?)
                """, (file_path, metadata_json))

                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"Error setting metadata: {e}")
            return False

    def get_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get cached metadata for a file.

        Args:
            file_path: Absolute file path

        Returns:
            Metadata dictionary or None
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT metadata FROM metadata_cache WHERE file_path = ?", (file_path,))
                row = cursor.fetchone()
                conn.close()

                if row:
                    return json.loads(row[0])
                return None
        except Exception:
            return None

    def set_hash(self, file_path: str, file_size: int, hash_quick: str = None, hash_full: str = None) -> bool:
        """
        Store file hash for duplicate detection.

        Args:
            file_path: Absolute file path
            file_size: File size in bytes
            hash_quick: Quick hash (first 1MB)
            hash_full: Full file hash (optional)

        Returns:
            True if successful
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO file_hashes (file_path, file_size, hash_quick, hash_full)
                    VALUES (?, ?, ?, ?)
                """, (file_path, file_size, hash_quick, hash_full))

                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"Error setting hash: {e}")
            return False

    def find_duplicates(self, file_path: str, file_size: int, hash_quick: str = None) -> List[str]:
        """
        Find potential duplicate files.

        Args:
            file_path: Absolute file path
            file_size: File size in bytes
            hash_quick: Quick hash for comparison

        Returns:
            List of duplicate file paths
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                if hash_quick:
                    cursor.execute("""
                        SELECT file_path FROM file_hashes
                        WHERE file_size = ? AND hash_quick = ? AND file_path != ?
                    """, (file_size, hash_quick, file_path))
                else:
                    cursor.execute("""
                        SELECT file_path FROM file_hashes
                        WHERE file_size = ? AND file_path != ?
                    """, (file_size, file_path))

                rows = cursor.fetchall()
                conn.close()

                return [row[0] for row in rows]
        except Exception:
            return []

    def clear_old_entries(self, days: int = 30) -> bool:
        """
        Remove metadata for files that no longer exist.

        Args:
            days: Only consider entries older than N days

        Returns:
            True if successful
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Remove entries for non-existent files
                cursor.execute("SELECT file_path FROM color_labels")
                for row in cursor.fetchall():
                    if not os.path.exists(row[0]):
                        cursor.execute("DELETE FROM color_labels WHERE file_path = ?", (row[0],))

                cursor.execute("SELECT file_path FROM file_tags")
                for row in cursor.fetchall():
                    if not os.path.exists(row[0]):
                        cursor.execute("DELETE FROM file_tags WHERE file_path = ?", (row[0],))

                cursor.execute("SELECT file_path FROM metadata_cache")
                for row in cursor.fetchall():
                    if not os.path.exists(row[0]):
                        cursor.execute("DELETE FROM metadata_cache WHERE file_path = ?", (row[0],))

                cursor.execute("SELECT file_path FROM file_hashes")
                for row in cursor.fetchall():
                    if not os.path.exists(row[0]):
                        cursor.execute("DELETE FROM file_hashes WHERE file_path = ?", (row[0],))

                conn.commit()
                conn.close()
                return True
        except Exception:
            return False


# Global metadata database instance
METADATA_DB = MetadataDB()


def calculate_quick_hash(file_path: str, size: int = 1048576) -> str:
    """
    Calculate hash of first N bytes of file (quick hash for duplicates).

    Args:
        file_path: Absolute file path
        size: Bytes to read (default 1MB)

    Returns:
        Hex hash string or empty string on error
    """
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            data = f.read(size)
            hasher.update(data)
        return hasher.hexdigest()
    except Exception:
        return ""


def calculate_full_hash(file_path: str) -> str:
    """
    Calculate full file hash.

    Args:
        file_path: Absolute file path

    Returns:
        Hex hash string or empty string on error
    """
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(8192)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()
    except Exception:
        return ""


def extract_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from file (EXIF, PDF, Office, etc.).

    Args:
        file_path: Absolute file path

    Returns:
        Dictionary of metadata
    """
    metadata = {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "file_size": 0,
        "created": None,
        "modified": None,
        "accessed": None,
    }

    try:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            metadata["file_size"] = stat.st_size
            metadata["created"] = stat.st_ctime
            metadata["modified"] = stat.st_mtime
            metadata["accessed"] = stat.st_atime

            ext = os.path.splitext(file_path)[1].lower()

            # EXIF extraction (JPEG, PNG)
            if ext in ['.jpg', '.jpeg', '.png']:
                try:
                    from PIL import Image
                    from PIL.ExifTags import TAGS

                    img = Image.open(file_path)
                    exif_data = img.getexif()
                    if exif_data:
                        exif_dict = {}
                        for tag_id, value in exif_data.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            try:
                                exif_dict[tag_name] = str(value)
                            except Exception:
                                pass
                        metadata["exif"] = exif_dict
                except ImportError:
                    pass
                except Exception as e:
                    print(f"Error extracting EXIF: {e}")

            # PDF metadata
            elif ext == '.pdf':
                try:
                    import pdfplumber

                    with pdfplumber.open(file_path) as pdf:
                        metadata["pdf_pages"] = len(pdf.pages)
                        if pdf.metadata:
                            metadata["pdf_metadata"] = {k: str(v) for k, v in pdf.metadata.items()}
                except ImportError:
                    pass
                except Exception as e:
                    print(f"Error extracting PDF metadata: {e}")

            # Office metadata (DOCX, PPTX, XLSX)
            elif ext in ['.docx', '.pptx', '.xlsx']:
                try:
                    from docx import Document

                    if ext == '.docx':
                        doc = Document(file_path)
                        props = doc.core_properties
                        metadata["office_author"] = props.author
                        metadata["office_title"] = props.title
                        metadata["office_subject"] = props.subject
                        metadata["office_created"] = str(props.created) if props.created else None
                except ImportError:
                    pass
                except Exception as e:
                    print(f"Error extracting Office metadata: {e}")

    except Exception as e:
        print(f"Error extracting file metadata: {e}")

    return metadata
