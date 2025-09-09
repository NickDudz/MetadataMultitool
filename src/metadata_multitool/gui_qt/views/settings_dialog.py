"""Settings dialog for application configuration."""

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QComboBox, QGroupBox, QDialogButtonBox, QFileDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt

from ..models.config_model import ConfigModel
from .common.theme_manager import ThemeManager


class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    def __init__(self, config_model: ConfigModel, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        
        self.config_model = config_model
        self.theme_manager = theme_manager
        
        # UI components
        self.tab_widget = None
        
        # General settings
        self.batch_size_spin = None
        self.max_workers_spin = None
        self.backup_check = None
        self.log_level_combo = None
        
        # GUI settings
        self.theme_combo = None
        self.show_thumbnails_check = None
        self.remember_folder_check = None
        self.auto_save_check = None
        
        # Advanced settings
        self.debug_check = None
        self.exiftool_path_edit = None
        self.temp_dir_edit = None
        
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.tab_widget.addTab(self._create_general_tab(), "General")
        self.tab_widget.addTab(self._create_gui_tab(), "Interface")
        self.tab_widget.addTab(self._create_advanced_tab(), "Advanced")
        
        layout.addWidget(self.tab_widget)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_settings)
        
        layout.addWidget(button_box)
        
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Performance settings
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout(perf_group)
        
        # Batch size
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 1000)
        self.batch_size_spin.setValue(100)
        batch_layout.addWidget(self.batch_size_spin)
        batch_layout.addStretch()
        perf_layout.addLayout(batch_layout)
        
        # Max workers
        workers_layout = QHBoxLayout()
        workers_layout.addWidget(QLabel("Max Workers:"))
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 16)
        self.max_workers_spin.setValue(4)
        workers_layout.addWidget(self.max_workers_spin)
        workers_layout.addStretch()
        perf_layout.addLayout(workers_layout)
        
        layout.addWidget(perf_group)
        
        # Operation settings
        ops_group = QGroupBox("Operations")
        ops_layout = QVBoxLayout(ops_group)
        
        self.backup_check = QCheckBox("Create backups before operations")
        self.backup_check.setChecked(True)
        ops_layout.addWidget(self.backup_check)
        
        layout.addWidget(ops_group)
        
        # Logging settings
        log_group = QGroupBox("Logging")
        log_layout = QVBoxLayout(log_group)
        
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()
        log_layout.addLayout(log_level_layout)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        return tab
        
    def _create_gui_tab(self) -> QWidget:
        """Create GUI settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Appearance settings
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout(appearance_group)
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText("light")
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        
        layout.addWidget(appearance_group)
        
        # Display settings
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout(display_group)
        
        self.show_thumbnails_check = QCheckBox("Show file thumbnails")
        self.show_thumbnails_check.setChecked(True)
        display_layout.addWidget(self.show_thumbnails_check)
        
        layout.addWidget(display_group)
        
        # Behavior settings
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.remember_folder_check = QCheckBox("Remember last folder")
        self.remember_folder_check.setChecked(True)
        behavior_layout.addWidget(self.remember_folder_check)
        
        self.auto_save_check = QCheckBox("Auto-save settings")
        self.auto_save_check.setChecked(True)
        behavior_layout.addWidget(self.auto_save_check)
        
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        return tab
        
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Debug settings
        debug_group = QGroupBox("Debug")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_check = QCheckBox("Enable debug logging")
        debug_layout.addWidget(self.debug_check)
        
        layout.addWidget(debug_group)
        
        # Tool paths
        paths_group = QGroupBox("Tool Paths")
        paths_layout = QVBoxLayout(paths_group)
        
        # ExifTool path
        exif_layout = QHBoxLayout()
        exif_layout.addWidget(QLabel("ExifTool Path:"))
        self.exiftool_path_edit = QLineEdit()
        self.exiftool_path_edit.setPlaceholderText("Auto-detect")
        exif_layout.addWidget(self.exiftool_path_edit)
        
        exif_browse_btn = QPushButton("Browse")
        exif_browse_btn.clicked.connect(self._browse_exiftool)
        exif_layout.addWidget(exif_browse_btn)
        
        paths_layout.addLayout(exif_layout)
        
        # Temp directory
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temp Directory:"))
        self.temp_dir_edit = QLineEdit()
        self.temp_dir_edit.setPlaceholderText("System default")
        temp_layout.addWidget(self.temp_dir_edit)
        
        temp_browse_btn = QPushButton("Browse")
        temp_browse_btn.clicked.connect(self._browse_temp_dir)
        temp_layout.addWidget(temp_browse_btn)
        
        paths_layout.addLayout(temp_layout)
        
        layout.addWidget(paths_group)
        
        layout.addStretch()
        return tab
        
    def _browse_exiftool(self) -> None:
        """Browse for ExifTool executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ExifTool Executable",
            "",
            "Executable files (*.exe);;All files (*.*)"
        )
        
        if file_path:
            self.exiftool_path_edit.setText(file_path)
            
    def _browse_temp_dir(self) -> None:
        """Browse for temp directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Temp Directory",
            self.temp_dir_edit.text()
        )
        
        if directory:
            self.temp_dir_edit.setText(directory)
            
    def _load_settings(self) -> None:
        """Load current settings."""
        # General settings
        self.batch_size_spin.setValue(self.config_model.get_general_setting("batch_size", 100))
        self.max_workers_spin.setValue(self.config_model.get_general_setting("max_workers", 4))
        self.backup_check.setChecked(self.config_model.get_general_setting("backup_before_operations", True))
        
        log_level = self.config_model.get_general_setting("log_level", "INFO")
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
            
        # GUI settings
        theme = self.config_model.get_gui_setting("theme", "light")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
        self.show_thumbnails_check.setChecked(self.config_model.get_gui_setting("show_thumbnails", True))
        self.remember_folder_check.setChecked(self.config_model.get_gui_setting("remember_last_folder", True))
        self.auto_save_check.setChecked(self.config_model.get_gui_setting("auto_save_settings", True))
        
        # Advanced settings
        self.debug_check.setChecked(self.config_model.get_value("advanced.enable_debug_logging", False))
        self.exiftool_path_edit.setText(self.config_model.get_value("advanced.exiftool_path", ""))
        self.temp_dir_edit.setText(self.config_model.get_value("advanced.temp_directory", ""))
        
    def _apply_settings(self) -> None:
        """Apply current settings."""
        # General settings
        self.config_model.set_general_setting("batch_size", self.batch_size_spin.value())
        self.config_model.set_general_setting("max_workers", self.max_workers_spin.value())
        self.config_model.set_general_setting("backup_before_operations", self.backup_check.isChecked())
        self.config_model.set_general_setting("log_level", self.log_level_combo.currentText())
        
        # GUI settings
        old_theme = self.config_model.get_gui_setting("theme", "light")
        new_theme = self.theme_combo.currentText()
        
        self.config_model.set_gui_setting("theme", new_theme)
        self.config_model.set_gui_setting("show_thumbnails", self.show_thumbnails_check.isChecked())
        self.config_model.set_gui_setting("remember_last_folder", self.remember_folder_check.isChecked())
        self.config_model.set_gui_setting("auto_save_settings", self.auto_save_check.isChecked())
        
        # Advanced settings
        self.config_model.set_value("advanced.enable_debug_logging", self.debug_check.isChecked())
        self.config_model.set_value("advanced.exiftool_path", self.exiftool_path_edit.text())
        self.config_model.set_value("advanced.temp_directory", self.temp_dir_edit.text())
        
        # Apply theme change if needed
        if old_theme != new_theme:
            self.theme_manager.apply_theme(new_theme)
            
        # Save configuration
        if self.auto_save_check.isChecked():
            self.config_model.save_config()
            
    def accept(self) -> None:
        """Accept and apply settings."""
        self._apply_settings()
        super().accept()
        
    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        self._load_settings()