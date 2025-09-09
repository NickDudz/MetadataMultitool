"""Main entry point for PyQt6 GUI application."""

import sys
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QIcon

# Add the project root to the path so we can import from the CLI modules
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from .main_window import MainWindow
from .utils.icons import IconManager
from .views.common.theme_manager import ThemeManager


class MetadataMultitoolApp(QApplication):
    """Main application class for Metadata Multitool PyQt6 GUI."""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set application properties
        self.setApplicationName("Metadata Multitool")
        self.setApplicationDisplayName("Metadata Multitool")
        self.setApplicationVersion("0.3.0")
        self.setOrganizationName("Metadata Multitool")
        
        # Enable high DPI support (these are enabled by default in PyQt6)
        # self.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)  # Deprecated in PyQt6
        # self.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)     # Deprecated in PyQt6
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Initialize icon manager
        self.icon_manager = IconManager()
        
        # Set application icon
        icon_path = self.icon_manager.get_app_icon()
        if icon_path and Path(icon_path).exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            
        # Apply initial theme
        self.theme_manager.apply_theme("light")  # Default to light theme
        
        # Create main window
        self.main_window: Optional[MainWindow] = None
        
    def create_main_window(self) -> MainWindow:
        """Create and return the main window."""
        if self.main_window is None:
            self.main_window = MainWindow()
            
        return self.main_window
        
    def run(self) -> int:
        """Run the application."""
        try:
            # Create main window
            main_window = self.create_main_window()
            
            # Show main window
            main_window.show()
            
            # Start event loop
            return self.exec()
            
        except Exception as e:
            print(f"Error starting application: {e}")
            return 1


def main():
    """Main entry point function."""
    # Create application
    app = MetadataMultitoolApp(sys.argv)
    
    # Run application
    exit_code = app.run()
    
    # Clean exit
    sys.exit(exit_code)


if __name__ == "__main__":
    main()