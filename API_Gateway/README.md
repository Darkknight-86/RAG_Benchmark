# API Gateway with Metrics Collection

This API Gateway service provides a centralized interface for RAG (Retrieval-Augmented Generation) microservices, with integrated metrics collection and benchmarking capabilities.

## Features

- **Metrics Collection**: Collects metrics from active RAG microservices
- **Benchmarking**: Measures and analyzes performance of RAG pipeline components
- **Dashboard**: Web interface for viewing metrics and benchmark results
- **CSV Export**: Export benchmark results for further analysis

## Architecture

The service consists of several key components:

1. **MetricsCollector**: Collects metrics from active RAG services
2. **RAGBenchmarks**: Handles benchmarking of RAG pipeline components
3. **MetricsDashboard**: Provides a web interface for viewing metrics
4. **APIGatewayServer**: Main server that integrates all components

## API Endpoints

### Metrics Collection

- `GET /api/metrics/active`: Get list of active services being monitored
- `POST /api/metrics/start`: Start collecting metrics for a service
- `POST /api/metrics/stop`: Stop collecting metrics for a service

### Benchmarks

- `GET /api/benchmarks`: Get benchmark results
- `GET /api/benchmarks/export`: Export benchmark results to CSV
- `POST /api/benchmarks/clear`: Clear benchmark data

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Run the server:
   ```bash
   poetry run python -m api_gateway.server
   ```

## Development

- Python 3.11.12 is required
- Uses Poetry for dependency management
- Tests can be run with:
  ```bash
  poetry run pytest
  ```

## Metrics Collection

The metrics collector operates on-demand, only collecting data from active microservices. It supports the following RAG components:

- A2: PDF Processing
- A3: Data Loading
- B2: Text Chunking
- B3: Embedding Generation
- B4: Vector Storage
- C3: Query Trigger
- D1: Query Ingestion
- D2: Vector Retrieval
- D3: LLM Response

## Dashboard Integration

The dashboard is integrated into the API Gateway but is activated by the GUI microservice. It provides:

- Real-time metrics visualization
- Benchmark results in tabular format
- CSV export functionality
- Service status monitoring

## License

MIT