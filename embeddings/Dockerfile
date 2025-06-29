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
COPY Embeddings/pyproject.toml Embeddings/poetry.lock* ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Production stage
FROM python:3.11-bookworm

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source (Embeddings directory structure)
COPY Embeddings/src ./src
COPY API_Gateway/protos ./protos

# Copy warnings_suppression.py to both locations to ensure it's found
# The code does: sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
# From /app/src/main.py, this resolves to / (root), so copy there too
COPY warnings_suppression.py ./
COPY warnings_suppression.py /warnings_suppression.py

# Generate gRPC stubs for current structure
RUN mkdir -p ./src/proto && \
    python -m grpc_tools.protoc -I./protos --python_out=./src/proto --grpc_python_out=./src/proto ./protos/rag_service.proto

# Set environment variables to match Poetry setup
ENV PYTHONPATH=/app/src:/app
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Create startup script matching Makefile behavior
RUN echo '#!/bin/bash\n\
# Start gRPC service in background (matches: cd Embeddings && PYTHONPATH=src poetry run python src/main.py)\n\
PYTHONPATH=src python src/main.py &\n\
\n\
# Start streaming service (matches: cd Embeddings && PYTHONPATH=src poetry run python src/streaming.py)\n\
PYTHONPATH=src python src/streaming.py\n\
' > /app/start_services.sh && chmod +x /app/start_services.sh

EXPOSE 50051

CMD ["/app/start_services.sh"]