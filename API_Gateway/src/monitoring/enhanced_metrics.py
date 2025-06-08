"""
Enhanced Metrics Collector for Financial RAG Microservices
Real-time monitoring with WebSocket streaming and dashboard integration
"""

import time
import json
import asyncio
import websockets
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)

@dataclass
class MetricEvent:
    """Represents a single metric event"""
    timestamp: float
    service: str
    metric_type: str
    value: float
    metadata: Dict[str, Any]

class EnhancedMetricsCollector:
    """
    Real-time metrics collector with rolling windows and WebSocket streaming
    """

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.window_seconds = window_minutes * 60

        # Rolling window storage
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Connected WebSocket clients
        self.websocket_clients = set()

        # Aggregated metrics cache
        self.aggregated_cache = {}
        self.cache_update_interval = 1.0  # seconds
        self.last_cache_update = 0

        # Service status tracking
        self.service_status = {
            "embeddings": {"status": "unknown", "last_seen": None},
            "llm": {"status": "unknown", "last_seen": None},
            "api_gateway": {"status": "healthy", "last_seen": time.time()},
            "clickhouse": {"status": "unknown", "last_seen": None}
        }

        # Start background tasks
        self._start_background_tasks()

        logger.info(f"🚀 Enhanced Metrics Collector initialized (window: {window_minutes}min)")

    def record_metric(self, service: str, metric_type: str, value: float, **metadata):
        """Record a metric event"""
        event = MetricEvent(
            timestamp=time.time(),
            service=service,
            metric_type=metric_type,
            value=value,
            metadata=metadata
        )

        key = f"{service}.{metric_type}"
        self.metrics_buffer[key].append(event)

        # Update service status
        self.service_status[service]["last_seen"] = time.time()
        self.service_status[service]["status"] = "healthy"

        # Broadcast to WebSocket clients
        asyncio.create_task(self._broadcast_metric(event))

    def record_query_metrics(self, metrics: Dict[str, Any], service: str = "llm"):
        """Record RAG query metrics"""
        timestamp = time.time()

        # Core performance metrics
        if "vector_latency" in metrics:
            self.record_metric(service, "vector_latency", metrics["vector_latency"])

        if "llm_latency" in metrics:
            self.record_metric(service, "llm_latency", metrics["llm_latency"])

        if "total_time" in metrics:
            self.record_metric(service, "total_time", metrics["total_time"])

        if "tokens_used" in metrics:
            self.record_metric(service, "tokens_used", metrics["tokens_used"])

    def record_streaming_metrics(self, ticker: str, records_processed: int, processing_time: float):
        """Record streaming data metrics"""
        self.record_metric(
            "embeddings",
            "streaming_throughput",
            records_processed / processing_time,
            ticker=ticker,
            records=records_processed
        )

        self.record_metric(
            "embeddings",
            "streaming_latency",
            processing_time,
            ticker=ticker
        )

    def record_database_metrics(self, operation: str, latency: float, success: bool):
        """Record database operation metrics"""
        self.record_metric(
            "clickhouse",
            f"db_{operation}_latency",
            latency,
            operation=operation,
            success=success
        )

        # Record success rate
        success_value = 1.0 if success else 0.0
        self.record_metric(
            "clickhouse",
            f"db_{operation}_success_rate",
            success_value,
            operation=operation
        )

    def record_embedding_metrics(self, batch_size: int, processing_time: float, model_name: str):
        """Record embedding generation metrics"""
        throughput = batch_size / processing_time

        self.record_metric(
            "embeddings",
            "embedding_throughput",
            throughput,
            batch_size=batch_size,
            model=model_name
        )

        self.record_metric(
            "embeddings",
            "embedding_latency",
            processing_time,
            batch_size=batch_size,
            model=model_name
        )

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        current_time = time.time()

        # Check if cache needs update
        if current_time - self.last_cache_update > self.cache_update_interval:
            self._update_aggregated_cache()
            self.last_cache_update = current_time

        return self.aggregated_cache

    def get_metrics_for_timeframe(self, minutes: int = None) -> Dict[str, Any]:
        """Get metrics for a specific timeframe"""
        if minutes is None:
            minutes = self.window_minutes

        cutoff_time = time.time() - (minutes * 60)
        aggregated = {}

        for key, events in self.metrics_buffer.items():
            recent_events = [e for e in events if e.timestamp >= cutoff_time]
            if recent_events:
                values = [e.value for e in recent_events]
                aggregated[key] = {
                    "count": len(values),
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1],
                    "sum": sum(values)
                }

                if len(values) > 1:
                    aggregated[key]["std"] = statistics.stdev(values)

        return aggregated

    def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services"""
        current_time = time.time()
        health_timeout = 30  # seconds

        for service, status in self.service_status.items():
            if status["last_seen"]:
                if current_time - status["last_seen"] > health_timeout:
                    status["status"] = "unhealthy"
                else:
                    status["status"] = "healthy"
            else:
                status["status"] = "unknown"

        return dict(self.service_status)

    def export_metrics_csv(self, filename: str = None, minutes: int = None) -> str:
        """Export metrics to CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_export_{timestamp}.csv"

        if minutes is None:
            minutes = self.window_minutes

        cutoff_time = time.time() - (minutes * 60)

        # Collect all events
        all_events = []
        for key, events in self.metrics_buffer.items():
            service, metric_type = key.split('.', 1)
            for event in events:
                if event.timestamp >= cutoff_time:
                    all_events.append({
                        'timestamp': datetime.fromtimestamp(event.timestamp).isoformat(),
                        'service': event.service,
                        'metric_type': event.metric_type,
                        'value': event.value,
                        'metadata': json.dumps(event.metadata)
                    })

        # Sort by timestamp
        all_events.sort(key=lambda x: x['timestamp'])

        # Write CSV
        if all_events:
            import csv
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'service', 'metric_type', 'value', 'metadata']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_events)

        logger.info(f"📄 Exported {len(all_events)} metrics to {filename}")
        return filename

    def export_query_metrics_csv(self, filename: str = None, minutes: int = None) -> str:
        """Export query metrics to a readable CSV file with proper columns"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_metrics_{timestamp}.csv"

        if minutes is None:
            minutes = self.window_minutes

        cutoff_time = time.time() - (minutes * 60)

        # Collect query-specific events
        query_events = []
        for key, events in self.metrics_buffer.items():
            service, metric_type = key.split('.', 1)

            # Only include query processing events
            if 'query_processed' in metric_type or 'financial_query_processed' in metric_type:
                for event in events:
                    if event.timestamp >= cutoff_time:
                        # Extract metadata into separate columns
                        metadata = event.metadata
                        query_events.append({
                            'timestamp': datetime.fromtimestamp(event.timestamp).isoformat(),
                            'query_type': 'financial' if 'financial' in metric_type else 'general',
                            'query': metadata.get('query', ''),
                            'ticker': metadata.get('ticker', ''),
                            'response': metadata.get('response', ''),
                            'total_time_seconds': round(event.value, 4),
                            'vector_latency_seconds': round(metadata.get('vector_latency', 0), 4),
                            'llm_latency_seconds': round(metadata.get('llm_latency', 0), 4),
                            'tokens_used': metadata.get('tokens_used', 0),
                            'model_name': metadata.get('model_name', ''),
                            'status': metadata.get('status', '')
                        })

        # Sort by timestamp
        query_events.sort(key=lambda x: x['timestamp'])

        # Write readable CSV
        if query_events:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'timestamp', 'query_type', 'query', 'ticker', 'response',
                    'total_time_seconds', 'vector_latency_seconds', 'llm_latency_seconds',
                    'tokens_used', 'model_name', 'status'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(query_events)

        logger.info(f"📊 Exported {len(query_events)} query metrics to {filename}")
        return filename

    async def register_websocket_client(self, websocket):
        """Register a new WebSocket client"""
        self.websocket_clients.add(websocket)
        logger.info(f"📡 WebSocket client connected ({len(self.websocket_clients)} total)")

        # Send current metrics immediately
        try:
            current_metrics = self.get_real_time_metrics()
            await websocket.send(json.dumps({
                "type": "current_metrics",
                "data": current_metrics,
                "timestamp": time.time()
            }))
        except Exception as e:
            logger.error(f"Error sending initial metrics: {e}")

    async def unregister_websocket_client(self, websocket):
        """Unregister a WebSocket client"""
        self.websocket_clients.discard(websocket)
        logger.info(f"📡 WebSocket client disconnected ({len(self.websocket_clients)} total)")

    async def _broadcast_metric(self, event: MetricEvent):
        """Broadcast metric to all WebSocket clients"""
        if not self.websocket_clients:
            return

        message = {
            "type": "metric_update",
            "data": asdict(event),
            "timestamp": time.time()
        }

        # Send to all connected clients
        disconnected_clients = set()
        for client in self.websocket_clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients

    def _update_aggregated_cache(self):
        """Update the aggregated metrics cache"""
        try:
            current_metrics = self.get_metrics_for_timeframe()
            service_health = self.get_service_health()

            self.aggregated_cache = {
                "metrics": current_metrics,
                "service_health": service_health,
                "summary": {
                    "total_services": len(service_health),
                    "healthy_services": sum(1 for s in service_health.values() if s["status"] == "healthy"),
                    "total_metrics": sum(len(events) for events in self.metrics_buffer.values()),
                    "window_minutes": self.window_minutes
                },
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Error updating aggregated cache: {e}")

    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        def cleanup_old_metrics():
            """Remove metrics outside the rolling window"""
            while True:
                try:
                    cutoff_time = time.time() - self.window_seconds
                    for key, events in self.metrics_buffer.items():
                        # Remove old events
                        while events and events[0].timestamp < cutoff_time:
                            events.popleft()

                    # Sleep for cleanup interval
                    time.sleep(60)  # Cleanup every minute

                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
                    time.sleep(60)

        # Start cleanup thread
        cleanup_thread = threading.Thread(target=cleanup_old_metrics, daemon=True)
        cleanup_thread.start()

# Global metrics collector instance
metrics_collector = EnhancedMetricsCollector()