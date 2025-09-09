"""File panel for managing selected files."""

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QItemSelectionModel, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ..models.file_model import FileModel
from ..utils.icons import IconManager


class FilePanel(QWidget):
    """Panel for file selection and management."""

    # Signals
    files_added = pyqtSignal(list)  # List[Path]
    files_removed = pyqtSignal(list)  # List[Path]
    selection_changed = pyqtSignal(list)  # List[Path]

    def __init__(self, file_model: FileModel, icon_manager: IconManager):
        super().__init__()

        self.file_model = file_model
        self.icon_manager = icon_manager

        # UI components
        self.table_view: Optional[QTableView] = None
        self.add_files_btn: Optional[QPushButton] = None
        self.add_folder_btn: Optional[QPushButton] = None
        self.remove_btn: Optional[QPushButton] = None
        self.clear_btn: Optional[QPushButton] = None

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Button toolbar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # Add files button
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.setIcon(self.icon_manager.get_icon("add"))
        self.add_files_btn.setToolTip("Add individual image files")
        button_layout.addWidget(self.add_files_btn)

        # Add folder button
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.setIcon(self.icon_manager.get_icon("folder"))
        self.add_folder_btn.setToolTip("Add all images from a folder")
        button_layout.addWidget(self.add_folder_btn)

        button_layout.addStretch()

        # Remove button
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setIcon(self.icon_manager.get_icon("remove"))
        self.remove_btn.setToolTip("Remove selected files")
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)

        # Clear button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setIcon(self.icon_manager.get_icon("clear"))
        self.clear_btn.setToolTip("Clear all files")
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

        # File table
        self.table_view = QTableView()
        self.table_view.setModel(self.file_model)
        self.table_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_view.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Configure table headers
        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name column
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )  # Size column
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )  # Modified column
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )  # Extension column
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )  # Has metadata column

        layout.addWidget(self.table_view)

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Button connections
        self.add_files_btn.clicked.connect(self._add_files)
        self.add_folder_btn.clicked.connect(self._add_folder)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.clear_btn.clicked.connect(self._clear_all)

        # Table connections
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Selection change
        selection_model = self.table_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

        # Model connections
        self.file_model.files_added.connect(self.files_added.emit)
        self.file_model.files_removed.connect(self.files_removed.emit)
        self.file_model.files_cleared.connect(lambda: self.files_removed.emit([]))

    def _add_files(self) -> None:
        """Add individual files."""
        filetypes = [
            "Image files (*.jpg *.jpeg *.png *.tif *.tiff *.webp *.bmp)",
            "All files (*.*)",
        ]

        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", ";;".join(filetypes)
        )

        if files:
            file_paths = [Path(f) for f in files]
            self.file_model.add_files(file_paths)

    def _add_folder(self) -> None:
        """Add all images from a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")

        if folder:
            folder_path = Path(folder)
            # Find all image files in the folder
            image_extensions = [
                ".jpg",
                ".jpeg",
                ".png",
                ".tif",
                ".tiff",
                ".webp",
                ".bmp",
            ]
            image_files = []

            try:
                for ext in image_extensions:
                    image_files.extend(folder_path.glob(f"*{ext}"))
                    image_files.extend(folder_path.glob(f"*{ext.upper()}"))

                if image_files:
                    self.file_model.add_files(image_files)
                else:
                    QMessageBox.information(
                        self, "No Images Found", f"No image files found in {folder}"
                    )

            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error scanning folder: {str(e)}")

    def _remove_selected(self) -> None:
        """Remove selected files."""
        selection_model = self.table_view.selectionModel()
        if not selection_model:
            return

        selected_indexes = selection_model.selectedRows()
        if not selected_indexes:
            return

        selected_paths = self.file_model.get_selected_files(selected_indexes)
        if selected_paths:
            self.file_model.remove_files(selected_paths)

    def _clear_all(self) -> None:
        """Clear all files."""
        if self.file_model.get_file_count() == 0:
            return

        reply = QMessageBox.question(
            self,
            "Clear All Files",
            f"Are you sure you want to clear all {self.file_model.get_file_count()} files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.file_model.clear_files()

    def _show_context_menu(self, position) -> None:
        """Show context menu for table."""
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)

        # Remove action
        remove_action = QAction(self.icon_manager.get_icon("remove"), "Remove", self)
        remove_action.triggered.connect(self._remove_selected)
        menu.addAction(remove_action)

        menu.addSeparator()

        # Clear all action
        clear_action = QAction(self.icon_manager.get_icon("clear"), "Clear All", self)
        clear_action.triggered.connect(self._clear_all)
        menu.addAction(clear_action)

        # Show menu
        menu.exec(self.table_view.mapToGlobal(position))

    def _on_selection_changed(self, selected, deselected) -> None:
        """Handle selection change."""
        selection_model = self.table_view.selectionModel()
        if not selection_model:
            return

        selected_indexes = selection_model.selectedRows()
        selected_paths = self.file_model.get_selected_files(selected_indexes)

        # Enable/disable remove button
        self.remove_btn.setEnabled(len(selected_paths) > 0)

        # Emit selection changed signal
        self.selection_changed.emit(selected_paths)

    def get_selected_files(self) -> List[Path]:
        """Get currently selected files."""
        selection_model = self.table_view.selectionModel()
        if not selection_model:
            return []

        selected_indexes = selection_model.selectedRows()
        return self.file_model.get_selected_files(selected_indexes)

    def select_all(self) -> None:
        """Select all files."""
        if self.table_view:
            self.table_view.selectAll()

    def clear_selection(self) -> None:
        """Clear selection."""
        if self.table_view:
            self.table_view.clearSelection()
