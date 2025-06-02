"""
Utility functions for RAG benchmarking.
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

@contextmanager
def measure_time(description: str = "operation") -> float:
    """
    Context manager to measure execution time.

    Args:
        description: Description of the operation being measured

    Yields:
        None

    Returns:
        float: Duration in seconds
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.debug(f"{description} took {duration:.3f} seconds")

@contextmanager
def measure_memory(description: str = "operation") -> float:
    """
    Context manager to measure memory usage.

    Args:
        description: Description of the operation being measured

    Yields:
        None

    Returns:
        float: Peak memory usage in MB
    """
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    peak_memory = start_memory

    try:
        yield
    finally:
        current_memory = process.memory_info().rss / 1024 / 1024
        peak_memory = max(peak_memory, current_memory)
        memory_increase = peak_memory - start_memory
        logger.debug(f"{description} memory usage: {memory_increase:.1f} MB")

def calculate_throughput(items_processed: int, duration: float) -> float:
    """
    Calculate throughput in items per second.

    Args:
        items_processed: Number of items processed
        duration: Duration in seconds

    Returns:
        float: Throughput in items per second
    """
    return items_processed / duration if duration > 0 else 0.0

def format_duration(seconds: float) -> str:
    """
    Format duration in a human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        str: Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds / 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"

def get_system_metrics() -> Dict[str, float]:
    """
    Get current system metrics.

    Returns:
        Dict[str, float]: Dictionary of system metrics
    """
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage_percent': psutil.disk_usage('/').percent
    }

def check_resource_limits(limits: Dict[str, float]) -> Dict[str, bool]:
    """
    Check if current resource usage exceeds limits.

    Args:
        limits: Dictionary of resource limits

    Returns:
        Dict[str, bool]: Dictionary indicating which limits are exceeded
    """
    current_metrics = get_system_metrics()
    return {
        resource: current_metrics[resource] > limit
        for resource, limit in limits.items()
    }

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0
) -> Any:
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to increase delay by after each retry

    Returns:
        Any: Result of the function call

    Raises:
        Exception: Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s")
                time.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)

    raise last_exception

def timestamp_to_iso(timestamp: Optional[float] = None) -> str:
    """
    Convert timestamp to ISO format string.

    Args:
        timestamp: Unix timestamp (defaults to current time)

    Returns:
        str: ISO format timestamp string
    """
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).isoformat()