# Embeddings Micro-service
_Chunk → Embed → Store vectors_

---

## 🔄 Responsibilities
1. Accept raw (clean) text documents over **gRPC**.
2. Apply the project-wide chunking strategy (configurable size & overlap).
3. Generate dense embeddings (default: `sentence-transformers/all-MiniLM-L6-v2`).
4. Persist vectors to the configured vector store (FAISS – local; ChromaDB optional).
5. Expose basic health & Prometheus `/metrics` endpoints.

## 🛠️ Tech Stack
| Layer | Library |
|-------|---------|
| API   | **FastAPI** (async) + `grpclib` server |
| Embedding | `sentence-transformers`, `langchain` wrappers |
| Vector DB | FAISS (in-process) • ChromaDB (optional remote) |
| Metrics | `prometheus-client` |

## 🗂️ Project layout
```
embeddings/
 ├── Dockerfile
 ├── pyproject.toml
 ├── src/
 │   └── rag/
 │        ├── embedder.py      # wraps sentence-transformers
 │        ├── chunker.py       # simple text splitter
 │        └── server.py        # FastAPI + gRPC endpoints
 └── tests/
```

## 📡 gRPC Interface (excerpt)
The service re-uses **`rag_service.proto`** (shared in `API_Gateway/protos/`). Only the _IngestDocuments_ RPC is implemented here:
```proto
service RAGService {
  rpc IngestDocuments(IngestRequest) returns (IngestResponse) {}
}
```
Example Python client call:
```python
from api_gateway.clients.embeddings_client import EmbeddingsClient
with EmbeddingsClient() as cli:
    resp = cli.ingest_documents(["s3://bucket/doc1.pdf"])
    print(resp.status, resp.vectors_created)
```

## 🚀 Running standalone (dev)
```bash
# Install deps
poetry install
# Generate stubs after you edit the proto
poetry run python -m grpc_tools.protoc -I ../../API_Gateway/protos \
    --python_out=./src --grpc_python_out=./src \
    ../../API_Gateway/protos/rag_service.proto
# Start API (http://127.0.0.1:8000/docs)
poetry run uvicorn rag.server:app --reload --port 8000
```

## 🐳 Container image
The **Dockerfile** is multi-stage and copies the shared proto folder at build time. Environment variables:
| Var | Default | Description |
|-----|---------|-------------|
| `VECTOR_STORE` | `faiss` | `faiss` (local) or `chroma` |
| `CHUNK_SIZE`   | `1000`  | Number of characters per chunk |
| `EMBED_MODEL`  | `all-MiniLM-L6-v2` | HF model name |

Start only this service:
```bash
docker build -t embeddings . && docker run -p 50052:50052 embeddings
```
In the full stack just run `docker compose up embeddings` – the container will join the `rag-network` and listen on **`50052`**.

## 🧪 Tests
```bash
poetry run pytest tests -v
```

## 📜 License
MIT
