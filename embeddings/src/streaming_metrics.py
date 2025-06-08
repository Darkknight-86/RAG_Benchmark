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
        self.chunking_events = deque()   # Text chunking events

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
        """Export streaming metrics to CSV file with append support."""
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

            # Check if file exists to determine if we need to write header
            import os
            file_exists = os.path.exists(filename)
            mode = 'a' if file_exists else 'w'

            # Write CSV with append support
            with open(filename, mode, newline='') as csvfile:
                if all_events:
                    fieldnames = all_events[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    # Only write header if this is a new file
                    if not file_exists:
                        writer.writeheader()

                    writer.writerows(all_events)

            logger.info(f"Exported {len(all_events)} streaming events to {filename}")
            return filename

    def export_component_csvs(self, minutes: int = 5) -> Dict[str, str]:
        """Export separate CSV files for each pipeline component."""
        with self.lock:
            cutoff = datetime.now() - timedelta(minutes=minutes)
            exported_files = {}

            # 1. DATA STREAMING METRICS
            streaming_data = []
            for event in self.ingestion_events:
                if event["timestamp"] > cutoff:
                    streaming_data.append({
                        "timestamp": event["timestamp"].isoformat(),
                        "ticker": event["ticker"],
                        "success": event["success"],
                        "ingestion_latency_ms": event["latency_ms"],
                        "data_size_bytes": event["data_size"],
                        "source": event["metadata"].get("source", "unknown"),
                        "throughput_bps": event["data_size"] / (event["latency_ms"] / 1000) if event["latency_ms"] > 0 else 0
                    })

            if streaming_data:
                exported_files["data_streaming"] = self._write_component_csv(
                    "streaming_data_metrics.csv", streaming_data
                )

            # 2. CHUNKING METRICS
            chunking_data = []
            for event in self.chunking_events:
                if event["timestamp"] > cutoff:
                    chunking_data.append({
                        "timestamp": event["timestamp"].isoformat(),
                        "ticker": event["ticker"],
                        "original_text_size": event["original_text_size"],
                        "chunk_count": event["chunk_count"],
                        "avg_chunk_size": event["avg_chunk_size"],
                        "min_chunk_size": min(event["chunks_sizes"]) if event["chunks_sizes"] else 0,
                        "max_chunk_size": max(event["chunks_sizes"]) if event["chunks_sizes"] else 0,
                        "chunking_latency_ms": event["latency_ms"],
                        "chunking_efficiency": event["efficiency_ratio"],
                        "chunk_size_variance": max(event["chunks_sizes"]) - min(event["chunks_sizes"]) if event["chunks_sizes"] else 0,
                        "chunker_config": json.dumps(event["chunker_config"])
                    })

            if chunking_data:
                exported_files["chunking"] = self._write_component_csv(
                    "chunking_metrics.csv", chunking_data
                )

            # 3. EMBEDDING METRICS
            embedding_data = []
            for event in self.embedding_events:
                if event["timestamp"] > cutoff:
                    embedding_data.append({
                        "timestamp": event["timestamp"].isoformat(),
                        "success": event["success"],
                        "embedding_latency_ms": event["latency_ms"],
                        "text_length": event["text_length"],
                        "embedding_dimension": event["embedding_dimension"],
                        "model_name": event["model_name"],
                        "tokens_per_second": (event["text_length"] / 4) / (event["latency_ms"] / 1000) if event["latency_ms"] > 0 else 0,  # Rough token estimate
                        "embedding_throughput": event["embedding_dimension"] / (event["latency_ms"] / 1000) if event["latency_ms"] > 0 else 0
                    })

            if embedding_data:
                exported_files["embedding"] = self._write_component_csv(
                    "embedding_metrics.csv", embedding_data
                )

            # 4. VECTOR DATABASE METRICS
            vector_db_data = []
            for event in self.database_events:
                if event["timestamp"] > cutoff:
                    # Determine operation type (ClickHouse MergeTree reality)
                    operation_type = "indexing"  # Default for new inserts
                    op_lower = event["operation"].lower()

                    # ClickHouse MergeTree reindexing patterns:
                    if any(keyword in op_lower for keyword in ["optimize", "merge", "compact"]):
                        operation_type = "background_merge"  # Automatic part merging
                    elif "table_optimization" in op_lower or "final" in op_lower:
                        operation_type = "manual_optimize"  # Manual OPTIMIZE TABLE FINAL
                    elif any(keyword in op_lower for keyword in ["alter", "schema", "modify"]):
                        operation_type = "schema_reindex"   # Schema changes trigger reindexing
                    elif any(keyword in op_lower for keyword in ["update", "upsert", "replace"]):
                        operation_type = "data_update"     # Data updates (rare in streaming)
                    elif any(keyword in op_lower for keyword in ["delete", "remove", "drop"]):
                        operation_type = "deletion"
                    elif "bulk" in op_lower and event["records_affected"] > 10:
                        operation_type = "bulk_insert"     # Large inserts that may trigger merging

                    # Detect potential reindexing by latency patterns
                    # Normal inserts: 50-200ms, Background merging: 500-2000ms, Manual optimize: 2000+ms
                    if event["latency_ms"] > 2000:
                        if operation_type == "indexing":
                            operation_type = "suspected_background_merge"

                    vector_db_data.append({
                        "timestamp": event["timestamp"].isoformat(),
                        "operation": event["operation"],
                        "operation_type": operation_type,  # indexing/reindexing/deletion/optimization
                        "table": event["table"],
                        "success": event["success"],
                        "vd_latency_ms": event["latency_ms"],
                        "records_affected": event["records_affected"],
                        "throughput_records_per_second": event["records_affected"] / (event["latency_ms"] / 1000) if event["latency_ms"] > 0 else 0,
                        "performance_tier": "excellent" if event["latency_ms"] < 50 else "good" if event["latency_ms"] < 150 else "slow"
                    })

            if vector_db_data:
                exported_files["vector_db"] = self._write_component_csv(
                    "vector_db_metrics.csv", vector_db_data
                )

            return exported_files

    def _write_component_csv(self, filename: str, data: List[Dict]) -> str:
        """Helper method to write component CSV with append support."""
        if not data:
            return filename

        import os

        # Ensure Data directory exists and use centralized location
        data_dir = os.path.join(os.path.dirname(__file__), '../../API_Gateway/Data')
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

        logger.info(f"Exported {len(data)} records to {full_path}")
        return full_path

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
        self.chunking_events = deque(e for e in self.chunking_events
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

    def record_chunking_operation(self, ticker: str, original_text: str, chunks: List[str],
                                 latency_ms: float, chunker_config: Dict[str, Any]):
        """Record a text chunking operation."""
        with self.lock:
            event = {
                "timestamp": datetime.now(),
                "type": "chunking",
                "ticker": ticker,
                "original_text_size": len(original_text),
                "chunk_count": len(chunks),
                "chunks_sizes": [len(chunk) for chunk in chunks],
                "avg_chunk_size": sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0,
                "latency_ms": latency_ms,
                "chunker_config": chunker_config,
                "efficiency_ratio": len(original_text) / len(chunks) if chunks else 0
            }

            self.chunking_events.append(event)
            self._cleanup_old_events()

            self.counters["total_chunking_operations"] += 1
            self.counters["total_chunks_created"] += len(chunks)

        self.timers["chunking_latency"].append(latency_ms)
        self._update_performance_stats()

    def trigger_reindex_operation(self, database_client, table_name: str = "financial_embeddings"):
        """Manually trigger reindexing operations for testing and monitoring."""
        try:
            import time

            # Record the start of reindex operation
            reindex_start = time.time()

            # Execute OPTIMIZE TABLE (forces ClickHouse to merge and reindex)
            optimize_query = f"OPTIMIZE TABLE {table_name} FINAL"

            logger.info(f"🔄 Triggering reindex operation: {optimize_query}")

            # Execute the optimization
            if hasattr(database_client, 'execute'):
                database_client.execute(optimize_query)
            elif hasattr(database_client, 'query'):
                database_client.query(optimize_query)

            reindex_latency = (time.time() - reindex_start) * 1000  # ms

            # Record the reindex operation
            self.record_database_operation(
                operation="table_optimization",
                table=table_name,
                success=True,
                latency_ms=reindex_latency,
                records_affected=0  # OPTIMIZE doesn't return affected count
            )

            logger.info(f"✅ Reindex operation completed in {reindex_latency:.2f}ms")

            return True

        except Exception as e:
            logger.error(f"❌ Reindex operation failed: {e}")

            # Record the failed reindex
            self.record_database_operation(
                operation="table_optimization",
                table=table_name,
                success=False,
                latency_ms=0,
                records_affected=0
            )

            return False

    def trigger_bulk_data_load(self, count: int = 1000):
        """Trigger bulk data insertion to force automatic reindexing."""
        logger.info(f"🚀 Triggering bulk data load of {count} records to force reindexing...")

        # This would be called from the streaming service
        # to insert a large volume of test data
        return f"Bulk load trigger set for {count} records"

# Global metrics collector instance
streaming_metrics = StreamingMetricsCollector()