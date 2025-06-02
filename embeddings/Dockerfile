FROM python:3.11-bookworm AS builder

# Install build deps and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 - && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# Increase Poetry HTTP timeout and retries
ENV POETRY_HTTP_TIMEOUT=600 \
    POETRY_HTTP_RETRIES=10

# Copy project metadata first
COPY embeddings/pyproject.toml embeddings/README.md ./

# Install main dependencies only
RUN poetry config virtualenvs.create false && poetry install --only main --no-root --no-interaction --no-ansi

# ------------------------------------------------------------------
FROM python:3.11-bookworm
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY embeddings .

# Copy shared protos folder from build context (assumes repo root is Docker build context)
COPY API_Gateway/protos ./protos

# Generate gRPC stubs (only messages)
RUN python -m grpc_tools.protoc -I./protos --python_out=./src --grpc_python_out=./src ./protos/rag_service.proto

# Ensure Python can find the package
ENV PYTHONPATH=/app/src

EXPOSE 50052
CMD ["python", "-m", "rag.server"]