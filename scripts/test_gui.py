#!/usr/bin/env python3
"""Test script for PyQt6 GUI."""

import sys
import os

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from metadata_multitool.gui_qt.main import main
    
    if __name__ == "__main__":
        print("Starting PyQt6 GUI test...")
        main()
        
except Exception as e:
    print(f"Error starting GUI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)