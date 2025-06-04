"""
RAG Benchmarking System.

This module provides comprehensive benchmarking capabilities for RAG pipeline components,
including performance measurement, analytics, and data export.
"""

# Prefer the lightweight benchmarking implementation to reduce dependencies
# If you need the full-featured implementation, import
# `from .core import RAGBenchmarks as FullRAGBenchmarks` explicitly.

from .lightweight import LightweightRAGBenchmarks as RAGBenchmarks
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