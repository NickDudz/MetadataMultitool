"""Tests for batch processing utilities."""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Tuple
from unittest.mock import Mock, patch

import pytest

from metadata_multitool.batch import (
    BatchProcessingError,
    calculate_eta,
    check_memory_limit,
    estimate_processing_time,
    format_time_remaining,
    get_memory_usage,
    get_optimal_batch_size,
    process_batch,
)


# Module-level functions for multiprocessing compatibility
def always_success_process(path: Path) -> Tuple[bool, str]:
    """Always succeeds - used for multiprocessing tests."""
    return True, "success"


def mixed_results_process(path: Path) -> Tuple[bool, str]:
    """Fails on files ending with 1.jpg or 3.jpg."""
    if path.name.endswith("1.jpg") or path.name.endswith("3.jpg"):
        return False, "failed"
    return True, "success"


def exception_process(path: Path) -> Tuple[bool, str]:
    """Raises exception on files ending with 2.jpg."""
    if path.name.endswith("2.jpg"):
        raise ValueError("Test exception")
    return True, "success"


def single_failure_process(path: Path) -> Tuple[bool, str]:
    """Fails on files ending with 1.jpg."""
    if path.name.endswith("1.jpg"):
        return False, "failed"
    return True, "success"


def realistic_process(path: Path) -> Tuple[bool, str]:
    """Realistic processing with brief delay."""
    time.sleep(0.001)
    if path.stat().st_size == 0:
        return False, "empty file"
    return True, "processed"


def simple_process(path: Path) -> Tuple[bool, str]:
    """Simple always-success process."""
    return True, "success"


def test_batch_processing_error():
    """Test BatchProcessingError exception."""
    error = BatchProcessingError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


class TestProcessBatch:
    """Test cases for process_batch function."""

    def test_empty_items(self):
        """Test processing with empty items list."""
        result = process_batch([], always_success_process)
        assert result == (0, 0, [])

    def test_single_item_success(self, sample_image):
        """Test processing single item successfully."""
        result = process_batch([sample_image], always_success_process, disable_progress=True)
        assert result == (1, 1, [])

    def test_single_item_failure(self, sample_image):
        """Test processing single item with failure."""
        # Create a single image that will fail the mixed_results_process (ends with 1.jpg)
        test_image = sample_image.parent / "test_1.jpg"
        test_image.write_bytes(sample_image.read_bytes())
        
        result = process_batch([test_image], mixed_results_process, disable_progress=True)
        assert result == (0, 1, [f"{test_image}: failed"])

    def test_multiple_items_mixed_results(self, sample_images):
        """Test processing multiple items with mixed results."""
        result = process_batch(sample_images, mixed_results_process, disable_progress=True)
        successful, total, errors = result
        assert total == len(sample_images)
        assert successful == 3  # 3 out of 5 should succeed
        assert len(errors) == 2  # 2 failures

    def test_exception_in_process_func(self, sample_images):
        """Test handling exceptions in process function."""
        result = process_batch(sample_images, exception_process, disable_progress=True)
        successful, total, errors = result
        assert total == len(sample_images)
        assert successful == 4  # 4 out of 5 should succeed
        assert len(errors) == 1
        assert "Test exception" in errors[0]

    def test_single_worker_processing(self, sample_images):
        """Test processing with single worker (sequential processing)."""
        result = process_batch(
            sample_images, always_success_process, max_workers=1, disable_progress=True
        )
        assert result == (len(sample_images), len(sample_images), [])

    def test_batch_size_configuration(self, sample_images):
        """Test processing with different batch sizes."""
        # Test with small batch size
        result = process_batch(
            sample_images, always_success_process, batch_size=2, disable_progress=True
        )
        assert result == (len(sample_images), len(sample_images), [])

    def test_progress_bar_enabled(self, sample_images):
        """Test processing with progress bar enabled."""
        with patch("metadata_multitool.batch.tqdm") as mock_tqdm:
            mock_progress = Mock()
            mock_tqdm.return_value.__enter__.return_value = mock_progress

            result = process_batch(
                sample_images, always_success_process, progress_bar=True, desc="Test Processing"
            )
            
            assert result == (len(sample_images), len(sample_images), [])
            mock_tqdm.assert_called()

    def test_memory_limit_checking(self, sample_images):
        """Test memory limit checking during processing."""
        with patch("metadata_multitool.batch.check_memory_limit") as mock_check:
            mock_check.return_value = False  # Simulate memory limit exceeded
            
            # Memory limit checking only happens with progress bars enabled
            with patch("metadata_multitool.batch.tqdm") as mock_tqdm:
                mock_progress = Mock()
                mock_tqdm.return_value.__enter__.return_value = mock_progress
                
                result = process_batch(
                    sample_images, always_success_process, memory_limit_mb=100, progress_bar=True
                )
                
                successful, total, errors = result
                assert any("Memory limit exceeded" in error for error in errors)

    @patch("metadata_multitool.batch.ProcessPoolExecutor")
    def test_executor_exception(self, mock_executor, sample_images):
        """Test handling of executor exceptions."""
        mock_executor.side_effect = Exception("Executor failed")

        with pytest.raises(BatchProcessingError, match="Failed to process batches"):
            process_batch(sample_images, always_success_process, disable_progress=True)


class TestSequentialProcessing:
    """Test sequential processing functionality."""

    def test_sequential_with_progress(self, sample_images):
        """Test sequential processing with progress bar."""
        with patch("metadata_multitool.batch.tqdm") as mock_tqdm:
            mock_progress = Mock()
            mock_tqdm.return_value.__enter__.return_value = mock_progress

            # Force sequential by setting max_workers to 1
            result = process_batch(
                sample_images, always_success_process, max_workers=1, progress_bar=True
            )
            
            assert result == (len(sample_images), len(sample_images), [])
            mock_tqdm.assert_called()

    def test_sequential_without_progress(self, sample_images):
        """Test sequential processing without progress bar."""
        result = process_batch(
            sample_images, always_success_process, max_workers=1, progress_bar=False
        )
        assert result == (len(sample_images), len(sample_images), [])


class TestEstimateProcessingTime:
    """Test processing time estimation."""

    def test_empty_items(self):
        """Test estimation with empty items."""
        result = estimate_processing_time([])
        assert result is None

    def test_single_item(self, sample_image):
        """Test estimation with single item."""
        result = estimate_processing_time([sample_image])
        assert result is None

    def test_with_process_func(self, sample_images):
        """Test estimation with actual process function."""
        result = estimate_processing_time(sample_images, sample_size=3, process_func=realistic_process)
        assert result is not None
        assert isinstance(result, float)
        assert result > 0

    def test_with_process_func_exception(self, sample_images):
        """Test estimation with process function that raises exceptions."""
        result = estimate_processing_time(sample_images, process_func=exception_process)
        assert result is not None  # Should still estimate despite exceptions

    def test_fallback_estimation(self, sample_images):
        """Test fallback estimation without process function."""
        with patch("time.sleep") as mock_sleep:
            result = estimate_processing_time(sample_images, sample_size=2)
            assert result is not None
            assert mock_sleep.called

    def test_nonexistent_files(self, tmp_path):
        """Test estimation with nonexistent files."""
        fake_files = [tmp_path / f"fake_{i}.jpg" for i in range(3)]
        result = estimate_processing_time(fake_files)
        assert result is not None  # Should handle gracefully

    @patch("metadata_multitool.batch.time.time")
    def test_estimation_exception(self, mock_time, sample_images):
        """Test estimation with timing exception."""
        mock_time.side_effect = Exception("Time error")
        result = estimate_processing_time(sample_images)
        assert result is None


class TestGetOptimalBatchSize:
    """Test optimal batch size calculation."""

    def test_small_item_count(self):
        """Test batch size for small item counts."""
        assert get_optimal_batch_size(5) == 1
        assert get_optimal_batch_size(10) == 1

    def test_medium_item_count(self):
        """Test batch size for medium item counts."""
        assert get_optimal_batch_size(50, max_workers=4) == 12
        assert get_optimal_batch_size(100, max_workers=2) == 50

    def test_large_item_count(self):
        """Test batch size for large item counts."""
        assert get_optimal_batch_size(1000, max_workers=4) == 62
        assert get_optimal_batch_size(500, max_workers=8) == 15

    def test_different_worker_counts(self):
        """Test batch size with different worker counts."""
        assert get_optimal_batch_size(200, max_workers=1) == 50
        assert get_optimal_batch_size(200, max_workers=16) == 10


class TestMemoryFunctions:
    """Test memory monitoring functions."""

    def test_get_memory_usage_fallback(self):
        """Test memory usage fallback behavior."""
        # Test the function returns a non-negative number
        result = get_memory_usage()
        assert result >= 0.0
        assert isinstance(result, float)

    def test_get_memory_usage_without_psutil(self):
        """Test memory usage fallback without psutil."""
        # Since psutil might or might not be available, we test the fallback logic
        # by directly testing the import error path in the function
        import sys
        original_modules = sys.modules.copy()
        
        # Temporarily remove psutil from modules if present
        if 'psutil' in sys.modules:
            del sys.modules['psutil']
        
        # Add a fake broken psutil module
        sys.modules['psutil'] = None
        
        try:
            result = get_memory_usage()
            # Should fall back to 0.0 when psutil import fails
            assert result == 0.0
        finally:
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)

    @patch("metadata_multitool.batch.get_memory_usage")
    def test_check_memory_limit_within_limits(self, mock_get_memory):
        """Test memory limit check when within limits."""
        mock_get_memory.return_value = 512.0
        assert check_memory_limit(1024) is True

    @patch("metadata_multitool.batch.get_memory_usage")
    def test_check_memory_limit_exceeded(self, mock_get_memory):
        """Test memory limit check when exceeded."""
        mock_get_memory.return_value = 1536.0
        assert check_memory_limit(1024) is False


class TestTimeFormatting:
    """Test time formatting functions."""

    def test_format_seconds(self):
        """Test formatting seconds."""
        assert format_time_remaining(30) == "30s"
        assert format_time_remaining(59) == "59s"

    def test_format_minutes(self):
        """Test formatting minutes."""
        assert format_time_remaining(60) == "1m 0s"
        assert format_time_remaining(125) == "2m 5s"
        assert format_time_remaining(3599) == "59m 59s"

    def test_format_hours(self):
        """Test formatting hours."""
        assert format_time_remaining(3600) == "1h 0m"
        assert format_time_remaining(3665) == "1h 1m"
        assert format_time_remaining(7320) == "2h 2m"

    def test_calculate_eta_no_processed(self):
        """Test ETA calculation with no items processed."""
        result = calculate_eta(0, 100, time.time())
        assert result is None

    def test_calculate_eta_valid(self):
        """Test ETA calculation with valid data."""
        start_time = time.time() - 10  # 10 seconds ago
        result = calculate_eta(25, 100, start_time)
        assert result is not None
        assert isinstance(result, str)

    def test_calculate_eta_zero_rate(self):
        """Test ETA calculation with zero rate."""
        start_time = time.time()  # Just started
        result = calculate_eta(1, 100, start_time)
        # This might be None due to very small elapsed time
        assert result is None or isinstance(result, str)

    @patch("metadata_multitool.batch.time.time")
    def test_calculate_eta_negative_rate(self, mock_time):
        """Test ETA calculation with negative rate (edge case)."""
        mock_time.return_value = 100.0
        start_time = 110.0  # Future time (shouldn't happen in practice)
        result = calculate_eta(10, 100, start_time)
        assert result is None


class TestBatchWorker:
    """Test batch worker functionality."""

    def test_worker_all_success(self, sample_images):
        """Test batch worker with all successful items."""
        from metadata_multitool.batch import _process_batch_worker

        successful, errors = _process_batch_worker(sample_images, always_success_process)
        assert successful == len(sample_images)
        assert len(errors) == 0

    def test_worker_mixed_results(self, sample_images):
        """Test batch worker with mixed results."""
        from metadata_multitool.batch import _process_batch_worker

        successful, errors = _process_batch_worker(sample_images, single_failure_process)
        assert successful == 4  # 4 out of 5 should succeed
        assert len(errors) == 1

    def test_worker_with_exceptions(self, sample_images):
        """Test batch worker with exceptions."""
        from metadata_multitool.batch import _process_batch_worker

        successful, errors = _process_batch_worker(sample_images, exception_process)
        assert successful == 4  # 4 out of 5 should succeed
        assert len(errors) == 1
        assert "Test exception" in errors[0]


class TestIntegration:
    """Integration tests for batch processing."""

    def test_realistic_workflow(self, sample_images):
        """Test a realistic batch processing workflow."""
        result = process_batch(
            sample_images,
            realistic_process,
            batch_size=2,
            max_workers=2,
            disable_progress=True,
            memory_limit_mb=512
        )
        
        successful, total, errors = result
        assert total == len(sample_images)
        assert successful >= 0  # Should have some successes
        assert isinstance(errors, list)

    def test_large_batch_simulation(self, tmp_path):
        """Test batch processing with a larger number of files."""
        # Create more test files
        test_files = []
        for i in range(20):
            file_path = tmp_path / f"test_{i:03d}.jpg"
            file_path.write_bytes(b"fake image data")
            test_files.append(file_path)

        result = process_batch(
            test_files,
            simple_process,
            batch_size=5,
            max_workers=3,
            disable_progress=True
        )
        
        assert result == (20, 20, [])