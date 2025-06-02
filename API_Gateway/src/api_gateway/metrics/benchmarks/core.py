"""
RAG benchmarking system.

Collects and analyzes metrics from RAG components:
- Population: A2 → A3 → B2 → B3 → B4
- Updates: Incremental B4 operations
- Queries: C3 → D1 → D2 → D3

Focuses on RAG-specific metrics not covered by OTC tools:
- Document processing quality and throughput
- Chunk generation statistics
- LLM token usage and efficiency
- Pipeline success rates
- Cross-component analysis

Note: Tool-specific metrics (FAISS, Redis, ChromaDB, Prometheus) are handled by their native implementations.
"""

import time
import threading
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from collections import deque
import statistics
import logging
from contextlib import contextmanager
import pandas as pd
import json
import os

from .models import StageMetric, PopulationPipelineBenchmark, UpdatePipelineBenchmark, QueryPipelineBenchmark
from .config import PERFORMANCE_TARGETS, PIPELINE_TARGETS, BENCHMARK_SETTINGS
from .utils import measure_time, measure_memory, calculate_throughput

class RAGBenchmarks:
    """
    RAG benchmarking system.

    Focuses on RAG-specific metrics not covered by OTC tools:
    1. Document Processing Quality
       - Chunk size distribution
       - Content preservation
       - Processing throughput

    2. LLM Efficiency
       - Token usage patterns
       - Response quality
       - Inference speed

    3. Pipeline Performance
       - End-to-end latency
       - Success rates
       - Resource utilization

    4. Cross-Component Analysis
       - Bottleneck identification
       - Component interaction
       - Resource sharing
    """

    def __init__(self, window_size: int = BENCHMARK_SETTINGS['window_size']):
        self.window_size = window_size

        # Pipeline-specific metrics
        self._population_benchmarks: deque = deque(maxlen=window_size)
        self._update_benchmarks: deque = deque(maxlen=window_size)
        self._query_benchmarks: deque = deque(maxlen=window_size)

        # Component-specific metrics
        self._stage_timings: Dict[str, deque] = {
            'A2': deque(maxlen=window_size),  # PDF Processing
            'A3': deque(maxlen=window_size),  # Load Raw Data
            'B2': deque(maxlen=window_size),  # Chunking
            'B3': deque(maxlen=window_size),  # Embedding Generation
            'B4': deque(maxlen=window_size),  # Vector Storage
            'C3': deque(maxlen=window_size),  # Query Trigger
            'D1': deque(maxlen=window_size),  # Query Ingestion
            'D2': deque(maxlen=window_size),  # Vector Retrieval
            'D3': deque(maxlen=window_size),  # LLM Response
        }

        # Cross-component analysis
        self._pipeline_interactions: Dict[str, List[Dict]] = {
            'population': [],
            'update': [],
            'query': []
        }

        self._lock = threading.RLock()
        self.performance_targets = PERFORMANCE_TARGETS
        self.logger = logging.getLogger(__name__)

    def to_dataframe(self) -> Dict[str, pd.DataFrame]:
        """Convert all benchmark data to pandas DataFrames."""
        with self._lock:
            # Convert stage timings to DataFrame
            stage_data = []
            for component, metrics in self._stage_timings.items():
                for metric in metrics:
                    stage_data.append({
                        'component': component,
                        'stage_name': metric.stage_name,
                        'service_name': metric.service_name,
                        'start_time': metric.start_time,
                        'end_time': metric.end_time,
                        'duration': metric.duration,
                        'input_size': metric.input_size,
                        'output_size': metric.output_size,
                        'throughput': metric.throughput,
                        'success': metric.success,
                        **metric.metadata
                    })
            stage_df = pd.DataFrame(stage_data) if stage_data else pd.DataFrame()

            # Convert population benchmarks to DataFrame
            pop_data = [{
                'documents_processed': b.documents_processed,
                'chunks_generated': b.chunks_generated,
                'avg_chunk_size': b.avg_chunk_size,
                'embedding_model': b.embedding_model,
                'total_pipeline_time': b.total_pipeline_time,
                'memory_peak': b.memory_peak,
                'documents_per_second': b.documents_per_second
            } for b in self._population_benchmarks]
            pop_df = pd.DataFrame(pop_data) if pop_data else pd.DataFrame()

            # Convert update benchmarks to DataFrame
            update_data = [{
                'update_type': b.update_type,
                'total_update_time': b.total_update_time,
                'documents_updated': b.documents_updated,
                'vectors_affected': b.vectors_affected,
                'concurrent_query_impact': b.concurrent_query_impact,
                'success': b.success,
                'update_throughput': b.update_throughput
            } for b in self._update_benchmarks]
            update_df = pd.DataFrame(update_data) if update_data else pd.DataFrame()

            # Convert query benchmarks to DataFrame
            query_data = [{
                'query_text': b.query_text,
                'top_k_requested': b.top_k_requested,
                'results_returned': b.results_returned,
                'input_tokens': b.input_tokens,
                'output_tokens': b.output_tokens,
                'llm_model': b.llm_model,
                'total_query_time': b.total_query_time,
                'llm_inference_time': b.llm_inference_time,
                'cache_hit': b.cache_hit,
                'tokens_per_second': b.tokens_per_second
            } for b in self._query_benchmarks]
            query_df = pd.DataFrame(query_data) if query_data else pd.DataFrame()

            # Convert pipeline interactions to DataFrame
            interaction_data = []
            for pipeline, interactions in self._pipeline_interactions.items():
                for interaction in interactions:
                    interaction_data.append({
                        'pipeline': pipeline,
                        **interaction
                    })
            interaction_df = pd.DataFrame(interaction_data) if interaction_data else pd.DataFrame()

            return {
                'stage_metrics': stage_df,
                'population_benchmarks': pop_df,
                'update_benchmarks': update_df,
                'query_benchmarks': query_df,
                'pipeline_interactions': interaction_df
            }

    def export_to_csv(self, directory: str):
        """Export all benchmark data to CSV files."""
        dfs = self.to_dataframe()
        for name, df in dfs.items():
            if not df.empty:
                df.to_csv(f"{directory}/{name}.csv", index=False)
                self.logger.info(f"Exported {name} to {directory}/{name}.csv")

    def export_to_json(self, directory: str):
        """Export all benchmark data to JSON files."""
        dfs = self.to_dataframe()
        for name, df in dfs.items():
            if not df.empty:
                # Convert datetime objects to strings
                df = df.copy()
                for col in df.select_dtypes(include=['datetime64']).columns:
                    df[col] = df[col].astype(str)

                # Export to JSON
                df.to_json(f"{directory}/{name}.json", orient='records', date_format='iso')
                self.logger.info(f"Exported {name} to {directory}/{name}.json")

    @contextmanager
    def measure_stage(self, component: str, stage_name: str,
                     service_name: str, input_size: int, **metadata):
        """
        Measure performance of specific RAG component.

        Args:
            component: Component ID ('A2', 'B3', 'D2', etc.)
            stage_name: Descriptive stage name
            service_name: Microservice name
            input_size: Number of items being processed
        """
        start_time = datetime.now()
        start_ts = time.time()
        success = True
        output_size = input_size

        def report_output_size(size: int):
            nonlocal output_size
            output_size = size

        try:
            self.logger.debug(f"Starting {component}: {stage_name}")
            yield report_output_size

        except Exception as e:
            success = False
            self.logger.error(f"{component} failed: {e}")
            raise

        finally:
            end_time = datetime.now()
            duration = time.time() - start_ts

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
                metadata=metadata
            )

            with self._lock:
                self._stage_timings[component].append(metric)

            self.logger.info(f"{component} completed: {duration:.3f}s, "
                           f"throughput: {metric.throughput:.2f} items/sec")

    def record_population_pipeline(self, documents_processed: int,
                                 chunks_generated: int, avg_chunk_size: int,
                                 embedding_model: str, total_pipeline_time: float,
                                 memory_peak: float):
        """Record complete population pipeline benchmark."""
        benchmark = PopulationPipelineBenchmark(
            documents_processed=documents_processed,
            chunks_generated=chunks_generated,
            avg_chunk_size=avg_chunk_size,
            embedding_model=embedding_model,
            total_pipeline_time=total_pipeline_time,
            memory_peak=memory_peak
        )

        with self._lock:
            self._population_benchmarks.append(benchmark)
            self._record_pipeline_interaction('population', {
                'documents_processed': documents_processed,
                'chunks_generated': chunks_generated,
                'avg_chunk_size': avg_chunk_size,
                'total_time': total_pipeline_time,
                'memory_peak': memory_peak
            })

        self.logger.info(f"Population pipeline: {documents_processed} docs, "
                        f"{total_pipeline_time:.2f}s total")
        self._check_population_performance(benchmark)

    def record_update_pipeline(self, update_type: str, total_update_time: float,
                             documents_updated: int, vectors_affected: int,
                             concurrent_query_impact: float, success: bool):
        """Record update pipeline benchmark."""
        benchmark = UpdatePipelineBenchmark(
            update_type=update_type,
            total_update_time=total_update_time,
            documents_updated=documents_updated,
            vectors_affected=vectors_affected,
            concurrent_query_impact=concurrent_query_impact,
            success=success
        )

        with self._lock:
            self._update_benchmarks.append(benchmark)
            self._record_pipeline_interaction('update', {
                'update_type': update_type,
                'documents_updated': documents_updated,
                'vectors_affected': vectors_affected,
                'total_time': total_update_time,
                'concurrent_impact': concurrent_query_impact,
                'success': success
            })

        self.logger.info(f"Update pipeline: {update_type}, {documents_updated} docs, "
                        f"{benchmark.update_throughput:.2f} docs/sec")
        self._check_update_performance(benchmark)

    def record_query_pipeline(self, query_text: str, top_k_requested: int,
                            results_returned: int, input_tokens: int,
                            output_tokens: int, llm_model: str,
                            total_query_time: float, llm_inference_time: float,
                            cache_hit: bool = False):
        """Record complete query pipeline benchmark."""
        benchmark = QueryPipelineBenchmark(
            query_text=query_text,
            top_k_requested=top_k_requested,
            results_returned=results_returned,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            llm_model=llm_model,
            total_query_time=total_query_time,
            llm_inference_time=llm_inference_time,
            cache_hit=cache_hit
        )

        with self._lock:
            self._query_benchmarks.append(benchmark)
            self._record_pipeline_interaction('query', {
                'query_length': len(query_text),
                'top_k': top_k_requested,
                'results': results_returned,
                'total_tokens': input_tokens + output_tokens,
                'total_time': total_query_time,
                'llm_time': llm_inference_time,
                'cache_hit': cache_hit
            })

        self.logger.info(f"Query pipeline: {total_query_time:.3f}s total, "
                        f"tokens: {input_tokens + output_tokens}")
        self._check_query_performance(benchmark)

    def get_component_analytics(self, component: str) -> Dict:
        """Get analytics for specific component (A2, B3, D2, etc.)."""
        with self._lock:
            stage_metrics = list(self._stage_timings[component])

        if not stage_metrics:
            return {'error': f'No data for component {component}'}

        throughputs = [m.throughput for m in stage_metrics]
        success_rate = sum(m.success for m in stage_metrics) / len(stage_metrics)

        return {
            'component': component,
            'avg_throughput': statistics.mean(throughputs),
            'success_rate': success_rate,
            'sample_count': len(stage_metrics),
            'latest_performance': {
                'throughput': throughputs[-1],
                'success': stage_metrics[-1].success
            }
        }

    def get_pipeline_analytics(self) -> Dict:
        """Get analytics for all three pipeline types."""
        return {
            'population_pipeline': self._analyze_population_pipeline(),
            'update_pipeline': self._analyze_update_pipeline(),
            'query_pipeline': self._analyze_query_pipeline(),
            'components': {
                component: self.get_component_analytics(component)
                for component in self._stage_timings.keys()
            },
            'pipeline_interactions': self._analyze_pipeline_interactions()
        }

    def _analyze_population_pipeline(self) -> Dict:
        """Analyze A2→A3→B2→B3→B4 pipeline performance."""
        with self._lock:
            benchmarks = list(self._population_benchmarks)

        if not benchmarks:
            return {'error': 'No population pipeline data available'}

        return {
            'avg_documents_per_second': statistics.mean(b.documents_per_second for b in benchmarks),
            'avg_memory_peak': statistics.mean(b.memory_peak for b in benchmarks),
            'avg_chunk_size': statistics.mean(b.avg_chunk_size for b in benchmarks),
            'sample_count': len(benchmarks),
            'latest_performance': {
                'documents_processed': benchmarks[-1].documents_processed,
                'chunks_generated': benchmarks[-1].chunks_generated,
                'memory_peak': benchmarks[-1].memory_peak
            }
        }

    def _analyze_update_pipeline(self) -> Dict:
        """Analyze update pipeline performance."""
        with self._lock:
            benchmarks = list(self._update_benchmarks)

        if not benchmarks:
            return {'error': 'No update pipeline data available'}

        return {
            'avg_update_throughput': statistics.mean(b.update_throughput for b in benchmarks),
            'success_rate': sum(b.success for b in benchmarks) / len(benchmarks),
            'avg_concurrent_impact': statistics.mean(b.concurrent_query_impact for b in benchmarks),
            'sample_count': len(benchmarks),
            'latest_performance': {
                'update_type': benchmarks[-1].update_type,
                'documents_updated': benchmarks[-1].documents_updated,
                'success': benchmarks[-1].success
            }
        }

    def _analyze_query_pipeline(self) -> Dict:
        """Analyze C3→D1→D2→D3 pipeline performance."""
        with self._lock:
            benchmarks = list(self._query_benchmarks)

        if not benchmarks:
            return {'error': 'No query pipeline data available'}

        return {
            'avg_tokens_per_second': statistics.mean(b.tokens_per_second for b in benchmarks),
            'cache_hit_rate': sum(b.cache_hit for b in benchmarks) / len(benchmarks),
            'avg_query_time': statistics.mean(b.total_query_time for b in benchmarks),
            'avg_llm_time': statistics.mean(b.llm_inference_time for b in benchmarks),
            'sample_count': len(benchmarks),
            'latest_performance': {
                'tokens_per_second': benchmarks[-1].tokens_per_second,
                'cache_hit': benchmarks[-1].cache_hit,
                'query_time': benchmarks[-1].total_query_time
            }
        }

    def _analyze_pipeline_interactions(self) -> Dict:
        """Analyze interactions between pipeline components."""
        with self._lock:
            interactions = {
                pipeline: list(data)
                for pipeline, data in self._pipeline_interactions.items()
            }

        if not any(interactions.values()):
            return {'error': 'No pipeline interaction data available'}

        return {
            'population_impact': self._analyze_population_impact(interactions['population']),
            'update_impact': self._analyze_update_impact(interactions['update']),
            'query_impact': self._analyze_query_impact(interactions['query'])
        }

    def _analyze_population_impact(self, interactions: List[Dict]) -> Dict:
        """Analyze impact of population pipeline on system."""
        if not interactions:
            return {'error': 'No population interaction data available'}

        return {
            'avg_documents_per_batch': statistics.mean(i['documents_processed'] for i in interactions),
            'avg_chunks_per_document': statistics.mean(
                i['chunks_generated'] / i['documents_processed']
                for i in interactions if i['documents_processed'] > 0
            ),
            'avg_memory_usage': statistics.mean(i['memory_peak'] for i in interactions),
            'avg_processing_time': statistics.mean(i['total_time'] for i in interactions),
            'total_documents_processed': sum(i['documents_processed'] for i in interactions),
            'total_chunks_generated': sum(i['chunks_generated'] for i in interactions)
        }

    def _analyze_update_impact(self, interactions: List[Dict]) -> Dict:
        """Analyze impact of update pipeline on system."""
        if not interactions:
            return {'error': 'No update interaction data available'}

        return {
            'avg_documents_per_update': statistics.mean(i['documents_updated'] for i in interactions),
            'avg_vectors_affected': statistics.mean(i['vectors_affected'] for i in interactions),
            'avg_update_time': statistics.mean(i['total_time'] for i in interactions),
            'avg_concurrent_impact': statistics.mean(i['concurrent_impact'] for i in interactions),
            'success_rate': sum(1 for i in interactions if i['success']) / len(interactions),
            'total_documents_updated': sum(i['documents_updated'] for i in interactions)
        }

    def _analyze_query_impact(self, interactions: List[Dict]) -> Dict:
        """Analyze impact of query pipeline on system."""
        if not interactions:
            return {'error': 'No query interaction data available'}

        return {
            'avg_query_length': statistics.mean(i['query_length'] for i in interactions),
            'avg_results_per_query': statistics.mean(i['results'] for i in interactions),
            'avg_tokens_per_query': statistics.mean(i['total_tokens'] for i in interactions),
            'avg_query_time': statistics.mean(i['total_time'] for i in interactions),
            'avg_llm_time': statistics.mean(i['llm_time'] for i in interactions),
            'cache_hit_rate': sum(1 for i in interactions if i['cache_hit']) / len(interactions),
            'total_queries': len(interactions)
        }

    def _record_pipeline_interaction(self, pipeline: str, data: Dict):
        """Record interaction between pipeline components."""
        self._pipeline_interactions[pipeline].append({
            'timestamp': datetime.now().isoformat(),
            **data
        })

    def _check_population_performance(self, benchmark: PopulationPipelineBenchmark):
        """Check if population pipeline meets performance targets."""
        targets = PIPELINE_TARGETS['population']
        if benchmark.documents_per_second < targets['min_docs_per_second']:
            self.logger.warning(f"Population throughput too low: {benchmark.documents_per_second:.2f} "
                              f"(target: {targets['min_docs_per_second']})")

    def _check_update_performance(self, benchmark: UpdatePipelineBenchmark):
        """Check if update pipeline meets performance targets."""
        targets = PIPELINE_TARGETS['update']
        if benchmark.update_throughput < targets['min_updates_per_second']:
            self.logger.warning(f"Update throughput too low: {benchmark.update_throughput:.2f} "
                              f"(target: {targets['min_updates_per_second']})")

    def _check_query_performance(self, benchmark: QueryPipelineBenchmark):
        """Check if query pipeline meets performance targets."""
        targets = PIPELINE_TARGETS['query']
        if benchmark.tokens_per_second < targets['min_queries_per_second']:
            self.logger.warning(f"Query throughput too low: {benchmark.tokens_per_second:.2f} "
                              f"(target: {targets['min_queries_per_second']})")