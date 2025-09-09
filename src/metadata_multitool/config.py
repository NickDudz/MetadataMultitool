"""Configuration management for the Metadata Multitool."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .core import MetadataMultitoolError


class ConfigError(MetadataMultitoolError):
    """Raised when configuration operations fail."""

    pass


DEFAULT_CONFIG = {
    "batch_size": 100,
    "max_workers": 4,
    "progress_bar": True,
    "verbose": False,
    "quiet": False,
    "backup_before_operations": True,
    "log_level": "INFO",
    "supported_formats": [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"],
    "exiftool_path": None,  # Auto-detect if None
    "temp_dir": None,  # Use system temp if None
}


def find_config_file(start_path: Path) -> Optional[Path]:
    """
    Find the configuration file by searching up the directory tree.

    Args:
        start_path: Starting directory to search from

    Returns:
        Path to config file if found, None otherwise
    """
    current = start_path.resolve()

    while True:
        config_file = current / ".mm_config.yaml"
        if config_file.exists():
            return config_file

        parent = current.parent
        if parent == current:  # Reached root directory
            break
        current = parent

    return None


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from file or return defaults.

    Args:
        config_path: Path to config file, or None to auto-detect

    Returns:
        Configuration dictionary

    Raises:
        ConfigError: If config file cannot be read or parsed
    """
    if config_path is None:
        # Try to find config file in current directory or parent directories
        config_path = find_config_file(Path.cwd())

    if config_path is None or not config_path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        # Merge with defaults, ensuring all keys exist
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)

        return merged_config
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse config file {config_path}: {e}")
    except OSError as e:
        raise ConfigError(f"Failed to read config file {config_path}: {e}")


def save_config(config: Dict[str, Any], config_path: Path) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration dictionary
        config_path: Path to save config file

    Raises:
        ConfigError: If config file cannot be written
    """
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    except OSError as e:
        raise ConfigError(f"Failed to write config file {config_path}: {e}")
    except (TypeError, ValueError) as e:
        raise ConfigError(f"Failed to serialize config data: {e}")


def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Get a configuration value with fallback to default.

    Args:
        config: Configuration dictionary
        key: Configuration key
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    return config.get(key, default)
