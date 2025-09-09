"""Poison mode view for metadata poisoning."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Optional

from ..models.config_model import ConfigModel
from ..models.file_model import FileModel
from ..models.operation_model import OperationModel
from ..utils.gui_utils import show_error, show_info, show_warning
from ..utils.validation_utils import validate_path, validate_rename_pattern


class PoisonView:
    """View for poison mode operations."""

    def __init__(
        self,
        parent: tk.Widget,
        file_model: FileModel,
        config_model: ConfigModel,
        operation_model: OperationModel,
    ):
        """Initialize the poison view."""
        self.parent = parent
        self.file_model = file_model
        self.config_model = config_model
        self.operation_model = operation_model
        self.frame: Optional[tk.Frame] = None

        # Widgets
        self.preset_var: Optional[tk.StringVar] = None
        self.true_hint_var: Optional[tk.StringVar] = None
        self.rename_pattern_var: Optional[tk.StringVar] = None
        self.csv_file_var: Optional[tk.StringVar] = None

        # Output format checkboxes
        self.xmp_var: Optional[tk.BooleanVar] = None
        self.iptc_var: Optional[tk.BooleanVar] = None
        self.exif_var: Optional[tk.BooleanVar] = None
        self.sidecar_var: Optional[tk.BooleanVar] = None
        self.json_var: Optional[tk.BooleanVar] = None
        self.html_var: Optional[tk.BooleanVar] = None

    def setup(self, parent: tk.Widget) -> None:
        """Setup the poison view."""
        self.frame = ttk.LabelFrame(parent, text="Poison Mode Options", padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.frame.columnconfigure(1, weight=1)

        # Preset selection
        self._setup_preset_selection()

        # True hint input
        self._setup_true_hint()

        # Output formats
        self._setup_output_formats()

        # Rename pattern
        self._setup_rename_pattern()

        # CSV mapping
        self._setup_csv_mapping()

        # File filters (reuse from clean view)
        self._setup_file_filters()

        # Processing options (reuse from clean view)
        self._setup_processing_options()

        # Action buttons
        self._setup_action_buttons()

    def _setup_preset_selection(self) -> None:
        """Setup preset selection."""
        preset_frame = ttk.LabelFrame(
            self.frame, text="Poison Preset Selection", padding="10"
        )
        preset_frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        preset_frame.columnconfigure(1, weight=1)

        # Preset selection label
        ttk.Label(
            preset_frame, text="Poison Preset:", font=("TkDefaultFont", 10, "bold")
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Preset dropdown
        self.preset_var = tk.StringVar(value="label_flip")
        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=[
                "label_flip - Replace labels with misleading ones",
                "clip_confuse - Add confusing random tokens",
                "style_bloat - Add style-related keywords",
            ],
            state="readonly",
            width=50,
        )
        preset_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 10))

        # Description label
        self.description_var = tk.StringVar(
            value="Replace labels with misleading ones to confuse AI training"
        )
        description_label = ttk.Label(
            preset_frame, textvariable=self.description_var, wraplength=400
        )
        description_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # Bind selection change to update description
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        # Set initial description
        self._update_preset_description()

    def _on_preset_change(self, event=None) -> None:
        """Handle preset selection change."""
        self._update_preset_description()

    def _update_preset_description(self) -> None:
        """Update the description based on selected preset."""
        preset = self.preset_var.get()
        if "label_flip" in preset:
            description = "Replace labels with misleading ones to confuse AI training. Use 'True Hint' to specify the actual content."
        elif "clip_confuse" in preset:
            description = "Add confusing random tokens to make the image description nonsensical and unusable for training."
        elif "style_bloat" in preset:
            description = "Add style-related keywords to dilute the actual content description with irrelevant style information."
        else:
            description = "Select a poison mode to see description."

        self.description_var.set(description)

    def _setup_true_hint(self) -> None:
        """Setup true hint input."""
        hint_frame = ttk.Frame(self.frame)
        hint_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        hint_frame.columnconfigure(1, weight=1)

        ttk.Label(hint_frame, text="True Hint:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        self.true_hint_var = tk.StringVar()
        hint_entry = ttk.Entry(hint_frame, textvariable=self.true_hint_var)
        hint_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        ttk.Label(hint_frame, text="(Optional hint about real content)").grid(
            row=0, column=2, sticky=tk.W, padx=(5, 0)
        )

    def _setup_output_formats(self) -> None:
        """Setup output format options."""
        formats_frame = ttk.LabelFrame(self.frame, text="Output Formats", padding="5")
        formats_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Metadata formats
        metadata_frame = ttk.Frame(formats_frame)
        metadata_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(metadata_frame, text="Metadata:").pack(side=tk.LEFT, padx=(0, 10))

        self.xmp_var = tk.BooleanVar(value=True)
        xmp_check = ttk.Checkbutton(metadata_frame, text="XMP", variable=self.xmp_var)
        xmp_check.pack(side=tk.LEFT, padx=(0, 10))

        self.iptc_var = tk.BooleanVar(value=True)
        iptc_check = ttk.Checkbutton(
            metadata_frame, text="IPTC", variable=self.iptc_var
        )
        iptc_check.pack(side=tk.LEFT, padx=(0, 10))

        self.exif_var = tk.BooleanVar(value=False)
        exif_check = ttk.Checkbutton(
            metadata_frame, text="EXIF", variable=self.exif_var
        )
        exif_check.pack(side=tk.LEFT)

        # Sidecar formats
        sidecar_frame = ttk.Frame(formats_frame)
        sidecar_frame.pack(fill=tk.X)

        ttk.Label(sidecar_frame, text="Sidecars:").pack(side=tk.LEFT, padx=(0, 10))

        self.sidecar_var = tk.BooleanVar(value=True)
        sidecar_check = ttk.Checkbutton(
            sidecar_frame, text=".txt", variable=self.sidecar_var
        )
        sidecar_check.pack(side=tk.LEFT, padx=(0, 10))

        self.json_var = tk.BooleanVar(value=False)
        json_check = ttk.Checkbutton(
            sidecar_frame, text=".json", variable=self.json_var
        )
        json_check.pack(side=tk.LEFT, padx=(0, 10))

        self.html_var = tk.BooleanVar(value=False)
        html_check = ttk.Checkbutton(
            sidecar_frame, text=".html", variable=self.html_var
        )
        html_check.pack(side=tk.LEFT)

    def _setup_rename_pattern(self) -> None:
        """Setup rename pattern input."""
        rename_frame = ttk.Frame(self.frame)
        rename_frame.grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        rename_frame.columnconfigure(1, weight=1)

        ttk.Label(rename_frame, text="Rename Pattern:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        self.rename_pattern_var = tk.StringVar()
        rename_entry = ttk.Entry(rename_frame, textvariable=self.rename_pattern_var)
        rename_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        ttk.Label(rename_frame, text="(use {stem}, {rand})").grid(
            row=0, column=2, sticky=tk.W, padx=(5, 0)
        )

    def _setup_csv_mapping(self) -> None:
        """Setup CSV mapping file selection."""
        csv_frame = ttk.Frame(self.frame)
        csv_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        csv_frame.columnconfigure(1, weight=1)

        ttk.Label(csv_frame, text="CSV Mapping:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        self.csv_file_var = tk.StringVar()
        csv_entry = ttk.Entry(csv_frame, textvariable=self.csv_file_var)
        csv_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        browse_csv_btn = ttk.Button(
            csv_frame, text="Browse...", command=self._browse_csv_file
        )
        browse_csv_btn.grid(row=0, column=2)

    def _setup_file_filters(self) -> None:
        """Setup file filtering options (reuse from clean view)."""
        filters_frame = ttk.LabelFrame(self.frame, text="File Filters", padding="5")
        filters_frame.grid(
            row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
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
        """Setup processing options (reuse from clean view)."""
        options_frame = ttk.LabelFrame(
            self.frame, text="Processing Options", padding="5"
        )
        options_frame.grid(
            row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
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
            row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0)
        )

        process_btn = ttk.Button(
            buttons_frame, text="Process", command=self._process_files
        )
        process_btn.pack(side=tk.LEFT, padx=(0, 10))

        dry_run_btn = ttk.Button(buttons_frame, text="Dry Run", command=self._dry_run)
        dry_run_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(buttons_frame, text="Clear", command=self._clear_options)
        clear_btn.pack(side=tk.LEFT)

    def _browse_csv_file(self) -> None:
        """Browse for CSV mapping file."""
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        file_path = filedialog.askopenfilename(
            title="Select CSV Mapping File", filetypes=filetypes
        )
        if file_path:
            self.csv_file_var.set(file_path)

    def _process_files(self) -> None:
        """Process files for poisoning."""
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
        self._start_poison_operation(filtered_files)

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
        self.preset_var.set("label_flip - Replace labels with misleading ones")
        self.true_hint_var.set("")
        self.rename_pattern_var.set("")
        self.csv_file_var.set("")

        self.xmp_var.set(True)
        self.iptc_var.set(True)
        self.exif_var.set(False)
        self.sidecar_var.set(True)
        self.json_var.set(False)
        self.html_var.set(False)

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
        # Validate rename pattern
        pattern = self.rename_pattern_var.get().strip()
        if pattern:
            is_valid, error = validate_rename_pattern(pattern)
            if not is_valid:
                show_error("Invalid Input", f"Rename pattern: {error}")
                return False

        # Validate CSV file if provided
        csv_path = self.csv_file_var.get().strip()
        if csv_path:
            is_valid, path, error = validate_path(csv_path)
            if not is_valid:
                show_error("Invalid Input", f"CSV file: {error}")
                return False

        return True

    def _apply_filters(self, files) -> list:
        """Apply file filters (reuse from clean view)."""
        filters = {}

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

    def _start_poison_operation(self, files) -> None:
        """Start the poison operation."""
        # TODO: Implement actual poison operation
        # This would integrate with the CLI backend
        preset = self._get_selected_preset()
        show_info(
            "Poison Operation",
            f"Would poison {len(files)} files with preset '{preset}'",
        )

    def _show_dry_run_results(self, files) -> None:
        """Show dry run results."""
        preset = self._get_selected_preset()
        results = []

        for file_path in files:
            info = self.file_model.get_file_info(file_path)
            size_str = (
                f"{info.get('size', 0) / 1024 / 1024:.1f} MB" if info else "Unknown"
            )
            results.append(f"{file_path.name} ({size_str}) → '{preset}' preset")

        # Show results in a dialog
        result_text = (
            f"DRY RUN: Would poison {len(files)} files with preset '{preset}'\n\n"
            + "\n".join(results)
        )
        show_info("Dry Run Results", result_text)

    def _get_selected_preset(self) -> str:
        """Get the selected preset value from the dropdown."""
        preset_text = self.preset_var.get()
        # Extract the actual preset value (before the dash)
        if " - " in preset_text:
            return preset_text.split(" - ")[0]
        return preset_text
