"""Poison operation panel."""

from pathlib import Path
from typing import Any, Dict

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...models.config_model import ConfigModel
from ...models.file_model import FileModel
from ...utils.icons import IconManager


class PoisonPanel(QWidget):
    """Panel for poison operation settings."""

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
        self.preset_combo = None
        self.true_hint_edit = None
        self.output_format_checks = {}
        self.start_button = None

        self._setup_ui()
        self._setup_connections()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Poison settings group
        poison_group = QGroupBox("Poison Settings")
        poison_layout = QVBoxLayout(poison_group)

        # Preset selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["label_flip", "clip_confuse", "style_bloat"])
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()

        poison_layout.addLayout(preset_layout)

        # True hint
        hint_layout = QHBoxLayout()
        hint_layout.addWidget(QLabel("True Hint:"))

        self.true_hint_edit = QLineEdit()
        self.true_hint_edit.setPlaceholderText("Optional hint about true content")
        hint_layout.addWidget(self.true_hint_edit)

        poison_layout.addLayout(hint_layout)

        layout.addWidget(poison_group)

        # Output formats group
        formats_group = QGroupBox("Output Formats")
        formats_layout = QVBoxLayout(formats_group)

        # Create checkboxes for output formats
        formats = [
            ("XMP Sidecar", "xmp"),
            ("IPTC", "iptc"),
            ("EXIF", "exif"),
            ("Sidecar", "sidecar"),
            ("JSON", "json"),
            ("HTML", "html"),
        ]

        for label, key in formats:
            check = QCheckBox(label)
            self.output_format_checks[key] = check
            formats_layout.addWidget(check)

        layout.addWidget(formats_group)

        # Start button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_button = QPushButton("Start Poison Operation")
        self.start_button.setIcon(self.icon_manager.get_icon("start"))
        self.start_button.clicked.connect(self._start_operation)
        button_layout.addWidget(self.start_button)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Save settings when changed
        self.preset_combo.currentTextChanged.connect(self._save_settings)
        self.true_hint_edit.textChanged.connect(self._save_settings)

        for check in self.output_format_checks.values():
            check.toggled.connect(self._save_settings)

        # File model connections
        self.file_model.files_added.connect(self._update_button_state)
        self.file_model.files_removed.connect(self._update_button_state)
        self.file_model.files_cleared.connect(self._update_button_state)

    def _start_operation(self) -> None:
        """Start poison operation."""
        if self.file_model.get_file_count() == 0:
            self.status_message.emit("No files selected")
            return

        # Collect options
        output_formats = {}
        for key, check in self.output_format_checks.items():
            output_formats[key] = check.isChecked()

        options = {
            "preset": self.preset_combo.currentText(),
            "true_hint": self.true_hint_edit.text(),
            "output_formats": output_formats,
        }

        # Emit operation request
        self.operation_requested.emit("poison", options)

    def _load_settings(self) -> None:
        """Load settings from config."""
        preset = self.config_model.get_operation_default(
            "poison", "preset", "label_flip"
        )
        true_hint = self.config_model.get_operation_default("poison", "true_hint", "")
        output_formats = self.config_model.get_operation_default(
            "poison",
            "output_formats",
            {
                "xmp": True,
                "iptc": True,
                "exif": False,
                "sidecar": True,
                "json": True,
                "html": False,
            },
        )

        # Set preset
        index = self.preset_combo.findText(preset)
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)

        self.true_hint_edit.setText(true_hint)

        # Set format checkboxes
        for key, check in self.output_format_checks.items():
            check.setChecked(output_formats.get(key, False))

    def _save_settings(self) -> None:
        """Save current settings to config."""
        output_formats = {}
        for key, check in self.output_format_checks.items():
            output_formats[key] = check.isChecked()

        self.config_model.set_operation_default(
            "poison", "preset", self.preset_combo.currentText()
        )
        self.config_model.set_operation_default(
            "poison", "true_hint", self.true_hint_edit.text()
        )
        self.config_model.set_operation_default(
            "poison", "output_formats", output_formats
        )

    def _update_button_state(self) -> None:
        """Update button enabled state."""
        has_files = self.file_model.get_file_count() > 0
        self.start_button.setEnabled(has_files)
