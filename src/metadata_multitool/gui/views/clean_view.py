"""Clean mode view for metadata stripping."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Optional

from ..models.config_model import ConfigModel
from ..models.file_model import FileModel
from ..models.operation_model import OperationModel
from ..utils.gui_utils import show_error, show_info, show_warning
from ..utils.validation_utils import (
    validate_batch_size,
    validate_max_workers,
    validate_path,
)


class CleanView:
    """View for clean mode operations."""

    def __init__(
        self,
        parent: tk.Widget,
        file_model: FileModel,
        config_model: ConfigModel,
        operation_model: OperationModel,
    ):
        """Initialize the clean view."""
        self.parent = parent
        self.file_model = file_model
        self.config_model = config_model
        self.operation_model = operation_model
        self.frame: Optional[tk.Frame] = None

        # Widgets
        self.output_folder_var: Optional[tk.StringVar] = None
        self.batch_size_var: Optional[tk.StringVar] = None
        self.max_workers_var: Optional[tk.StringVar] = None
        self.backup_var: Optional[tk.BooleanVar] = None
        self.progress_bar_var: Optional[tk.BooleanVar] = None

    def setup(self, parent: tk.Widget) -> None:
        """Setup the clean view."""
        self.frame = ttk.LabelFrame(parent, text="Clean Mode Options", padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.frame.columnconfigure(1, weight=1)

        # Output folder
        ttk.Label(self.frame, text="Output Folder:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )

        folder_frame = ttk.Frame(self.frame)
        folder_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        folder_frame.columnconfigure(0, weight=1)

        self.output_folder_var = tk.StringVar(value="safe_upload")
        output_entry = ttk.Entry(folder_frame, textvariable=self.output_folder_var)
        output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        browse_btn = ttk.Button(
            folder_frame, text="Browse...", command=self._browse_output_folder
        )
        browse_btn.grid(row=0, column=1)

        # File filters section
        self._setup_file_filters()

        # Processing options section
        self._setup_processing_options()

        # Action buttons
        self._setup_action_buttons()

    def _setup_file_filters(self) -> None:
        """Setup file filtering options."""
        filters_frame = ttk.LabelFrame(self.frame, text="File Filters", padding="5")
        filters_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )
        filters_frame.columnconfigure(1, weight=1)

        # Size filter
        ttk.Label(filters_frame, text="Size:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        self.size_var = tk.StringVar()
        size_entry = ttk.Entry(filters_frame, textvariable=self.size_var, width=20)
        size_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        ttk.Label(filters_frame, text="(e.g., 1MB, 500KB-2MB, >1GB)").grid(
            row=0, column=2, sticky=tk.W
        )

        # Date filter
        ttk.Label(filters_frame, text="Date:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        self.date_var = tk.StringVar()
        date_entry = ttk.Entry(filters_frame, textvariable=self.date_var, width=20)
        date_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        ttk.Label(filters_frame, text="(e.g., 2024-01-01, 2024-01-01:2024-12-31)").grid(
            row=1, column=2, sticky=tk.W, pady=(5, 0)
        )

        # Format filter
        ttk.Label(filters_frame, text="Formats:").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        self.format_var = tk.StringVar(value=".jpg .jpeg .png .tif .tiff .webp .bmp")
        format_entry = ttk.Entry(filters_frame, textvariable=self.format_var, width=20)
        format_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        ttk.Label(filters_frame, text="(space-separated)").grid(
            row=2, column=2, sticky=tk.W, pady=(5, 0)
        )

        # Metadata filter
        self.metadata_var = tk.StringVar(value="all")
        metadata_frame = ttk.Frame(filters_frame)
        metadata_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0)
        )

        ttk.Radiobutton(
            metadata_frame, text="All files", variable=self.metadata_var, value="all"
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(
            metadata_frame, text="Has metadata", variable=self.metadata_var, value="has"
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(
            metadata_frame, text="No metadata", variable=self.metadata_var, value="none"
        ).pack(side=tk.LEFT)

    def _setup_processing_options(self) -> None:
        """Setup processing options."""
        options_frame = ttk.LabelFrame(
            self.frame, text="Processing Options", padding="5"
        )
        options_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )
        options_frame.columnconfigure(1, weight=1)

        # Backup option
        self.backup_var = tk.BooleanVar(value=True)
        backup_check = ttk.Checkbutton(
            options_frame,
            text="Create backup before processing",
            variable=self.backup_var,
        )
        backup_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # Progress bar option
        self.progress_bar_var = tk.BooleanVar(value=True)
        progress_check = ttk.Checkbutton(
            options_frame, text="Show progress bar", variable=self.progress_bar_var
        )
        progress_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # Batch size
        ttk.Label(options_frame, text="Batch size:").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5)
        )
        self.batch_size_var = tk.StringVar(
            value=str(self.config_model.get_value("batch_size", 100))
        )
        batch_size_entry = ttk.Entry(
            options_frame, textvariable=self.batch_size_var, width=10
        )
        batch_size_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 20))

        # Max workers
        ttk.Label(options_frame, text="Max workers:").grid(
            row=2, column=2, sticky=tk.W, padx=(0, 5)
        )
        self.max_workers_var = tk.StringVar(
            value=str(self.config_model.get_value("max_workers", 4))
        )
        max_workers_entry = ttk.Entry(
            options_frame, textvariable=self.max_workers_var, width=10
        )
        max_workers_entry.grid(row=2, column=3, sticky=tk.W)

    def _setup_action_buttons(self) -> None:
        """Setup action buttons."""
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0)
        )

        process_btn = ttk.Button(
            buttons_frame, text="Process", command=self._process_files
        )
        process_btn.pack(side=tk.LEFT, padx=(0, 10))

        dry_run_btn = ttk.Button(buttons_frame, text="Dry Run", command=self._dry_run)
        dry_run_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(buttons_frame, text="Clear", command=self._clear_options)
        clear_btn.pack(side=tk.LEFT)

    def _browse_output_folder(self) -> None:
        """Browse for output folder."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)

    def _process_files(self) -> None:
        """Process files for cleaning."""
        if not self._validate_inputs():
            return

        files = self.file_model.get_files()
        if not files:
            show_warning("No Files", "Please select files to process")
            return

        # Apply filters
        filtered_files = self._apply_filters(files)
        if not filtered_files:
            show_warning("No Files", "No files match the selected filters")
            return

        # Start processing
        self._start_clean_operation(filtered_files)

    def _dry_run(self) -> None:
        """Perform a dry run."""
        if not self._validate_inputs():
            return

        files = self.file_model.get_files()
        if not files:
            show_warning("No Files", "Please select files to process")
            return

        # Apply filters
        filtered_files = self._apply_filters(files)
        if not filtered_files:
            show_warning("No Files", "No files match the selected filters")
            return

        # Show dry run results
        self._show_dry_run_results(filtered_files)

    def _clear_options(self) -> None:
        """Clear all options."""
        self.output_folder_var.set("safe_upload")
        self.size_var.set("")
        self.date_var.set("")
        self.format_var.set(".jpg .jpeg .png .tif .tiff .webp .bmp")
        self.metadata_var.set("all")
        self.backup_var.set(True)
        self.progress_bar_var.set(True)
        self.batch_size_var.set(str(self.config_model.get_value("batch_size", 100)))
        self.max_workers_var.set(str(self.config_model.get_value("max_workers", 4)))

    def _validate_inputs(self) -> bool:
        """Validate input values."""
        # Validate batch size
        try:
            batch_size = int(self.batch_size_var.get())
            is_valid, error = validate_batch_size(batch_size)
            if not is_valid:
                show_error("Invalid Input", f"Batch size: {error}")
                return False
        except ValueError:
            show_error("Invalid Input", "Batch size must be a number")
            return False

        # Validate max workers
        try:
            max_workers = int(self.max_workers_var.get())
            is_valid, error = validate_max_workers(max_workers)
            if not is_valid:
                show_error("Invalid Input", f"Max workers: {error}")
                return False
        except ValueError:
            show_error("Invalid Input", "Max workers must be a number")
            return False

        return True

    def _apply_filters(self, files) -> list:
        """Apply file filters."""
        filters = {}

        # Size filter
        size_str = self.size_var.get().strip()
        if size_str:
            # TODO: Implement size filtering
            pass

        # Date filter
        date_str = self.date_var.get().strip()
        if date_str:
            # TODO: Implement date filtering
            pass

        # Format filter
        format_str = self.format_var.get().strip()
        if format_str:
            extensions = [ext.strip() for ext in format_str.split()]
            filters["extensions"] = extensions

        # Metadata filter
        metadata_filter = self.metadata_var.get()
        if metadata_filter == "has":
            filters["has_metadata"] = True
        elif metadata_filter == "none":
            filters["has_metadata"] = False

        return self.file_model.filter_files(**filters)

    def _start_clean_operation(self, files) -> None:
        """Start the clean operation."""
        # TODO: Implement actual clean operation
        # This would integrate with the CLI backend
        show_info(
            "Clean Operation",
            f"Would clean {len(files)} files to {self.output_folder_var.get()}",
        )

    def _show_dry_run_results(self, files) -> None:
        """Show dry run results."""
        output_folder = self.output_folder_var.get()
        results = []

        for file_path in files:
            info = self.file_model.get_file_info(file_path)
            size_str = (
                f"{info.get('size', 0) / 1024 / 1024:.1f} MB" if info else "Unknown"
            )
            results.append(
                f"{file_path.name} ({size_str}) → {output_folder}/{file_path.name}"
            )

        # Show results in a dialog
        result_text = f"DRY RUN: Would process {len(files)} files\n\n" + "\n".join(
            results
        )
        show_info("Dry Run Results", result_text)
