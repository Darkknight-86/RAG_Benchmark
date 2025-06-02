"""
Data models for RAG benchmarking system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class StageMetric:
    """Metrics for a single RAG component stage."""
    component: str
    stage_name: str
    service_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    input_size: int
    output_size: int
    success: bool
    metadata: Dict[str, Any]

    @property
    def throughput(self) -> float:
        """Calculate items processed per second."""
        return self.output_size / self.duration if self.duration > 0 else 0.0

@dataclass
class PopulationPipelineBenchmark:
    """Complete population pipeline benchmark data."""
    documents_processed: int
    chunks_generated: int
    avg_chunk_size: int
    embedding_model: str
    total_pipeline_time: float
    memory_peak: float

    @property
    def documents_per_second(self) -> float:
        """Calculate documents processed per second."""
        return self.documents_processed / self.total_pipeline_time if self.total_pipeline_time > 0 else 0.0

@dataclass
class UpdatePipelineBenchmark:
    """Update pipeline benchmark data."""
    update_type: str
    total_update_time: float
    documents_updated: int
    vectors_affected: int
    concurrent_query_impact: float
    success: bool

    @property
    def update_throughput(self) -> float:
        """Calculate updates per second."""
        return self.documents_updated / self.total_update_time if self.total_update_time > 0 else 0.0

@dataclass
class QueryPipelineBenchmark:
    """Query pipeline benchmark data."""
    query_text: str
    top_k_requested: int
    results_returned: int
    input_tokens: int
    output_tokens: int
    llm_model: str
    total_query_time: float
    llm_inference_time: float
    cache_hit: bool = False

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens processed per second."""
        total_tokens = self.input_tokens + self.output_tokens
        return total_tokens / self.llm_inference_time if self.llm_inference_time > 0 else 0.0