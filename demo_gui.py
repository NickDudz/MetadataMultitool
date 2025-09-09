#!/usr/bin/env python3
"""Demo script to test the Metadata Multitool GUI."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from metadata_multitool.gui.main_window import MainWindow

def main():
    """Run the GUI demo."""
    print("Starting Metadata Multitool GUI Demo...")
    print("This will open the GUI window.")
    print("Close the window to exit.")
    
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"Error running GUI: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
