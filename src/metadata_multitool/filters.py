"""File filtering utilities for the Metadata Multitool."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .core import MetadataMultitoolError, iter_images
from .exif import has_exiftool, run_exiftool


class FilterError(MetadataMultitoolError):
    """Raised when filtering operations fail."""

    pass


class FileFilter:
    """File filter for processing images based on various criteria."""

    def __init__(self):
        self.filters: List[Callable[[Path], bool]] = []

    def add_size_filter(
        self, min_size: Optional[int] = None, max_size: Optional[int] = None
    ) -> None:
        """
        Add size-based filtering.

        Args:
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
        """

        def size_filter(path: Path) -> bool:
            try:
                size = path.stat().st_size
                if min_size is not None and size < min_size:
                    return False
                if max_size is not None and size > max_size:
                    return False
                return True
            except OSError:
                return False

        self.filters.append(size_filter)

    def add_date_filter(
        self,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
        use_modified: bool = True,
    ) -> None:
        """
        Add date-based filtering.

        Args:
            min_date: Minimum date (inclusive)
            max_date: Maximum date (inclusive)
            use_modified: If True, use modification time; if False, use creation time
        """

        def date_filter(path: Path) -> bool:
            try:
                if use_modified:
                    timestamp = path.stat().st_mtime
                else:
                    timestamp = path.stat().st_ctime

                file_date = datetime.fromtimestamp(timestamp)

                if min_date is not None and file_date < min_date:
                    return False
                if max_date is not None and file_date > max_date:
                    return False
                return True
            except OSError:
                return False

        self.filters.append(date_filter)

    def add_format_filter(self, formats: List[str]) -> None:
        """
        Add format-based filtering.

        Args:
            formats: List of file extensions to include (e.g., ['.jpg', '.png'])
        """
        formats_lower = [f.lower() for f in formats]

        def format_filter(path: Path) -> bool:
            return path.suffix.lower() in formats_lower

        self.filters.append(format_filter)

    def add_metadata_filter(self, has_metadata: bool = True) -> None:
        """
        Add metadata presence filtering.

        Args:
            has_metadata: If True, include only files with metadata; if False, include only files without metadata
        """

        def metadata_filter(path: Path) -> bool:
            try:
                if not has_exiftool():
                    # Fallback: check if file is readable as image
                    from PIL import Image

                    try:
                        with Image.open(path) as img:
                            # Check if image has any metadata
                            has_any_metadata = bool(img.info)
                        return has_any_metadata == has_metadata
                    except Exception:
                        return False

                # Use exiftool to check for metadata
                result = run_exiftool(["-m", "-q", "-q", str(path)])
                has_any_metadata = bool(result.strip())
                return has_any_metadata == has_metadata
            except Exception:
                return False

        self.filters.append(metadata_filter)

    def add_custom_filter(self, filter_func: Callable[[Path], bool]) -> None:
        """
        Add a custom filter function.

        Args:
            filter_func: Function that takes a Path and returns True if file should be included
        """
        self.filters.append(filter_func)

    def filter_images(self, path: Path) -> List[Path]:
        """
        Filter images based on all added filters.

        Args:
            path: Path to file or directory to filter

        Returns:
            List of filtered image paths
        """
        images = list(iter_images(path))

        if not self.filters:
            return images

        filtered_images = []
        for img in images:
            if all(filter_func(img) for filter_func in self.filters):
                filtered_images.append(img)

        return filtered_images

    def clear_filters(self) -> None:
        """Clear all filters."""
        self.filters.clear()


def parse_size_filter(size_str: str) -> tuple[Optional[int], Optional[int]]:
    """
    Parse size filter string.

    Args:
        size_str: Size string like "1MB", "500KB-2MB", ">1GB", "<500KB"

    Returns:
        Tuple of (min_size, max_size) in bytes

    Raises:
        FilterError: If size string is invalid
    """
    size_str = size_str.strip().upper()

    # Size multipliers
    multipliers = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
        "TB": 1024 * 1024 * 1024 * 1024,
    }

    def parse_size(size_part: str) -> int:
        size_part = size_part.strip()
        for suffix, multiplier in multipliers.items():
            if size_part.endswith(suffix):
                try:
                    number = float(size_part[: -len(suffix)])
                    return int(number * multiplier)
                except ValueError:
                    raise FilterError(f"Invalid size number: {size_part}")

        # Try parsing as plain number (assume bytes)
        try:
            return int(float(size_part))
        except ValueError:
            raise FilterError(f"Invalid size format: {size_part}")

    try:
        if "-" in size_str:
            # Range format: "1MB-2MB"
            min_str, max_str = size_str.split("-", 1)
            return parse_size(min_str), parse_size(max_str)
        elif size_str.startswith(">"):
            # Greater than: ">1MB"
            return parse_size(size_str[1:]), None
        elif size_str.startswith("<"):
            # Less than: "<1MB"
            return None, parse_size(size_str[1:])
        else:
            # Exact size: "1MB"
            size = parse_size(size_str)
            return size, size
    except Exception as e:
        raise FilterError(f"Failed to parse size filter '{size_str}': {e}")


def parse_date_filter(date_str: str) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse date filter string.

    Args:
        date_str: Date string like "2024-01-01", "2024-01-01:2024-12-31", ">2024-01-01", "<2024-12-31"

    Returns:
        Tuple of (min_date, max_date)

    Raises:
        FilterError: If date string is invalid
    """
    date_str = date_str.strip()

    def parse_date(date_part: str) -> datetime:
        try:
            return datetime.strptime(date_part.strip(), "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(date_part.strip(), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise FilterError(f"Invalid date format: {date_part}")

    try:
        if ":" in date_str:
            # Range format: "2024-01-01:2024-12-31"
            min_str, max_str = date_str.split(":", 1)
            return parse_date(min_str), parse_date(max_str)
        elif date_str.startswith(">"):
            # Greater than: ">2024-01-01"
            return parse_date(date_str[1:]), None
        elif date_str.startswith("<"):
            # Less than: "<2024-01-01"
            return None, parse_date(date_str[1:])
        else:
            # Exact date: "2024-01-01"
            date = parse_date(date_str)
            return date, date
    except Exception as e:
        raise FilterError(f"Failed to parse date filter '{date_str}': {e}")


def create_filter_from_args(args: Dict[str, Any]) -> FileFilter:
    """
    Create a file filter from command line arguments.

    Args:
        args: Dictionary of filter arguments

    Returns:
        Configured FileFilter instance
    """
    filter_obj = FileFilter()

    # Size filter
    if "min_size" in args and args["min_size"] is not None:
        filter_obj.add_size_filter(min_size=args["min_size"])
    if "max_size" in args and args["max_size"] is not None:
        filter_obj.add_size_filter(max_size=args["max_size"])
    if "size" in args and args["size"] is not None:
        min_size, max_size = parse_size_filter(args["size"])
        filter_obj.add_size_filter(min_size=min_size, max_size=max_size)

    # Date filter
    if "min_date" in args and args["min_date"] is not None:
        filter_obj.add_date_filter(min_date=args["min_date"])
    if "max_date" in args and args["max_date"] is not None:
        filter_obj.add_date_filter(max_date=args["max_date"])
    if "date" in args and args["date"] is not None:
        min_date, max_date = parse_date_filter(args["date"])
        filter_obj.add_date_filter(min_date=min_date, max_date=max_date)

    # Format filter
    if "formats" in args and args["formats"]:
        filter_obj.add_format_filter(args["formats"])

    # Metadata filter
    if "has_metadata" in args and args["has_metadata"] is not None:
        filter_obj.add_metadata_filter(has_metadata=args["has_metadata"])

    return filter_obj
