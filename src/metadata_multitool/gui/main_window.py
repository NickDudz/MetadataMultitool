"""Main GUI window for the Metadata Multitool."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..config import load_config, save_config, get_config_value
from .models.file_model import FileModel
from .models.config_model import ConfigModel
from .models.operation_model import OperationModel
from .views.clean_view import CleanView
from .views.poison_view import PoisonView
from .views.revert_view import RevertView
from .views.settings_view import SettingsView
from .views.file_list_view import FileListView
from .views.progress_view import ProgressView
from .utils.gui_utils import show_error, show_warning, show_info
from .utils.threading_utils import BackgroundProcessor


class MainWindow:
    """Main GUI window for the Metadata Multitool."""

    def __init__(self):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("Metadata Multitool v0.3.0")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Load configuration
        self.config = load_config()

        # Initialize models
        self.file_model = FileModel()
        self.config_model = ConfigModel(self.config)
        self.operation_model = OperationModel()

        # Initialize background processor
        self.background_processor = BackgroundProcessor()

        # Current mode
        self.current_mode = "clean"

        # Initialize views
        self.views = {}
        self._setup_views()

        # Setup UI
        self._setup_ui()

        # Load GUI settings
        self._load_gui_settings()

    def _setup_views(self):
        """Initialize all views."""
        self.views = {
            "clean": CleanView(
                self.root, self.file_model, self.config_model, self.operation_model
            ),
            "poison": PoisonView(
                self.root, self.file_model, self.config_model, self.operation_model
            ),
            "revert": RevertView(
                self.root, self.file_model, self.config_model, self.operation_model
            ),
            "settings": SettingsView(self.root, self.config_model),
            "file_list": FileListView(self.root, self.file_model),
            "progress": ProgressView(self.root, self.operation_model),
        }

    def _setup_ui(self):
        """Setup the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title and menu bar
        self._setup_title_bar(main_frame)

        # Status bar
        self._setup_status_bar(main_frame)

        # Tabbed interface
        self._setup_tabbed_interface(main_frame)

    def _setup_title_bar(self, parent):
        """Setup the title bar with menu."""
        title_frame = ttk.Frame(parent)
        title_frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Title
        title_label = ttk.Label(
            title_frame, text="Metadata Multitool", font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # Menu buttons
        menu_frame = ttk.Frame(title_frame)
        menu_frame.pack(side=tk.RIGHT)

        settings_btn = ttk.Button(
            menu_frame, text="Settings", command=self._show_settings
        )
        settings_btn.pack(side=tk.LEFT, padx=(0, 5))

        help_btn = ttk.Button(menu_frame, text="Help", command=self._show_help)
        help_btn.pack(side=tk.LEFT)

    def _setup_tabbed_interface(self, parent):
        """Setup the tabbed interface for different modes."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(
            row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0)
        )

        # Create tab frames
        self.tab_frames = {}
        self.tab_frames["clean"] = ttk.Frame(self.notebook)
        self.tab_frames["poison"] = ttk.Frame(self.notebook)
        self.tab_frames["revert"] = ttk.Frame(self.notebook)

        # Add tabs to notebook
        self.notebook.add(self.tab_frames["clean"], text="Clean Mode")
        self.notebook.add(self.tab_frames["poison"], text="Poison Mode")
        self.notebook.add(self.tab_frames["revert"], text="Revert Mode")

        # Configure tab frames
        for frame in self.tab_frames.values():
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(1, weight=1)

        # Setup each tab
        self._setup_clean_tab()
        self._setup_poison_tab()
        self._setup_revert_tab()

        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _setup_clean_tab(self):
        """Setup the Clean mode tab."""
        tab_frame = self.tab_frames["clean"]

        # File selection area
        file_frame = ttk.LabelFrame(tab_frame, text="File Selection", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)

        # File selection controls
        file_controls = ttk.Frame(file_frame)
        file_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_controls.columnconfigure(3, weight=1)

        browse_files_btn = ttk.Button(
            file_controls, text="Browse Files", command=self._browse_files
        )
        browse_files_btn.grid(row=0, column=0, padx=(0, 10))

        browse_folder_btn = ttk.Button(
            file_controls, text="Browse Folder", command=self._browse_folder
        )
        browse_folder_btn.grid(row=0, column=1, padx=(0, 10))

        clear_btn = ttk.Button(
            file_controls, text="Clear All", command=self._clear_files
        )
        clear_btn.grid(row=0, column=2)

        # File list
        self.file_list_view = self.views["file_list"]
        self.file_list_view.setup(file_frame)

        # Clean options
        clean_options_frame = ttk.LabelFrame(
            tab_frame, text="Clean Options", padding="10"
        )
        clean_options_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        clean_options_frame.columnconfigure(0, weight=1)
        clean_options_frame.rowconfigure(1, weight=1)

        self.views["clean"].setup(clean_options_frame)

        # Progress area
        self.progress_view = self.views["progress"]
        self.progress_view.setup(tab_frame, row=1, column=0, columnspan=2)

    def _setup_poison_tab(self):
        """Setup the Poison mode tab."""
        tab_frame = self.tab_frames["poison"]

        # File selection area
        file_frame = ttk.LabelFrame(tab_frame, text="File Selection", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)

        # File selection controls
        file_controls = ttk.Frame(file_frame)
        file_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_controls.columnconfigure(3, weight=1)

        browse_files_btn = ttk.Button(
            file_controls, text="Browse Files", command=self._browse_files
        )
        browse_files_btn.grid(row=0, column=0, padx=(0, 10))

        browse_folder_btn = ttk.Button(
            file_controls, text="Browse Folder", command=self._browse_folder
        )
        browse_folder_btn.grid(row=0, column=1, padx=(0, 10))

        clear_btn = ttk.Button(
            file_controls, text="Clear All", command=self._clear_files
        )
        clear_btn.grid(row=0, column=2)

        # File list
        self.file_list_view = self.views["file_list"]
        self.file_list_view.setup(file_frame)

        # Poison options
        poison_options_frame = ttk.LabelFrame(
            tab_frame, text="Poison Options", padding="10"
        )
        poison_options_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        poison_options_frame.columnconfigure(0, weight=1)
        poison_options_frame.rowconfigure(1, weight=1)

        self.views["poison"].setup(poison_options_frame)

        # Progress area
        self.progress_view = self.views["progress"]
        self.progress_view.setup(tab_frame, row=1, column=0, columnspan=2)

    def _setup_revert_tab(self):
        """Setup the Revert mode tab."""
        tab_frame = self.tab_frames["revert"]

        # File selection area
        file_frame = ttk.LabelFrame(tab_frame, text="File Selection", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)

        # File selection controls
        file_controls = ttk.Frame(file_frame)
        file_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_controls.columnconfigure(3, weight=1)

        browse_files_btn = ttk.Button(
            file_controls, text="Browse Files", command=self._browse_files
        )
        browse_files_btn.grid(row=0, column=0, padx=(0, 10))

        browse_folder_btn = ttk.Button(
            file_controls, text="Browse Folder", command=self._browse_folder
        )
        browse_folder_btn.grid(row=0, column=1, padx=(0, 10))

        clear_btn = ttk.Button(
            file_controls, text="Clear All", command=self._clear_files
        )
        clear_btn.grid(row=0, column=2)

        # File list
        self.file_list_view = self.views["file_list"]
        self.file_list_view.setup(file_frame)

        # Revert options
        revert_options_frame = ttk.LabelFrame(
            tab_frame, text="Revert Options", padding="10"
        )
        revert_options_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        revert_options_frame.columnconfigure(0, weight=1)
        revert_options_frame.rowconfigure(1, weight=1)

        self.views["revert"].setup(revert_options_frame)

        # Progress area
        self.progress_view = self.views["progress"]
        self.progress_view.setup(tab_frame, row=1, column=0, columnspan=2)

    def _setup_status_bar(self, parent):
        """Setup the status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(parent, textvariable=self.status_var)
        status_label.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )

    def _on_tab_changed(self, event=None):
        """Handle tab change events."""
        selected_tab = self.notebook.select()
        tab_index = self.notebook.index(selected_tab)

        if tab_index == 0:
            self.current_mode = "clean"
            self.status_var.set("Clean Mode - Remove metadata from images")
        elif tab_index == 1:
            self.current_mode = "poison"
            self.status_var.set("Poison Mode - Add misleading metadata to images")
        elif tab_index == 2:
            self.current_mode = "revert"
            self.status_var.set("Revert Mode - Undo previous operations")

    def _browse_files(self):
        """Browse for individual files."""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.tif *.tiff *.webp *.bmp"),
            ("All files", "*.*"),
        ]

        files = filedialog.askopenfilenames(title="Select Images", filetypes=filetypes)

        if files:
            self.file_model.add_files([Path(f) for f in files])
            self.file_list_view.refresh()
            self.status_var.set(f"Added {len(files)} files")

    def _browse_folder(self):
        """Browse for a folder."""
        folder = filedialog.askdirectory(title="Select Folder")

        if folder:
            folder_path = Path(folder)
            # Find all image files in the folder
            image_files = []
            for ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"]:
                image_files.extend(folder_path.glob(f"*{ext}"))
                image_files.extend(folder_path.glob(f"*{ext.upper()}"))

            if image_files:
                self.file_model.add_files(image_files)
                self.file_list_view.refresh()
                self.status_var.set(f"Added {len(image_files)} files from folder")
            else:
                show_warning("No Images Found", f"No image files found in {folder}")

    def _clear_files(self):
        """Clear all selected files."""
        self.file_model.clear_files()
        self.file_list_view.refresh()
        self.status_var.set("Cleared all files")

    def _show_settings(self):
        """Show settings dialog."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x400")
        settings_window.transient(self.root)
        settings_window.grab_set()

        self.views["settings"].setup(settings_window)

    def _show_help(self):
        """Show help dialog."""
        help_text = """
Metadata Multitool Help

Clean Mode:
- Strips metadata from images for safe upload
- Creates clean copies in specified output folder

Poison Mode:
- Adds misleading metadata to images
- Useful for anti-scraping purposes
- Multiple presets available

Revert Mode:
- Undoes previous operations
- Removes sidecar files and metadata

For more information, visit the project documentation.
        """

        show_info("Help", help_text)

    def _load_gui_settings(self):
        """Load GUI-specific settings."""
        gui_settings = get_config_value(self.config, "gui_settings", {})

        # Window size and position
        window_size = gui_settings.get("window_size", [1000, 700])
        window_position = gui_settings.get("window_position", [100, 100])

        self.root.geometry(
            f"{window_size[0]}x{window_size[1]}+{window_position[0]}+{window_position[1]}"
        )

        # Theme
        theme = gui_settings.get("theme", "light")
        if theme == "dark":
            # TODO: Implement dark theme
            pass

    def _save_gui_settings(self):
        """Save GUI-specific settings."""
        try:
            gui_settings = get_config_value(self.config, "gui_settings", {})

            # Save window size and position
            geometry = self.root.geometry()
            if geometry and "x" in geometry:
                try:
                    # Parse geometry string (format: "WIDTHxHEIGHT+X+Y")
                    if "+" in geometry:
                        size_part, pos_part = geometry.split("+", 1)
                        width, height = map(int, size_part.split("x"))
                        x, y = map(int, pos_part.split("+"))
                        gui_settings["window_size"] = [width, height]
                        gui_settings["window_position"] = [x, y]
                    else:
                        # Just size, no position
                        width, height = map(int, geometry.split("x"))
                        gui_settings["window_size"] = [width, height]
                except (ValueError, IndexError):
                    # If parsing fails, skip saving geometry
                    pass

            self.config["gui_settings"] = gui_settings

            # Save to file
            config_path = Path(".mm_config.yaml")
            save_config(self.config, config_path)
        except Exception as e:
            # Don't show error dialog when closing, just log it
            print(f"Warning: Failed to save GUI settings: {e}")

    def run(self):
        """Run the GUI application."""
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Start the main loop
        self.root.mainloop()

    def _on_closing(self):
        """Handle window closing."""
        # Save settings
        self._save_gui_settings()

        # Cleanup background processor
        self.background_processor.shutdown()

        # Close window
        self.root.destroy()
