"""Progress widget for displaying operation progress."""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models.operation_model import (
    OperationModel,
    OperationProgress,
    OperationResult,
    OperationState,
)


class ProgressWidget(QWidget):
    """Widget for displaying operation progress and status."""

    # Signals
    operation_cancelled = pyqtSignal()
    operation_paused = pyqtSignal()
    operation_resumed = pyqtSignal()

    def __init__(self, operation_model: OperationModel):
        super().__init__()

        self.operation_model = operation_model

        # UI components
        self.status_label: Optional[QLabel] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.progress_text: Optional[QLabel] = None
        self.current_file_label: Optional[QLabel] = None
        self.cancel_btn: Optional[QPushButton] = None
        self.pause_btn: Optional[QPushButton] = None
        self.log_text: Optional[QTextEdit] = None

        # Timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.setInterval(100)  # Update every 100ms

        self._setup_ui()
        self._setup_connections()
        self._update_display()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Status section
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(4)

        # Status label
        self.status_label = QLabel("Ready")
        font = QFont()
        font.setBold(True)
        self.status_label.setFont(font)
        status_layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        # Progress text
        self.progress_text = QLabel("")
        self.progress_text.setVisible(False)
        status_layout.addWidget(self.progress_text)

        # Current file label
        self.current_file_label = QLabel("")
        self.current_file_label.setVisible(False)
        self.current_file_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(font.pointSize() - 1)
        self.current_file_label.setFont(font)
        status_layout.addWidget(self.current_file_label)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setVisible(False)
        self.pause_btn.setMinimumWidth(80)
        button_layout.addWidget(self.pause_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setMinimumWidth(80)
        button_layout.addWidget(self.cancel_btn)

        status_layout.addLayout(button_layout)

        layout.addWidget(status_frame)

        # Log section (initially hidden)
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setVisible(False)

        # Use monospace font for log
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.log_text.setFont(font)

        layout.addWidget(self.log_text)

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Model connections
        self.operation_model.state_changed.connect(self._on_state_changed)
        self.operation_model.progress_updated.connect(self._on_progress_updated)
        self.operation_model.operation_completed.connect(self._on_operation_completed)

        # Button connections
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.pause_btn.clicked.connect(self._on_pause_clicked)

    def _update_display(self) -> None:
        """Update the display based on current state."""
        state = self.operation_model.state

        # Update status label
        self.status_label.setText(self.operation_model.get_state_description())

        # Show/hide progress components based on state
        show_progress = state in [OperationState.RUNNING, OperationState.PAUSED]
        self.progress_bar.setVisible(show_progress)
        self.progress_text.setVisible(show_progress)
        self.current_file_label.setVisible(show_progress)

        # Show/hide control buttons
        show_controls = state in [OperationState.RUNNING, OperationState.PAUSED]
        self.cancel_btn.setVisible(show_controls)
        self.pause_btn.setVisible(show_controls)

        # Update pause button text
        if state == OperationState.PAUSED:
            self.pause_btn.setText("Resume")
        else:
            self.pause_btn.setText("Pause")

        # Update progress display
        if show_progress:
            progress = self.operation_model.progress
            self._update_progress_display(progress)

    def _update_progress_display(self, progress: OperationProgress) -> None:
        """Update progress display components."""
        # Update progress bar
        if progress.total > 0:
            self.progress_bar.setMaximum(progress.total)
            self.progress_bar.setValue(progress.current)
        else:
            self.progress_bar.setMaximum(0)  # Indeterminate progress

        # Update progress text
        progress_text = self.operation_model.get_progress_text()
        self.progress_text.setText(progress_text)

        # Update current file
        if progress.current_file:
            filename = Path(progress.current_file).name
            self.current_file_label.setText(f"Processing: {filename}")
        else:
            self.current_file_label.setText("")

    def _on_state_changed(self, state_str: str) -> None:
        """Handle state change."""
        self._update_display()

        # Start/stop update timer
        state = OperationState(state_str)
        if state == OperationState.RUNNING:
            self.update_timer.start()
        else:
            self.update_timer.stop()

        # Add log entry
        self._add_log_entry(f"State changed to: {state_str}")

    def _on_progress_updated(self, progress: OperationProgress) -> None:
        """Handle progress update."""
        self._update_progress_display(progress)

    def _on_operation_completed(self, result: OperationResult) -> None:
        """Handle operation completion."""
        self._update_display()

        # Add completion log entry
        if result.success:
            message = f"Operation completed successfully: {result.message}"
        else:
            message = f"Operation failed: {result.message}"

        self._add_log_entry(message)

        # Show log if there were errors
        if not result.success or result.errors:
            self._show_log()

            # Add error details to log
            for error in result.errors:
                self._add_log_entry(f"Error: {error}")

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.operation_cancelled.emit()

    def _on_pause_clicked(self) -> None:
        """Handle pause button click."""
        state = self.operation_model.state
        if state == OperationState.PAUSED:
            self.operation_resumed.emit()
        elif state == OperationState.RUNNING:
            self.operation_paused.emit()

    def _add_log_entry(self, message: str) -> None:
        """Add an entry to the log."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        self.log_text.append(log_entry)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _show_log(self) -> None:
        """Show the log text area."""
        self.log_text.setVisible(True)

    def _hide_log(self) -> None:
        """Hide the log text area."""
        self.log_text.setVisible(False)

    def toggle_log(self) -> None:
        """Toggle log visibility."""
        if self.log_text.isVisible():
            self._hide_log()
        else:
            self._show_log()

    def clear_log(self) -> None:
        """Clear the log."""
        self.log_text.clear()

    def get_log_text(self) -> str:
        """Get the current log text."""
        return self.log_text.toPlainText()
