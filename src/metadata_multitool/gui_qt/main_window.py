"""Main window for the PyQt6 Metadata Multitool GUI."""

from typing import Optional, Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QMenuBar, QMenu, QToolBar, QStatusBar, QSplitter, QDockWidget,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt6.QtGui import QAction, QKeySequence

from .views.main_view import MainView
from .views.file_panel import FilePanel
from .views.progress_widget import ProgressWidget
from .views.settings_dialog import SettingsDialog
from .controllers.main_controller import MainController
from .models.file_model import FileModel
from .models.config_model import ConfigModel
from .models.operation_model import OperationModel
from .services.cli_service import CLIService
from .services.config_service import ConfigService
from .utils.icons import IconManager
from .views.common.theme_manager import ThemeManager


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    mode_changed = pyqtSignal(str)  # mode_name
    files_added = pyqtSignal(list)  # file_paths
    operation_requested = pyqtSignal(str, dict)  # operation_type, options
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.icon_manager = IconManager()
        self.theme_manager = ThemeManager()
        
        # Initialize services
        self.config_service = ConfigService()
        self.cli_service = CLIService()
        
        # Initialize models
        self.file_model = FileModel()
        self.config_model = ConfigModel(self.config_service)
        self.operation_model = OperationModel()
        
        # Initialize controller
        self.main_controller = MainController(
            self.file_model,
            self.config_model, 
            self.operation_model,
            self.cli_service
        )
        
        # UI components
        self.central_widget: Optional[QWidget] = None
        self.main_view: Optional[MainView] = None
        self.file_panel: Optional[FilePanel] = None
        self.progress_widget: Optional[ProgressWidget] = None
        
        # Dialogs
        self.settings_dialog: Optional[SettingsDialog] = None
        
        # Current mode
        self.current_mode = "clean"
        
        # Setup UI
        self._setup_window()
        self._setup_menus()
        # self._setup_toolbar()  # Removed empty toolbar
        self._setup_status_bar()
        self._setup_docks()
        self._setup_central_widget()
        self._setup_connections()
        
        # Load settings
        self._load_settings()
        
        # Initialize icon cache
        self.icon_manager.preload_icons()
        
    def _setup_window(self) -> None:
        """Setup main window properties."""
        self.setWindowTitle("Metadata Multitool v0.4.0")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Set application icon
        app_icon = self.icon_manager.get_icon("app")
        if app_icon:
            self.setWindowIcon(app_icon)
            
    def _setup_menus(self) -> None:
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Add files action
        add_files_action = QAction(self.icon_manager.get_icon("add"), "&Add Files...", self)
        add_files_action.setShortcut(QKeySequence.StandardKey.Open)
        add_files_action.setStatusTip("Add image files to process")
        add_files_action.triggered.connect(self._add_files)
        file_menu.addAction(add_files_action)
        
        # Add folder action
        add_folder_action = QAction(self.icon_manager.get_icon("folder"), "Add &Folder...", self)
        add_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        add_folder_action.setStatusTip("Add all images from a folder")
        add_folder_action.triggered.connect(self._add_folder)
        file_menu.addAction(add_folder_action)
        
        file_menu.addSeparator()
        
        # Clear files action
        clear_files_action = QAction(self.icon_manager.get_icon("clear"), "&Clear All", self)
        clear_files_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_files_action.setStatusTip("Clear all selected files")
        clear_files_action.triggered.connect(self._clear_files)
        file_menu.addAction(clear_files_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Settings action
        settings_action = QAction(self.icon_manager.get_icon("settings"), "&Settings...", self)
        settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
        settings_action.setStatusTip("Open application settings")
        settings_action.triggered.connect(self._show_settings)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Theme submenu
        theme_menu = view_menu.addMenu("&Theme")
        
        # Light theme action
        light_theme_action = QAction("&Light", self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(self.theme_manager.get_current_theme() == "light")
        light_theme_action.triggered.connect(lambda: self._change_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        # Dark theme action
        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.setChecked(self.theme_manager.get_current_theme() == "dark")
        dark_theme_action.triggered.connect(lambda: self._change_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About...", self)
        about_action.setStatusTip("About Metadata Multitool")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        # Help action
        help_action = QAction(self.icon_manager.get_icon("help"), "&Help...", self)
        help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_action.setStatusTip("Show application help")
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)
        
    def _setup_toolbar(self) -> None:
        """Setup toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Settings action
        settings_action = QAction(self.icon_manager.get_icon("settings"), "Settings", self)
        settings_action.setStatusTip("Open settings")
        settings_action.triggered.connect(self._show_settings)
        toolbar.addAction(settings_action)
        
        # Help action
        help_action = QAction(self.icon_manager.get_icon("help"), "Help", self)
        help_action.setStatusTip("Show help")
        help_action.triggered.connect(self._show_help)
        toolbar.addAction(help_action)
        
    def _setup_status_bar(self) -> None:
        """Setup status bar."""
        self.statusBar().showMessage("Ready")
        
    def _setup_docks(self) -> None:
        """Setup fixed panels (non-movable dock widgets)."""
        # File panel dock
        file_dock = QDockWidget("Files", self)
        # Make dock widget non-movable and non-closable
        file_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        file_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        
        self.file_panel = FilePanel(self.file_model, self.icon_manager)
        file_dock.setWidget(self.file_panel)
        
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, file_dock)
        
        # Progress panel dock
        progress_dock = QDockWidget("Progress", self)
        # Make dock widget non-movable and non-closable
        progress_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        progress_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        
        self.progress_widget = ProgressWidget(self.operation_model)
        progress_dock.setWidget(self.progress_widget)
        
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, progress_dock)
        
    def _setup_central_widget(self) -> None:
        """Setup central widget with main view."""
        self.main_view = MainView(
            self.file_model,
            self.config_model,
            self.operation_model,
            self.icon_manager,
            self.theme_manager
        )
        
        self.setCentralWidget(self.main_view)
        
    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # File panel connections
        if self.file_panel:
            self.file_panel.files_added.connect(self.files_added.emit)
            self.file_panel.files_removed.connect(self._update_status)
            
        # Main view connections
        if self.main_view:
            self.main_view.operation_requested.connect(self.operation_requested.emit)
            self.main_view.status_message.connect(self._update_status)
            # Connect tab changes to mode changes
            self.main_view.tab_widget.currentChanged.connect(self._on_main_view_tab_changed)
            
        # Progress widget connections
        if self.progress_widget:
            self.progress_widget.operation_cancelled.connect(self._cancel_operation)
            
        # Controller connections
        self.main_controller.operation_started.connect(self._on_operation_started)
        self.main_controller.operation_completed.connect(self._on_operation_completed)
        self.main_controller.operation_progress.connect(self._on_operation_progress)
        self.main_controller.operation_error.connect(self._on_operation_error)
        
        # Theme manager connections
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        
    def _change_mode(self, mode: str) -> None:
        """Change the current operation mode."""
        if mode == self.current_mode:
            return
            
        # Update current mode
        old_mode = self.current_mode
        self.current_mode = mode
        
        # Update main view
        if self.main_view:
            self.main_view.set_mode(mode)
            
        # Update status
        mode_descriptions = {
            "clean": "Clean Mode - Remove metadata from images",
            "poison": "Poison Mode - Add misleading metadata to images", 
            "revert": "Revert Mode - Undo previous operations"
        }
        self._update_status(mode_descriptions.get(mode, f"{mode.title()} Mode"))
        
        # Emit signal
        self.mode_changed.emit(mode)
        
    def _change_theme(self, theme: str) -> None:
        """Change the application theme."""
        self.theme_manager.apply_theme(theme)
        
    def _add_files(self) -> None:
        """Open file dialog to add files."""
        filetypes = [
            "Image files (*.jpg *.jpeg *.png *.tif *.tiff *.webp *.bmp)",
            "All files (*.*)"
        ]
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            ";;".join(filetypes)
        )
        
        if files:
            file_paths = [Path(f) for f in files]
            self.file_model.add_files(file_paths)
            self.files_added.emit(file_paths)
            self._update_status(f"Added {len(files)} files")
            
    def _add_folder(self) -> None:
        """Open folder dialog to add all images from a folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder"
        )
        
        if folder:
            folder_path = Path(folder)
            # Find all image files in the folder
            image_extensions = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"]
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(folder_path.glob(f"*{ext}"))
                image_files.extend(folder_path.glob(f"*{ext.upper()}"))
                
            if image_files:
                self.file_model.add_files(image_files)
                self.files_added.emit(image_files)
                self._update_status(f"Added {len(image_files)} files from folder")
            else:
                QMessageBox.warning(
                    self,
                    "No Images Found",
                    f"No image files found in {folder}"
                )
                
    def _clear_files(self) -> None:
        """Clear all selected files."""
        self.file_model.clear_files()
        self._update_status("Cleared all files")
        
    def _show_settings(self) -> None:
        """Show settings dialog."""
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self.config_model, self.theme_manager, self)
            
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()
        
    def _show_help(self) -> None:
        """Show help dialog."""
        help_text = """
<h2>Metadata Multitool Help</h2>

<h3>Clean Mode:</h3>
<ul>
<li>Strips metadata from images for safe upload</li>
<li>Creates clean copies in specified output folder</li>
<li>Never modifies original files</li>
</ul>

<h3>Poison Mode:</h3>
<ul>
<li>Adds misleading metadata to images</li>
<li>Useful for anti-scraping purposes</li>
<li>Multiple presets available</li>
<li>Optional sidecar file generation</li>
</ul>

<h3>Revert Mode:</h3>
<ul>
<li>Undoes previous operations</li>
<li>Removes sidecar files and metadata</li>
<li>Uses operation logs for accurate reversal</li>
</ul>

<p>For more information, visit the project documentation.</p>
        """
        
        QMessageBox.about(self, "Help", help_text)
        
    def _show_about(self) -> None:
        """Show about dialog."""
        about_text = """
<h2>Metadata Multitool v0.4.0</h2>
<p>A privacy-focused tool for managing image metadata.</p>
<p>Built with PyQt6 for modern desktop experience.</p>
<p><a href="https://github.com/NickDudz/MetadataMultitool">GitHub Repository</a></p>
        """
        
        QMessageBox.about(self, "About", about_text)
        
    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        self.statusBar().showMessage(message)
        
        # Clear message after 5 seconds
        QTimer.singleShot(5000, lambda: self.statusBar().clearMessage())
        
    def _on_operation_started(self, operation_type: str) -> None:
        """Handle operation started."""
        self._update_status(f"Starting {operation_type} operation...")
        
    def _on_operation_completed(self, success: bool, message: str) -> None:
        """Handle operation completed."""
        if success:
            self._update_status(f"Operation completed: {message}")
        else:
            self._update_status(f"Operation failed: {message}")
            
    def _on_operation_progress(self, current: int, total: int, current_file: str = "") -> None:
        """Handle operation progress."""
        if current_file:
            self._update_status(f"Processing {current}/{total}: {Path(current_file).name}")
        else:
            self._update_status(f"Processing {current}/{total} files")
            
    def _on_operation_error(self, error_message: str) -> None:
        """Handle operation error."""
        QMessageBox.critical(self, "Operation Error", error_message)
        
    def _cancel_operation(self) -> None:
        """Cancel current operation."""
        if self.main_controller:
            self.main_controller.cancel_operation()
            
    def _on_main_view_tab_changed(self, index: int) -> None:
        """Handle main view tab change."""
        modes = ["clean", "poison", "revert"]
        if 0 <= index < len(modes):
            self._change_mode(modes[index])
            
    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change."""
        self._update_status(f"Theme changed to {theme_name}")
        
    def _load_settings(self) -> None:
        """Load application settings."""
        settings = QSettings()
        
        # Window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Window state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
            
        # Theme
        theme = settings.value("theme", "light")
        self.theme_manager.apply_theme(theme)
        
    def _save_settings(self) -> None:
        """Save application settings."""
        settings = QSettings()
        
        # Window geometry and state
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        
        # Theme
        settings.setValue("theme", self.theme_manager.get_current_theme())
        
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Save settings
        self._save_settings()
        
        # Cancel any running operations
        if self.main_controller:
            self.main_controller.shutdown()
            
        # Accept close event
        event.accept()