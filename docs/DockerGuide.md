# Docker Guide for RAG Project

This guide provides detailed instructions for building, running, and managing the RAG project's Docker containers.

## Project Structure

The project consists of several microservices:
- API Gateway (HTTP:8000, gRPC:50052)
- LLM Service (RAG) (gRPC:50054)
- Embeddings Service (gRPC:50052)
- Ingestion Service (gRPC:50053)
- UI Service (HTTP:3000)

## Prerequisites

1. Install Docker and Docker Compose:
   ```bash
   # For macOS
   brew install docker docker-compose
   ```

2. Ensure you have the following environment variables set up:
   - `HUGGINGFACE_API_KEY` for model access (if using gated models)
   - `DEFAULT_LLM_MODEL` (optional, defaults to "google/flan-t5-small")

## Building and Running

### Building the Containers

1. Build all services:
   ```bash
   docker-compose build
   ```

2. Build specific services:
   ```bash
   docker-compose build [service_name]
   # Example:
   docker-compose build llm-service
   ```

### Running the Services

1. Start all services:
   ```bash
   docker-compose up
   ```

2. Start services in detached mode:
   ```bash
   docker-compose up -d
   ```

3. Start specific services:
   ```bash
   docker-compose up [service_name]
   # Example:
   docker-compose up llm-service
   ```

## Service-Specific Instructions

### LLM Service (RAG)
- Port: 50054 (gRPC)
- Environment Variables:
  - `DEFAULT_LLM_MODEL`: Model to use (default: "google/flan-t5-small")
  - `DEFAULT_TEMPERATURE`: Model temperature (default: 0.7)
  - `DEFAULT_MAX_TOKENS`: Max tokens for generation (default: 200)
  - `DEFAULT_TOP_K`: Top-k sampling parameter (default: 5)

### API Gateway
- Ports:
  - 8000 (HTTP) - For UI and external API access
  - 50052 (gRPC) - For internal microservice communication
- Dependencies: LLM Service, Embeddings Service

### Ingestion Service
- Port: 50053 (gRPC)
- Dependencies: Embeddings Service

### UI Service
- Port: 3000 (HTTP)
- Dependencies: API Gateway (HTTP:8000)

### Embeddings Service
- Port: 50052 (gRPC)
- Dependencies: None

## Monitoring and Debugging

### Service Status

1. List All Services:
   ```bash
   docker compose ps
   ```

2. Check Service Health with Ports:
   ```bash
   docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
   ```

### Service-Specific Logs

1. API Gateway Logs:
   ```bash
   # View logs
   docker compose logs api-gateway

   # Follow logs
   docker compose logs -f api-gateway

   # Check for gRPC issues
   docker compose logs api-gateway | grep "UNAVAILABLE"
   ```

2. LLM Service Logs:
   ```bash
   # View logs
   docker compose logs llm

   # Follow logs
   docker compose logs -f llm

   # Check model loading
   docker compose logs llm | grep "model"
   ```

3. Embeddings Service Logs:
   ```bash
   # View logs
   docker compose logs embeddings

   # Follow logs
   docker compose logs -f embeddings

   # Check vector operations
   docker compose logs embeddings | grep "vector"
   ```

4. Ingestion Service Logs:
   ```bash
   # View logs
   docker compose logs ingestion

   # Follow logs
   docker compose logs -f ingestion

   # Check processing
   docker compose logs ingestion | grep "processing"
   ```

### Resource Monitoring

1. Monitor All Services:
   ```bash
   docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
   ```

2. Service-Specific Monitoring:
   ```bash
   # LLM Service (highest resource usage)
   docker stats llm

   # Embeddings Service
   docker stats embeddings

   # API Gateway
   docker stats api-gateway

   # Ingestion Service
   docker stats ingestion
   ```

3. Resource Usage Analysis:
   ```bash
   # CPU usage over time
   docker stats --format "{{.Name}} - CPU: {{.CPUPerc}}" --interval 5

   # Memory usage over time
   docker stats --format "{{.Name}} - Memory: {{.MemUsage}}" --interval 5

   # Network I/O over time
   docker stats --format "{{.Name}} - Network: {{.NetIO}}" --interval 5
   ```

### Network Monitoring

1. Check Service Communication:
   ```bash
   # View all networks
   docker network ls

   # Inspect the RAG project network
   docker network inspect rag-project_default
   ```

2. Test Service Connectivity:
   ```bash
   # Test LLM service
   docker compose exec api-gateway ping llm

   # Test embeddings service
   docker compose exec api-gateway ping embeddings

   # Test ingestion service
   docker compose exec api-gateway ping ingestion
   ```

## Troubleshooting

### Common Issues

1. Port Conflicts:
   ```bash
   # Check if ports are in use
   lsof -i :50052  # API Gateway gRPC
   lsof -i :50053  # Ingestion Service
   lsof -i :50054  # LLM Service
   lsof -i :8000   # API Gateway HTTP
   lsof -i :3000   # UI Service
   ```

2. Service Connection Issues:
   ```bash
   # Check API Gateway logs
   docker compose logs api-gateway

   # Test HTTP endpoint
   curl http://localhost:8000/health

   # Test gRPC endpoint
   grpcurl -plaintext localhost:50052 list
   ```

### Performance Monitoring

1. API Gateway Performance:
   ```bash
   # Monitor response times
   docker compose logs api-gateway | grep "response_time"

   # Check gRPC latencies
   docker compose logs api-gateway | grep "latency"
   ```

2. LLM Service Performance:
   ```bash
   # Monitor inference times
   docker compose logs llm | grep "inference"

   # Check token generation
   docker compose logs llm | grep "tokens"
   ```

3. Embeddings Service Performance:
   ```bash
   # Monitor vector operations
   docker compose logs embeddings | grep "vector_operation"

   # Check batch processing
   docker compose logs embeddings | grep "batch"
   ```

## Development Workflow

1. Start the development environment:
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

2. Rebuild after dependency changes:
   ```bash
   docker-compose build --no-cache [service_name]
   ```

3. View logs:
   ```bash
   docker-compose logs -f [service_name]
   ```

## Production Deployment

1. Use production configuration:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. Set up proper environment variables:
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with production values
   ```

3. Enable health checks:
   ```bash
   # Check service health
   curl http://localhost:8000/health  # API Gateway
   curl http://localhost:50054/health # LLM Service
   curl http://localhost:50053/health # Ingestion Service
   curl http://localhost:50052/health # Embeddings Service
   ```

## Best Practices

1. **Resource Management**:
   - Set appropriate limits for LLM service
   - Monitor memory usage
   - Use appropriate batch sizes

2. **Log Management**:
   - Monitor API Gateway access logs
   - Track LLM inference times
   - Log vector operation performance
   - Track ingestion processing times

3. **Network Management**:
   - Monitor gRPC connection health
   - Check service discovery
   - Verify port mappings
   - Monitor inter-service communication

4. **Security**:
   - Never commit sensitive environment variables
   - Use Docker secrets for production credentials
   - Regularly update base images
   - Implement proper network segmentation
   - Use non-root users in containers

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [gRPC Documentation](https://grpc.io/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/)
