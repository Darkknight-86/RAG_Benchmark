# RAG Benchmarking – Current State and Roadmap

_Last updated: {{TODAY}}_

---

## What is Implemented Today ✅

| Area | Details |
|------|---------|
| **Query-level metrics** | Recorded via `metrics.metrics_collector`. Captures vector latency, LLM latency, total time, tokens used, vector-store type, and status.  Exposed in Prometheus counters/histograms and downloadable as CSV via `/api/metrics/export` (default CSV, `?format=json` optional). |
| **Light-weight stage benchmarking** | `metrics.benchmarks.LightweightRAGBenchmarks` gives a tiny, dependency-free context-manager (`measure_stage`) to time any component stage (A2, B3, D2, …).  Provides an in-memory ring-buffer and `summary()` helper for quick analytics. |
| **CSV export** | `MetricsCollector.export_metrics()` now writes CSV by default.  UI button downloads the CSV straight from the Gateway. |

## How to Use 🛠️

```python
from api_gateway.metrics import metrics_collector, RAGBenchmarks

# Record a query
metrics_collector.record_query(
    query="How tall is Mount Everest?",
    response="Mount Everest is about 8,848 metres tall.",
    vector_latency=0.012,
    llm_latency=0.350,
    total_time=0.402,
    tokens_used=42,
    vector_store_type="pgvector",
)

# Benchmark a stage in your micro-service
benchmarks = RAGBenchmarks()  # lightweight version by default
with benchmarks.measure_stage("D2", "Vector Retrieval", "embeddings", input_size=10):
    do_vector_search()
```

## API Endpoints 🌐

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/metrics/summary` | GET | JSON snapshot of aggregate query metrics. |
| `/api/metrics/export` | GET | Download metrics file. `format` query-param (`csv` default, `json` optional). |

## Future Goals 🚀

1. **Full Pipeline Analytics**
   Bring back the heavy-duty `benchmarks.core.RAGBenchmarks` in a separate _analysis_ container or cron job that loads the daily CSV and computes deep statistics with pandas.
2. **UI Visualisations**
   Charts for stage latencies, throughput trends, success-rate gauges.
3. **Real-time Streaming**
   Push Prometheus metrics to Grafana for live dashboarding.
4. **Alerting Rules**
   Prometheus alert manager rules based on targets in `benchmarks/config.py`.
5. **Cross-Service Correlation**
   Stitch together timings from Embeddings, Ingestion and LLM services using the same `LightweightRAGBenchmarks` context IDs.

---

Feel free to expand this document as the benchmarking stack evolves.