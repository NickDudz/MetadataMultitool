"""Operation model for tracking operation state and progress."""

from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal


class OperationState(Enum):
    """Operation state enumeration."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class OperationProgress:
    """Progress information for an operation."""

    current: int = 0
    total: int = 0
    current_file: str = ""
    message: str = ""
    percentage: float = 0.0

    def __post_init__(self):
        if self.total > 0:
            self.percentage = (self.current / self.total) * 100


@dataclass
class OperationResult:
    """Result of a completed operation."""

    success: bool
    message: str
    processed_count: int
    error_count: int
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class OperationModel(QObject):
    """Model for managing operation state and progress."""

    # Signals
    state_changed = pyqtSignal(str)  # state
    progress_updated = pyqtSignal(object)  # OperationProgress
    operation_completed = pyqtSignal(object)  # OperationResult
    operation_error = pyqtSignal(str)  # error_message

    def __init__(self):
        super().__init__()

        # Current operation state
        self._state = OperationState.IDLE
        self._operation_type = ""
        self._progress = OperationProgress()
        self._result: Optional[OperationResult] = None

        # Operation history
        self._history: List[OperationResult] = []

    @property
    def state(self) -> OperationState:
        """Get current operation state."""
        return self._state

    @property
    def operation_type(self) -> str:
        """Get current operation type."""
        return self._operation_type

    @property
    def progress(self) -> OperationProgress:
        """Get current progress."""
        return self._progress

    @property
    def result(self) -> Optional[OperationResult]:
        """Get current result."""
        return self._result

    @property
    def history(self) -> List[OperationResult]:
        """Get operation history."""
        return self._history.copy()

    def start_operation(self, operation_type: str) -> None:
        """Start a new operation."""
        self._operation_type = operation_type
        self._state = OperationState.RUNNING
        self._progress = OperationProgress()
        self._result = None

        # Emit signal
        self.state_changed.emit(self._state.value)

    def update_progress(
        self, current: int, total: int, current_file: str = "", message: str = ""
    ) -> None:
        """Update operation progress."""
        self._progress = OperationProgress(
            current=current, total=total, current_file=current_file, message=message
        )

        # Emit signal
        self.progress_updated.emit(self._progress)

    def complete_operation(self, result: OperationResult) -> None:
        """Complete the operation with a result."""
        self._state = (
            OperationState.COMPLETED if result.success else OperationState.ERROR
        )
        self._result = result

        # Add to history
        self._history.append(result)

        # Keep only last 50 operations in history
        if len(self._history) > 50:
            self._history = self._history[-50:]

        # Emit signals
        self.state_changed.emit(self._state.value)
        self.operation_completed.emit(result)

    def cancel_operation(self) -> None:
        """Cancel the current operation."""
        if self._state == OperationState.RUNNING:
            self._state = OperationState.CANCELLED
            self.state_changed.emit(self._state.value)

    def pause_operation(self) -> None:
        """Pause the current operation."""
        if self._state == OperationState.RUNNING:
            self._state = OperationState.PAUSED
            self.state_changed.emit(self._state.value)

    def resume_operation(self) -> None:
        """Resume a paused operation."""
        if self._state == OperationState.PAUSED:
            self._state = OperationState.RUNNING
            self.state_changed.emit(self._state.value)

    def reset(self) -> None:
        """Reset to idle state."""
        self._state = OperationState.IDLE
        self._operation_type = ""
        self._progress = OperationProgress()
        self._result = None

        self.state_changed.emit(self._state.value)

    def is_idle(self) -> bool:
        """Check if operation is idle."""
        return self._state == OperationState.IDLE

    def is_running(self) -> bool:
        """Check if operation is running."""
        return self._state == OperationState.RUNNING

    def is_paused(self) -> bool:
        """Check if operation is paused."""
        return self._state == OperationState.PAUSED

    def is_completed(self) -> bool:
        """Check if operation is completed."""
        return self._state == OperationState.COMPLETED

    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._state == OperationState.CANCELLED

    def is_error(self) -> bool:
        """Check if operation ended in error."""
        return self._state == OperationState.ERROR

    def get_state_description(self) -> str:
        """Get human-readable state description."""
        descriptions = {
            OperationState.IDLE: "Ready",
            OperationState.RUNNING: f"Running {self._operation_type}...",
            OperationState.PAUSED: f"Paused {self._operation_type}",
            OperationState.COMPLETED: f"Completed {self._operation_type}",
            OperationState.CANCELLED: f"Cancelled {self._operation_type}",
            OperationState.ERROR: f"Error in {self._operation_type}",
        }
        return descriptions.get(self._state, "Unknown state")

    def get_progress_text(self) -> str:
        """Get progress as text."""
        if self._progress.total == 0:
            return ""

        percentage = int(self._progress.percentage)
        text = f"{self._progress.current}/{self._progress.total} ({percentage}%)"

        if self._progress.current_file:
            from pathlib import Path

            filename = Path(self._progress.current_file).name
            text += f" - {filename}"

        return text

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics from history."""
        if not self._history:
            return {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "total_files_processed": 0,
                "total_errors": 0,
            }

        total_operations = len(self._history)
        successful_operations = sum(1 for r in self._history if r.success)
        failed_operations = total_operations - successful_operations
        total_files_processed = sum(r.processed_count for r in self._history)
        total_errors = sum(r.error_count for r in self._history)

        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "total_files_processed": total_files_processed,
            "total_errors": total_errors,
        }
