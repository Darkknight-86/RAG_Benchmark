"""
Tests for RAG benchmarking system.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import pandas as pd
import tempfile
import os

from api_gateway.metrics.benchmarks import RAGBenchmarks
from api_gateway.metrics.benchmarks.models import (
    StageMetric,
    PopulationPipelineBenchmark,
    UpdatePipelineBenchmark,
    QueryPipelineBenchmark
)

@pytest.fixture
def benchmarks():
    """Create a RAGBenchmarks instance for testing."""
    return RAGBenchmarks(window_size=10)

def test_benchmarks_to_dataframe(benchmarks):
    """Test conversion of benchmarks to pandas DataFrame."""
    # Add some test data
    benchmarks.record_population_pipeline(
        documents_processed=100,
        chunks_generated=500,
        avg_chunk_size=1000,
        embedding_model='test-model',
        total_pipeline_time=10.0,
        memory_peak=1024.0
    )

    benchmarks.record_update_pipeline(
        update_type='incremental',
        total_update_time=5.0,
        documents_updated=50,
        vectors_affected=200,
        concurrent_query_impact=0.1,
        success=True
    )

    benchmarks.record_query_pipeline(
        query_text='test query',
        top_k_requested=5,
        results_returned=5,
        input_tokens=100,
        output_tokens=200,
        llm_model='test-model',
        total_query_time=2.0,
        llm_inference_time=1.5,
        cache_hit=False
    )

    # Get analytics and convert to DataFrame
    analytics = benchmarks.get_pipeline_analytics()
    df = pd.DataFrame(analytics)

    # Test DataFrame structure
    assert not df.empty
    assert 'population_pipeline' in df.columns
    assert 'update_pipeline' in df.columns
    assert 'query_pipeline' in df.columns
    assert 'components' in df.columns

def test_export_benchmarks_to_csv(benchmarks):
    """Test exporting benchmarks to CSV."""
    # Add test data
    benchmarks.record_population_pipeline(
        documents_processed=100,
        chunks_generated=500,
        avg_chunk_size=1000,
        embedding_model='test-model',
        total_pipeline_time=10.0,
        memory_peak=1024.0
    )
    benchmarks.record_update_pipeline(
        update_type='incremental',
        total_update_time=5.0,
        documents_updated=50,
        vectors_affected=200,
        concurrent_query_impact=0.1,
        success=True
    )
    benchmarks.record_query_pipeline(
        query_text='test query',
        top_k_requested=5,
        results_returned=5,
        input_tokens=100,
        output_tokens=200,
        llm_model='test-model',
        total_query_time=2.0,
        llm_inference_time=1.5,
        cache_hit=False
    )
    # Add stage metrics
    with benchmarks.measure_stage(
        component='A2',
        stage_name='Test Stage',
        service_name='test-service',
        input_size=10
    ) as report_output:
        report_output(8)
    # Create temporary directory for exports
    with tempfile.TemporaryDirectory() as tmpdir:
        # Export to CSV
        benchmarks.export_to_csv(tmpdir)
        # Verify files were created
        assert os.path.exists(os.path.join(tmpdir, 'stage_metrics.csv'))
        assert os.path.exists(os.path.join(tmpdir, 'population_benchmarks.csv'))
        assert os.path.exists(os.path.join(tmpdir, 'update_benchmarks.csv'))
        assert os.path.exists(os.path.join(tmpdir, 'query_benchmarks.csv'))

def test_export_benchmarks_to_json(benchmarks):
    """Test exporting benchmarks to JSON."""
    # Add test data
    benchmarks.record_population_pipeline(
        documents_processed=100,
        chunks_generated=500,
        avg_chunk_size=1000,
        embedding_model='test-model',
        total_pipeline_time=10.0,
        memory_peak=1024.0
    )
    benchmarks.record_update_pipeline(
        update_type='incremental',
        total_update_time=5.0,
        documents_updated=50,
        vectors_affected=200,
        concurrent_query_impact=0.1,
        success=True
    )
    benchmarks.record_query_pipeline(
        query_text='test query',
        top_k_requested=5,
        results_returned=5,
        input_tokens=100,
        output_tokens=200,
        llm_model='test-model',
        total_query_time=2.0,
        llm_inference_time=1.5,
        cache_hit=False
    )
    # Add stage metrics
    with benchmarks.measure_stage(
        component='A2',
        stage_name='Test Stage',
        service_name='test-service',
        input_size=10
    ) as report_output:
        report_output(8)
    # Create temporary directory for exports
    with tempfile.TemporaryDirectory() as tmpdir:
        # Export to JSON
        benchmarks.export_to_json(tmpdir)
        # Verify files were created
        assert os.path.exists(os.path.join(tmpdir, 'stage_metrics.json'))
        assert os.path.exists(os.path.join(tmpdir, 'population_benchmarks.json'))
        assert os.path.exists(os.path.join(tmpdir, 'update_benchmarks.json'))
        assert os.path.exists(os.path.join(tmpdir, 'query_benchmarks.json'))

def test_measure_stage(benchmarks):
    """Test stage measurement functionality."""
    with benchmarks.measure_stage(
        component='A2',
        stage_name='Test Stage',
        service_name='test-service',
        input_size=10
    ) as report_output:
        report_output(8)  # Simulate output size

    # Verify stage metrics were recorded
    analytics = benchmarks.get_component_analytics('A2')
    assert analytics['component'] == 'A2'
    assert analytics['sample_count'] == 1
    assert analytics['success_rate'] == 1.0

def test_pipeline_analytics(benchmarks):
    """Test pipeline analytics functionality."""
    # Add test data for all pipeline types
    benchmarks.record_population_pipeline(
        documents_processed=100,
        chunks_generated=500,
        avg_chunk_size=1000,
        embedding_model='test-model',
        total_pipeline_time=10.0,
        memory_peak=1024.0
    )

    benchmarks.record_update_pipeline(
        update_type='incremental',
        total_update_time=5.0,
        documents_updated=50,
        vectors_affected=200,
        concurrent_query_impact=0.1,
        success=True
    )

    benchmarks.record_query_pipeline(
        query_text='test query',
        top_k_requested=5,
        results_returned=5,
        input_tokens=100,
        output_tokens=200,
        llm_model='test-model',
        total_query_time=2.0,
        llm_inference_time=1.5,
        cache_hit=False
    )

    # Get analytics
    analytics = benchmarks.get_pipeline_analytics()

    # Verify analytics structure
    assert 'population_pipeline' in analytics
    assert 'update_pipeline' in analytics
    assert 'query_pipeline' in analytics
    assert 'components' in analytics

    # Verify population pipeline analytics
    pop_analytics = analytics['population_pipeline']
    assert 'avg_documents_per_second' in pop_analytics
    assert 'avg_memory_peak' in pop_analytics
    assert 'sample_count' in pop_analytics

    # Verify update pipeline analytics
    update_analytics = analytics['update_pipeline']
    assert 'avg_update_throughput' in update_analytics
    assert 'success_rate' in update_analytics
    assert 'sample_count' in update_analytics

    # Verify query pipeline analytics
    query_analytics = analytics['query_pipeline']
    assert 'avg_tokens_per_second' in query_analytics
    assert 'cache_hit_rate' in query_analytics
    assert 'sample_count' in query_analytics