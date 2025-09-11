"""
Performance testing suite for Metadata Multitool.

This package contains performance benchmarks, memory profiling,
and regression testing utilities.
"""

from .memory_profiling import (
    MemoryProfiler,
    MemoryProfilerContext,
    MemoryAnalysis,
    profile_function,
    generate_memory_report,
    export_memory_data,
    compare_memory_profiles
)

__all__ = [
    'MemoryProfiler',
    'MemoryProfilerContext', 
    'MemoryAnalysis',
    'profile_function',
    'generate_memory_report',
    'export_memory_data',
    'compare_memory_profiles'
]