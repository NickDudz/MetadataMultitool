"""Revert operation panel."""

from typing import Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFileDialog, QTextEdit
)
from PyQt6.QtCore import pyqtSignal

from ...models.file_model import FileModel
from ...models.config_model import ConfigModel
from ...utils.icons import IconManager


class RevertPanel(QWidget):
    """Panel for revert operation settings."""
    
    # Signals
    operation_requested = pyqtSignal(str, dict)  # operation_type, options
    status_message = pyqtSignal(str)  # message
    
    def __init__(self, file_model: FileModel, config_model: ConfigModel, icon_manager: IconManager):
        super().__init__()
        
        self.file_model = file_model
        self.config_model = config_model
        self.icon_manager = icon_manager
        
        # UI components
        self.directory_edit = None
        self.info_text = None
        self.start_button = None
        
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Directory selection group
        dir_group = QGroupBox("Directory to Revert")
        dir_layout = QVBoxLayout(dir_group)
        
        # Directory path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Directory:"))
        
        self.directory_edit = QLineEdit()
        self.directory_edit.setPlaceholderText("Select directory to revert operations")
        path_layout.addWidget(self.directory_edit)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setIcon(self.icon_manager.get_icon("folder"))
        browse_btn.clicked.connect(self._browse_directory)
        path_layout.addWidget(browse_btn)
        
        dir_layout.addLayout(path_layout)
        
        layout.addWidget(dir_group)
        
        # Information text
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.setPlainText(
            "Revert operation will undo previous metadata operations in the selected directory.\n"
            "This will remove sidecar files and restore original metadata where possible.\n"
            "Make sure you have selected the correct directory before proceeding."
        )
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(info_group)
        
        # Start button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.start_button = QPushButton("Start Revert Operation")
        self.start_button.setIcon(self.icon_manager.get_icon("start"))
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self._start_operation)
        button_layout.addWidget(self.start_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Update button state when directory changes
        self.directory_edit.textChanged.connect(self._update_button_state)
        
    def _browse_directory(self) -> None:
        """Browse for directory to revert."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Revert",
            self.directory_edit.text()
        )
        
        if directory:
            self.directory_edit.setText(directory)
            
    def _start_operation(self) -> None:
        """Start revert operation."""
        directory = self.directory_edit.text().strip()
        if not directory:
            self.status_message.emit("No directory selected")
            return
            
        directory_path = Path(directory)
        if not directory_path.exists():
            self.status_message.emit("Directory does not exist")
            return
            
        if not directory_path.is_dir():
            self.status_message.emit("Path is not a directory")
            return
            
        # Collect options
        options = {
            "directory": directory
        }
        
        # Emit operation request
        self.operation_requested.emit("revert", options)
        
    def _update_button_state(self) -> None:
        """Update button enabled state."""
        directory = self.directory_edit.text().strip()
        has_directory = bool(directory)
        self.start_button.setEnabled(has_directory)