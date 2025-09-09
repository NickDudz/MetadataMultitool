"""Main controller for coordinating application business logic."""

from typing import List, Dict, Any, Optional
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from ..models.file_model import FileModel
from ..models.config_model import ConfigModel
from ..models.operation_model import OperationModel, OperationResult
from ..services.cli_service import (
    CLIService,
    CleanOptions,
    PoisonOptions,
    RevertOptions,
)


class MainController(QObject):
    """Main controller for coordinating business logic."""

    # Signals
    operation_started = pyqtSignal(str)  # operation_type
    operation_progress = pyqtSignal(int, int, str)  # current, total, current_file
    operation_completed = pyqtSignal(bool, str)  # success, message
    operation_error = pyqtSignal(str)  # error_message

    def __init__(
        self,
        file_model: FileModel,
        config_model: ConfigModel,
        operation_model: OperationModel,
        cli_service: CLIService,
    ):
        super().__init__()

        self.file_model = file_model
        self.config_model = config_model
        self.operation_model = operation_model
        self.cli_service = cli_service

        self._setup_connections()

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # CLI service connections
        self.cli_service.operation_started.connect(self._on_operation_started)
        self.cli_service.operation_progress.connect(self._on_operation_progress)
        self.cli_service.operation_completed.connect(self._on_operation_completed)
        self.cli_service.operation_error.connect(self._on_operation_error)

    def execute_clean(self, options_dict: Dict[str, Any]) -> None:
        """Execute clean operation."""
        files = self.file_model.get_files()
        if not files:
            self.operation_error.emit("No files selected")
            return

        # Validate files
        validation_result = self.cli_service.validate_files(files)
        if validation_result["missing"]:
            missing_files = [str(f) for f in validation_result["missing"]]
            self.operation_error.emit(f"Missing files: {', '.join(missing_files)}")
            return

        if validation_result["invalid"]:
            invalid_files = [str(f) for f in validation_result["invalid"]]
            self.operation_error.emit(
                f"Invalid file formats: {', '.join(invalid_files)}"
            )
            return

        # Create options from config and user input
        options = CleanOptions(
            output_folder=options_dict.get(
                "output_folder",
                self.config_model.get_operation_default(
                    "clean", "output_folder", "safe_upload"
                ),
            ),
            preserve_structure=options_dict.get(
                "preserve_structure",
                self.config_model.get_operation_default(
                    "clean", "preserve_structure", True
                ),
            ),
            batch_size=self.config_model.get_general_setting("batch_size", 100),
            max_workers=self.config_model.get_general_setting("max_workers", 4),
        )

        # Start operation
        self.cli_service.clean_files(validation_result["valid"], options)

    def execute_poison(self, options_dict: Dict[str, Any]) -> None:
        """Execute poison operation."""
        files = self.file_model.get_files()
        if not files:
            self.operation_error.emit("No files selected")
            return

        # Validate files
        validation_result = self.cli_service.validate_files(files)
        if validation_result["missing"]:
            missing_files = [str(f) for f in validation_result["missing"]]
            self.operation_error.emit(f"Missing files: {', '.join(missing_files)}")
            return

        if validation_result["invalid"]:
            invalid_files = [str(f) for f in validation_result["invalid"]]
            self.operation_error.emit(
                f"Invalid file formats: {', '.join(invalid_files)}"
            )
            return

        # Create options from config and user input
        default_formats = self.config_model.get_operation_default(
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

        options = PoisonOptions(
            preset=options_dict.get(
                "preset",
                self.config_model.get_operation_default(
                    "poison", "preset", "label_flip"
                ),
            ),
            true_hint=options_dict.get("true_hint", ""),
            output_formats=options_dict.get("output_formats", default_formats),
            rename_pattern=options_dict.get("rename_pattern", ""),
            csv_mapping_file=options_dict.get("csv_mapping_file"),
            batch_size=self.config_model.get_general_setting("batch_size", 100),
            max_workers=self.config_model.get_general_setting("max_workers", 4),
        )

        # Start operation
        self.cli_service.poison_files(validation_result["valid"], options)

    def execute_revert(self, options_dict: Dict[str, Any]) -> None:
        """Execute revert operation."""
        directory = options_dict.get("directory")
        if not directory:
            self.operation_error.emit("No directory specified")
            return

        directory_path = Path(directory)
        if not directory_path.exists():
            self.operation_error.emit(f"Directory does not exist: {directory}")
            return

        if not directory_path.is_dir():
            self.operation_error.emit(f"Path is not a directory: {directory}")
            return

        # Create options
        options = RevertOptions(
            directory=directory,
            batch_size=self.config_model.get_general_setting("batch_size", 100),
            max_workers=self.config_model.get_general_setting("max_workers", 4),
        )

        # Start operation
        self.cli_service.revert_directory(directory_path, options)

    def cancel_operation(self) -> None:
        """Cancel current operation."""
        if self.cli_service.is_operation_running():
            self.cli_service.cancel_operation()
            self.operation_model.cancel_operation()
        else:
            self.operation_error.emit("No operation running")

    def pause_operation(self) -> None:
        """Pause current operation."""
        if self.operation_model.is_running():
            # Note: CLI service doesn't support pause, so we just update the model
            self.operation_model.pause_operation()
        else:
            self.operation_error.emit("No operation running")

    def resume_operation(self) -> None:
        """Resume paused operation."""
        if self.operation_model.is_paused():
            # Note: CLI service doesn't support resume, so we just update the model
            self.operation_model.resume_operation()
        else:
            self.operation_error.emit("No operation paused")

    def is_operation_running(self) -> bool:
        """Check if operation is running."""
        return self.cli_service.is_operation_running()

    def get_operation_history(self) -> List[OperationResult]:
        """Get operation history."""
        return self.operation_model.history

    def get_operation_stats(self) -> Dict[str, Any]:
        """Get operation statistics."""
        return self.operation_model.get_summary_stats()

    def _on_operation_started(self, operation_type: str) -> None:
        """Handle operation started."""
        self.operation_model.start_operation(operation_type)
        self.operation_started.emit(operation_type)

    def _on_operation_progress(
        self, current: int, total: int, current_file: str
    ) -> None:
        """Handle operation progress."""
        self.operation_model.update_progress(current, total, current_file)
        self.operation_progress.emit(current, total, current_file)

    def _on_operation_completed(self, success: bool, message: str, result: Any) -> None:
        """Handle operation completion."""
        # Create operation result
        if result and hasattr(result, "processed_count"):
            # CLI service returned a result object
            operation_result = result
        else:
            # Create basic result
            operation_result = OperationResult(
                success=success,
                message=message,
                processed_count=0,
                error_count=0 if success else 1,
                errors=[] if success else [message],
            )

        self.operation_model.complete_operation(operation_result)
        self.operation_completed.emit(success, message)

    def _on_operation_error(self, error_message: str) -> None:
        """Handle operation error."""
        self.operation_error.emit(error_message)

    def shutdown(self) -> None:
        """Shutdown the controller and clean up resources."""
        # Cancel any running operations
        if self.is_operation_running():
            self.cancel_operation()

        # Shutdown CLI service
        self.cli_service.shutdown()
