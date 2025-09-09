"""Threading utilities for GUI background processing."""

from __future__ import annotations

import threading
from queue import Queue, Empty
from typing import Callable, Any, Optional
import time


class BackgroundProcessor:
    """Background processor for running tasks without blocking the GUI."""
    
    def __init__(self):
        """Initialize the background processor."""
        self.queue = Queue()
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.running = True
        self.thread.start()
        
    def submit(self, func: Callable, *args, callback: Optional[Callable] = None, **kwargs) -> None:
        """Submit a task to be processed in the background."""
        self.queue.put((func, args, kwargs, callback))
        
    def _process_queue(self) -> None:
        """Process tasks from the queue."""
        while self.running:
            try:
                func, args, kwargs, callback = self.queue.get(timeout=1.0)
                try:
                    result = func(*args, **kwargs)
                    if callback:
                        callback(result, None)
                except Exception as e:
                    if callback:
                        callback(None, e)
                finally:
                    self.queue.task_done()
            except Empty:
                continue
            except Exception:
                # Log error and continue
                continue
                
    def shutdown(self) -> None:
        """Shutdown the background processor."""
        self.running = False
        self.thread.join(timeout=5.0)


class ProgressTracker:
    """Track progress of background operations."""
    
    def __init__(self, total: int, callback: Optional[Callable[[int, int], None]] = None):
        """Initialize progress tracker.
        
        Args:
            total: Total number of items to process
            callback: Callback function called with (current, total)
        """
        self.total = total
        self.current = 0
        self.callback = callback
        self._lock = threading.Lock()
        
    def update(self, increment: int = 1) -> None:
        """Update progress by increment."""
        with self._lock:
            self.current = min(self.current + increment, self.total)
            if self.callback:
                self.callback(self.current, self.total)
                
    def set_progress(self, current: int) -> None:
        """Set current progress."""
        with self._lock:
            self.current = min(current, self.total)
            if self.callback:
                self.callback(self.current, self.total)
                
    def get_progress(self) -> tuple[int, int]:
        """Get current progress as (current, total)."""
        with self._lock:
            return self.current, self.total
            
    def is_complete(self) -> bool:
        """Check if processing is complete."""
        with self._lock:
            return self.current >= self.total


class CancellableOperation:
    """Wrapper for operations that can be cancelled."""
    
    def __init__(self):
        """Initialize cancellable operation."""
        self._cancelled = False
        self._lock = threading.Lock()
        
    def cancel(self) -> None:
        """Cancel the operation."""
        with self._lock:
            self._cancelled = True
            
    def is_cancelled(self) -> bool:
        """Check if the operation is cancelled."""
        with self._lock:
            return self._cancelled
            
    def check_cancelled(self) -> None:
        """Raise exception if operation is cancelled."""
        if self.is_cancelled():
            raise OperationCancelledError("Operation was cancelled")
            
    def __enter__(self):
        """Enter context manager."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass


class OperationCancelledError(Exception):
    """Raised when an operation is cancelled."""
    pass
