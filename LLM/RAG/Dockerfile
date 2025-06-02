FROM python:3.11-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 - && ln -s /root/.local/bin/poetry /usr/local/bin/poetry
WORKDIR /app
COPY LLM/RAG/pyproject.toml LLM/RAG/README.md ./
RUN poetry config virtualenvs.create false && poetry install --only main --no-root --no-interaction --no-ansi

FROM python:3.11-bookworm
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY LLM/RAG .
COPY API_Gateway/protos ./protos
RUN python -m grpc_tools.protoc -I./protos --python_out=./src --grpc_python_out=./src ./protos/rag_service.proto

# Ensure Python imports rag package
ENV PYTHONPATH=/app/src

EXPOSE 50054
CMD ["python", "-m", "rag.main"]