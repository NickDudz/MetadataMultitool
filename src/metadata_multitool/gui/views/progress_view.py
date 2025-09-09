"""Progress view for displaying operation progress."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ..models.operation_model import OperationModel, OperationStatus


class ProgressView:
    """View for displaying operation progress."""
    
    def __init__(self, parent: tk.Widget, operation_model: OperationModel):
        """Initialize the progress view."""
        self.parent = parent
        self.operation_model = operation_model
        self.frame: Optional[tk.Frame] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.status_label: Optional[tk.Label] = None
        self.cancel_button: Optional[ttk.Button] = None
        
        # Setup callbacks
        self.operation_model.add_progress_callback(self._on_progress_update)
        self.operation_model.add_status_callback(self._on_status_update)
        self.operation_model.add_completion_callback(self._on_operation_complete)
        
    def setup(self, parent: tk.Widget, row: int = 0, column: int = 0, columnspan: int = 1) -> None:
        """Setup the progress view."""
        self.frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        self.frame.grid(row=row, column=column, columnspan=columnspan, sticky=(tk.W, tk.E), pady=(10, 0))
        self.frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.frame,
            mode="determinate",
            length=400
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Status label
        self.status_label = ttk.Label(
            self.frame,
            text="Ready",
            font=("Arial", 9)
        )
        self.status_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Cancel button
        self.cancel_button = ttk.Button(
            self.frame,
            text="Cancel",
            command=self._cancel_operation,
            state="disabled"
        )
        self.cancel_button.grid(row=2, column=0, sticky=tk.E, pady=(0, 5))
        
    def _on_progress_update(self, progress: float) -> None:
        """Handle progress update."""
        if self.progress_bar:
            self.progress_bar["value"] = progress * 100
            
    def _on_status_update(self, status_message: str) -> None:
        """Handle status update."""
        if self.status_label:
            self.status_label["text"] = status_message
            
        # Update cancel button state
        if self.cancel_button:
            if self.operation_model.status == OperationStatus.RUNNING:
                self.cancel_button["state"] = "normal"
            else:
                self.cancel_button["state"] = "disabled"
                
    def _on_operation_complete(self, success: bool) -> None:
        """Handle operation completion."""
        if self.cancel_button:
            self.cancel_button["state"] = "disabled"
            
    def _cancel_operation(self) -> None:
        """Cancel the current operation."""
        self.operation_model.cancel_operation()
        
    def reset(self) -> None:
        """Reset the progress view."""
        if self.progress_bar:
            self.progress_bar["value"] = 0
        if self.status_label:
            self.status_label["text"] = "Ready"
        if self.cancel_button:
            self.cancel_button["state"] = "disabled"
