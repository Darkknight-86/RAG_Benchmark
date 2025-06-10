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
RUN python -m grpc_tools.protoc -I./protos --python_out=./src/rag/proto --grpc_python_out=./src/rag/proto ./protos/rag_service.proto && \
    sed -i 's/import rag_service_pb2/from . import rag_service_pb2/' ./src/rag/proto/rag_service_pb2_grpc.py && \
    echo "from . import rag_service_pb2" > ./src/rag/proto/__init__.py && \
    echo "from . import rag_service_pb2_grpc" >> ./src/rag/proto/__init__.py

# Create cache directory for Hugging Face models
RUN mkdir -p /root/.cache/huggingface

# Set environment variables for Hugging Face
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface
ENV HF_HOME=/root/.cache/huggingface
ENV PYTHONPATH=/app/src
ENV DEFAULT_LLM_MODEL=google/flan-t5-small

EXPOSE 50054
CMD ["python", "-m", "rag.main"]