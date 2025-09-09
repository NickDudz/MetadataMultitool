"""Clean operation panel."""

from pathlib import Path
from typing import Any, Dict

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...models.config_model import ConfigModel
from ...models.file_model import FileModel
from ...utils.icons import IconManager


class CleanPanel(QWidget):
    """Panel for clean operation settings."""

    # Signals
    operation_requested = pyqtSignal(str, dict)  # operation_type, options
    status_message = pyqtSignal(str)  # message

    def __init__(
        self,
        file_model: FileModel,
        config_model: ConfigModel,
        icon_manager: IconManager,
    ):
        super().__init__()

        self.file_model = file_model
        self.config_model = config_model
        self.icon_manager = icon_manager

        # UI components
        self.output_folder_edit = None
        self.preserve_structure_check = None
        self.start_button = None

        self._setup_ui()
        self._setup_connections()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Output settings group
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout(output_group)

        # Output folder
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Output Folder:"))

        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("safe_upload")
        folder_layout.addWidget(self.output_folder_edit)

        browse_btn = QPushButton("Browse")
        browse_btn.setIcon(self.icon_manager.get_icon("folder"))
        browse_btn.clicked.connect(self._browse_output_folder)
        folder_layout.addWidget(browse_btn)

        output_layout.addLayout(folder_layout)

        # Options
        self.preserve_structure_check = QCheckBox("Preserve directory structure")
        self.preserve_structure_check.setChecked(True)
        output_layout.addWidget(self.preserve_structure_check)

        layout.addWidget(output_group)

        # Start button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_button = QPushButton("Start Clean Operation")
        self.start_button.setIcon(self.icon_manager.get_icon("start"))
        self.start_button.clicked.connect(self._start_operation)
        button_layout.addWidget(self.start_button)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Save settings when changed
        self.output_folder_edit.textChanged.connect(self._save_settings)
        self.preserve_structure_check.toggled.connect(self._save_settings)

        # File model connections
        self.file_model.files_added.connect(self._update_button_state)
        self.file_model.files_removed.connect(self._update_button_state)
        self.file_model.files_cleared.connect(self._update_button_state)

    def _browse_output_folder(self) -> None:
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self.output_folder_edit.text()
        )

        if folder:
            self.output_folder_edit.setText(folder)

    def _start_operation(self) -> None:
        """Start clean operation."""
        if self.file_model.get_file_count() == 0:
            self.status_message.emit("No files selected")
            return

        # Collect options
        options = {
            "output_folder": self.output_folder_edit.text() or "safe_upload",
            "preserve_structure": self.preserve_structure_check.isChecked(),
        }

        # Emit operation request
        self.operation_requested.emit("clean", options)

    def _load_settings(self) -> None:
        """Load settings from config."""
        output_folder = self.config_model.get_operation_default(
            "clean", "output_folder", "safe_upload"
        )
        preserve_structure = self.config_model.get_operation_default(
            "clean", "preserve_structure", True
        )

        self.output_folder_edit.setText(output_folder)
        self.preserve_structure_check.setChecked(preserve_structure)

    def _save_settings(self) -> None:
        """Save current settings to config."""
        self.config_model.set_operation_default(
            "clean", "output_folder", self.output_folder_edit.text()
        )
        self.config_model.set_operation_default(
            "clean", "preserve_structure", self.preserve_structure_check.isChecked()
        )

    def _update_button_state(self) -> None:
        """Update button enabled state."""
        has_files = self.file_model.get_file_count() > 0
        self.start_button.setEnabled(has_files)
