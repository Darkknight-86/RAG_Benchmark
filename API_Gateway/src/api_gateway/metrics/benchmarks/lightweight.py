"""
Lightweight RAG Benchmarking.

A simplified benchmarking utility focused on stage timings only.  It avoids heavy
runtime dependencies (e.g., pandas) and large dataframes, while still allowing
micro-services to annotate key pipeline stages for later analysis.
"""

from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime
from typing import DefaultDict, Deque, Dict, List, Tuple, Generator, Any

from .models import StageMetric  # Re-use existing dataclass
from .config import BENCHMARK_SETTINGS

__all__ = ["LightweightRAGBenchmarks"]


class LightweightRAGBenchmarks:
    """Very small footprint benchmarking helper.

    Usage::

        benchmarks = LightweightRAGBenchmarks()
        with benchmarks.measure_stage("D2", "Vector Retrieval", "embeddings", 10):
            # code to benchmark …
            pass

    After your application has run you can call :py:meth:`summary` to obtain a
    dict that the UI (or an API endpoint) can easily render.
    """

    def __init__(self, window_size: int | None = None):
        if window_size is None:
            window_size = BENCHMARK_SETTINGS.get("window_size", 1000)
        self._window_size = window_size

        # Store StageMetric objects per component (A2, B3, etc.)
        self._stage_timings: DefaultDict[str, Deque[StageMetric]] = defaultdict(
            lambda: deque(maxlen=self._window_size)
        )
        self._lock = threading.RLock()

    # ---------------------------------------------------------------------
    # Context manager helpers
    # ---------------------------------------------------------------------

    @contextmanager
    def measure_stage(
        self,
        component: str,
        stage_name: str,
        service_name: str,
        input_size: int,
        **metadata: Any,
    ) -> Generator[None, None, None]:
        """Context-manager to measure a code block.

        Parameters
        ----------
        component
            Component identifier (e.g. "D2").
        stage_name
            Human readable stage name.
        service_name
            Name of the micro-service running this stage.
        input_size
            Number of items processed.
        metadata
            Arbitrary extra information.
        """
        start_time = datetime.utcnow()
        start_ts = time.perf_counter()
        output_size = input_size
        success = True

        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.perf_counter() - start_ts
            end_time = datetime.utcnow()

            metric = StageMetric(
                component=component,
                stage_name=stage_name,
                service_name=service_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                input_size=input_size,
                output_size=output_size,
                success=success,
                metadata=metadata,
            )

            with self._lock:
                self._stage_timings[component].append(metric)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Dict[str, float]]:
        """Return simple avg latency & throughput per component."""
        with self._lock:
            result: Dict[str, Dict[str, float]] = {}
            for comp, metrics in self._stage_timings.items():
                if not metrics:
                    continue
                total_duration = sum(m.duration for m in metrics)
                total_items = sum(m.output_size for m in metrics)
                avg_latency = total_duration / len(metrics)
                throughput = total_items / total_duration if total_duration > 0 else 0.0
                result[comp] = {
                    "samples": len(metrics),
                    "avg_latency": avg_latency,
                    "throughput": throughput,
                }
            return result

    # Convenience to export as JSON-serialisable structure
    def export(self) -> List[Dict[str, Any]]:
        """Return raw metrics as list of dicts for later JSON dumps."""
        with self._lock:
            return [metric.__dict__ for metrics in self._stage_timings.values() for metric in metrics]