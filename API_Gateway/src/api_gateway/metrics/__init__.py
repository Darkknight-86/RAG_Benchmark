"""
RAG Metrics Collection System.

This module provides lightweight metrics collection for RAG pipeline components.
"""

from typing import Any, List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import os
import csv

@dataclass
class QueryMetrics:
    timestamp: datetime
    query: str
    response: str
    vector_latency: float
    llm_latency: float
    total_time: float
    tokens_used: int
    vector_store_type: str
    status: str
    error: Optional[str] = None

class MetricsCollector:
    def __init__(self, export_dir: str = "API_Gateway/exports"):
        self.export_dir = export_dir
        self.metrics_buffer: List[QueryMetrics] = []
        os.makedirs(export_dir, exist_ok=True)

    def record_query(
        self,
        query: str,
        response: str,
        vector_latency: float,
        llm_latency: float,
        total_time: float,
        tokens_used: int,
        vector_store_type: str,
        status: str = "success",
        error: Optional[str] = None
    ):
        """Record metrics for a single query."""
        metrics = QueryMetrics(
            timestamp=datetime.now(),
            query=query,
            response=response,
            vector_latency=vector_latency,
            llm_latency=llm_latency,
            total_time=total_time,
            tokens_used=tokens_used,
            vector_store_type=vector_store_type,
            status=status,
            error=error
        )
        self.metrics_buffer.append(metrics)

    def export_metrics(self, format: str = "csv") -> str:
        """Export collected metrics to CSV (default) or JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "csv":
            filename = f"rag_metrics_{timestamp}.csv"
            filepath = os.path.join(self.export_dir, filename)

            fieldnames = [
                "timestamp",
                "query",
                "response",
                "vector_latency",
                "llm_latency",
                "total_time",
                "tokens_used",
                "vector_store_type",
                "status",
                "error",
            ]

            with open(filepath, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for m in self.metrics_buffer:
                    writer.writerow({k: getattr(m, k) for k in fieldnames})

        elif format == "json":
            filename = f"rag_metrics_{timestamp}.json"
            filepath = os.path.join(self.export_dir, filename)

            with open(filepath, "w") as f:
                json.dump([vars(m) for m in self.metrics_buffer], f, default=str, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        return filepath

    def get_metrics_summary(self) -> Dict:
        """Get a summary of collected metrics."""
        if not self.metrics_buffer:
            return {
                "total_queries": 0,
                "average_latencies": {},
                "total_tokens": 0
            }

        total_queries = len(self.metrics_buffer)
        total_tokens = sum(m.tokens_used for m in self.metrics_buffer)

        avg_vector_latency = sum(m.vector_latency for m in self.metrics_buffer) / total_queries
        avg_llm_latency = sum(m.llm_latency for m in self.metrics_buffer) / total_queries
        avg_total_time = sum(m.total_time for m in self.metrics_buffer) / total_queries

        return {
            "total_queries": total_queries,
            "average_latencies": {
                "vector_search": avg_vector_latency,
                "llm_processing": avg_llm_latency,
                "total": avg_total_time
            },
            "total_tokens": total_tokens,
            "vector_store_types": list(set(m.vector_store_type for m in self.metrics_buffer))
        }

# Global instance
metrics_collector = MetricsCollector()