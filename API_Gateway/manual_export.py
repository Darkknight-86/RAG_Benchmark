import os
from api_gateway.metrics.benchmarks import RAGBenchmarks

benchmarks = RAGBenchmarks(window_size=10)

# Record RAG pipeline metrics
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

# Record stage metrics
with benchmarks.measure_stage(
    component='A2',
    stage_name='Test Stage',
    service_name='test-service',
    input_size=10
) as report_output:
    report_output(8)

os.makedirs('exports', exist_ok=True)
benchmarks.export_to_csv('exports')
print('Exported files to ./exports/')
