"""Core utilities for the Metadata Multitool."""

from __future__ import annotations

import json
import random
import string
from pathlib import Path
from typing import Any, Dict, Iterable

LOG_NAME = ".mm_poisonlog.json"

# Supported image extensions
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}


class MetadataMultitoolError(Exception):
    """Base exception for Metadata Multitool errors."""

    pass


class InvalidPathError(MetadataMultitoolError):
    """Raised when an invalid path is provided."""

    pass


class LogError(MetadataMultitoolError):
    """Raised when there's an error with log operations."""

    pass


def iter_images(path: Path) -> Iterable[Path]:
    """
    Iterate over image files in a path.

    Args:
        path: File or directory path to search

    Yields:
        Path objects for supported image files

    Raises:
        InvalidPathError: If path doesn't exist
    """
    if not path.exists():
        raise InvalidPathError(f"Path does not exist: {path}")

    if path.is_file():
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path
        return

    if not path.is_dir():
        raise InvalidPathError(f"Path is neither file nor directory: {path}")

    try:
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield file_path
    except PermissionError as e:
        raise InvalidPathError(f"Permission denied accessing {path}: {e}")


def read_log(dirpath: Path) -> Dict[str, Any]:
    """
    Read the poison log from a directory.

    Args:
        dirpath: Directory containing the log file

    Returns:
        Dictionary containing log data

    Raises:
        LogError: If log file is corrupted or unreadable
    """
    log_path = dirpath / LOG_NAME
    if not log_path.exists():
        return {"entries": {}}

    try:
        content = log_path.read_text(encoding="utf-8")
        return json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise LogError(f"Failed to read log file {log_path}: {e}")
    except OSError as e:
        raise LogError(f"Failed to access log file {log_path}: {e}")


def write_log(dirpath: Path, data: Dict[str, Any]) -> None:
    """
    Write the poison log to a directory.

    Args:
        dirpath: Directory to write the log file
        data: Dictionary containing log data

    Raises:
        LogError: If log file cannot be written
    """
    try:
        log_path = dirpath / LOG_NAME
        content = json.dumps(data, ensure_ascii=False, indent=2)
        log_path.write_text(content, encoding="utf-8")
    except (TypeError, ValueError) as e:
        raise LogError(f"Failed to serialize log data: {e}")
    except OSError as e:
        raise LogError(f"Failed to write log file {dirpath / LOG_NAME}: {e}")


def ensure_dir(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to create

    Returns:
        The created directory path

    Raises:
        InvalidPathError: If directory cannot be created
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        raise InvalidPathError(f"Failed to create directory {path}: {e}")


def rand_token(n: int = 6) -> str:
    """
    Generate a random alphanumeric token.

    Args:
        n: Length of the token (default: 6)

    Returns:
        Random token string

    Raises:
        ValueError: If n is not positive
    """
    if n <= 0:
        raise ValueError("Token length must be positive")

    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(n))


def rel_to_root(target: Path, root: Path) -> str:
    """
    Get relative path from target to root.

    Args:
        target: Target file path
        root: Root directory or file path

    Returns:
        Relative path string

    Raises:
        ValueError: If target is not relative to root
    """
    try:
        base = root if root.is_dir() else root.parent
        return str(target.relative_to(base))
    except ValueError as e:
        raise ValueError(f"Target {target} is not relative to root {root}: {e}")
