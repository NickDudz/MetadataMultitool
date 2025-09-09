"""Qt-based file model for managing selected files."""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import os
from dataclasses import dataclass, field
from datetime import datetime

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal, QVariant
from PyQt6.QtGui import QIcon


@dataclass
class FileInfo:
    """Information about a selected file."""
    
    path: Path
    name: str = ""
    size: int = 0
    modified: datetime = field(default_factory=datetime.now)
    extension: str = ""
    has_metadata: bool = False
    metadata_types: List[str] = field(default_factory=list)
    thumbnail_available: bool = False
    error_message: str = ""
    
    def __post_init__(self):
        if not self.name:
            self.name = self.path.name
        if not self.extension:
            self.extension = self.path.suffix.lower()


class FileModel(QAbstractTableModel):
    """Qt model for file list display and management."""
    
    # Signals
    files_added = pyqtSignal(list)  # List[Path]
    files_removed = pyqtSignal(list)  # List[Path]
    files_cleared = pyqtSignal()
    metadata_loaded = pyqtSignal(Path)  # File path
    
    # Column definitions
    COLUMNS = [
        ("Name", "name"),
        ("Size", "size"), 
        ("Modified", "modified"),
        ("Extension", "extension"),
        ("Has Metadata", "has_metadata")
    ]
    
    def __init__(self):
        super().__init__()
        
        self.files: List[FileInfo] = []
        self._path_to_index: Dict[Path, int] = {}
        
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of rows."""
        return len(self.files)
        
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns."""
        return len(self.COLUMNS)
        
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> QVariant:
        """Return header data."""
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self.COLUMNS):
                return QVariant(self.COLUMNS[section][0])
        return QVariant()
        
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> QVariant:
        """Return data for given index and role."""
        if not index.isValid():
            return QVariant()
            
        row = index.row()
        col = index.column()
        
        if not (0 <= row < len(self.files)) or not (0 <= col < len(self.COLUMNS)):
            return QVariant()
            
        file_info = self.files[row]
        column_attr = self.COLUMNS[col][1]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_data(file_info, column_attr)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._get_tooltip_data(file_info, column_attr)
        elif role == Qt.ItemDataRole.UserRole:
            return QVariant(file_info.path)
            
        return QVariant()
        
    def _get_display_data(self, file_info: FileInfo, column_attr: str) -> QVariant:
        """Get display data for a column."""
        if column_attr == "name":
            return QVariant(file_info.name)
        elif column_attr == "size":
            return QVariant(self._format_size(file_info.size))
        elif column_attr == "modified":
            return QVariant(file_info.modified.strftime("%Y-%m-%d %H:%M"))
        elif column_attr == "extension":
            return QVariant(file_info.extension)
        elif column_attr == "has_metadata":
            return QVariant("Yes" if file_info.has_metadata else "No")
        else:
            return QVariant(str(getattr(file_info, column_attr, "")))
            
    def _get_tooltip_data(self, file_info: FileInfo, column_attr: str) -> QVariant:
        """Get tooltip data for a column."""
        if column_attr == "name":
            tooltip = f"Full path: {file_info.path}"
            if file_info.error_message:
                tooltip += f"\nError: {file_info.error_message}"
            return QVariant(tooltip)
        elif column_attr == "size":
            return QVariant(f"{file_info.size:,} bytes")
        elif column_attr == "has_metadata":
            if file_info.metadata_types:
                return QVariant(f"Metadata types: {', '.join(file_info.metadata_types)}")
            else:
                return QVariant("No metadata detected")
        else:
            return QVariant("")
            
    def _format_size(self, size: int) -> str:
        """Format file size for display."""
        if size == 0:
            return "0 B"
            
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size_float = float(size)
        
        while size_float >= 1024 and unit_index < len(units) - 1:
            size_float /= 1024
            unit_index += 1
            
        if unit_index == 0:
            return f"{int(size_float)} {units[unit_index]}"
        else:
            return f"{size_float:.1f} {units[unit_index]}"
            
    def add_files(self, file_paths: List[Path]) -> None:
        """Add files to the model."""
        if not file_paths:
            return
            
        # Filter out files that are already in the model
        new_files = []
        for file_path in file_paths:
            if file_path not in self._path_to_index:
                new_files.append(file_path)
                
        if not new_files:
            return
            
        # Begin insertion
        start_row = len(self.files)
        end_row = start_row + len(new_files) - 1
        
        self.beginInsertRows(QModelIndex(), start_row, end_row)
        
        # Add file info objects
        for file_path in new_files:
            file_info = self._create_file_info(file_path)
            self.files.append(file_info)
            self._path_to_index[file_path] = len(self.files) - 1
            
        self.endInsertRows()
        
        # Emit signal
        self.files_added.emit(new_files)
        
        # Load metadata asynchronously for new files
        for file_path in new_files:
            self._load_file_metadata_async(file_path)
            
    def remove_files(self, file_paths: List[Path]) -> None:
        """Remove files from the model."""
        if not file_paths:
            return
            
        # Find files that exist in model
        indices_to_remove = []
        for file_path in file_paths:
            if file_path in self._path_to_index:
                index = self._path_to_index[file_path]
                indices_to_remove.append(index)
                
        if not indices_to_remove:
            return
            
        # Sort indices in descending order to remove from end first
        indices_to_remove.sort(reverse=True)
        
        removed_paths = []
        for index in indices_to_remove:
            if 0 <= index < len(self.files):
                # Begin removal
                self.beginRemoveRows(QModelIndex(), index, index)
                
                # Remove file
                file_info = self.files.pop(index)
                removed_paths.append(file_info.path)
                
                # Update index mapping
                del self._path_to_index[file_info.path]
                
                # Update indices for remaining files
                for path, idx in self._path_to_index.items():
                    if idx > index:
                        self._path_to_index[path] = idx - 1
                        
                self.endRemoveRows()
                
        # Emit signal
        if removed_paths:
            self.files_removed.emit(removed_paths)
            
    def clear_files(self) -> None:
        """Clear all files from the model."""
        if not self.files:
            return
            
        self.beginResetModel()
        self.files.clear()
        self._path_to_index.clear()
        self.endResetModel()
        
        # Emit signal
        self.files_cleared.emit()
        
    def get_files(self) -> List[Path]:
        """Get all file paths."""
        return [file_info.path for file_info in self.files]
        
    def get_file_count(self) -> int:
        """Get number of files."""
        return len(self.files)
        
    def get_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """Get file info for a specific path."""
        index = self._path_to_index.get(file_path)
        if index is not None and 0 <= index < len(self.files):
            return self.files[index]
        return None
        
    def get_selected_files(self, indices: List[QModelIndex]) -> List[Path]:
        """Get file paths for selected indices."""
        paths = []
        for index in indices:
            if index.isValid():
                row = index.row()
                if 0 <= row < len(self.files):
                    paths.append(self.files[row].path)
        return paths
        
    def _create_file_info(self, file_path: Path) -> FileInfo:
        """Create FileInfo object from path."""
        try:
            stat = file_path.stat()
            return FileInfo(
                path=file_path,
                name=file_path.name,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
                extension=file_path.suffix.lower(),
                has_metadata=False,  # Will be updated asynchronously
                metadata_types=[],
                thumbnail_available=False
            )
        except OSError as e:
            return FileInfo(
                path=file_path,
                name=file_path.name,
                size=0,
                modified=datetime.now(),
                extension=file_path.suffix.lower(),
                has_metadata=False,
                metadata_types=[],
                thumbnail_available=False,
                error_message=str(e)
            )
            
    def _load_file_metadata_async(self, file_path: Path) -> None:
        """Load file metadata asynchronously."""
        # This would normally be done in a background thread
        # For now, we'll do a simple synchronous check
        
        try:
            # Simple metadata check - in practice this would use ExifTool or similar
            has_metadata = self._check_has_metadata(file_path)
            
            # Update file info
            index = self._path_to_index.get(file_path)
            if index is not None and 0 <= index < len(self.files):
                self.files[index].has_metadata = has_metadata
                
                # Emit data changed signal
                model_index = self.index(index, 4)  # Has metadata column
                self.dataChanged.emit(model_index, model_index)
                
                # Emit metadata loaded signal
                self.metadata_loaded.emit(file_path)
                
        except Exception as e:
            print(f"Error loading metadata for {file_path}: {e}")
            
    def _check_has_metadata(self, file_path: Path) -> bool:
        """Simple check if file has metadata."""
        try:
            # This is a placeholder - in practice would use ExifTool or PIL
            stat = file_path.stat()
            
            # Very basic heuristic - if file is readable and has reasonable size
            return stat.st_size > 1024  # Files > 1KB likely have some metadata
            
        except OSError:
            return False
            
    def filter_files(self, **filters) -> List[Path]:
        """Filter files based on criteria."""
        filtered = []
        
        for file_info in self.files:
            # Size filter
            if "min_size" in filters and file_info.size < filters["min_size"]:
                continue
            if "max_size" in filters and file_info.size > filters["max_size"]:
                continue
                
            # Extension filter
            if "extensions" in filters:
                if file_info.extension not in filters["extensions"]:
                    continue
                    
            # Metadata filter
            if "has_metadata" in filters:
                if file_info.has_metadata != filters["has_metadata"]:
                    continue
                    
            # Date filter
            if "min_date" in filters:
                if file_info.modified < filters["min_date"]:
                    continue
            if "max_date" in filters:
                if file_info.modified > filters["max_date"]:
                    continue
                    
            filtered.append(file_info.path)
            
        return filtered