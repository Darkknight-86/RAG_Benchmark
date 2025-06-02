# Ingestion Micro-service
_Raw data acquisition → S3 / Object storage_

---

## 🚚 Responsibilities
1. Receive **IngestDocuments** requests with external URLs or file references.
2. Download / fetch data, perform lightweight validation.
3. Push raw artefacts to an S3-compatible bucket (MinIO in dev).
4. Emit basic processing metrics and success status over gRPC.
5. Expose Prometheus `/metrics`.

## 🛠️ Tech Stack
| Layer | Library |
|-------|---------|
| API   | **FastAPI** (for health) + `grpclib` server |
| Storage | `boto3` S3 client |
| Parsing | `llama-parse` (optional PDF → text) |
| Metrics | `prometheus-client` |

## 📂 Directory tree
```
Ingestion/grpc/
 ├── Dockerfile
 ├── pyproject.toml
 ├── protos/rawdataingestion.proto   # service-specific example (legacy)
 └── src/grpc/
      ├── server.py   # gRPC server impl
      └── client.py   # quick test client
```

> **Note**   With the new unified `rag_service.proto` this service currently implements only `IngestDocuments`, but the old `rawdataingestion.proto` is kept for backwards-compat functional tests.

## 📡 gRPC RPC implemented
```proto
service RAGService {
  rpc IngestDocuments(IngestRequest) returns (IngestResponse) {}
}
```
The `IngestResponse.status` will be `QUEUED`, `DOWNLOADED`, or `FAILED`.

## 🔧 Environment variables
| Var | Default | Description |
|-----|---------|-------------|
| `S3_ENDPOINT` | `http://minio:9000` | Target bucket host |
| `S3_BUCKET`   | `rag-raw` | Bucket name |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | _none_ | Credentials |

## 🚀 Local dev
```bash
poetry install
# (re)generate shared proto stubs
poetry run python -m grpc_tools.protoc -I ../../API_Gateway/protos \
  --python_out=./src --grpc_python_out=./src \
  ../../API_Gateway/protos/rag_service.proto
# start server
poetry run python src/grpc/server.py
```
Test with:
```bash
poetry run python src/grpc/client.py --urls https://example.com/doc.pdf
```

## 🐳 Docker
Container listens on **50053**. Example:
```bash
docker compose up ingestion
```

## 🧪 Tests
```bash
poetry run pytest -v
```

## 📜 License
MIT