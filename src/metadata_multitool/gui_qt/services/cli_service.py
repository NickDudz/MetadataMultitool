"""CLI service for integrating with the backend operations."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Iterator
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

# Add project root to path for CLI imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from metadata_multitool.core import iter_images, MetadataMultitoolError
from metadata_multitool.clean import clean_copy
from metadata_multitool.poison import write_metadata, write_sidecars
from metadata_multitool.revert import revert_dir
from metadata_multitool.config import load_config


@dataclass
class OperationOptions:
    """Base class for operation options."""
    
    batch_size: int = 100
    max_workers: int = 4
    dry_run: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "batch_size": self.batch_size,
            "max_workers": self.max_workers,
            "dry_run": self.dry_run
        }


@dataclass  
class CleanOptions(OperationOptions):
    """Options for clean operations."""
    
    output_folder: str = "safe_upload"
    preserve_structure: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result.update({
            "output_folder": self.output_folder,
            "preserve_structure": self.preserve_structure
        })
        return result


@dataclass
class PoisonOptions(OperationOptions):
    """Options for poison operations."""
    
    preset: str = "label_flip"
    true_hint: str = ""
    output_formats: Dict[str, bool] = None
    rename_pattern: str = ""
    csv_mapping_file: Optional[str] = None
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = {
                "xmp": True,
                "iptc": True,
                "exif": False,
                "sidecar": True,
                "json": True,
                "html": False
            }
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result.update({
            "preset": self.preset,
            "true_hint": self.true_hint,
            "output_formats": self.output_formats,
            "rename_pattern": self.rename_pattern,
            "csv_mapping_file": self.csv_mapping_file
        })
        return result


@dataclass
class RevertOptions(OperationOptions):
    """Options for revert operations."""
    
    directory: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result.update({
            "directory": self.directory
        })
        return result


@dataclass
class OperationResult:
    """Result of an operation."""
    
    success: bool
    message: str
    processed_count: int
    error_count: int
    errors: List[str]
    duration: float = 0.0


class OperationWorker(QObject):
    """Worker for executing operations in background thread."""
    
    # Signals
    progress = pyqtSignal(int, int, str)  # current, total, current_file
    finished = pyqtSignal(bool, str, object)  # success, message, result
    error = pyqtSignal(str)  # error_message
    
    def __init__(self, operation_func: Callable, *args, **kwargs):
        super().__init__()
        self.operation_func = operation_func
        self.args = args
        self.kwargs = kwargs
        self._cancelled = False
        
    def cancel(self) -> None:
        """Cancel the operation."""
        self._cancelled = True
        
    def run(self) -> None:
        """Execute the operation."""
        try:
            # Set up progress callback
            def progress_callback(current: int, total: int, current_file: str = ""):
                if not self._cancelled:
                    self.progress.emit(current, total, current_file)
                return not self._cancelled  # Return False if cancelled
                
            # Add progress callback to kwargs
            self.kwargs['progress_callback'] = progress_callback
            
            # Execute operation
            result = self.operation_func(*self.args, **self.kwargs)
            
            if self._cancelled:
                self.finished.emit(False, "Operation cancelled", None)
            else:
                self.finished.emit(True, "Operation completed successfully", result)
                
        except Exception as e:
            error_msg = f"Operation failed: {str(e)}"
            print(f"Operation error: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            self.error.emit(error_msg)
            self.finished.emit(False, error_msg, None)


class CLIService(QObject):
    """Service for integrating with CLI backend operations."""
    
    # Signals
    operation_started = pyqtSignal(str)  # operation_type
    operation_progress = pyqtSignal(int, int, str)  # current, total, current_file
    operation_completed = pyqtSignal(bool, str, object)  # success, message, result
    operation_error = pyqtSignal(str)  # error_message
    
    def __init__(self):
        super().__init__()
        
        # Thread management
        self._current_thread: Optional[QThread] = None
        self._current_worker: Optional[OperationWorker] = None
        
        # Configuration
        self.config = load_config()
        
    def is_operation_running(self) -> bool:
        """Check if an operation is currently running."""
        return (
            self._current_thread is not None and 
            self._current_thread.isRunning()
        )
        
    def cancel_operation(self) -> None:
        """Cancel the current operation."""
        if self._current_worker:
            self._current_worker.cancel()
            
    def clean_files(self, files: List[Path], options: CleanOptions) -> None:
        """Execute clean operation in background thread."""
        if self.is_operation_running():
            self.operation_error.emit("An operation is already running")
            return
            
        self._start_operation("clean", self._clean_files_impl, files, options)
        
    def poison_files(self, files: List[Path], options: PoisonOptions) -> None:
        """Execute poison operation in background thread."""
        if self.is_operation_running():
            self.operation_error.emit("An operation is already running")
            return
            
        self._start_operation("poison", self._poison_files_impl, files, options)
        
    def revert_directory(self, directory: Path, options: RevertOptions) -> None:
        """Execute revert operation in background thread."""
        if self.is_operation_running():
            self.operation_error.emit("An operation is already running")
            return
            
        self._start_operation("revert", self._revert_directory_impl, directory, options)
        
    def _start_operation(self, operation_type: str, operation_func: Callable, *args, **kwargs) -> None:
        """Start an operation in a background thread."""
        # Emit started signal
        self.operation_started.emit(operation_type)
        
        # Create worker
        self._current_worker = OperationWorker(operation_func, *args, **kwargs)
        
        # Create thread
        self._current_thread = QThread()
        
        # Move worker to thread
        self._current_worker.moveToThread(self._current_thread)
        
        # Connect signals
        self._current_worker.progress.connect(self.operation_progress.emit)
        self._current_worker.finished.connect(self._on_operation_finished)
        self._current_worker.error.connect(self.operation_error.emit)
        
        # Connect thread signals
        self._current_thread.started.connect(self._current_worker.run)
        self._current_worker.finished.connect(self._current_thread.quit)
        self._current_worker.finished.connect(self._current_worker.deleteLater)
        self._current_thread.finished.connect(self._current_thread.deleteLater)
        
        # Start thread
        self._current_thread.start()
        
    def _on_operation_finished(self, success: bool, message: str, result: Any) -> None:
        """Handle operation completion."""
        # Clean up references
        self._current_worker = None
        self._current_thread = None
        
        # Emit completion signal
        self.operation_completed.emit(success, message, result)
        
    def _clean_files_impl(self, files: List[Path], options: CleanOptions, progress_callback: Optional[Callable] = None) -> OperationResult:
        """Implementation of clean operation."""
        output_folder = Path(options.output_folder)
        processed_count = 0
        error_count = 0
        errors = []
        
        try:
            # Ensure output folder exists
            output_folder.mkdir(parents=True, exist_ok=True)
            
            total_files = len(files)
            
            for i, file_path in enumerate(files):
                # Check for cancellation
                if progress_callback and not progress_callback(i, total_files, str(file_path)):
                    break
                    
                try:
                    # Determine output path
                    if options.preserve_structure:
                        # Preserve directory structure relative to common root
                        output_path = output_folder / file_path.name
                    else:
                        output_path = output_folder / file_path.name
                        
                    # Ensure output path is unique
                    counter = 1
                    original_output_path = output_path
                    while output_path.exists():
                        stem = original_output_path.stem
                        suffix = original_output_path.suffix
                        output_path = original_output_path.parent / f"{stem}_{counter}{suffix}"
                        counter += 1
                        
                    # Clean copy the file
                    clean_copy(file_path, output_path)
                    processed_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"{file_path.name}: {str(e)}"
                    errors.append(error_msg)
                    print(f"Error cleaning {file_path}: {e}")
                    
            # Final progress update
            if progress_callback:
                progress_callback(total_files, total_files, "")
                
            return OperationResult(
                success=error_count == 0,
                message=f"Processed {processed_count} files, {error_count} errors",
                processed_count=processed_count,
                error_count=error_count,
                errors=errors
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Operation failed: {str(e)}",
                processed_count=processed_count,
                error_count=error_count + 1,
                errors=errors + [str(e)]
            )
            
    def _poison_files_impl(self, files: List[Path], options: PoisonOptions, progress_callback: Optional[Callable] = None) -> OperationResult:
        """Implementation of poison operation."""
        processed_count = 0
        error_count = 0
        errors = []
        
        try:
            total_files = len(files)
            
            for i, file_path in enumerate(files):
                # Check for cancellation
                if progress_callback and not progress_callback(i, total_files, str(file_path)):
                    break
                    
                try:
                    # Write metadata based on options
                    metadata_options = {
                        'preset': options.preset,
                        'true_hint': options.true_hint,
                        'output_formats': options.output_formats
                    }
                    
                    # Use the CLI poison functionality
                    write_metadata(file_path, **metadata_options)
                    
                    # Write sidecar files if requested
                    if options.output_formats.get("sidecar", False):
                        write_sidecars([file_path], metadata_options)
                        
                    processed_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"{file_path.name}: {str(e)}"
                    errors.append(error_msg)
                    print(f"Error poisoning {file_path}: {e}")
                    
            # Final progress update
            if progress_callback:
                progress_callback(total_files, total_files, "")
                
            return OperationResult(
                success=error_count == 0,
                message=f"Processed {processed_count} files, {error_count} errors",
                processed_count=processed_count,
                error_count=error_count,
                errors=errors
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Operation failed: {str(e)}",
                processed_count=processed_count,
                error_count=error_count + 1,
                errors=errors + [str(e)]
            )
            
    def _revert_directory_impl(self, directory: Path, options: RevertOptions, progress_callback: Optional[Callable] = None) -> OperationResult:
        """Implementation of revert operation."""
        try:
            if progress_callback:
                progress_callback(0, 1, f"Reverting {directory}")
                
            # Use CLI revert functionality
            result = revert_dir(directory)
            
            if progress_callback:
                progress_callback(1, 1, "")
                
            return OperationResult(
                success=True,
                message="Revert completed successfully",
                processed_count=1,
                error_count=0,
                errors=[]
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Revert failed: {str(e)}",
                processed_count=0,
                error_count=1,
                errors=[str(e)]
            )
            
    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats."""
        return [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"]
        
    def validate_files(self, file_paths: List[Path]) -> Dict[str, List[Path]]:
        """Validate files and return categorized results."""
        supported_formats = self.get_supported_formats()
        
        valid_files = []
        invalid_files = []
        missing_files = []
        
        for file_path in file_paths:
            if not file_path.exists():
                missing_files.append(file_path)
            elif file_path.suffix.lower() not in supported_formats:
                invalid_files.append(file_path)
            else:
                valid_files.append(file_path)
                
        return {
            "valid": valid_files,
            "invalid": invalid_files,
            "missing": missing_files
        }
        
    def shutdown(self) -> None:
        """Shutdown the service and clean up resources."""
        if self.is_operation_running():
            self.cancel_operation()
            
            # Wait for thread to finish (with timeout)
            if self._current_thread:
                self._current_thread.quit()
                self._current_thread.wait(3000)  # 3 second timeout