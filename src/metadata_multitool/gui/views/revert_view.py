"""Revert mode view for undoing operations."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Optional

from ..models.file_model import FileModel
from ..models.config_model import ConfigModel
from ..models.operation_model import OperationModel
from ..utils.gui_utils import show_error, show_warning, show_info
from ..utils.validation_utils import validate_path


class RevertView:
    """View for revert mode operations."""
    
    def __init__(self, parent: tk.Widget, file_model: FileModel, config_model: ConfigModel, operation_model: OperationModel):
        """Initialize the revert view."""
        self.parent = parent
        self.file_model = file_model
        self.config_model = config_model
        self.operation_model = operation_model
        self.frame: Optional[tk.Frame] = None
        
        # Widgets
        self.directory_var: Optional[tk.StringVar] = None
        self.files_listbox: Optional[tk.Listbox] = None
        self.scrollbar: Optional[ttk.Scrollbar] = None
        
    def setup(self, parent: tk.Widget) -> None:
        """Setup the revert view."""
        self.frame = ttk.LabelFrame(parent, text="Revert Mode Options", padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.frame.columnconfigure(1, weight=1)
        
        # Directory selection
        self._setup_directory_selection()
        
        # Files to revert
        self._setup_files_list()
        
        # Action buttons
        self._setup_action_buttons()
        
    def _setup_directory_selection(self) -> None:
        """Setup directory selection."""
        dir_frame = ttk.Frame(self.frame)
        dir_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.directory_var = tk.StringVar()
        dir_entry = ttk.Entry(dir_frame, textvariable=self.directory_var)
        dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(dir_frame, text="Browse...", command=self._browse_directory)
        browse_btn.grid(row=0, column=2)
        
        # Add change listener to update files list
        self.directory_var.trace('w', self._on_directory_changed)
        
    def _setup_files_list(self) -> None:
        """Setup files to revert list."""
        files_frame = ttk.LabelFrame(self.frame, text="Files to Revert", padding="5")
        files_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)
        
        # Listbox with scrollbar
        listbox_frame = ttk.Frame(files_frame)
        listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        self.files_listbox = tk.Listbox(listbox_frame, height=8)
        self.files_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.files_listbox.configure(yscrollcommand=self.scrollbar.set)
        
        # Status label
        self.status_label = ttk.Label(files_frame, text="No directory selected")
        self.status_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def _setup_action_buttons(self) -> None:
        """Setup action buttons."""
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        
        revert_btn = ttk.Button(buttons_frame, text="Revert", command=self._revert_files)
        revert_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        dry_run_btn = ttk.Button(buttons_frame, text="Dry Run", command=self._dry_run)
        dry_run_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_btn = ttk.Button(buttons_frame, text="Refresh", command=self._refresh_files)
        refresh_btn.pack(side=tk.LEFT)
        
    def _browse_directory(self) -> None:
        """Browse for directory."""
        directory = filedialog.askdirectory(title="Select Directory to Revert")
        if directory:
            self.directory_var.set(directory)
            
    def _on_directory_changed(self, *args) -> None:
        """Handle directory change."""
        self._refresh_files()
        
    def _refresh_files(self) -> None:
        """Refresh the files list."""
        if not self.files_listbox:
            return
            
        # Clear existing items
        self.files_listbox.delete(0, tk.END)
        
        directory = self.directory_var.get().strip()
        if not directory:
            self.status_label.config(text="No directory selected")
            return
            
        # Validate directory
        is_valid, path, error = validate_path(directory)
        if not is_valid:
            self.status_label.config(text=f"Invalid directory: {error}")
            return
            
        if not path.is_dir():
            self.status_label.config(text="Path is not a directory")
            return
            
        # Find files to revert
        files_to_revert = self._find_files_to_revert(path)
        
        if not files_to_revert:
            self.status_label.config(text="No files found to revert")
            return
            
        # Add files to listbox
        for file_path in files_to_revert:
            self.files_listbox.insert(tk.END, file_path.name)
            
        self.status_label.config(text=f"Found {len(files_to_revert)} files to revert")
        
    def _find_files_to_revert(self, directory: Path) -> list[Path]:
        """Find files that can be reverted."""
        files_to_revert = []
        
        # Look for sidecar files (.txt, .json, .html)
        for ext in [".txt", ".json", ".html"]:
            files_to_revert.extend(directory.glob(f"*{ext}"))
            
        # Look for .mm_operations.log file
        log_file = directory / ".mm_operations.log"
        if log_file.exists():
            # TODO: Parse log file to find processed images
            pass
            
        return files_to_revert
        
    def _revert_files(self) -> None:
        """Revert files."""
        directory = self.directory_var.get().strip()
        if not directory:
            show_warning("No Directory", "Please select a directory to revert")
            return
            
        # Validate directory
        is_valid, path, error = validate_path(directory)
        if not is_valid:
            show_error("Invalid Directory", f"Directory: {error}")
            return
            
        if not path.is_dir():
            show_error("Invalid Directory", "Path is not a directory")
            return
            
        # Confirm revert
        files_count = self.files_listbox.size()
        if files_count == 0:
            show_warning("No Files", "No files found to revert")
            return
            
        confirm = tk.messagebox.askyesno(
            "Confirm Revert",
            f"Are you sure you want to revert {files_count} files in {directory}?\n\nThis action cannot be undone."
        )
        
        if not confirm:
            return
            
        # Start revert operation
        self._start_revert_operation(path)
        
    def _dry_run(self) -> None:
        """Perform a dry run."""
        directory = self.directory_var.get().strip()
        if not directory:
            show_warning("No Directory", "Please select a directory to revert")
            return
            
        # Validate directory
        is_valid, path, error = validate_path(directory)
        if not is_valid:
            show_error("Invalid Directory", f"Directory: {error}")
            return
            
        if not path.is_dir():
            show_error("Invalid Directory", "Path is not a directory")
            return
            
        # Show dry run results
        files_to_revert = self._find_files_to_revert(path)
        
        if not files_to_revert:
            show_info("Dry Run Results", "No files found to revert")
            return
            
        results = [f"• {file_path.name}" for file_path in files_to_revert]
        result_text = f"DRY RUN: Would revert {len(files_to_revert)} files\n\n" + "\n".join(results)
        show_info("Dry Run Results", result_text)
        
    def _start_revert_operation(self, directory: Path) -> None:
        """Start the revert operation."""
        # TODO: Implement actual revert operation
        # This would integrate with the CLI backend
        files_count = self.files_listbox.size()
        show_info("Revert Operation", f"Would revert {files_count} files in {directory}")
