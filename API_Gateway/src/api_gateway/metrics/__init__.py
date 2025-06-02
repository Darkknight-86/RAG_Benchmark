"""
RAG Metrics and Benchmarking System.

This module provides comprehensive metrics collection and benchmarking capabilities
for RAG pipeline components, focusing on:
- Population pipeline (A2 → A3 → B2 → B3 → B4)
- Update pipeline (Incremental B4 operations)
- Query pipeline (C3 → D1 → D2 → D3)
"""

from .benchmarks import (
    # Core benchmarking
    RAGBenchmarks,

    # Models
    StageMetric,
    PopulationPipelineBenchmark,
    UpdatePipelineBenchmark,
    QueryPipelineBenchmark,

    # Configuration
    PERFORMANCE_TARGETS,
    PIPELINE_TARGETS,
    BENCHMARK_SETTINGS,

    # Utilities
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

__all__ += ['MetricsCollector', 'MetricsDashboard']

# ---------------------------------------------------------------------------
# Lightweight placeholders to let the API Gateway boot. Replace with full
# implementation from metrics.collector and metrics.dashboard as soon as
# those modules are stabilised.
# ---------------------------------------------------------------------------

from typing import Any, List
from flask import Blueprint, jsonify


class MetricsCollector:  # pragma: no cover – minimal stub
    """Minimal stub so API Gateway can start.

    A real implementation should live in metrics.collector and handle async
    collection / Prometheus registry sharing.  For the MVP we just record an
    *active_services* set so the dashboard route works.
    """

    def __init__(self, benchmarks: 'RAGBenchmarks') -> None:
        self.benchmarks = benchmarks
        self.active_services: set[str] = set()

    # simple API used by server.py in shutdown
    def stop_collection_for_service(self, name: str) -> None:
        self.active_services.discard(name)

    # dashboard helper
    def list_active(self) -> List[str]:
        return list(self.active_services)


class MetricsDashboard:  # pragma: no cover – minimal stub
    """Flask blueprint exposing two basic endpoints."""

    def __init__(self, benchmarks: 'RAGBenchmarks', metrics_collector: MetricsCollector):
        bp = Blueprint('metrics', __name__)

        @bp.route('/metrics/active', methods=['GET'])
        def get_active():
            return jsonify(metrics_collector.list_active())

        @bp.route('/healthz', methods=['GET'])
        def healthz():
            return 'OK', 200

        self.blueprint = bp