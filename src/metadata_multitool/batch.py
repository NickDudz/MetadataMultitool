"""Batch processing utilities for handling large directories efficiently."""

from __future__ import annotations

import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from tqdm import tqdm

from .core import MetadataMultitoolError


class BatchProcessingError(MetadataMultitoolError):
    """Raised when batch processing operations fail."""

    pass


def process_batch(
    items: List[Path],
    process_func: Callable[[Path], Tuple[bool, str]],
    batch_size: int = 100,
    max_workers: int = 4,
    progress_bar: bool = True,
    desc: str = "Processing",
    disable_progress: bool = False,
    memory_limit_mb: float = 1024,
    show_eta: bool = True,
) -> Tuple[int, int, List[str]]:
    """
    Process a list of items in batches with parallel processing.

    Args:
        items: List of items to process
        process_func: Function to process each item, returns (success, message)
        batch_size: Number of items per batch
        max_workers: Maximum number of worker processes
        progress_bar: Whether to show progress bar
        desc: Description for progress bar
        disable_progress: Whether to disable progress bar entirely
        memory_limit_mb: Memory limit in MB for monitoring
        show_eta: Whether to show estimated time remaining

    Returns:
        Tuple of (successful_count, total_count, error_messages)

    Raises:
        BatchProcessingError: If batch processing fails
    """
    if not items:
        return 0, 0, []

    total = len(items)
    successful = 0
    errors = []

    # Determine number of workers (don't exceed available CPUs or item count)
    workers = min(max_workers, mp.cpu_count(), total)

    if workers <= 1:
        # Single-threaded processing
        return _process_sequential(
            items, process_func, progress_bar, desc, disable_progress
        )

    # Create batches
    batches = [items[i : i + batch_size] for i in range(0, total, batch_size)]

    try:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(_process_batch_worker, batch, process_func): batch
                for batch in batches
            }

            # Process results with progress bar
            if progress_bar and not disable_progress:
                start_time = time.time()
                with tqdm(total=total, desc=desc, unit="item") as pbar:
                    for future in as_completed(future_to_batch):
                        batch = future_to_batch[future]
                        try:
                            batch_successful, batch_errors = future.result()
                            successful += batch_successful
                            errors.extend(batch_errors)
                            pbar.update(len(batch))

                            # Update progress bar with ETA if enabled
                            if show_eta and successful > 0:
                                eta = calculate_eta(successful, total, start_time)
                                if eta:
                                    pbar.set_postfix(
                                        eta=eta, memory=f"{get_memory_usage():.1f}MB"
                                    )

                            # Check memory limit
                            if not check_memory_limit(memory_limit_mb):
                                errors.append(
                                    f"Memory limit exceeded ({memory_limit_mb}MB)"
                                )

                        except Exception as e:
                            errors.append(f"Batch processing error: {e}")
                            pbar.update(len(batch))
            else:
                # Process without progress bar
                for future in as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    try:
                        batch_successful, batch_errors = future.result()
                        successful += batch_successful
                        errors.extend(batch_errors)
                    except Exception as e:
                        errors.append(f"Batch processing error: {e}")

    except Exception as e:
        raise BatchProcessingError(f"Failed to process batches: {e}")

    return successful, total, errors


def _process_sequential(
    items: List[Path],
    process_func: Callable[[Path], Tuple[bool, str]],
    progress_bar: bool,
    desc: str,
    disable_progress: bool,
) -> Tuple[int, int, List[str]]:
    """Process items sequentially (fallback for single-threaded processing)."""
    total = len(items)
    successful = 0
    errors = []

    if progress_bar and not disable_progress:
        with tqdm(total=total, desc=desc, unit="item") as pbar:
            for item in items:
                try:
                    success, message = process_func(item)
                    if success:
                        successful += 1
                    else:
                        errors.append(f"{item}: {message}")
                except Exception as e:
                    errors.append(f"{item}: {e}")
                pbar.update(1)
    else:
        for item in items:
            try:
                success, message = process_func(item)
                if success:
                    successful += 1
                else:
                    errors.append(f"{item}: {message}")
            except Exception as e:
                errors.append(f"{item}: {e}")

    return successful, total, errors


def _process_batch_worker(
    batch: List[Path], process_func: Callable[[Path], Tuple[bool, str]]
) -> Tuple[int, List[str]]:
    """Worker function for processing a batch of items."""
    successful = 0
    errors = []

    for item in batch:
        try:
            success, message = process_func(item)
            if success:
                successful += 1
            else:
                errors.append(f"{item}: {message}")
        except Exception as e:
            errors.append(f"{item}: {e}")

    return successful, errors


def estimate_processing_time(
    items: List[Path],
    sample_size: int = 10,
    process_func: Optional[Callable[[Path], Tuple[bool, str]]] = None,
) -> Optional[float]:
    """
    Estimate processing time by sampling a few items.

    Args:
        items: List of items to process
        sample_size: Number of items to sample for timing
        process_func: Optional function to actually process items for timing

    Returns:
        Estimated time per item in seconds, or None if estimation fails
    """
    if len(items) < 2:
        return None

    sample_items = items[: min(sample_size, len(items))]

    try:
        start_time = time.time()

        if process_func:
            # Use actual processing function for accurate timing
            for item in sample_items:
                try:
                    process_func(item)
                except Exception:
                    # Continue with other items if one fails
                    pass
        else:
            # Fallback: estimate based on file characteristics
            for item in sample_items:
                if item.exists():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    # More realistic estimation based on file size and type
                    if item.suffix.lower() in [".tiff", ".tif"]:
                        # TIFF files are typically slower to process
                        time.sleep(min(0.02, size_mb * 0.002))
                    elif item.suffix.lower() in [".jpg", ".jpeg"]:
                        # JPEG files are typically faster
                        time.sleep(min(0.005, size_mb * 0.0005))
                    else:
                        # Other formats
                        time.sleep(min(0.01, size_mb * 0.001))

        elapsed = time.time() - start_time
        return elapsed / len(sample_items)
    except Exception:
        return None


def get_optimal_batch_size(total_items: int, max_workers: int = 4) -> int:
    """
    Calculate optimal batch size based on total items and workers.

    Args:
        total_items: Total number of items to process
        max_workers: Maximum number of workers

    Returns:
        Optimal batch size
    """
    if total_items <= 10:
        return 1
    elif total_items <= 100:
        return max(1, total_items // max_workers)
    else:
        return max(10, total_items // (max_workers * 4))


def get_memory_usage() -> float:
    """
    Get current memory usage in MB.

    Returns:
        Memory usage in MB
    """
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        # Fallback if psutil not available
        return 0.0


def check_memory_limit(memory_limit_mb: float = 1024) -> bool:
    """
    Check if current memory usage is within limits.

    Args:
        memory_limit_mb: Memory limit in MB

    Returns:
        True if within limits, False otherwise
    """
    current_memory = get_memory_usage()
    return current_memory < memory_limit_mb


def format_time_remaining(seconds: float) -> str:
    """
    Format time remaining in a human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def calculate_eta(processed: int, total: int, start_time: float) -> Optional[str]:
    """
    Calculate estimated time of arrival.

    Args:
        processed: Number of items processed
        total: Total number of items
        start_time: Start time of processing

    Returns:
        Formatted ETA string or None if cannot calculate
    """
    if processed <= 0:
        return None

    elapsed = time.time() - start_time
    rate = processed / elapsed
    remaining = total - processed

    if rate <= 0:
        return None

    eta_seconds = remaining / rate
    return format_time_remaining(eta_seconds)
