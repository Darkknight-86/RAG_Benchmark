"""
Configuration and performance targets for RAG benchmarking.
"""

from typing import Dict, Any

# Performance targets for each RAG component
PERFORMANCE_TARGETS: Dict[str, Dict[str, Any]] = {
    'A2': {  # PDF Processing
        'min_throughput': 2.0,  # docs/sec
        'success_rate': 0.95
    },
    'A3': {  # Load Raw Data
        'min_throughput': 5.0,
        'success_rate': 0.98
    },
    'B2': {  # Chunking
        'min_throughput': 10.0,
        'success_rate': 0.99
    },
    'B3': {  # Embedding Generation
        'min_throughput': 5.0,
        'success_rate': 0.98
    },
    'B4': {  # Vector Storage
        'min_throughput': 20.0,
        'success_rate': 0.99
    },
    'C3': {  # Query Trigger
        'min_throughput': 50.0,
        'success_rate': 0.99
    },
    'D1': {  # Query Ingestion
        'min_throughput': 30.0,
        'success_rate': 0.99
    },
    'D2': {  # Vector Retrieval
        'min_throughput': 20.0,
        'success_rate': 0.98
    },
    'D3': {  # LLM Response
        'min_throughput': 10.0,
        'success_rate': 0.95
    }
}

# Pipeline performance targets
PIPELINE_TARGETS = {
    'population': {
        'min_docs_per_second': 1.0,
        'success_rate': 0.95
    },
    'update': {
        'min_updates_per_second': 2.0,
        'success_rate': 0.98
    },
    'query': {
        'min_queries_per_second': 5.0,
        'success_rate': 0.95
    }
}

# Resource utilization limits
RESOURCE_LIMITS = {
    'cpu_percent': 80.0,
    'memory_percent': 75.0,
    'disk_usage_percent': 85.0
}

# Benchmarking window settings
BENCHMARK_SETTINGS = {
    'window_size': 1000,  # Number of samples to keep
    'min_samples': 10,    # Minimum samples for analysis
    'max_age': 3600      # Maximum age of samples in seconds
}