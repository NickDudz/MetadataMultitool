"""Settings view for configuration management."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional

from ..models.config_model import ConfigModel
from ..utils.gui_utils import center_window, show_error, show_info, show_warning


class SettingsView:
    """View for settings and configuration management."""

    def __init__(self, parent: tk.Widget, config_model: ConfigModel):
        """Initialize the settings view."""
        self.parent = parent
        self.config_model = config_model
        self.frame: Optional[tk.Frame] = None

        # Widgets
        self.batch_size_var: Optional[tk.StringVar] = None
        self.max_workers_var: Optional[tk.StringVar] = None
        self.progress_bar_var: Optional[tk.BooleanVar] = None
        self.verbose_var: Optional[tk.BooleanVar] = None
        self.quiet_var: Optional[tk.BooleanVar] = None
        self.backup_var: Optional[tk.BooleanVar] = None
        self.log_level_var: Optional[tk.StringVar] = None
        self.theme_var: Optional[tk.StringVar] = None
        self.window_size_var: Optional[tk.StringVar] = None
        self.show_thumbnails_var: Optional[tk.BooleanVar] = None
        self.thumbnail_size_var: Optional[tk.StringVar] = None

    def setup(self, parent: tk.Widget) -> None:
        """Setup the settings view."""
        self.frame = ttk.Frame(parent, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create notebook for tabs
        notebook = ttk.Notebook(self.frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # General settings tab
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="General")
        self._setup_general_settings(general_frame)

        # Processing settings tab
        processing_frame = ttk.Frame(notebook, padding="10")
        notebook.add(processing_frame, text="Processing")
        self._setup_processing_settings(processing_frame)

        # GUI settings tab
        gui_frame = ttk.Frame(notebook, padding="10")
        notebook.add(gui_frame, text="GUI")
        self._setup_gui_settings(gui_frame)

        # Action buttons
        self._setup_action_buttons()

    def _setup_general_settings(self, parent: tk.Widget) -> None:
        """Setup general settings."""
        parent.columnconfigure(1, weight=1)

        # Log level
        ttk.Label(parent, text="Log Level:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 5)
        )
        self.log_level_var = tk.StringVar(
            value=self.config_model.get_value("log_level", "INFO")
        )
        log_level_combo = ttk.Combobox(
            parent,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly",
            width=15,
        )
        log_level_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))

        # Backup before operations
        self.backup_var = tk.BooleanVar(
            value=self.config_model.get_value("backup_before_operations", True)
        )
        backup_check = ttk.Checkbutton(
            parent, text="Create backup before operations", variable=self.backup_var
        )
        backup_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        # Verbose mode
        self.verbose_var = tk.BooleanVar(
            value=self.config_model.get_value("verbose", False)
        )
        verbose_check = ttk.Checkbutton(
            parent, text="Verbose output", variable=self.verbose_var
        )
        verbose_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # Quiet mode
        self.quiet_var = tk.BooleanVar(
            value=self.config_model.get_value("quiet", False)
        )
        quiet_check = ttk.Checkbutton(
            parent, text="Quiet output (minimal messages)", variable=self.quiet_var
        )
        quiet_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

    def _setup_processing_settings(self, parent: tk.Widget) -> None:
        """Setup processing settings."""
        parent.columnconfigure(1, weight=1)

        # Batch size
        ttk.Label(parent, text="Batch Size:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 5)
        )
        self.batch_size_var = tk.StringVar(
            value=str(self.config_model.get_value("batch_size", 100))
        )
        batch_size_entry = ttk.Entry(parent, textvariable=self.batch_size_var, width=15)
        batch_size_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        ttk.Label(parent, text="Number of files to process in each batch").grid(
            row=0, column=2, sticky=tk.W, padx=(10, 0), pady=(0, 5)
        )

        # Max workers
        ttk.Label(parent, text="Max Workers:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 5)
        )
        self.max_workers_var = tk.StringVar(
            value=str(self.config_model.get_value("max_workers", 4))
        )
        max_workers_entry = ttk.Entry(
            parent, textvariable=self.max_workers_var, width=15
        )
        max_workers_entry.grid(row=1, column=1, sticky=tk.W, pady=(10, 5))
        ttk.Label(parent, text="Maximum number of parallel worker processes").grid(
            row=1, column=2, sticky=tk.W, padx=(10, 0), pady=(10, 5)
        )

        # Progress bar
        self.progress_bar_var = tk.BooleanVar(
            value=self.config_model.get_value("progress_bar", True)
        )
        progress_check = ttk.Checkbutton(
            parent,
            text="Show progress bar during processing",
            variable=self.progress_bar_var,
        )
        progress_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))

        # Supported formats
        ttk.Label(parent, text="Supported Formats:").grid(
            row=3, column=0, sticky=(tk.W, tk.N), padx=(0, 10), pady=(10, 5)
        )
        formats_frame = ttk.Frame(parent)
        formats_frame.grid(
            row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5)
        )

        supported_formats = self.config_model.get_supported_formats()
        self.format_vars = {}

        for i, fmt in enumerate(supported_formats):
            var = tk.BooleanVar(value=True)
            self.format_vars[fmt] = var
            check = ttk.Checkbutton(formats_frame, text=fmt, variable=var)
            check.grid(row=i // 4, column=i % 4, sticky=tk.W, padx=(0, 10))

    def _setup_gui_settings(self, parent: tk.Widget) -> None:
        """Setup GUI-specific settings."""
        parent.columnconfigure(1, weight=1)

        # Theme
        ttk.Label(parent, text="Theme:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 5)
        )
        self.theme_var = tk.StringVar(
            value=self.config_model.get_gui_setting("theme", "light")
        )
        theme_combo = ttk.Combobox(
            parent,
            textvariable=self.theme_var,
            values=["light", "dark"],
            state="readonly",
            width=15,
        )
        theme_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))

        # Window size
        ttk.Label(parent, text="Window Size:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 5)
        )
        window_size = self.config_model.get_gui_setting("window_size", [1000, 700])
        self.window_size_var = tk.StringVar(value=f"{window_size[0]}x{window_size[1]}")
        window_size_entry = ttk.Entry(
            parent, textvariable=self.window_size_var, width=15
        )
        window_size_entry.grid(row=1, column=1, sticky=tk.W, pady=(10, 5))
        ttk.Label(parent, text="Width x Height (e.g., 1000x700)").grid(
            row=1, column=2, sticky=tk.W, padx=(10, 0), pady=(10, 5)
        )

        # Show thumbnails
        self.show_thumbnails_var = tk.BooleanVar(
            value=self.config_model.get_gui_setting("show_thumbnails", True)
        )
        thumbnails_check = ttk.Checkbutton(
            parent,
            text="Show file thumbnails in file list",
            variable=self.show_thumbnails_var,
        )
        thumbnails_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))

        # Thumbnail size
        ttk.Label(parent, text="Thumbnail Size:").grid(
            row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 5)
        )
        thumbnail_size = self.config_model.get_gui_setting("thumbnail_size", 64)
        self.thumbnail_size_var = tk.StringVar(value=str(thumbnail_size))
        thumbnail_size_entry = ttk.Entry(
            parent, textvariable=self.thumbnail_size_var, width=15
        )
        thumbnail_size_entry.grid(row=3, column=1, sticky=tk.W, pady=(10, 5))
        ttk.Label(parent, text="Size in pixels (e.g., 64)").grid(
            row=3, column=2, sticky=tk.W, padx=(10, 0), pady=(10, 5)
        )

        # Auto backup
        self.auto_backup_var = tk.BooleanVar(
            value=self.config_model.get_gui_setting("auto_backup", True)
        )
        auto_backup_check = ttk.Checkbutton(
            parent,
            text="Automatically create backups before operations",
            variable=self.auto_backup_var,
        )
        auto_backup_check.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))

        # Remember last folder
        self.remember_folder_var = tk.BooleanVar(
            value=self.config_model.get_gui_setting("remember_last_folder", True)
        )
        remember_folder_check = ttk.Checkbutton(
            parent, text="Remember last used folder", variable=self.remember_folder_var
        )
        remember_folder_check.grid(
            row=5, column=0, columnspan=3, sticky=tk.W, pady=(0, 5)
        )

    def _setup_action_buttons(self) -> None:
        """Setup action buttons."""
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        buttons_frame.columnconfigure(2, weight=1)  # Make middle column expandable

        save_btn = ttk.Button(buttons_frame, text="Save", command=self._save_settings)
        save_btn.grid(row=0, column=0, padx=(0, 10))

        reset_btn = ttk.Button(
            buttons_frame, text="Reset to Defaults", command=self._reset_settings
        )
        reset_btn.grid(row=0, column=1, padx=(0, 10))

        cancel_btn = ttk.Button(
            buttons_frame, text="Cancel", command=self._cancel_settings
        )
        cancel_btn.grid(row=0, column=2, sticky=tk.E)

    def _save_settings(self) -> None:
        """Save settings."""
        try:
            # Validate inputs
            if not self._validate_inputs():
                return

            # Update configuration
            self._update_config()

            # Save to file
            self.config_model.save_config()

            show_info("Settings Saved", "Settings have been saved successfully")

            # Close settings window
            if isinstance(self.parent, tk.Toplevel):
                self.parent.destroy()

        except Exception as e:
            show_error("Save Error", f"Failed to save settings: {e}")

    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
        result = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?\n\nThis action cannot be undone.",
        )

        if result:
            self._load_default_values()

    def _cancel_settings(self) -> None:
        """Cancel settings changes."""
        if isinstance(self.parent, tk.Toplevel):
            self.parent.destroy()

    def _validate_inputs(self) -> bool:
        """Validate input values."""
        # Validate batch size
        try:
            batch_size = int(self.batch_size_var.get())
            if batch_size <= 0:
                show_error("Invalid Input", "Batch size must be positive")
                return False
        except ValueError:
            show_error("Invalid Input", "Batch size must be a number")
            return False

        # Validate max workers
        try:
            max_workers = int(self.max_workers_var.get())
            if max_workers <= 0:
                show_error("Invalid Input", "Max workers must be positive")
                return False
        except ValueError:
            show_error("Invalid Input", "Max workers must be a number")
            return False

        # Validate window size
        try:
            size_str = self.window_size_var.get()
            if "x" in size_str:
                width, height = map(int, size_str.split("x"))
                if width <= 0 or height <= 0:
                    show_error("Invalid Input", "Window size must be positive")
                    return False
            else:
                show_error(
                    "Invalid Input", "Window size format: WIDTHxHEIGHT (e.g., 1000x700)"
                )
                return False
        except ValueError:
            show_error("Invalid Input", "Window size must be numbers")
            return False

        # Validate thumbnail size
        try:
            thumbnail_size = int(self.thumbnail_size_var.get())
            if thumbnail_size <= 0:
                show_error("Invalid Input", "Thumbnail size must be positive")
                return False
        except ValueError:
            show_error("Invalid Input", "Thumbnail size must be a number")
            return False

        return True

    def _update_config(self) -> None:
        """Update configuration with current values."""
        # General settings
        self.config_model.set_value("log_level", self.log_level_var.get())
        self.config_model.set_value("backup_before_operations", self.backup_var.get())
        self.config_model.set_value("verbose", self.verbose_var.get())
        self.config_model.set_value("quiet", self.quiet_var.get())

        # Processing settings
        self.config_model.set_value("batch_size", int(self.batch_size_var.get()))
        self.config_model.set_value("max_workers", int(self.max_workers_var.get()))
        self.config_model.set_value("progress_bar", self.progress_bar_var.get())

        # GUI settings
        self.config_model.set_gui_setting("theme", self.theme_var.get())

        # Window size
        size_str = self.window_size_var.get()
        width, height = map(int, size_str.split("x"))
        self.config_model.set_gui_setting("window_size", [width, height])

        self.config_model.set_gui_setting(
            "show_thumbnails", self.show_thumbnails_var.get()
        )
        self.config_model.set_gui_setting(
            "thumbnail_size", int(self.thumbnail_size_var.get())
        )
        self.config_model.set_gui_setting("auto_backup", self.auto_backup_var.get())
        self.config_model.set_gui_setting(
            "remember_last_folder", self.remember_folder_var.get()
        )

    def _load_default_values(self) -> None:
        """Load default values."""
        # General settings
        self.log_level_var.set("INFO")
        self.backup_var.set(True)
        self.verbose_var.set(False)
        self.quiet_var.set(False)

        # Processing settings
        self.batch_size_var.set("100")
        self.max_workers_var.set("4")
        self.progress_bar_var.set(True)

        # GUI settings
        self.theme_var.set("light")
        self.window_size_var.set("1000x700")
        self.show_thumbnails_var.set(True)
        self.thumbnail_size_var.set("64")
        self.auto_backup_var.set(True)
        self.remember_folder_var.set(True)
