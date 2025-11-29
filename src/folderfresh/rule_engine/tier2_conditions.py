"""
Tier-2 Hazel-advanced conditions for FolderFresh.

Includes:
- ColorIs: Match files with specific color labels
- HasTag: Match files with specific tags
- MetadataContains: Match files by metadata content
- MetadataFieldEquals: Match files by exact metadata values
- IsDuplicate: Match files identified as duplicates

All conditions follow FolderFresh patterns:
- Inherit from Condition base class
- Implement evaluate(fileinfo) -> bool
- Print debug info during evaluation
"""

import os
from typing import Dict, Any
from .backbone import Condition
from .tier2_metadata import METADATA_DB, calculate_quick_hash


class ColorIsCondition(Condition):
    """Check if file has a specific color label."""

    def __init__(self, color: str):
        """
        Args:
            color: Color name (e.g., "red", "blue", "green", "yellow", "orange", "purple")
        """
        self.color = color.lower()

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Check if file has the specified color label.

        Returns:
            True if file has the color label
        """
        try:
            file_path = fileinfo.get("path", "")

            if not file_path or not os.path.exists(file_path):
                print(f"  [CONDITION] ColorIs - file not accessible: {fileinfo.get('name', '')}")
                return False

            current_color = METADATA_DB.get_color(file_path)
            result = (current_color is not None) and (current_color.lower() == self.color)

            print(f"  [CONDITION] ColorIs '{self.color}' -> {result}")
            return result

        except Exception as e:
            print(f"  [CONDITION] ColorIs error: {str(e)}")
            return False


class HasTagCondition(Condition):
    """Check if file has a specific tag."""

    def __init__(self, tag: str):
        """
        Args:
            tag: Tag string to match
        """
        self.tag = tag

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Check if file has the specified tag.

        Returns:
            True if file has the tag
        """
        try:
            file_path = fileinfo.get("path", "")

            if not file_path or not os.path.exists(file_path):
                print(f"  [CONDITION] HasTag - file not accessible: {fileinfo.get('name', '')}")
                return False

            result = METADATA_DB.has_tag(file_path, self.tag)

            print(f"  [CONDITION] HasTag '{self.tag}' -> {result}")
            return result

        except Exception as e:
            print(f"  [CONDITION] HasTag error: {str(e)}")
            return False


class MetadataContainsCondition(Condition):
    """Check if file metadata contains a keyword."""

    def __init__(self, field: str, keyword: str):
        """
        Args:
            field: Metadata field name (e.g., "Author", "exif.CameraModel")
            keyword: Keyword to search for (case-insensitive)
        """
        self.field = field
        self.keyword = keyword.lower()

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Check if metadata field contains the keyword.

        Returns:
            True if keyword found in field
        """
        try:
            file_path = fileinfo.get("path", "")

            if not file_path or not os.path.exists(file_path):
                print(f"  [CONDITION] MetadataContains - file not accessible: {fileinfo.get('name', '')}")
                return False

            metadata = METADATA_DB.get_metadata(file_path)
            if not metadata:
                # Try to extract and cache metadata
                from .tier2_metadata import extract_file_metadata
                metadata = extract_file_metadata(file_path)
                METADATA_DB.set_metadata(file_path, metadata)

            # Navigate nested fields (e.g., "exif.CameraModel")
            value = metadata
            for key in self.field.split("."):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break

            if value is None:
                print(f"  [CONDITION] MetadataContains '{self.field}' - field not found")
                return False

            result = self.keyword in str(value).lower()
            print(f"  [CONDITION] MetadataContains '{self.field}' contains '{self.keyword}' -> {result}")
            return result

        except Exception as e:
            print(f"  [CONDITION] MetadataContains error: {str(e)}")
            return False


class MetadataFieldEqualsCondition(Condition):
    """Check if metadata field equals a specific value."""

    def __init__(self, field: str, value: str):
        """
        Args:
            field: Metadata field name
            value: Value to match
        """
        self.field = field
        self.value = value

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Check if metadata field exactly equals the value.

        Returns:
            True if field value matches
        """
        try:
            file_path = fileinfo.get("path", "")

            if not file_path or not os.path.exists(file_path):
                print(f"  [CONDITION] MetadataFieldEquals - file not accessible: {fileinfo.get('name', '')}")
                return False

            metadata = METADATA_DB.get_metadata(file_path)
            if not metadata:
                # Try to extract and cache metadata
                from .tier2_metadata import extract_file_metadata
                metadata = extract_file_metadata(file_path)
                METADATA_DB.set_metadata(file_path, metadata)

            # Navigate nested fields
            value = metadata
            for key in self.field.split("."):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break

            if value is None:
                print(f"  [CONDITION] MetadataFieldEquals '{self.field}' - field not found")
                return False

            result = str(value).lower() == self.value.lower()
            print(f"  [CONDITION] MetadataFieldEquals '{self.field}'={self.value} -> {result}")
            return result

        except Exception as e:
            print(f"  [CONDITION] MetadataFieldEquals error: {str(e)}")
            return False


class IsDuplicateCondition(Condition):
    """Check if file is a duplicate (hash-based)."""

    def __init__(self, match_type: str = "quick"):
        """
        Args:
            match_type: "quick" (first 1MB hash) or "full" (entire file hash)
        """
        self.match_type = match_type.lower()

    def evaluate(self, fileinfo: Dict[str, Any]) -> bool:
        """
        Check if file matches another file by hash.

        Returns:
            True if duplicates found
        """
        try:
            file_path = fileinfo.get("path", "")

            if not file_path or not os.path.exists(file_path):
                print(f"  [CONDITION] IsDuplicate - file not accessible: {fileinfo.get('name', '')}")
                return False

            try:
                file_size = os.path.getsize(file_path)
            except Exception:
                return False

            # Calculate hash
            if self.match_type == "full":
                from .tier2_metadata import calculate_full_hash
                hash_value = calculate_full_hash(file_path)
            else:
                hash_value = calculate_quick_hash(file_path)

            if not hash_value:
                print(f"  [CONDITION] IsDuplicate - could not calculate hash")
                return False

            # Find duplicates
            duplicates = METADATA_DB.find_duplicates(file_path, file_size, hash_value)
            result = len(duplicates) > 0

            print(f"  [CONDITION] IsDuplicate (match_type={self.match_type}) -> {result}")
            return result

        except Exception as e:
            print(f"  [CONDITION] IsDuplicate error: {str(e)}")
            return False
