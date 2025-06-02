# RAG Project Docker Monitoring Guide

This guide covers monitoring and debugging the microservices in the RAG project, which consists of:
- API Gateway (port 8000, 50051)
- LLM Service (port 50054)
- Embeddings Service (port 50052)
- Ingestion Service (port 50053)
- PostgreSQL with pgvector (port 5432)

## 1. Service Status

### List All Services
```bash
docker compose ps
```

Expected output should show all services:
- api-gateway
- llm
- embeddings
- ingestion
- postgres

### Check Service Health with Ports
```bash
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

Expected ports:
- api-gateway: 8000, 50051
- llm: 50054
- embeddings: 50052
- ingestion: 50053
- postgres: 5432

## 2. Service-Specific Logs

### API Gateway Logs
```bash
# View API Gateway logs
docker compose logs api-gateway

# Follow API Gateway logs
docker compose logs -f api-gateway

# Check for gRPC connection issues
docker compose logs api-gateway | grep "UNAVAILABLE"
```

### LLM Service Logs
```bash
# View LLM service logs
docker compose logs llm

# Follow LLM service logs
docker compose logs -f llm

# Check for model loading issues
docker compose logs llm | grep "model"
```

### Embeddings Service Logs
```bash
# View embeddings service logs
docker compose logs embeddings

# Follow embeddings service logs
docker compose logs -f embeddings

# Check for vector database issues
docker compose logs embeddings | grep "vector"
```

### Ingestion Service Logs
```bash
# View ingestion service logs
docker compose logs ingestion

# Follow ingestion service logs
docker compose logs -f ingestion

# Check for document processing issues
docker compose logs ingestion | grep "processing"
```

### PostgreSQL Logs
```bash
# View PostgreSQL logs
docker compose logs postgres

# Check for database connection issues
docker compose logs postgres | grep "connection"
```

## 3. Resource Usage by Service

### Monitor All Services
```bash
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

Expected resource usage patterns:
- LLM Service: Higher CPU/Memory (model inference)
- Embeddings: Moderate CPU (vector operations)
- API Gateway: Low CPU, Moderate Memory
- Ingestion: Burst CPU during processing
- PostgreSQL: Moderate CPU/Memory

### Service-Specific Resource Monitoring
```bash
# LLM Service (highest resource usage)
docker stats llm

# Embeddings Service
docker stats embeddings

# API Gateway
docker stats api-gateway

# Ingestion Service
docker stats ingestion

# PostgreSQL
docker stats postgres
```

## 4. Network Monitoring

### Check Service Communication
```bash
# View all networks
docker network ls

# Inspect the RAG project network
docker network inspect rag-project_default
```

Expected connections:
- api-gateway → llm (50054)
- api-gateway → embeddings (50052)
- api-gateway → ingestion (50053)
- embeddings → postgres (5432)
- ingestion → postgres (5432)

### Test Service Connectivity
```bash
# Test LLM service connectivity
docker compose exec api-gateway ping llm

# Test embeddings service connectivity
docker compose exec api-gateway ping embeddings

# Test ingestion service connectivity
docker compose exec api-gateway ping ingestion
```

## 5. Storage Monitoring

### Check PostgreSQL Storage
```bash
# View PostgreSQL volume usage
docker volume inspect rag-project_postgres_data

# Check database size
docker compose exec postgres psql -U postgres -c "\l+"
```

### Check Model Cache Storage
```bash
# Check LLM model cache
docker compose exec llm du -sh /root/.cache/huggingface

# Check embeddings model cache
docker compose exec embeddings du -sh /root/.cache/huggingface
```

## 6. Common Issues and Solutions

### API Gateway Issues
1. Check gRPC connections:
   ```bash
   docker compose logs api-gateway | grep "UNAVAILABLE"
   ```
2. Verify service discovery:
   ```bash
   docker network inspect rag-project_default | grep "llm\|embeddings\|ingestion"
   ```

### LLM Service Issues
1. Check model loading:
   ```bash
   docker compose logs llm | grep "model"
   ```
2. Monitor memory usage:
   ```bash
   docker stats llm --format "table {{.Name}}\t{{.MemUsage}}"
   ```

### Embeddings Service Issues
1. Check vector operations:
   ```bash
   docker compose logs embeddings | grep "vector"
   ```
2. Verify PostgreSQL connection:
   ```bash
   docker compose logs embeddings | grep "postgres"
   ```

### Ingestion Service Issues
1. Check document processing:
   ```bash
   docker compose logs ingestion | grep "processing"
   ```
2. Monitor processing queue:
   ```bash
   docker compose logs ingestion | grep "queue"
   ```

## 7. Performance Monitoring

### API Gateway Performance
```bash
# Monitor API Gateway response times
docker compose logs api-gateway | grep "response_time"

# Check gRPC call latencies
docker compose logs api-gateway | grep "latency"
```

### LLM Service Performance
```bash
# Monitor inference times
docker compose logs llm | grep "inference"

# Check token generation speed
docker compose logs llm | grep "tokens"
```

### Embeddings Service Performance
```bash
# Monitor vector operation times
docker compose logs embeddings | grep "vector_operation"

# Check batch processing times
docker compose logs embeddings | grep "batch"
```

## 8. Troubleshooting Checklist

### API Gateway Issues
- [ ] Check gRPC connections to all services
- [ ] Verify service discovery
- [ ] Check API endpoint responses
- [ ] Monitor request/response times

### LLM Service Issues
- [ ] Verify model loading
- [ ] Check memory usage
- [ ] Monitor inference times
- [ ] Check token generation

### Embeddings Service Issues
- [ ] Verify vector operations
- [ ] Check PostgreSQL connection
- [ ] Monitor batch processing
- [ ] Check cache usage

### Ingestion Service Issues
- [ ] Check document processing
- [ ] Monitor processing queue
- [ ] Verify database connections
- [ ] Check file system access

### PostgreSQL Issues
- [ ] Check connection pool
- [ ] Monitor query performance
- [ ] Verify vector operations
- [ ] Check disk space

## 9. Best Practices

1. **Regular Health Checks**
   - Monitor all service ports
   - Check service dependencies
   - Verify data flow between services

2. **Resource Management**
   - Set appropriate limits for LLM service
   - Monitor PostgreSQL connection pool
   - Watch for memory leaks in long-running services

3. **Log Management**
   - Monitor API Gateway access logs
   - Track LLM inference times
   - Log vector operation performance
   - Track ingestion processing times

4. **Network Management**
   - Monitor gRPC connection health
   - Check service discovery
   - Verify port mappings
   - Monitor inter-service communication

5. **Storage Management**
   - Monitor PostgreSQL growth
   - Track model cache usage
   - Manage document storage
   - Regular database backups