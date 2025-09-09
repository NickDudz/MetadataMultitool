"""Configuration service for managing application settings."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from PyQt6.QtCore import QObject, pyqtSignal

# Add project root to path for CLI imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from metadata_multitool.config import get_config_value, load_config, save_config


class ConfigService(QObject):
    """Service for managing application configuration."""

    # Signals
    config_changed = pyqtSignal(str, object)  # key, value
    config_loaded = pyqtSignal()
    config_saved = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._config: Dict[str, Any] = {}
        self._config_file = Path(".mm_config.yaml")

        # Load initial config
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            self._config = load_config()
            self.config_loaded.emit()
            return self._config
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = self._get_default_config()
            return self._config

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Save configuration to file."""
        try:
            config_to_save = config if config is not None else self._config
            save_config(config_to_save, self._config_file)
            self.config_saved.emit()
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return get_config_value(self._config, key, default)

    def set_value(self, key: str, value: Any) -> None:
        """Set configuration value by key."""
        # Navigate to nested keys
        keys = key.split(".")
        current_dict = self._config

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current_dict:
                current_dict[k] = {}
            current_dict = current_dict[k]

        # Set the value
        current_dict[keys[-1]] = value

        # Emit change signal
        self.config_changed.emit(key, value)

    def get_config(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        return self._config.copy()

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with a dictionary of changes."""
        self._config.update(updates)

        # Emit signals for each changed key
        for key, value in updates.items():
            self.config_changed.emit(key, value)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "general": {
                "batch_size": 100,
                "max_workers": 4,
                "backup_before_operations": True,
                "log_level": "INFO",
            },
            "gui_settings": {
                "theme": "light",
                "window_size": [1200, 800],
                "window_position": [100, 100],
                "show_thumbnails": True,
                "remember_last_folder": True,
                "auto_save_settings": True,
            },
            "operation_defaults": {
                "clean": {"output_folder": "safe_upload", "preserve_structure": True},
                "poison": {
                    "preset": "label_flip",
                    "output_formats": {
                        "xmp": True,
                        "iptc": True,
                        "exif": False,
                        "sidecar": True,
                        "json": True,
                        "html": False,
                    },
                    "true_hint": "",
                    "rename_pattern": "",
                },
            },
            "advanced": {
                "enable_debug_logging": False,
                "exiftool_path": "",
                "temp_directory": "",
            },
        }
