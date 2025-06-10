"""
ClickHouse Native Metrics Integration

Enhances existing custom metrics with ClickHouse's built-in monitoring capabilities.
Designed for minimal invasion - works alongside existing streaming_metrics.py
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ClickHouseNativeMetrics:
    """
    Collects ClickHouse native performance data to enhance custom metrics.

    Integrates with existing streaming_metrics without replacing it.
    Uses ClickHouse system tables: query_log, parts, merges, metrics.
    """

    def __init__(self, clickhouse_client):
        self.client = clickhouse_client
        self.last_query_log_check = datetime.now()

    def get_native_metrics_for_operation(self, operation_timestamp: datetime) -> Dict[str, Any]:
        """
        Get native ClickHouse metrics for a specific operation timeframe.

        Args:
            operation_timestamp: When the operation occurred

        Returns:
            Dict with native ClickHouse insights
        """
        try:
            # Look for queries around the operation time (±5 seconds)
            time_window_start = operation_timestamp - timedelta(seconds=5)
            time_window_end = operation_timestamp + timedelta(seconds=5)

            return {
                "query_performance": self._get_query_log_metrics(time_window_start, time_window_end),
                "parts_status": self._get_parts_metrics(),
                "merge_activity": self._get_merge_metrics(),
                "system_metrics": self._get_system_metrics()
            }

        except Exception as e:
            logger.warning(f"Failed to get native ClickHouse metrics: {e}")
            return self._get_empty_metrics()

    def _get_query_log_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get recent query performance from system.query_log and system.part_log"""
        try:
            # Try to get bulk insert metrics from part_log (for client.insert() operations)
            part_query = """
                SELECT
                    event_time,
                    rows,
                    size_in_bytes,
                    duration_ms
                FROM system.part_log
                WHERE event_time >= %(start_time)s
                  AND event_time <= %(end_time)s
                  AND table = 'rag_chunks_v2'
                  AND event_type = 'NewPart'
                ORDER BY event_time DESC
                LIMIT 5
            """

            part_results = self.client.query(part_query, {
                'start_time': start_time,
                'end_time': end_time
            })

            if part_results.result_rows:
                recent_part = part_results.result_rows[0]
                return {
                    "ch_query_duration_ms": recent_part[3] if recent_part[3] else 0,
                    "ch_inserted_rows": recent_part[1] if recent_part[1] else 0,
                    "ch_inserted_bytes": recent_part[2] if recent_part[2] else 0,
                    "ch_memory_usage_bytes": 0,  # Not available in part_log
                    "ch_disk_read_us": 0,  # Not available in part_log
                    "ch_disk_write_us": 0  # Not available in part_log
                }

            # Fallback to query_log (for any text-based operations)
            query = """
                SELECT
                    type,
                    query_duration_ms,
                    ProfileEvents['InsertedRows'] as inserted_rows,
                    ProfileEvents['InsertedBytes'] as inserted_bytes,
                    ProfileEvents['MemoryUsage'] as memory_usage,
                    ProfileEvents['DiskReadElapsedMicroseconds'] as disk_read_us,
                    ProfileEvents['DiskWriteElapsedMicroseconds'] as disk_write_us
                FROM system.query_log
                WHERE event_time >= %(start_time)s
                  AND event_time <= %(end_time)s
                  AND (query LIKE '%%rag_chunks_v2%%' OR query LIKE '%%INSERT%%')
                  AND type = 'QueryFinish'
                ORDER BY event_time DESC
                LIMIT 5
            """

            query_results = self.client.query(query, {
                'start_time': start_time,
                'end_time': end_time
            })

            if query_results.result_rows:
                recent_query = query_results.result_rows[0]
                return {
                    "ch_query_duration_ms": recent_query[1] if recent_query[1] else 0,
                    "ch_inserted_rows": recent_query[2] if recent_query[2] else 0,
                    "ch_inserted_bytes": recent_query[3] if recent_query[3] else 0,
                    "ch_memory_usage_bytes": recent_query[4] if recent_query[4] else 0,
                    "ch_disk_read_us": recent_query[5] if recent_query[5] else 0,
                    "ch_disk_write_us": recent_query[6] if recent_query[6] else 0
                }
            else:
                return self._get_empty_query_metrics()

        except Exception as e:
            logger.warning(f"Failed to get query log metrics: {e}")
            return self._get_empty_query_metrics()

    def _get_parts_metrics(self) -> Dict[str, Any]:
        """Get current table parts status"""
        try:
            query = """
                SELECT
                    count() as part_count,
                    sum(rows) as total_rows,
                    sum(data_compressed_bytes) as compressed_bytes,
                    sum(data_uncompressed_bytes) as uncompressed_bytes,
                    max(modification_time) as last_modification
                FROM system.parts
                WHERE table = 'rag_chunks_v2'
                  AND active = 1
            """

            results = self.client.query(query)
            if results.result_rows:
                row = results.result_rows[0]
                compressed = row[2] if row[2] else 1
                uncompressed = row[3] if row[3] else 1

                return {
                    "ch_parts_count": row[0] if row[0] else 0,
                    "ch_total_rows": row[1] if row[1] else 0,
                    "ch_compressed_bytes": compressed,
                    "ch_uncompressed_bytes": uncompressed,
                    "ch_compression_ratio": round(uncompressed / compressed, 2) if compressed > 0 else 0,
                    "ch_last_modification": row[4]
                }
            else:
                return self._get_empty_parts_metrics()

        except Exception as e:
            logger.warning(f"Failed to get parts metrics: {e}")
            return self._get_empty_parts_metrics()

    def _get_merge_metrics(self) -> Dict[str, Any]:
        """Get current merge activity"""
        try:
            query = """
                SELECT
                    count() as active_merges,
                    sum(num_parts) as parts_being_merged,
                    sum(total_size_bytes_compressed) as merge_size_bytes,
                    avg(progress) as avg_progress
                FROM system.merges
                WHERE table = 'rag_chunks_v2'
            """

            results = self.client.query(query)
            if results.result_rows:
                row = results.result_rows[0]
                return {
                    "ch_active_merges": row[0] if row[0] else 0,
                    "ch_parts_being_merged": row[1] if row[1] else 0,
                    "ch_merge_size_bytes": row[2] if row[2] else 0,
                    "ch_merge_progress": round(row[3], 2) if row[3] else 0
                }
            else:
                return {
                    "ch_active_merges": 0,
                    "ch_parts_being_merged": 0,
                    "ch_merge_size_bytes": 0,
                    "ch_merge_progress": 0
                }

        except Exception as e:
            logger.warning(f"Failed to get merge metrics: {e}")
            return {
                "ch_active_merges": 0,
                "ch_parts_being_merged": 0,
                "ch_merge_size_bytes": 0,
                "ch_merge_progress": 0
            }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            query = """
                SELECT
                    value
                FROM system.metrics
                WHERE metric IN ('MemoryUsage', 'BackgroundSchedulePoolTask', 'Query')
            """

            results = self.client.query(query)
            metrics = {}

            for i, metric_name in enumerate(['MemoryUsage', 'BackgroundSchedulePoolTask', 'Query']):
                if i < len(results.result_rows):
                    metrics[f"ch_system_{metric_name.lower()}"] = results.result_rows[i][0]
                else:
                    metrics[f"ch_system_{metric_name.lower()}"] = 0

            return metrics

        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            return {
                "ch_system_memoryusage": 0,
                "ch_system_backgroundschedulepooltask": 0,
                "ch_system_query": 0
            }

    def classify_operation_with_native_data(self, custom_latency_ms: float, native_metrics: Dict[str, Any]) -> str:
        """
        Enhanced operation classification using both custom timing and native ClickHouse data.

        Improves on existing classification with native insights.
        """
        # Start with existing custom classification
        if custom_latency_ms < 50:
            base_classification = "indexing"
        elif custom_latency_ms < 500:
            base_classification = "indexing"
        elif custom_latency_ms < 2000:
            base_classification = "background_merge"
        else:
            base_classification = "manual_optimize"

        # Enhance with native ClickHouse data
        active_merges = native_metrics.get("ch_active_merges", 0)
        parts_count = native_metrics.get("ch_parts_count", 0)

        # Refine classification with native insights
        if active_merges > 0:
            if base_classification == "indexing":
                return "indexing_with_background_merge"
            else:
                return "confirmed_background_merge"

        if parts_count > 100:  # High part count suggests need for merging
            return f"{base_classification}_high_part_count"

        return base_classification

    def _get_empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure when ClickHouse queries fail"""
        return {
            "query_performance": self._get_empty_query_metrics(),
            "parts_status": self._get_empty_parts_metrics(),
            "merge_activity": {
                "ch_active_merges": 0,
                "ch_parts_being_merged": 0,
                "ch_merge_size_bytes": 0,
                "ch_merge_progress": 0
            },
            "system_metrics": {
                "ch_system_memoryusage": 0,
                "ch_system_backgroundschedulepooltask": 0,
                "ch_system_query": 0
            }
        }

    def _get_empty_query_metrics(self) -> Dict[str, Any]:
        return {
            "ch_query_duration_ms": 0,
            "ch_inserted_rows": 0,
            "ch_inserted_bytes": 0,
            "ch_memory_usage_bytes": 0,
            "ch_disk_read_us": 0,
            "ch_disk_write_us": 0
        }

    def _get_empty_parts_metrics(self) -> Dict[str, Any]:
        return {
            "ch_parts_count": 0,
            "ch_total_rows": 0,
            "ch_compressed_bytes": 0,
            "ch_uncompressed_bytes": 0,
            "ch_compression_ratio": 0,
            "ch_last_modification": None
        }

# Global instance to be imported by streaming.py
native_metrics_collector = None

def initialize_native_metrics(clickhouse_client):
    """Initialize the global native metrics collector"""
    global native_metrics_collector
    native_metrics_collector = ClickHouseNativeMetrics(clickhouse_client)
    logger.info("ClickHouse native metrics collector initialized")

def get_native_metrics_for_operation(operation_timestamp: datetime) -> Dict[str, Any]:
    """Get native metrics for an operation (called from streaming.py)"""
    if native_metrics_collector:
        return native_metrics_collector.get_native_metrics_for_operation(operation_timestamp)
    else:
        logger.warning("Native metrics collector not initialized")
        return {}