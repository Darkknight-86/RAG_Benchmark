# LLM Micro-service
_Query → Retrieve vectors → Generate answer_

---

## 🎯 Responsibilities
1. Accept **Query** RPCs with natural-language input.
2. Retrieve top-K relevant vectors from the Embeddings service / vector DB.
3. Craft a prompt and call the selected LLM (`mistral-7B` by default via `transformers`).
4. Return answer plus sources & metadata.
5. Emit latency / token metrics (`prometheus-client`).

## 🛠️ Tech Stack
| Layer | Library |
|-------|---------|
| Retrieval | FAISS index wrapper (`faiss-cpu`), ChromaDB optional |
| LLM | `transformers`, `accelerate`, `sentence-transformers` |
| API | `grpclib` server + FastAPI health route |
| Metrics | `prometheus-client` |

## Project structure
```
LLM/RAG/
 ├── Dockerfile
 ├── pyproject.toml
 ├── src/rag/
 │    ├── __init__.py
 │    ├── embeddings_client.py   # talks to vector store
 │    ├── prompt.py              # prompt engineering helpers
 │    ├── llm.py                 # wraps HF model
 │    └── main.py                # gRPC server entrypoint
 └── tests/
```

## 📡 gRPC API
```proto
service RAGService {
  rpc Query(QueryRequest) returns (QueryResponse) {}
}
```
`QueryResponse` returns `response`, `sources[]`, and `metadata.latency / tokens_used`.

## 🔧 Environment variables
| Var | Default | Description |
|-----|---------|-------------|
| `LLM_MODEL` | `mistralai/Mistral-7B-Instruct-v0.2` | HF model id |
| `TOP_K` | `5` | default number of vectors |
| `VECTOR_HOST` | `embeddings:50052` | GRPC target to retrieve vectors |

## 🚀 Local dev
```bash
poetry install
# generate stubs after editing proto
poetry run python -m grpc_tools.protoc -I ../../API_Gateway/protos \
  --python_out=./src --grpc_python_out=./src \
  ../../API_Gateway/protos/rag_service.proto
# start service
poetry run python src/rag/main.py
```
Test:
```bash
from api_gateway.clients.llm_client import LLMClient
with LLMClient() as cli:
    print(cli.query("What is RAG?"))
```

## 🐳 Docker
Image listens on **50054** and will load the HF model at container build time (cache layer). Build alone:
```bash
docker compose build llm
```

## 🧪 Tests
```bash
poetry run pytest tests -v
```

## 📜 License
MIT
