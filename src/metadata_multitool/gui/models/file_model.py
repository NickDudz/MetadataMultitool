"""File model for managing selected files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileModel:
    """Model for managing selected files and their metadata."""

    def __init__(self):
        """Initialize the file model."""
        self.files: List[Path] = []
        self.file_info: Dict[Path, Dict[str, Any]] = {}

    def add_files(self, files: List[Path]) -> None:
        """Add files to the model."""
        for file_path in files:
            if file_path not in self.files:
                self.files.append(file_path)
                self._load_file_info(file_path)

    def remove_file(self, file_path: Path) -> None:
        """Remove a file from the model."""
        if file_path in self.files:
            self.files.remove(file_path)
            if file_path in self.file_info:
                del self.file_info[file_path]

    def clear_files(self) -> None:
        """Clear all files from the model."""
        self.files.clear()
        self.file_info.clear()

    def get_files(self) -> List[Path]:
        """Get all selected files."""
        return self.files.copy()

    def get_file_count(self) -> int:
        """Get the number of selected files."""
        return len(self.files)

    def get_file_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get information about a specific file."""
        return self.file_info.get(file_path)

    def _load_file_info(self, file_path: Path) -> None:
        """Load information about a file."""
        try:
            stat = file_path.stat()
            self.file_info[file_path] = {
                "name": file_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": file_path.suffix.lower(),
                "has_metadata": self._check_has_metadata(file_path),
            }
        except OSError:
            # File might not exist or be accessible
            self.file_info[file_path] = {
                "name": file_path.name,
                "size": 0,
                "modified": 0,
                "extension": file_path.suffix.lower(),
                "has_metadata": False,
            }

    def _check_has_metadata(self, file_path: Path) -> bool:
        """Check if a file has metadata."""
        # This is a simplified check - in a real implementation,
        # you might want to use exiftool or PIL to check for metadata
        try:
            # Check if file is readable and has reasonable size
            stat = file_path.stat()
            return stat.st_size > 0
        except OSError:
            return False

    def filter_files(self, **filters) -> List[Path]:
        """Filter files based on criteria."""
        filtered = []

        for file_path in self.files:
            info = self.file_info.get(file_path, {})

            # Size filter
            if "min_size" in filters and info.get("size", 0) < filters["min_size"]:
                continue
            if "max_size" in filters and info.get("size", 0) > filters["max_size"]:
                continue

            # Extension filter
            if "extensions" in filters:
                if info.get("extension", "") not in filters["extensions"]:
                    continue

            # Metadata filter
            if "has_metadata" in filters:
                if info.get("has_metadata", False) != filters["has_metadata"]:
                    continue

            # Date filter
            if "min_date" in filters and info.get("modified", 0) < filters["min_date"]:
                continue
            if "max_date" in filters and info.get("modified", 0) > filters["max_date"]:
                continue

            filtered.append(file_path)

        return filtered
