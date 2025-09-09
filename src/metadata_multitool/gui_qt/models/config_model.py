"""Configuration model for Qt GUI."""

from typing import Any, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from ..services.config_service import ConfigService


class ConfigModel(QObject):
    """Model for managing configuration data."""

    # Signals
    value_changed = pyqtSignal(str, object)  # key, value
    config_updated = pyqtSignal()

    def __init__(self, config_service: ConfigService):
        super().__init__()

        self.config_service = config_service

        # Connect to service signals
        self.config_service.config_changed.connect(self.value_changed.emit)
        self.config_service.config_loaded.connect(self.config_updated.emit)
        self.config_service.config_saved.connect(self.config_updated.emit)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config_service.get_value(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config_service.set_value(key, value)

    def get_config(self) -> Dict[str, Any]:
        """Get entire configuration."""
        return self.config_service.get_config()

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with dictionary."""
        self.config_service.update_config(updates)

    def save_config(self) -> bool:
        """Save configuration to file."""
        return self.config_service.save_config()

    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.config_service.load_config()

    # Convenience methods for common configuration sections

    def get_gui_setting(self, key: str, default: Any = None) -> Any:
        """Get GUI setting."""
        return self.get_value(f"gui_settings.{key}", default)

    def set_gui_setting(self, key: str, value: Any) -> None:
        """Set GUI setting."""
        self.set_value(f"gui_settings.{key}", value)

    def get_operation_default(
        self, operation: str, key: str, default: Any = None
    ) -> Any:
        """Get operation default setting."""
        return self.get_value(f"operation_defaults.{operation}.{key}", default)

    def set_operation_default(self, operation: str, key: str, value: Any) -> None:
        """Set operation default setting."""
        self.set_value(f"operation_defaults.{operation}.{key}", value)

    def get_general_setting(self, key: str, default: Any = None) -> Any:
        """Get general setting."""
        return self.get_value(f"general.{key}", default)

    def set_general_setting(self, key: str, value: Any) -> None:
        """Set general setting."""
        self.set_value(f"general.{key}", value)
