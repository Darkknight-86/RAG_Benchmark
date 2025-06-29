FROM python:3.11-bookworm AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# Copy Poetry configuration
COPY API_Gateway/pyproject.toml API_Gateway/poetry.lock* ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Production stage
FROM python:3.11-bookworm

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source (API Gateway directory structure)
COPY API_Gateway/src ./src
COPY API_Gateway/protos ./protos
COPY API_Gateway/Data ./Data

# Create data directories for CSV exports (query_metrics and streaming_metrics)
RUN mkdir -p ./Data/query_metrics ./Data/streaming_metrics

# Copy warnings_suppression.py to root level (where services expect it)
COPY warnings_suppression.py ./

# Generate gRPC stubs for current structure
RUN python -m grpc_tools.protoc -I./protos --python_out=./src --grpc_python_out=./src ./protos/rag_service.proto

# Set environment variables to match Poetry setup
ENV PYTHONPATH=/app/src:/app

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8502

# Create startup script matching Makefile behavior
RUN echo '#!/bin/bash\n\
# Start FastAPI server in background (matches: cd API_Gateway && PYTHONPATH=src poetry run uvicorn api_gateway.fastapi_server:app --host 0.0.0.0 --port 8000)\n\
PYTHONPATH=src uvicorn api_gateway.fastapi_server:app --host 0.0.0.0 --port 8000 &\n\
\n\
# Start Streamlit dashboard (matches: cd API_Gateway && PYTHONPATH=src poetry run streamlit run src/dashboard/enhanced_streamlit_dashboard.py --server.port 8502)\n\
PYTHONPATH=src streamlit run src/dashboard/enhanced_streamlit_dashboard.py --server.port 8502 --server.address 0.0.0.0\n\
' > /app/start_services.sh && chmod +x /app/start_services.sh

CMD ["/app/start_services.sh"]