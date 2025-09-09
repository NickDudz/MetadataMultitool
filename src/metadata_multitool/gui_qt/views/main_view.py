"""Main view containing tabbed operation interfaces."""

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from ..models.config_model import ConfigModel
from ..models.file_model import FileModel
from ..models.operation_model import OperationModel
from ..utils.icons import IconManager
from .common.theme_manager import ThemeManager
from .operation_panels.clean_panel import CleanPanel
from .operation_panels.poison_panel import PoisonPanel
from .operation_panels.revert_panel import RevertPanel


class MainView(QWidget):
    """Main view with tabbed operation interfaces."""

    # Signals
    operation_requested = pyqtSignal(str, dict)  # operation_type, options
    status_message = pyqtSignal(str)  # message

    def __init__(
        self,
        file_model: FileModel,
        config_model: ConfigModel,
        operation_model: OperationModel,
        icon_manager: IconManager,
        theme_manager: ThemeManager,
    ):
        super().__init__()

        self.file_model = file_model
        self.config_model = config_model
        self.operation_model = operation_model
        self.icon_manager = icon_manager
        self.theme_manager = theme_manager

        # Current mode
        self.current_mode = "clean"

        # UI components
        self.tab_widget: Optional[QTabWidget] = None
        self.clean_panel: Optional[CleanPanel] = None
        self.poison_panel: Optional[PoisonPanel] = None
        self.revert_panel: Optional[RevertPanel] = None

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create operation panels
        self.clean_panel = CleanPanel(
            self.file_model, self.config_model, self.icon_manager
        )
        self.poison_panel = PoisonPanel(
            self.file_model, self.config_model, self.icon_manager
        )
        self.revert_panel = RevertPanel(
            self.file_model, self.config_model, self.icon_manager
        )

        # Add tabs
        self.tab_widget.addTab(
            self.clean_panel, self.icon_manager.get_icon("clean"), "Clean"
        )
        self.tab_widget.addTab(
            self.poison_panel, self.icon_manager.get_icon("poison"), "Poison"
        )
        self.tab_widget.addTab(
            self.revert_panel, self.icon_manager.get_icon("revert"), "Revert"
        )

        layout.addWidget(self.tab_widget)

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Tab change
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Panel connections
        self.clean_panel.operation_requested.connect(self.operation_requested.emit)
        self.clean_panel.status_message.connect(self.status_message.emit)

        self.poison_panel.operation_requested.connect(self.operation_requested.emit)
        self.poison_panel.status_message.connect(self.status_message.emit)

        self.revert_panel.operation_requested.connect(self.operation_requested.emit)
        self.revert_panel.status_message.connect(self.status_message.emit)

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        modes = ["clean", "poison", "revert"]
        if 0 <= index < len(modes):
            self.current_mode = modes[index]
            self.status_message.emit(f"Switched to {self.current_mode} mode")

    def set_mode(self, mode: str) -> None:
        """Set the current mode."""
        mode_indices = {"clean": 0, "poison": 1, "revert": 2}
        if mode in mode_indices:
            self.tab_widget.setCurrentIndex(mode_indices[mode])

    def get_current_mode(self) -> str:
        """Get the current mode."""
        return self.current_mode
