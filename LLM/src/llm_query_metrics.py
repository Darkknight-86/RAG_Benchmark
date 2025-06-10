"""
LLM Query Metrics Collector

Tracks LLM query performance with optimized metrics for benchmarking:
- Vector search performance
- LLM generation performance
- End-to-end query timing
- Retrieval effectiveness
- Resource consumption
"""

import time
import threading
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)

class LLMQueryMetricsCollector:
    """Collects and exports optimized LLM query performance metrics."""

    def __init__(self, window_size_minutes: int = 10):
        self.window_size = timedelta(minutes=window_size_minutes)
        self.lock = threading.Lock()

        # Time-series data storage (last N minutes)
        self.query_events = deque()

        # Track exported events to prevent duplicates
        self.last_export_time = datetime.min
        self.exported_event_ids = set()

        # Counters
        self.counters = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "rag_queries": 0,
            "direct_queries": 0
        }

        logger.info("LLM Query Metrics Collector initialized")

    def record_query(self, query: str, query_type: str, success: bool,
                    vector_latency: float, llm_latency: float, total_time: float,
                    tokens_used: int, docs_found: int, avg_relevance_score: float,
                    model_name: str, error: str = None):
        """Record a query event with optimized metrics."""

        with self.lock:
            timestamp = datetime.now()
            # Create unique ID for each event to prevent duplicate exports
            event_id = f"{timestamp.isoformat()}_{len(self.query_events)}"

            event = {
                "id": event_id,
                "timestamp": timestamp,
                "query": query[:100],  # Truncate for storage
                "query_type": query_type,
                "success": success,
                "vector_latency_ms": vector_latency * 1000,  # Convert to ms
                "llm_latency_ms": llm_latency * 1000,  # Convert to ms
                "total_time_ms": total_time * 1000,  # Convert to ms
                "tokens_used": tokens_used,
                "docs_found": docs_found,
                "avg_relevance_score": avg_relevance_score,
                "model_name": model_name,
                "error": error
            }

            self.query_events.append(event)
            self._cleanup_old_events()

            # Update counters
            self.counters["total_queries"] += 1
            if success:
                self.counters["successful_queries"] += 1
            else:
                self.counters["failed_queries"] += 1

            if query_type == "rag":
                self.counters["rag_queries"] += 1
            else:
                self.counters["direct_queries"] += 1

    def export_query_metrics_csv(self, minutes: int = 5) -> Optional[str]:
        """Export optimized query metrics to CSV (only NEW events since last export)."""

        with self.lock:
            current_time = datetime.now()

            # Only export events since last export to prevent duplicates
            cutoff = max(self.last_export_time, current_time - timedelta(minutes=minutes))

            # Collect NEW query events not yet exported
            query_data = []
            new_exported_ids = set()

            for event in self.query_events:
                event_id = event["id"]

                # Skip if already exported or too old
                if (event["timestamp"] > cutoff and
                    event_id not in self.exported_event_ids):

                    # Optimized 10-column structure for benchmarking
                    query_data.append({
                        "timestamp": event["timestamp"].isoformat(),
                        "query_type": event["query_type"],
                        "success": event["success"],
                        "vector_latency_ms": round(event["vector_latency_ms"], 2),
                        "llm_latency_ms": round(event["llm_latency_ms"], 2),
                        "total_time_ms": round(event["total_time_ms"], 2),
                        "tokens_used": event["tokens_used"],
                        "docs_found": event["docs_found"],
                        "avg_relevance_score": round(event["avg_relevance_score"], 3),
                        "model_name": event["model_name"]
                    })

                    new_exported_ids.add(event_id)

            if query_data:
                # Update tracking to prevent future duplicates
                self.last_export_time = current_time
                self.exported_event_ids.update(new_exported_ids)

                # Clean up old exported IDs to prevent memory growth
                cutoff_for_cleanup = current_time - timedelta(hours=1)
                events_to_keep = {e["id"] for e in self.query_events if e["timestamp"] > cutoff_for_cleanup}
                self.exported_event_ids &= events_to_keep

                return self._write_query_csv("llm_query_metrics.csv", query_data)
            else:
                logger.debug("No new query events to export")

            return None

    def manual_export_csv(self, minutes: int = 30) -> Optional[str]:
        """Manual export for dashboard - exports all recent queries without deduplication."""

        with self.lock:
            cutoff = datetime.now() - timedelta(minutes=minutes)

            # Collect recent query events for manual export
            query_data = []
            for event in self.query_events:
                if event["timestamp"] > cutoff:
                    # Export all fields for manual review
                    query_data.append({
                        "timestamp": event["timestamp"].isoformat(),
                        "query_type": event["query_type"],
                        "success": event["success"],
                        "vector_latency_ms": round(event["vector_latency_ms"], 2),
                        "llm_latency_ms": round(event["llm_latency_ms"], 2),
                        "total_time_ms": round(event["total_time_ms"], 2),
                        "tokens_used": event["tokens_used"],
                        "docs_found": event["docs_found"],
                        "avg_relevance_score": round(event["avg_relevance_score"], 3),
                        "model_name": event["model_name"]
                    })

            if query_data:
                # Generate timestamped filename for manual exports
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"LLM_query_performance_{timestamp}.csv"
                return self._write_query_csv(filename, query_data)
            else:
                logger.info("No query events found for manual export")
                return None

    def _write_query_csv(self, filename: str, data: List[Dict]) -> str:
        """Write query metrics to CSV in organized query_metrics folder."""
        if not data:
            return filename

        # Ensure query_metrics directory exists
        data_dir = os.path.join(os.path.dirname(__file__), '../../API_Gateway/Data/query_metrics')
        os.makedirs(data_dir, exist_ok=True)

        # Full path to CSV file
        full_path = os.path.join(data_dir, filename)

        file_exists = os.path.exists(full_path)
        mode = 'a' if file_exists else 'w'

        with open(full_path, mode, newline='') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Only write header if this is a new file
            if not file_exists:
                writer.writeheader()

            writer.writerows(data)

        logger.info(f"Exported {len(data)} query metrics to {full_path}")
        return full_path

    def _cleanup_old_events(self):
        """Remove events older than window size."""
        cutoff = datetime.now() - self.window_size
        self.query_events = deque(e for e in self.query_events if e["timestamp"] > cutoff)

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time query performance metrics."""
        with self.lock:
            current_time = datetime.now()
            minute_ago = current_time - timedelta(minutes=1)

            # Recent performance
            recent_queries = [e for e in self.query_events if e["timestamp"] > minute_ago]

            if recent_queries:
                avg_total_time = sum(e["total_time_ms"] for e in recent_queries) / len(recent_queries)
                avg_vector_time = sum(e["vector_latency_ms"] for e in recent_queries) / len(recent_queries)
                avg_llm_time = sum(e["llm_latency_ms"] for e in recent_queries) / len(recent_queries)
                avg_tokens = sum(e["tokens_used"] for e in recent_queries) / len(recent_queries)
                success_rate = sum(1 for e in recent_queries if e["success"]) / len(recent_queries) * 100
            else:
                avg_total_time = avg_vector_time = avg_llm_time = avg_tokens = success_rate = 0

            return {
                "timestamp": current_time.isoformat(),
                "queries_last_minute": len(recent_queries),
                "avg_total_time_ms": round(avg_total_time, 2),
                "avg_vector_latency_ms": round(avg_vector_time, 2),
                "avg_llm_latency_ms": round(avg_llm_time, 2),
                "avg_tokens_used": round(avg_tokens, 1),
                "success_rate_percent": round(success_rate, 1),
                "counters": dict(self.counters),
                "window_size_minutes": self.window_size.total_seconds() / 60
            }

# Global instance for the LLM service
llm_query_metrics = LLMQueryMetricsCollector()

def start_automatic_export():
    """Automatic export disabled - manual export only via dashboard."""
    logger.info("Automatic LLM query metrics export disabled - manual export only via dashboard")