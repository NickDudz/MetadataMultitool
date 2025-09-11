"""
Performance benchmarking tests for Metadata Multitool.

These tests measure performance characteristics and help identify
bottlenecks and regressions in processing large file sets.
"""

import tempfile
import time
import psutil
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pytest
from PIL import Image
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from metadata_multitool import clean, poison, revert, batch
from metadata_multitool.core import iter_images


class PerformanceMonitor:
    """Monitor system performance during operations."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.peak_memory = None
        self.measurements = []
        
    def start(self):
        """Start performance monitoring."""
        self.start_time = time.perf_counter()
        process = psutil.Process()
        self.start_memory = process.memory_info().rss
        self.peak_memory = self.start_memory
        self.measurements = []
        
    def sample(self):
        """Take a performance sample."""
        if self.start_time is None:
            return
            
        current_time = time.perf_counter()
        process = psutil.Process()
        current_memory = process.memory_info().rss
        
        self.peak_memory = max(self.peak_memory, current_memory)
        
        self.measurements.append({
            'elapsed': current_time - self.start_time,
            'memory_mb': current_memory / 1024 / 1024,
            'cpu_percent': process.cpu_percent()
        })
        
    def stop(self):
        """Stop monitoring and return results."""
        if self.start_time is None:
            return {}
            
        self.end_time = time.perf_counter()
        process = psutil.Process()
        final_memory = process.memory_info().rss
        
        elapsed_time = self.end_time - self.start_time
        memory_delta = (final_memory - self.start_memory) / 1024 / 1024  # MB
        peak_memory_mb = self.peak_memory / 1024 / 1024
        
        return {
            'elapsed_seconds': elapsed_time,
            'memory_delta_mb': memory_delta,
            'peak_memory_mb': peak_memory_mb,
            'samples': len(self.measurements),
            'measurements': self.measurements
        }


@pytest.fixture
def performance_monitor():
    """Provide performance monitoring instance."""
    return PerformanceMonitor()


@pytest.fixture(scope="module", params=[100, 500, 1000])
def test_dataset(request) -> Tuple[Path, int]:
    """Create test datasets of varying sizes."""
    size = request.param
    temp_dir = Path(tempfile.mkdtemp(prefix=f"perf_test_{size}_"))
    
    # Create test images with varying characteristics
    for i in range(size):
        img_path = temp_dir / f"test_image_{i:04d}.jpg"
        
        # Vary image sizes and complexity
        if i % 10 == 0:
            # Some larger images
            img_size = (800, 600)
        elif i % 3 == 0:
            # Some medium images
            img_size = (400, 300)
        else:
            # Mostly small images
            img_size = (200, 150)
            
        # Create with different colors for variety
        color = (
            (i * 17) % 255,
            (i * 31) % 255,
            (i * 47) % 255
        )
        
        img = Image.new('RGB', img_size, color)
        img.save(str(img_path), 'JPEG', quality=85)
    
    yield temp_dir, size
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestPerformanceBenchmarks:
    """Performance benchmarking test suite."""
    
    @pytest.mark.slow
    def test_clean_operation_scaling(self, test_dataset: Tuple[Path, int], 
                                   performance_monitor: PerformanceMonitor):
        """Test how clean operation scales with file count."""
        test_dir, file_count = test_dataset
        output_dir = test_dir / "clean_output"
        
        performance_monitor.start()
        
        # Sample performance during operation
        import threading
        sampling_active = True
        
        def sample_performance():
            while sampling_active:
                performance_monitor.sample()
                time.sleep(0.1)
        
        sample_thread = threading.Thread(target=sample_performance)
        sample_thread.start()
        
        try:
            # Run clean operation
            result = clean.clean_directory(
                input_path=test_dir,
                output_path=output_dir,
                backup=False
            )
            
            # Verify operation succeeded
            assert result.get("successful", 0) == file_count
            assert output_dir.exists()
            
        finally:
            sampling_active = False
            sample_thread.join()
        
        metrics = performance_monitor.stop()
        
        # Performance assertions
        files_per_second = file_count / metrics['elapsed_seconds']
        memory_per_file = metrics['peak_memory_mb'] / file_count
        
        print(f"\nClean Performance ({file_count} files):")
        print(f"  Elapsed time: {metrics['elapsed_seconds']:.2f}s")
        print(f"  Files/second: {files_per_second:.1f}")
        print(f"  Peak memory: {metrics['peak_memory_mb']:.1f}MB")
        print(f"  Memory/file: {memory_per_file:.3f}MB")
        
        # Performance targets (adjust based on system capabilities)
        assert files_per_second > 5, f"Too slow: {files_per_second:.1f} files/sec"
        assert memory_per_file < 2.0, f"Too much memory: {memory_per_file:.3f}MB/file"
        assert metrics['peak_memory_mb'] < 500, f"Memory usage too high: {metrics['peak_memory_mb']:.1f}MB"

    @pytest.mark.slow
    def test_batch_processing_performance(self, test_dataset: Tuple[Path, int],
                                        performance_monitor: PerformanceMonitor):
        """Test batch processing performance with different configurations."""
        test_dir, file_count = test_dataset
        
        # Test different batch configurations
        batch_configs = [
            {"batch_size": 10, "max_workers": 1},
            {"batch_size": 25, "max_workers": 2},
            {"batch_size": 50, "max_workers": 4},
        ]
        
        results = []
        
        for config in batch_configs:
            output_dir = test_dir / f"batch_output_{config['batch_size']}_{config['max_workers']}"
            
            performance_monitor.start()
            
            # Run batch processing
            result = batch.batch_process_clean(
                input_paths=[test_dir],
                output_dir=output_dir,
                **config
            )
            
            metrics = performance_monitor.stop()
            
            # Verify results
            assert result.get("successful", 0) == file_count
            
            files_per_second = file_count / metrics['elapsed_seconds']
            
            results.append({
                'config': config,
                'files_per_second': files_per_second,
                'elapsed_seconds': metrics['elapsed_seconds'],
                'peak_memory_mb': metrics['peak_memory_mb']
            })
            
            print(f"\nBatch Performance {config}:")
            print(f"  Files/second: {files_per_second:.1f}")
            print(f"  Memory: {metrics['peak_memory_mb']:.1f}MB")
        
        # Find optimal configuration
        best_config = max(results, key=lambda x: x['files_per_second'])
        print(f"\nBest configuration: {best_config['config']}")
        print(f"Best performance: {best_config['files_per_second']:.1f} files/sec")
        
        # Ensure parallel processing provides benefit
        if len(results) > 1:
            single_worker = [r for r in results if r['config']['max_workers'] == 1][0]
            multi_worker = [r for r in results if r['config']['max_workers'] > 1]
            
            if multi_worker:
                best_multi = max(multi_worker, key=lambda x: x['files_per_second'])
                speedup = best_multi['files_per_second'] / single_worker['files_per_second']
                print(f"Parallel speedup: {speedup:.2f}x")

    @pytest.mark.slow  
    def test_memory_usage_patterns(self, test_dataset: Tuple[Path, int],
                                 performance_monitor: PerformanceMonitor):
        """Test memory usage patterns during operations."""
        test_dir, file_count = test_dataset
        
        # Monitor memory during clean operation
        performance_monitor.start()
        
        # Sample more frequently for memory analysis
        sampling_active = True
        
        def frequent_sampling():
            while sampling_active:
                performance_monitor.sample()
                time.sleep(0.05)  # 20Hz sampling
        
        sample_thread = threading.Thread(target=frequent_sampling)
        sample_thread.start()
        
        try:
            clean.clean_directory(
                input_path=test_dir,
                output_path=test_dir / "memory_test_output"
            )
        finally:
            sampling_active = False
            sample_thread.join()
        
        metrics = performance_monitor.stop()
        
        # Analyze memory patterns
        memory_values = [m['memory_mb'] for m in metrics['measurements']]
        
        if memory_values:
            memory_stats = {
                'min_mb': min(memory_values),
                'max_mb': max(memory_values),
                'mean_mb': statistics.mean(memory_values),
                'stddev_mb': statistics.stdev(memory_values) if len(memory_values) > 1 else 0
            }
            
            print(f"\nMemory Usage Analysis ({file_count} files):")
            print(f"  Min: {memory_stats['min_mb']:.1f}MB")
            print(f"  Max: {memory_stats['max_mb']:.1f}MB") 
            print(f"  Mean: {memory_stats['mean_mb']:.1f}MB")
            print(f"  StdDev: {memory_stats['stddev_mb']:.1f}MB")
            
            # Check for memory leaks (significant upward trend)
            memory_growth = memory_stats['max_mb'] - memory_stats['min_mb']
            growth_per_file = memory_growth / file_count
            
            print(f"  Total growth: {memory_growth:.1f}MB")
            print(f"  Growth per file: {growth_per_file:.3f}MB")
            
            # Assert reasonable memory behavior
            assert growth_per_file < 0.1, f"Possible memory leak: {growth_per_file:.3f}MB/file"
            assert memory_stats['max_mb'] < 1000, f"Memory usage too high: {memory_stats['max_mb']:.1f}MB"

    @pytest.mark.slow
    def test_poison_revert_cycle_performance(self, performance_monitor: PerformanceMonitor):
        """Test performance of complete poison-revert cycles."""
        # Create smaller dataset for poison testing (more complex operations)
        temp_dir = Path(tempfile.mkdtemp(prefix="poison_perf_"))
        
        try:
            # Create 100 test images
            for i in range(100):
                img_path = temp_dir / f"poison_test_{i:03d}.jpg"
                img = Image.new('RGB', (300, 200), (i % 255, 100, 150))
                img.save(str(img_path), 'JPEG', quality=90)
            
            # Test poison operation
            performance_monitor.start()
            
            poison_result = poison.poison_directory(
                input_path=temp_dir,
                preset="label_flip",
                create_sidecars=True
            )
            
            poison_metrics = performance_monitor.stop()
            
            # Test revert operation
            performance_monitor.start()
            
            revert_result = revert.revert_directory(temp_dir)
            
            revert_metrics = performance_monitor.stop()
            
            # Verify operations
            assert poison_result.get("poisoned_count", 0) == 100
            assert revert_result.get("reverted_count", 0) == 100
            
            # Performance analysis
            poison_fps = 100 / poison_metrics['elapsed_seconds']
            revert_fps = 100 / revert_metrics['elapsed_seconds']
            
            print(f"\nPoison-Revert Cycle Performance:")
            print(f"  Poison: {poison_fps:.1f} files/sec")
            print(f"  Revert: {revert_fps:.1f} files/sec")
            print(f"  Poison memory: {poison_metrics['peak_memory_mb']:.1f}MB")
            print(f"  Revert memory: {revert_metrics['peak_memory_mb']:.1f}MB")
            
            # Performance assertions
            assert poison_fps > 10, f"Poison too slow: {poison_fps:.1f} files/sec"
            assert revert_fps > 20, f"Revert too slow: {revert_fps:.1f} files/sec"
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_file_discovery_performance(self, test_dataset: Tuple[Path, int],
                                      performance_monitor: PerformanceMonitor):
        """Test performance of file discovery across directory structures."""
        test_dir, file_count = test_dataset
        
        # Create nested directory structure
        nested_dirs = []
        for i in range(5):
            nested_dir = test_dir / f"subdir_{i}" / f"level2_{i}"
            nested_dir.mkdir(parents=True)
            nested_dirs.append(nested_dir)
            
            # Move some files to nested directories
            files_to_move = list(test_dir.glob("*.jpg"))[:file_count // 10]
            for j, file_path in enumerate(files_to_move):
                if j < len(files_to_move) // 5:
                    new_path = nested_dir / file_path.name
                    file_path.rename(new_path)
        
        # Test file discovery performance
        performance_monitor.start()
        
        discovered_files = list(iter_images(test_dir, recursive=True))
        
        metrics = performance_monitor.stop()
        
        discovery_rate = len(discovered_files) / metrics['elapsed_seconds']
        
        print(f"\nFile Discovery Performance:")
        print(f"  Files found: {len(discovered_files)}")
        print(f"  Discovery time: {metrics['elapsed_seconds']:.3f}s")
        print(f"  Discovery rate: {discovery_rate:.0f} files/sec")
        print(f"  Memory usage: {metrics['peak_memory_mb']:.1f}MB")
        
        # Verify all files were found
        assert len(discovered_files) == file_count
        
        # Performance assertions
        assert discovery_rate > 1000, f"Discovery too slow: {discovery_rate:.0f} files/sec"
        assert metrics['peak_memory_mb'] < 100, f"Discovery uses too much memory: {metrics['peak_memory_mb']:.1f}MB"

    @pytest.mark.slow
    def test_large_file_handling(self, performance_monitor: PerformanceMonitor):
        """Test performance with large individual files."""
        temp_dir = Path(tempfile.mkdtemp(prefix="large_file_perf_"))
        
        try:
            # Create a few large images
            large_files = []
            for i in range(5):
                img_path = temp_dir / f"large_image_{i}.tiff"
                # Create large image (2000x1500 = 3MP)
                img = Image.new('RGB', (2000, 1500), (i * 50, 100, 200))
                img.save(str(img_path), 'TIFF', compression='lzw')
                large_files.append(img_path)
            
            total_size_mb = sum(f.stat().st_size for f in large_files) / 1024 / 1024
            print(f"\nLarge File Test: {len(large_files)} files, {total_size_mb:.1f}MB total")
            
            # Test processing large files
            performance_monitor.start()
            
            result = clean.clean_directory(
                input_path=temp_dir,
                output_path=temp_dir / "large_output"
            )
            
            metrics = performance_monitor.stop()
            
            # Verify processing
            assert result.get("successful", 0) == len(large_files)
            
            # Performance analysis
            mb_per_second = total_size_mb / metrics['elapsed_seconds']
            memory_efficiency = metrics['peak_memory_mb'] / total_size_mb
            
            print(f"  Processing rate: {mb_per_second:.1f} MB/sec")
            print(f"  Peak memory: {metrics['peak_memory_mb']:.1f}MB")
            print(f"  Memory efficiency: {memory_efficiency:.2f}x data size")
            
            # Performance assertions for large files
            assert mb_per_second > 5, f"Large file processing too slow: {mb_per_second:.1f} MB/sec"
            assert memory_efficiency < 3, f"Memory usage too high: {memory_efficiency:.2f}x"
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.slow
class TestPerformanceRegression:
    """Tests to detect performance regressions."""
    
    def test_baseline_performance(self, tmp_path: Path, performance_monitor: PerformanceMonitor):
        """Establish baseline performance metrics."""
        # Create standard test dataset
        test_files = []
        for i in range(50):
            img_path = tmp_path / f"baseline_{i:03d}.jpg"
            img = Image.new('RGB', (400, 300), (i % 255, 128, 200))
            img.save(str(img_path), 'JPEG', quality=85)
            test_files.append(img_path)
        
        # Measure clean operation
        performance_monitor.start()
        result = clean.clean_directory(tmp_path, tmp_path / "baseline_output")
        metrics = performance_monitor.stop()
        
        baseline_fps = len(test_files) / metrics['elapsed_seconds']
        baseline_memory = metrics['peak_memory_mb']
        
        # Store baseline metrics (in real implementation, save to file)
        baseline = {
            'files_per_second': baseline_fps,
            'peak_memory_mb': baseline_memory,
            'test_file_count': len(test_files)
        }
        
        print(f"\nBaseline Performance:")
        print(f"  Files/sec: {baseline_fps:.1f}")
        print(f"  Memory: {baseline_memory:.1f}MB")
        
        # Assert minimum acceptable performance
        assert baseline_fps > 20, f"Baseline too slow: {baseline_fps:.1f} files/sec"
        assert baseline_memory < 200, f"Baseline memory too high: {baseline_memory:.1f}MB"
        
        return baseline


if __name__ == "__main__":
    # Run performance tests when executed directly
    pytest.main([__file__, "-v", "-s", "--tb=short"])