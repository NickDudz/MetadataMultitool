"""Theme management for the application."""

from typing import Dict, Optional
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication


class ThemeManager(QObject):
    """Manages application themes and styling."""

    theme_changed = pyqtSignal(str)  # theme_name

    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.themes: Dict[str, str] = {}

        # Initialize theme paths
        self._initialize_themes()

    def _initialize_themes(self) -> None:
        """Initialize available themes."""
        resources_dir = Path(__file__).parent.parent.parent / "resources" / "styles"

        self.themes = {
            "light": str(resources_dir / "light_theme.qss"),
            "dark": str(resources_dir / "dark_theme.qss"),
        }

    def get_available_themes(self) -> list[str]:
        """Get list of available theme names."""
        return list(self.themes.keys())

    def get_current_theme(self) -> str:
        """Get current theme name."""
        return self.current_theme

    def apply_theme(self, theme_name: str) -> bool:
        """Apply a theme to the application."""
        if theme_name not in self.themes:
            print(f"Theme '{theme_name}' not found")
            return False

        theme_path = Path(self.themes[theme_name])

        # Load stylesheet
        stylesheet = self._load_stylesheet(theme_path)
        if stylesheet is None:
            # Fall back to default styling if theme file doesn't exist
            stylesheet = self._get_default_stylesheet(theme_name)

        # Apply to application
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)

        # Update current theme
        old_theme = self.current_theme
        self.current_theme = theme_name

        # Emit signal if theme changed
        if old_theme != theme_name:
            self.theme_changed.emit(theme_name)

        return True

    def _load_stylesheet(self, theme_path: Path) -> Optional[str]:
        """Load stylesheet from file."""
        try:
            if theme_path.exists():
                with open(theme_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            print(f"Error loading theme file {theme_path}: {e}")

        return None

    def _get_default_stylesheet(self, theme_name: str) -> str:
        """Get default stylesheet for theme."""
        if theme_name == "dark":
            return self._get_dark_theme_default()
        else:
            return self._get_light_theme_default()

    def _get_light_theme_default(self) -> str:
        """Default light theme stylesheet."""
        return """
/* Light Theme - Improved Contrast */
QMainWindow {
    background-color: #ffffff;
    color: #000000;
}

QWidget {
    color: #000000;
    background-color: #ffffff;
}

QLabel {
    color: #000000;
    background-color: transparent;
}

QDialog {
    background-color: #ffffff;
    color: #000000;
}

QFrame {
    background-color: #ffffff;
    color: #000000;
    border: none;
}

QFrame[frameShape="4"] {  /* StyledPanel */
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 6px;
}

QScrollArea {
    background-color: #ffffff;
    border: 1px solid #ced4da;
}

QScrollBar:vertical {
    background-color: #f8f9fa;
    width: 16px;
    border-radius: 8px;
}

QScrollBar::handle:vertical {
    background-color: #ced4da;
    border-radius: 8px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #adb5bd;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QScrollBar:horizontal {
    background-color: #f8f9fa;
    height: 16px;
    border-radius: 8px;
}

QScrollBar::handle:horizontal {
    background-color: #ced4da;
    border-radius: 8px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #adb5bd;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

QSpinBox {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 6px 8px;
    color: #000000;
}

QMenuBar {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    color: #000000;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
}

QMenuBar::item:selected {
    background-color: #e8f4fd;
    color: #0078d4;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    color: #000000;
    padding: 4px;
}

QMenu::item {
    background-color: transparent;
    padding: 6px 20px;
    margin: 2px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #e8f4fd;
    color: #0078d4;
}

QMenu::separator {
    height: 1px;
    background-color: #dee2e6;
    margin: 4px 8px;
}

QToolBar {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    spacing: 4px;
    padding: 8px;
    color: #000000;
}

QToolBar::separator {
    background: #d0d0d0;
    width: 1px;
    margin: 2px 4px;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 8px 16px;
    min-width: 80px;
    min-height: 32px;
    color: #000000;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #e8f4fd;
    border-color: #0078d4;
}

QPushButton:pressed {
    background-color: #005a9e;
    color: white;
}

QPushButton:disabled {
    background-color: #f8f9fa;
    color: #6c757d;
    border-color: #dee2e6;
}

QTabWidget {
    background-color: #ffffff;
    color: #000000;
}

QTabWidget::pane {
    border: 1px solid #ced4da;
    background-color: #ffffff;
    color: #000000;
    top: -1px;
}

QTabWidget::tab-bar {
    left: 5px;
    background-color: #ffffff;
}

QTabBar {
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f8f9fa;
    border: 1px solid #ced4da;
    border-bottom-color: #ced4da;
    padding: 8px 16px;
    margin-right: 2px;
    color: #000000;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom-color: #ffffff;
    border-bottom: 1px solid #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #e8f4fd;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #ced4da;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 4px;
    color: #000000;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    background-color: #f5f5f5;
}

QTreeView, QTableView, QListView {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    selection-background-color: #0078d4;
    selection-color: white;
    color: #000000;
}

QTreeView::item, QTableView::item, QListView::item {
    padding: 4px;
}

QTreeView::item:hover, QTableView::item:hover, QListView::item:hover {
    background-color: #e8f4fd;
}

QHeaderView::section {
    background-color: #f8f9fa;
    padding: 6px 8px;
    border: 1px solid #dee2e6;
    font-weight: bold;
    color: #000000;
}

QProgressBar {
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    text-align: center;
    background-color: #f0f0f0;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                     stop:0 #4CAF50, stop:1 #45a049);
    border-radius: 3px;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 6px 8px;
    color: #000000;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #0078d4;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 6px 8px;
    min-width: 80px;
    color: #000000;
}

QComboBox:hover {
    border-color: #0078d4;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(down_arrow_light.png);
    width: 12px;
    height: 12px;
}

QCheckBox, QRadioButton {
    spacing: 8px;
    color: #000000;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #ced4da;
    background-color: #ffffff;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    border: 1px solid #0078d4;
    background-color: #0078d4;
    border-radius: 3px;
}

QCheckBox::indicator:checked:hover {
    background-color: #106ebe;
}

QCheckBox::indicator:unchecked:hover {
    border-color: #0078d4;
}

QStatusBar {
    background-color: #f8f9fa;
    border-top: 1px solid #dee2e6;
    color: #000000;
}

QSplitter::handle {
    background-color: #d0d0d0;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QDockWidget {
    background-color: #ffffff;
    color: #000000;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QDockWidget::title {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-bottom: none;
    padding: 8px;
    color: #000000;
    font-weight: bold;
}

QDockWidget::close-button, QDockWidget::float-button {
    background: transparent;
    border: none;
}

QProgressBar {
    border: 1px solid #ced4da;
    border-radius: 6px;
    text-align: center;
    background-color: #ffffff;
    color: #000000;
    font-weight: 500;
    min-height: 20px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                     stop:0 #28a745, stop:1 #20c997);
    border-radius: 5px;
    margin: 1px;
}
"""

    def _get_dark_theme_default(self) -> str:
        """Default dark theme stylesheet."""
        return """
/* Dark Theme */
QMainWindow {
    background-color: #2d2d2d;
    color: #ffffff;
}

QMenuBar {
    background-color: #3d3d3d;
    border-bottom: 1px solid #555555;
    color: #ffffff;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
}

QMenuBar::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QToolBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #3d3d3d, stop:1 #2d2d2d);
    border: 1px solid #555555;
    spacing: 4px;
    padding: 4px;
}

QToolBar::separator {
    background: #555555;
    width: 1px;
    margin: 2px 4px;
}

QPushButton {
    background-color: #3d3d3d;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 16px;
    min-width: 80px;
    min-height: 24px;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #0078d4;
    border-color: #005a9e;
}

QPushButton:pressed {
    background-color: #005a9e;
    color: white;
}

QPushButton:disabled {
    background-color: #2d2d2d;
    color: #666666;
    border-color: #444444;
}

QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #2d2d2d;
}

QTabWidget::tab-bar {
    left: 5px;
}

QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #404040, stop:1 #353535);
    border: 1px solid #555555;
    border-bottom-color: #555555;
    padding: 8px 16px;
    margin-right: 2px;
    color: #ffffff;
}

QTabBar::tab:selected {
    background-color: #2d2d2d;
    border-bottom-color: #2d2d2d;
}

QTabBar::tab:hover {
    background-color: #0078d4;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #555555;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 4px;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    background-color: #2d2d2d;
}

QTreeView, QTableView, QListView {
    background-color: #2d2d2d;
    border: 1px solid #555555;
    selection-background-color: #0078d4;
    selection-color: white;
    color: #ffffff;
}

QTreeView::item, QTableView::item, QListView::item {
    padding: 4px;
}

QTreeView::item:hover, QTableView::item:hover, QListView::item:hover {
    background-color: #404040;
}

QHeaderView::section {
    background-color: #3d3d3d;
    padding: 6px 8px;
    border: 1px solid #555555;
    font-weight: bold;
    color: #ffffff;
}

QProgressBar {
    border: 1px solid #555555;
    border-radius: 4px;
    text-align: center;
    background-color: #3d3d3d;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                     stop:0 #4CAF50, stop:1 #45a049);
    border-radius: 3px;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2d2d2d;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #0078d4;
}

QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 80px;
    color: #ffffff;
}

QComboBox:hover {
    border-color: #0078d4;
}

QComboBox::drop-down {
    border: none;
}

QCheckBox, QRadioButton {
    spacing: 8px;
    color: #ffffff;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #555555;
    background-color: #2d2d2d;
}

QCheckBox::indicator:checked {
    border: 1px solid #0078d4;
    background-color: #0078d4;
}

QStatusBar {
    background-color: #3d3d3d;
    border-top: 1px solid #555555;
    color: #ffffff;
}

QSplitter::handle {
    background-color: #555555;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}
"""

    def detect_system_theme(self) -> str:
        """Detect system theme preference."""
        # For now, return light as default
        # In the future, this could check system preferences
        return "light"
