"""
RAG Benchmarking System.

This module provides comprehensive benchmarking capabilities for RAG pipeline components,
including performance measurement, analytics, and data export.
"""

from .core import RAGBenchmarks
from .models import (
    StageMetric,
    PopulationPipelineBenchmark,
    UpdatePipelineBenchmark,
    QueryPipelineBenchmark
)
from .config import PERFORMANCE_TARGETS, PIPELINE_TARGETS, BENCHMARK_SETTINGS
from .utils import (
    measure_time,
    measure_memory,
    calculate_throughput,
    format_duration,
    get_system_metrics,
    check_resource_limits,
    retry_with_backoff,
    timestamp_to_iso
)

__all__ = [
    # Core benchmarking
    'RAGBenchmarks',

    # Models
    'StageMetric',
    'PopulationPipelineBenchmark',
    'UpdatePipelineBenchmark',
    'QueryPipelineBenchmark',

    # Configuration
    'PERFORMANCE_TARGETS',
    'PIPELINE_TARGETS',
    'BENCHMARK_SETTINGS',

    # Utilities
    'measure_time',
    'measure_memory',
    'calculate_throughput',
    'format_duration',
    'get_system_metrics',
    'check_resource_limits',
    'retry_with_backoff',
    'timestamp_to_iso'
]