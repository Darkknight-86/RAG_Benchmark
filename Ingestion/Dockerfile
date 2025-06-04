FROM python:3.11-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 - && ln -s /root/.local/bin/poetry /usr/local/bin/poetry
WORKDIR /app
COPY Ingestion/pyproject.toml Ingestion/README.md ./
RUN poetry config virtualenvs.create false && poetry install --only main --no-root --no-interaction --no-ansi

FROM python:3.11-bookworm
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY Ingestion .
COPY API_Gateway/protos ./protos
RUN python -m grpc_tools.protoc -I./protos --python_out=./src --grpc_python_out=./src ./protos/ingestion_service.proto
EXPOSE 50053
# Run server script directly
ENV PYTHONPATH=/app/src
CMD ["python", "src/rag/main.py"]