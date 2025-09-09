"""Configuration model for managing settings."""

from __future__ import annotations

from typing import Dict, Any, Optional
from pathlib import Path

from ...config import save_config, get_config_value


class ConfigModel:
    """Model for managing configuration settings."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the config model."""
        self.config = config.copy()
        
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return get_config_value(self.config, key, default)
        
    def set_value(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value
        
    def get_gui_setting(self, key: str, default: Any = None) -> Any:
        """Get a GUI-specific setting."""
        gui_settings = self.get_value("gui_settings", {})
        return gui_settings.get(key, default)
        
    def set_gui_setting(self, key: str, value: Any) -> None:
        """Set a GUI-specific setting."""
        if "gui_settings" not in self.config:
            self.config["gui_settings"] = {}
        self.config["gui_settings"][key] = value
        
    def save_config(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = Path(".mm_config.yaml")
        save_config(self.config, config_path)
        
    def get_supported_formats(self) -> list[str]:
        """Get list of supported file formats."""
        return self.get_value("supported_formats", [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"])
        
    def get_batch_settings(self) -> Dict[str, int]:
        """Get batch processing settings."""
        return {
            "batch_size": self.get_value("batch_size", 100),
            "max_workers": self.get_value("max_workers", 4)
        }
        
    def get_processing_settings(self) -> Dict[str, bool]:
        """Get processing settings."""
        return {
            "progress_bar": self.get_value("progress_bar", True),
            "verbose": self.get_value("verbose", False),
            "quiet": self.get_value("quiet", False),
            "backup_before_operations": self.get_value("backup_before_operations", True)
        }
        
    def get_logging_settings(self) -> Dict[str, str]:
        """Get logging settings."""
        return {
            "log_level": self.get_value("log_level", "INFO")
        }
