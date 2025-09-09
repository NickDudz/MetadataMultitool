"""Enhanced logging utilities for the Metadata Multitool."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .core import MetadataMultitoolError


class LoggingError(MetadataMultitoolError):
    """Raised when logging operations fail."""

    pass


class OperationLogger:
    """Enhanced logger for tracking operations with timestamps and details."""
    
    def __init__(self, log_file: Optional[Path] = None, log_level: str = "INFO"):
        """
        Initialize the operation logger.
        
        Args:
            log_file: Path to log file (if None, uses default)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_file = log_file or Path(".mm_operations.log")
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Set up logger
        self.logger = logging.getLogger("metadata_multitool")
        self.logger.setLevel(self.log_level)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def log_operation_start(self, operation: str, details: Dict[str, Any]) -> None:
        """
        Log the start of an operation.
        
        Args:
            operation: Name of the operation
            details: Additional details about the operation
        """
        self.logger.info(f"Starting {operation}")
        self.logger.debug(f"Operation details: {json.dumps(details, indent=2)}")
    
    def log_operation_end(self, operation: str, success: bool, details: Dict[str, Any]) -> None:
        """
        Log the end of an operation.
        
        Args:
            operation: Name of the operation
            success: Whether the operation was successful
            details: Additional details about the operation result
        """
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Completed {operation} - {status}")
        self.logger.debug(f"Operation result: {json.dumps(details, indent=2)}")
    
    def log_file_processed(self, file_path: Path, operation: str, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log processing of a single file.
        
        Args:
            file_path: Path to the processed file
            operation: Name of the operation
            success: Whether the file was processed successfully
            details: Additional details about the file processing
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"File {operation}: {file_path.name} - {status}"
        
        if success:
            self.logger.debug(message)
        else:
            self.logger.warning(message)
        
        if details:
            self.logger.debug(f"File details: {json.dumps(details, indent=2)}")
    
    def log_batch_progress(self, operation: str, processed: int, total: int, errors: int) -> None:
        """
        Log batch processing progress.
        
        Args:
            operation: Name of the operation
            processed: Number of files processed
            total: Total number of files
            errors: Number of errors encountered
        """
        progress = (processed / total * 100) if total > 0 else 0
        self.logger.info(f"Batch {operation} progress: {processed}/{total} ({progress:.1f}%) - {errors} errors")
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """
        Log an error with context.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        self.logger.error(f"Error: {error}")
        if context:
            self.logger.error(f"Context: {context}")
    
    def log_warning(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a warning message.
        
        Args:
            message: Warning message
            details: Additional details about the warning
        """
        self.logger.warning(message)
        if details:
            self.logger.debug(f"Warning details: {json.dumps(details, indent=2)}")
    
    def log_info(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an info message.
        
        Args:
            message: Info message
            details: Additional details about the info
        """
        self.logger.info(message)
        if details:
            self.logger.debug(f"Info details: {json.dumps(details, indent=2)}")
    
    def log_debug(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a debug message.
        
        Args:
            message: Debug message
            details: Additional details about the debug info
        """
        self.logger.debug(message)
        if details:
            self.logger.debug(f"Debug details: {json.dumps(details, indent=2)}")


def get_logger(log_file: Optional[Path] = None, log_level: str = "INFO") -> OperationLogger:
    """
    Get a configured operation logger.
    
    Args:
        log_file: Path to log file (if None, uses default)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured OperationLogger instance
    """
    return OperationLogger(log_file, log_level)


def log_operation_summary(logger: OperationLogger, operation: str, results: Dict[str, Any]) -> None:
    """
    Log a summary of an operation.
    
    Args:
        logger: Operation logger instance
        operation: Name of the operation
        results: Dictionary containing operation results
    """
    total = results.get('total', 0)
    successful = results.get('successful', 0)
    failed = results.get('failed', 0)
    errors = results.get('errors', [])
    
    logger.log_info(f"Operation {operation} completed")
    logger.log_info(f"Total files: {total}")
    logger.log_info(f"Successful: {successful}")
    logger.log_info(f"Failed: {failed}")
    
    if errors:
        logger.log_warning(f"Errors encountered: {len(errors)}")
        for error in errors[:5]:  # Log first 5 errors
            logger.log_error(error, "File processing error")
        if len(errors) > 5:
            logger.log_warning(f"... and {len(errors) - 5} more errors")


def create_operation_log_entry(
    operation: str,
    file_path: Path,
    success: bool,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a structured log entry for an operation.
    
    Args:
        operation: Name of the operation
        file_path: Path to the processed file
        success: Whether the operation was successful
        details: Additional details about the operation
        
    Returns:
        Dictionary containing the log entry
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "file_path": str(file_path),
        "success": success,
    }
    
    if details:
        entry["details"] = details
    
    return entry


def write_operation_log(log_file: Path, entries: list[Dict[str, Any]]) -> None:
    """
    Write operation log entries to a file.
    
    Args:
        log_file: Path to the log file
        entries: List of log entries to write
        
    Raises:
        LoggingError: If the log file cannot be written
    """
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing log if it exists
        existing_entries = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    existing_entries = json.load(f)
            except (json.JSONDecodeError, OSError):
                # If file is corrupted or unreadable, start fresh
                existing_entries = []
        
        # Append new entries
        existing_entries.extend(entries)
        
        # Write back to file
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(existing_entries, f, indent=2, ensure_ascii=False)
            
    except OSError as e:
        raise LoggingError(f"Failed to write operation log to {log_file}: {e}")
    except (TypeError, ValueError) as e:
        raise LoggingError(f"Failed to serialize operation log entries: {e}")
