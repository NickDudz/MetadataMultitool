#!/usr/bin/env python3
"""Detailed test script for PyQt6 GUI."""

import sys
import os
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from PyQt6.QtWidgets import QApplication
    from metadata_multitool.gui_qt.main import MetadataMultitoolApp
    
    def test_gui_components():
        """Test GUI components."""
        print("Creating application...")
        app = MetadataMultitoolApp([])
        
        print("Creating main window...")
        main_window = app.create_main_window()
        
        print("Testing file model...")
        file_count = main_window.file_model.get_file_count()
        print(f"Initial file count: {file_count}")
        
        print("Testing configuration...")
        theme = main_window.config_model.get_gui_setting("theme", "light")
        print(f"Current theme: {theme}")
        
        print("Testing operation model...")
        state = main_window.operation_model.get_state_description()
        print(f"Operation state: {state}")
        
        print("Testing CLI service...")
        formats = main_window.main_controller.cli_service.get_supported_formats()
        print(f"Supported formats: {', '.join(formats)}")
        
        print("Testing UI components...")
        if main_window.file_panel:
            print("File panel: OK")
        if main_window.progress_widget:
            print("Progress widget: OK")
        if main_window.main_view:
            print("Main view: OK")
            
        print("\nAll components initialized successfully!")
        
        # Show window for visual inspection
        print("Showing main window...")
        main_window.show()
        
        # Run for a short time to test
        from PyQt6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(3000)  # Close after 3 seconds
        
        return app.exec()
        
    if __name__ == "__main__":
        print("Starting detailed PyQt6 GUI test...")
        exit_code = test_gui_components()
        print(f"Test completed with exit code: {exit_code}")
        sys.exit(exit_code)
        
except Exception as e:
    print(f"Error during GUI test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)