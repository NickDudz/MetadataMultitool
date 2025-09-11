"""
Memory profiling utilities for Metadata Multitool.

Provides detailed memory usage analysis and profiling tools
for identifying memory leaks and optimization opportunities.
"""

import psutil
import time
import gc
import tracemalloc
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import threading
import sys
from dataclasses import dataclass
from collections import defaultdict
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a point in time."""
    timestamp: float
    rss_mb: float
    vms_mb: float
    percent: float
    available_mb: float
    tracemalloc_current: Optional[int] = None
    tracemalloc_peak: Optional[int] = None


@dataclass
class MemoryAnalysis:
    """Analysis results from memory profiling."""
    total_duration: float
    snapshots: List[MemorySnapshot]
    peak_usage_mb: float
    average_usage_mb: float
    memory_growth_mb: float
    potential_leaks: List[Dict[str, Any]]
    gc_collections: Dict[str, int]


class MemoryProfiler:
    """Advanced memory profiler for tracking usage patterns."""
    
    def __init__(self, enable_tracemalloc: bool = True):
        self.enable_tracemalloc = enable_tracemalloc
        self.snapshots: List[MemorySnapshot] = []
        self.start_time: Optional[float] = None
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.gc_stats_start: Optional[Dict[str, int]] = None
        
    def start_profiling(self, interval: float = 0.1):
        """Start memory profiling with specified interval."""
        if self.monitoring:
            return
            
        self.snapshots.clear()
        self.start_time = time.perf_counter()
        self.monitoring = True
        
        # Enable tracemalloc if requested
        if self.enable_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Capture initial GC stats
        self.gc_stats_start = {
            f"gen_{i}": gc.get_stats()[i]['collections'] 
            for i in range(len(gc.get_stats()))
        }
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_profiling(self) -> MemoryAnalysis:
        """Stop profiling and return analysis."""
        if not self.monitoring:
            raise RuntimeError("Profiling not started")
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        # Take final snapshot
        self._take_snapshot()
        
        # Calculate final GC stats
        gc_collections = {}
        if self.gc_stats_start:
            current_stats = gc.get_stats()
            for i in range(len(current_stats)):
                gen_key = f"gen_{i}"
                if gen_key in self.gc_stats_start:
                    gc_collections[gen_key] = (
                        current_stats[i]['collections'] - 
                        self.gc_stats_start[gen_key]
                    )
        
        # Analyze results
        analysis = self._analyze_snapshots(gc_collections)
        
        # Stop tracemalloc if we started it
        if self.enable_tracemalloc and tracemalloc.is_tracing():
            tracemalloc.stop()
        
        return analysis
    
    def _monitor_loop(self, interval: float):
        """Main monitoring loop running in separate thread."""
        while self.monitoring:
            self._take_snapshot()
            time.sleep(interval)
    
    def _take_snapshot(self):
        """Take a memory usage snapshot."""
        if not self.monitoring or self.start_time is None:
            return
        
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # System memory info
        system_memory = psutil.virtual_memory()
        
        # Tracemalloc info if enabled
        tracemalloc_current = None
        tracemalloc_peak = None
        if self.enable_tracemalloc and tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc_current = current
            tracemalloc_peak = peak
        
        snapshot = MemorySnapshot(
            timestamp=time.perf_counter() - self.start_time,
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            percent=memory_percent,
            available_mb=system_memory.available / 1024 / 1024,
            tracemalloc_current=tracemalloc_current,
            tracemalloc_peak=tracemalloc_peak
        )
        
        self.snapshots.append(snapshot)
    
    def _analyze_snapshots(self, gc_collections: Dict[str, int]) -> MemoryAnalysis:
        """Analyze collected snapshots."""
        if not self.snapshots:
            raise ValueError("No snapshots to analyze")
        
        # Basic statistics
        rss_values = [s.rss_mb for s in self.snapshots]
        peak_usage = max(rss_values)
        average_usage = sum(rss_values) / len(rss_values)
        memory_growth = rss_values[-1] - rss_values[0]
        total_duration = self.snapshots[-1].timestamp
        
        # Detect potential memory leaks
        potential_leaks = self._detect_leaks()
        
        return MemoryAnalysis(
            total_duration=total_duration,
            snapshots=self.snapshots.copy(),
            peak_usage_mb=peak_usage,
            average_usage_mb=average_usage,
            memory_growth_mb=memory_growth,
            potential_leaks=potential_leaks,
            gc_collections=gc_collections
        )
    
    def _detect_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks from usage patterns."""
        if len(self.snapshots) < 10:
            return []
        
        leaks = []
        
        # Check for consistent upward trend
        rss_values = [s.rss_mb for s in self.snapshots]
        
        # Calculate trend over time
        time_points = [s.timestamp for s in self.snapshots]
        
        # Simple linear regression to detect trend
        n = len(rss_values)
        sum_x = sum(time_points)
        sum_y = sum(rss_values)
        sum_xy = sum(x * y for x, y in zip(time_points, rss_values))
        sum_x2 = sum(x * x for x in time_points)
        
        if n > 1 and (n * sum_x2 - sum_x * sum_x) != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # If slope is significantly positive, potential leak
            if slope > 0.1:  # More than 0.1 MB/second growth
                leaks.append({
                    'type': 'linear_growth',
                    'growth_rate_mb_per_sec': slope,
                    'description': f'Consistent memory growth at {slope:.3f} MB/sec'
                })
        
        # Check for step increases (sudden jumps)
        for i in range(1, len(rss_values)):
            increase = rss_values[i] - rss_values[i-1]
            if increase > 50:  # Sudden 50MB+ increase
                leaks.append({
                    'type': 'step_increase',
                    'increase_mb': increase,
                    'timestamp': time_points[i],
                    'description': f'Sudden {increase:.1f}MB increase at {time_points[i]:.1f}s'
                })
        
        return leaks


class MemoryProfilerContext:
    """Context manager for memory profiling."""
    
    def __init__(self, profiler: MemoryProfiler, interval: float = 0.1):
        self.profiler = profiler
        self.interval = interval
        self.analysis: Optional[MemoryAnalysis] = None
    
    def __enter__(self) -> MemoryProfiler:
        self.profiler.start_profiling(self.interval)
        return self.profiler
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.analysis = self.profiler.stop_profiling()


def profile_function(func: Callable, *args, **kwargs) -> tuple[Any, MemoryAnalysis]:
    """Profile memory usage of a function call."""
    profiler = MemoryProfiler()
    
    with MemoryProfilerContext(profiler, interval=0.05) as p:
        result = func(*args, **kwargs)
    
    return result, p.analysis


def generate_memory_report(analysis: MemoryAnalysis, output_file: Optional[Path] = None) -> str:
    """Generate a detailed memory usage report."""
    report_lines = [
        "# Memory Usage Report",
        "",
        f"**Duration:** {analysis.total_duration:.2f} seconds",
        f"**Peak Usage:** {analysis.peak_usage_mb:.2f} MB",
        f"**Average Usage:** {analysis.average_usage_mb:.2f} MB", 
        f"**Memory Growth:** {analysis.memory_growth_mb:.2f} MB",
        f"**Snapshots Collected:** {len(analysis.snapshots)}",
        "",
        "## Garbage Collection Statistics",
        ""
    ]
    
    for gen, collections in analysis.gc_collections.items():
        report_lines.append(f"- {gen}: {collections} collections")
    
    if analysis.potential_leaks:
        report_lines.extend([
            "",
            "## Potential Memory Leaks",
            ""
        ])
        
        for leak in analysis.potential_leaks:
            report_lines.append(f"- **{leak['type']}**: {leak['description']}")
    
    # Memory usage timeline
    if analysis.snapshots:
        report_lines.extend([
            "",
            "## Memory Usage Timeline",
            "",
            "| Time (s) | RSS (MB) | VMS (MB) | % Used |",
            "|----------|----------|----------|---------|"
        ])
        
        # Sample every 10th snapshot for readability
        sample_snapshots = analysis.snapshots[::max(1, len(analysis.snapshots) // 20)]
        
        for snapshot in sample_snapshots:
            report_lines.append(
                f"| {snapshot.timestamp:8.2f} | "
                f"{snapshot.rss_mb:8.2f} | "
                f"{snapshot.vms_mb:8.2f} | "
                f"{snapshot.percent:7.2f} |"
            )
    
    report_text = "\n".join(report_lines)
    
    if output_file:
        output_file.write_text(report_text)
    
    return report_text


def export_memory_data(analysis: MemoryAnalysis, output_file: Path):
    """Export raw memory data as JSON for further analysis."""
    data = {
        'metadata': {
            'total_duration': analysis.total_duration,
            'peak_usage_mb': analysis.peak_usage_mb,
            'average_usage_mb': analysis.average_usage_mb,
            'memory_growth_mb': analysis.memory_growth_mb,
            'snapshot_count': len(analysis.snapshots)
        },
        'gc_collections': analysis.gc_collections,
        'potential_leaks': analysis.potential_leaks,
        'snapshots': [
            {
                'timestamp': s.timestamp,
                'rss_mb': s.rss_mb,
                'vms_mb': s.vms_mb,
                'percent': s.percent,
                'available_mb': s.available_mb,
                'tracemalloc_current': s.tracemalloc_current,
                'tracemalloc_peak': s.tracemalloc_peak
            }
            for s in analysis.snapshots
        ]
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)


def compare_memory_profiles(baseline: MemoryAnalysis, current: MemoryAnalysis) -> Dict[str, Any]:
    """Compare two memory profiles to detect regressions."""
    comparison = {
        'peak_usage_change_mb': current.peak_usage_mb - baseline.peak_usage_mb,
        'average_usage_change_mb': current.average_usage_mb - baseline.average_usage_mb,
        'growth_change_mb': current.memory_growth_mb - baseline.memory_growth_mb,
        'duration_change_sec': current.total_duration - baseline.total_duration,
    }
    
    # Calculate percentage changes
    if baseline.peak_usage_mb > 0:
        comparison['peak_usage_change_percent'] = (
            (current.peak_usage_mb / baseline.peak_usage_mb - 1) * 100
        )
    
    if baseline.average_usage_mb > 0:
        comparison['average_usage_change_percent'] = (
            (current.average_usage_mb / baseline.average_usage_mb - 1) * 100
        )
    
    # Regression detection
    comparison['regressions'] = []
    
    if comparison['peak_usage_change_mb'] > 20:  # 20MB increase
        comparison['regressions'].append('peak_memory_increased')
    
    if comparison.get('peak_usage_change_percent', 0) > 15:  # 15% increase
        comparison['regressions'].append('peak_memory_percentage_increased')
    
    if comparison['growth_change_mb'] > 10:  # 10MB more growth
        comparison['regressions'].append('memory_growth_increased')
    
    if len(current.potential_leaks) > len(baseline.potential_leaks):
        comparison['regressions'].append('new_potential_leaks')
    
    return comparison


# Example usage functions for testing
def example_memory_intensive_operation():
    """Example function that uses significant memory."""
    # Simulate memory-intensive work
    data = []
    for i in range(1000):
        # Create some data structures
        chunk = [i] * 1000
        data.append(chunk)
        
        # Simulate some processing
        if i % 100 == 0:
            time.sleep(0.01)
    
    # Clean up most data but keep some
    result = data[::10]
    return len(result)


if __name__ == "__main__":
    # Example usage
    print("Running memory profiling example...")
    
    # Profile a function
    result, analysis = profile_function(example_memory_intensive_operation)
    
    # Generate report
    report = generate_memory_report(analysis)
    print(report)
    
    # Export data
    export_memory_data(analysis, Path("memory_profile.json"))
    
    print(f"\nFunction returned: {result}")
    print(f"Peak memory usage: {analysis.peak_usage_mb:.2f} MB")
    print(f"Memory growth: {analysis.memory_growth_mb:.2f} MB")
    
    if analysis.potential_leaks:
        print(f"Potential leaks detected: {len(analysis.potential_leaks)}")
        for leak in analysis.potential_leaks:
            print(f"  - {leak['description']}")