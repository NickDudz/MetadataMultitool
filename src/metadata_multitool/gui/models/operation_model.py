"""Operation model for tracking processing state."""

from __future__ import annotations

from typing import Dict, Any, Optional, Callable
from enum import Enum
import threading


class OperationStatus(Enum):
    """Status of an operation."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class OperationModel:
    """Model for tracking operation state and progress."""
    
    def __init__(self):
        """Initialize the operation model."""
        self.status = OperationStatus.IDLE
        self.progress = 0.0  # 0.0 to 1.0
        self.current_file: Optional[str] = None
        self.total_files = 0
        self.processed_files = 0
        self.successful_files = 0
        self.failed_files = 0
        self.errors: list[str] = []
        self.status_message = "Ready"
        
        # Callbacks
        self.progress_callbacks: list[Callable[[float], None]] = []
        self.status_callbacks: list[Callable[[str], None]] = []
        self.completion_callbacks: list[Callable[[bool], None]] = []
        
        # Threading
        self._lock = threading.Lock()
        self._cancelled = False
        
    def start_operation(self, total_files: int, operation_name: str) -> None:
        """Start a new operation."""
        with self._lock:
            self.status = OperationStatus.RUNNING
            self.progress = 0.0
            self.current_file = None
            self.total_files = total_files
            self.processed_files = 0
            self.successful_files = 0
            self.failed_files = 0
            self.errors.clear()
            self.status_message = f"Starting {operation_name}..."
            self._cancelled = False
            
        self._notify_status_callbacks()
        
    def update_progress(self, processed: int, current_file: Optional[str] = None) -> None:
        """Update operation progress."""
        with self._lock:
            if self.status != OperationStatus.RUNNING:
                return
                
            self.processed_files = processed
            self.current_file = current_file
            
            if self.total_files > 0:
                self.progress = processed / self.total_files
            else:
                self.progress = 0.0
                
            self.status_message = f"Processing {processed}/{self.total_files} files"
            if current_file:
                self.status_message += f" - {current_file}"
                
        self._notify_progress_callbacks()
        self._notify_status_callbacks()
        
    def file_completed(self, success: bool, error_message: Optional[str] = None) -> None:
        """Mark a file as completed."""
        with self._lock:
            if success:
                self.successful_files += 1
            else:
                self.failed_files += 1
                if error_message:
                    self.errors.append(error_message)
                    
    def complete_operation(self, success: bool = True) -> None:
        """Complete the operation."""
        with self._lock:
            if success:
                self.status = OperationStatus.COMPLETED
                self.progress = 1.0
                self.status_message = f"Completed successfully. {self.successful_files} files processed."
            else:
                self.status = OperationStatus.ERROR
                self.status_message = f"Operation failed. {self.failed_files} files failed."
                
        self._notify_completion_callbacks(success)
        self._notify_status_callbacks()
        
    def cancel_operation(self) -> None:
        """Cancel the current operation."""
        with self._lock:
            self._cancelled = True
            self.status = OperationStatus.CANCELLED
            self.status_message = "Operation cancelled"
            
        self._notify_status_callbacks()
        
    def is_cancelled(self) -> bool:
        """Check if the operation is cancelled."""
        with self._lock:
            return self._cancelled
            
    def reset(self) -> None:
        """Reset the operation model."""
        with self._lock:
            self.status = OperationStatus.IDLE
            self.progress = 0.0
            self.current_file = None
            self.total_files = 0
            self.processed_files = 0
            self.successful_files = 0
            self.failed_files = 0
            self.errors.clear()
            self.status_message = "Ready"
            self._cancelled = False
            
        self._notify_status_callbacks()
        
    def add_progress_callback(self, callback: Callable[[float], None]) -> None:
        """Add a progress callback."""
        self.progress_callbacks.append(callback)
        
    def add_status_callback(self, callback: Callable[[str], None]) -> None:
        """Add a status callback."""
        self.status_callbacks.append(callback)
        
    def add_completion_callback(self, callback: Callable[[bool], None]) -> None:
        """Add a completion callback."""
        self.completion_callbacks.append(callback)
        
    def _notify_progress_callbacks(self) -> None:
        """Notify progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(self.progress)
            except Exception:
                pass  # Ignore callback errors
                
    def _notify_status_callbacks(self) -> None:
        """Notify status callbacks."""
        for callback in self.status_callbacks:
            try:
                callback(self.status_message)
            except Exception:
                pass  # Ignore callback errors
                
    def _notify_completion_callbacks(self, success: bool) -> None:
        """Notify completion callbacks."""
        for callback in self.completion_callbacks:
            try:
                callback(success)
            except Exception:
                pass  # Ignore callback errors
