"""
Streaming Pipeline Metrics Collector

Tracks live financial data streaming performance:
- Data ingestion rates from yliveticker
- Embedding generation latency
- Database insertion performance
- Stream processing health
- Real-time throughput metrics
- Direct CSV export (no cross-process sharing needed)
"""

import time
import threading
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class StreamingMetricsCollector:
    """Collects and manages streaming pipeline metrics with direct CSV export."""

    def __init__(self, window_size_minutes: int = 10):
        self.window_size = timedelta(minutes=window_size_minutes)
        self.lock = threading.Lock()

        # Time-series data storage (last N minutes)
        self.ingestion_events = deque()  # Raw ingestion events
        self.embedding_events = deque()  # Embedding generation events
        self.database_events = deque()   # Database operation events
        self.error_events = deque()      # Error events

        # Real-time counters
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.timers = defaultdict(list)

        # Health status tracking
        self.health_status = {
            "yliveticker_connection": "unknown",
            "clickhouse_connection": "unknown",
            "embedding_model": "unknown",
            "overall_health": "unknown",
            "last_data_timestamp": None,
            "consecutive_errors": 0
        }

        # Performance aggregates
        self.performance_stats = {
            "ingestion_rate_per_second": 0.0,
            "avg_embedding_latency_ms": 0.0,
            "avg_database_latency_ms": 0.0,
            "success_rate_percentage": 0.0,
            "total_records_processed": 0,
            "errors_last_hour": 0
        }

        logger.info("StreamingMetricsCollector initialized for direct CSV export")

    def record_data_ingestion(self, ticker: str, success: bool, latency_ms: float,
                            data_size: int, metadata: Dict[str, Any] = None):
        """Record a data ingestion event from yliveticker."""
        with self.lock:
            event = {
                "timestamp": datetime.now(),
                "type": "ingestion",
                "ticker": ticker,
                "success": success,
                "latency_ms": latency_ms,
                "data_size": data_size,
                "metadata": metadata or {}
            }

            self.ingestion_events.append(event)
            self._cleanup_old_events()

            # Update counters
            if success:
                self.counters["successful_ingestions"] += 1
                self.gauges["last_successful_ingestion"] = time.time()
                self.health_status["last_data_timestamp"] = datetime.now()
                self.health_status["consecutive_errors"] = 0
            else:
                self.counters["failed_ingestions"] += 1
                self.health_status["consecutive_errors"] += 1

        self.timers["ingestion_latency"].append(latency_ms)
        self._update_performance_stats()

    def record_embedding_generation(self, text: str, success: bool, latency_ms: float,
                                  embedding_dim: int, model_name: str):
        """Record an embedding generation event."""
        with self.lock:
            event = {
                "timestamp": datetime.now(),
                "type": "embedding",
                "text_length": len(text),
                "success": success,
                "latency_ms": latency_ms,
                "embedding_dimension": embedding_dim,
                "model_name": model_name
            }

            self.embedding_events.append(event)
            self._cleanup_old_events()

            if success:
                self.counters["successful_embeddings"] += 1
                self.health_status["embedding_model"] = "healthy"
            else:
                self.counters["failed_embeddings"] += 1
                self.health_status["embedding_model"] = "unhealthy"

        self.timers["embedding_latency"].append(latency_ms)
        self._update_performance_stats()

    def record_database_operation(self, operation: str, table: str, success: bool,
                                latency_ms: float, records_affected: int):
        """Record a database operation event."""
        with self.lock:
            event = {
                "timestamp": datetime.now(),
                "type": "database",
                "operation": operation,
                "table": table,
                "success": success,
                "latency_ms": latency_ms,
                "records_affected": records_affected
            }

            self.database_events.append(event)
            self._cleanup_old_events()

            if success:
                self.counters[f"successful_{operation}"] += 1
                self.health_status["clickhouse_connection"] = "healthy"
            else:
                self.counters[f"failed_{operation}"] += 1
                self.health_status["clickhouse_connection"] = "unhealthy"

            self.timers["database_latency"].append(latency_ms)
            self._update_performance_stats()

    def record_error(self, error_type: str, error_message: str, component: str,
                    ticker: Optional[str] = None):
        """Record an error event."""
        with self.lock:
            event = {
                "timestamp": datetime.now(),
                "type": "error",
                "error_type": error_type,
                "error_message": error_message,
                "component": component,
                "ticker": ticker
            }

            self.error_events.append(event)
            self._cleanup_old_events()

            self.counters[f"errors_{component}"] += 1
            self.counters["total_errors"] += 1

            # Update health based on error patterns
            if component == "yliveticker":
                self.health_status["yliveticker_connection"] = "unhealthy"
            elif component == "clickhouse":
                self.health_status["clickhouse_connection"] = "unhealthy"
            elif component == "embedding":
                self.health_status["embedding_model"] = "unhealthy"

    def update_connection_status(self, component: str, status: str):
        """Update connection status for a component."""
        with self.lock:
            if component in self.health_status:
                self.health_status[component] = status
            self._update_overall_health()

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics for dashboard display."""
        with self.lock:
            current_time = datetime.now()

            # Calculate rates over last minute
            minute_ago = current_time - timedelta(minutes=1)
            recent_ingestions = [e for e in self.ingestion_events
                               if e["timestamp"] > minute_ago and e["success"]]

            ingestion_rate = len(recent_ingestions) / 60.0  # per second

            return {
                "timestamp": current_time.isoformat(),
                "streaming_health": self.health_status,
                "performance": self.performance_stats,
                "real_time": {
                    "ingestion_rate_per_second": round(ingestion_rate, 2),
                    "active_tickers": len(set(e["ticker"] for e in recent_ingestions)),
                    "avg_embedding_latency_ms": self._avg_timer("embedding_latency", 60),
                    "avg_database_latency_ms": self._avg_timer("database_latency", 60),
                    "error_rate_per_minute": len([e for e in self.error_events
                                                 if e["timestamp"] > minute_ago])
                },
                "counters": dict(self.counters),
                "window_size_minutes": self.window_size.total_seconds() / 60
            }

    def get_historical_data(self, minutes: int = 10) -> Dict[str, List[Dict]]:
        """Get historical time-series data for charts."""
        with self.lock:
            cutoff = datetime.now() - timedelta(minutes=minutes)

            return {
                "ingestion_events": [dict(e) for e in self.ingestion_events
                                   if e["timestamp"] > cutoff],
                "embedding_events": [dict(e) for e in self.embedding_events
                                   if e["timestamp"] > cutoff],
                "database_events": [dict(e) for e in self.database_events
                                  if e["timestamp"] > cutoff],
                "error_events": [dict(e) for e in self.error_events
                               if e["timestamp"] > cutoff]
            }

    def export_streaming_csv(self, filename: Optional[str] = None,
                           minutes: int = 60) -> str:
        """Export streaming metrics to CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"streaming_metrics_{timestamp}.csv"

        with self.lock:
            cutoff = datetime.now() - timedelta(minutes=minutes)
            all_events = []

            # Combine all events
            for event in self.ingestion_events:
                if event["timestamp"] > cutoff:
                    all_events.append({
                        "timestamp": event["timestamp"].isoformat(),
                        "event_type": "ingestion",
                        "ticker": event["ticker"],
                        "success": event["success"],
                        "latency_ms": event["latency_ms"],
                        "data_size": event["data_size"]
                    })

            for event in self.embedding_events:
                if event["timestamp"] > cutoff:
                    all_events.append({
                        "timestamp": event["timestamp"].isoformat(),
                        "event_type": "embedding",
                        "ticker": "N/A",
                        "success": event["success"],
                        "latency_ms": event["latency_ms"],
                        "data_size": event["text_length"]
                    })

            for event in self.database_events:
                if event["timestamp"] > cutoff:
                    all_events.append({
                        "timestamp": event["timestamp"].isoformat(),
                        "event_type": f"database_{event['operation']}",
                        "ticker": "N/A",
                        "success": event["success"],
                        "latency_ms": event["latency_ms"],
                        "data_size": event["records_affected"]
                    })

            # Sort by timestamp
            all_events.sort(key=lambda x: x["timestamp"])

            # Write CSV
            with open(filename, 'w', newline='') as csvfile:
                if all_events:
                    fieldnames = all_events[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_events)

            logger.info(f"Exported {len(all_events)} streaming events to {filename}")
            return filename

    def _cleanup_old_events(self):
        """Remove events older than window size."""
        cutoff = datetime.now() - self.window_size

        self.ingestion_events = deque(e for e in self.ingestion_events
                                    if e["timestamp"] > cutoff)
        self.embedding_events = deque(e for e in self.embedding_events
                                    if e["timestamp"] > cutoff)
        self.database_events = deque(e for e in self.database_events
                                   if e["timestamp"] > cutoff)
        self.error_events = deque(e for e in self.error_events
                                if e["timestamp"] > cutoff)

    def _update_performance_stats(self):
        """Update aggregated performance statistics."""
        self.performance_stats["total_records_processed"] = (
            self.counters["successful_ingestions"] + self.counters["failed_ingestions"]
        )

        total_operations = (
            self.counters["successful_ingestions"] +
            self.counters["failed_ingestions"] +
            self.counters["successful_embeddings"] +
            self.counters["failed_embeddings"]
        )

        if total_operations > 0:
            success_operations = (
                self.counters["successful_ingestions"] +
                self.counters["successful_embeddings"]
            )
            self.performance_stats["success_rate_percentage"] = (
                success_operations / total_operations * 100
            )

        self.performance_stats["avg_embedding_latency_ms"] = self._avg_timer("embedding_latency")
        self.performance_stats["avg_database_latency_ms"] = self._avg_timer("database_latency")

        # Calculate ingestion rate over last minute
        current_time = datetime.now()
        minute_ago = current_time - timedelta(minutes=1)
        recent_successes = [e for e in self.ingestion_events
                          if e["timestamp"] > minute_ago and e["success"]]
        self.performance_stats["ingestion_rate_per_second"] = len(recent_successes) / 60.0

        # Count errors in last hour
        hour_ago = current_time - timedelta(hours=1)
        self.performance_stats["errors_last_hour"] = len([
            e for e in self.error_events if e["timestamp"] > hour_ago
        ])

    def _avg_timer(self, timer_name: str, last_n: int = 100) -> float:
        """Calculate average for timer values."""
        values = self.timers.get(timer_name, [])
        if not values:
            return 0.0

        recent_values = values[-last_n:] if len(values) > last_n else values
        return sum(recent_values) / len(recent_values)

    def _update_overall_health(self):
        """Update overall system health based on component health."""
        statuses = [
            self.health_status["yliveticker_connection"],
            self.health_status["clickhouse_connection"],
            self.health_status["embedding_model"]
        ]

        if all(s == "healthy" for s in statuses):
            self.health_status["overall_health"] = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            self.health_status["overall_health"] = "unhealthy"
        else:
            self.health_status["overall_health"] = "unknown"

# Global metrics collector instance
streaming_metrics = StreamingMetricsCollector()