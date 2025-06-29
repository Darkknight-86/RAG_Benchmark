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
COPY LLM/pyproject.toml LLM/poetry.lock* ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Production stage
FROM python:3.11-bookworm

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source (LLM directory structure)
COPY LLM/src ./src
COPY API_Gateway/protos ./protos

# Copy Adapters directory from Embeddings service (needed for ClickHouse connection)
COPY Embeddings/src/Adapters ./src/Adapters

# Copy warnings_suppression.py to both locations to ensure it's found
# The code does: sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
# From /app/src/main.py, this resolves to / (root), so copy there too
COPY warnings_suppression.py ./
COPY warnings_suppression.py /warnings_suppression.py

# Generate gRPC stubs for the current structure
RUN mkdir -p ./src/proto && \
    python -m grpc_tools.protoc -I./protos --python_out=./src/proto --grpc_python_out=./src/proto ./protos/rag_service.proto

# Create HuggingFace cache directory
RUN mkdir -p /root/.cache/huggingface

# Set environment variables to match Poetry setup
ENV PYTHONPATH=/app/src:/app
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface
ENV HF_HOME=/root/.cache/huggingface
ENV DEFAULT_LLM_MODEL=meta-llama/Llama-3.2-1B-Instruct

EXPOSE 50054

# Start the LLM service (matches: cd LLM && PYTHONPATH=src poetry run python src/main.py)
CMD ["sh", "-c", "PYTHONPATH=src python src/main.py"]