"""Icon and resource management for the application."""

from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QPixmap


class IconManager:
    """Manages application icons and images."""

    def __init__(self):
        self.icons_dir = Path(__file__).parent.parent / "resources" / "icons"
        self.images_dir = Path(__file__).parent.parent / "resources" / "images"

        # Icon cache
        self._icon_cache: Dict[str, QIcon] = {}

        # Standard icon names
        self.icon_names = {
            "app": "app.png",
            "clean": "clean.png",
            "poison": "poison.png",
            "revert": "revert.png",
            "settings": "settings.png",
            "help": "help.png",
            "folder": "folder.png",
            "file": "file.png",
            "image": "image.png",
            "add": "add.png",
            "remove": "remove.png",
            "clear": "clear.png",
            "start": "start.png",
            "stop": "stop.png",
            "pause": "pause.png",
            "refresh": "refresh.png",
        }

    def get_icon(self, name: str, size: Optional[QSize] = None) -> QIcon:
        """Get an icon by name."""
        if name in self._icon_cache:
            return self._icon_cache[name]

        # Try to load from resources
        icon_path = self.icons_dir / self.icon_names.get(name, f"{name}.png")

        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            # Fallback to built-in icons or create simple text-based icon
            icon = self._create_fallback_icon(name)

        if size:
            # Ensure icon has the requested size
            pixmap = icon.pixmap(size)
            icon = QIcon(pixmap)

        self._icon_cache[name] = icon
        return icon

    def get_app_icon(self) -> Optional[str]:
        """Get the application icon path."""
        app_icon_path = self.icons_dir / self.icon_names["app"]
        if app_icon_path.exists():
            return str(app_icon_path)
        return None

    def _create_fallback_icon(self, name: str) -> QIcon:
        """Create a fallback icon when file is not found."""
        # For now, return empty icon
        # In the future, could create simple programmatic icons
        return QIcon()

    def preload_icons(self) -> None:
        """Preload commonly used icons."""
        common_icons = ["app", "clean", "poison", "revert", "settings", "help"]
        for icon_name in common_icons:
            self.get_icon(icon_name)

    def clear_cache(self) -> None:
        """Clear the icon cache."""
        self._icon_cache.clear()
