FROM python:3.11-bookworm AS builder

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# Copy only poetry files first (layer caching)
COPY API_Gateway/pyproject.toml API_Gateway/poetry.lock* API_Gateway/README.md ./

# Disable virtualenvs so deps go into global site-packages
RUN poetry config virtualenvs.create false && \
    poetry lock --no-interaction --no-ansi && \
    poetry install --only main --no-root --no-interaction --no-ansi

# ────────────────────────────────────────────────────────────
# Production image
FROM python:3.11-bookworm
WORKDIR /app

# Copy installed site-packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Ensure imports work when running as module
ENV PYTHONPATH=/app/API_Gateway/src

# Generate gRPC stubs (shared proto folder lives inside image already)
RUN python API_Gateway/generate_grpc.py

EXPOSE 50051 8000

CMD ["python", "-m", "api_gateway.server"]