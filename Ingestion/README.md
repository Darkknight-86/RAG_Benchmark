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
| Layer    | Library                                   |
|----------|-------------------------------------------|
| API      | **FastAPI** (for health) + `grpclib`      |
| Storage  | `boto3` S3 client                         |
| Parsing  | `llama-parse` (optional PDF → text)       |
| Metrics  | `prometheus-client`                       |

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

> **Note**  
With the new unified `rag_service.proto` this service currently implements only `IngestDocuments`, but the old `rawdataingestion.proto` is kept for backwards-compat functional tests.

## 📡 gRPC RPC implemented
```proto
service RAGService {
  rpc IngestDocuments(IngestRequest) returns (IngestResponse) {}
}
```
The `IngestResponse.status` will be `QUEUED`, `DOWNLOADED`, or `FAILED`.

## 🔧 Environment variables
| Var                        | Default                | Description         |
|----------------------------|------------------------|---------------------|
| `S3_ENDPOINT`              | `http://minio:9000`    | Target bucket host  |
| `S3_BUCKET`                | `rag-raw`              | Bucket name         |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | _none_         | Credentials         |

---

# AWS CLI Basics

### 0. Install
```shell
pip3 install awscli
```

### 1. Set up credentials
```shell
aws configure
```
Follow the prompts given, make sure you properly set the region (it matters!).  
Set the output format to `json`.

### 2. Helpful Commands
```shell
# List contents of our bucket
aws s3 ls s3://ragproject-store/papers/

# Print a file to the terminal
aws s3 cp s3://ragproject-store/papers/something.txt -

# Delete all papers
aws s3 rm s3://ragproject-store/papers/ --recursive

# Delete all papers (except Ronnie's test document)
aws s3 rm s3://ragproject-store/papers/ --recursive --exclude "scores.txt"
```

---

# Start Virtual Environment

```shell
# Windows via installed python
python -m poetry install

# OR assuming you have poetry installed systemwide
poetry install
```

# Scraping the PDFs then Uploading to S3

```shell
# after your virtual environment is complete...
poetry run python src/rag/main.py
```

---

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

<!-- 
currently toml is not locked but should be and set for versions >= 3.11 python 
-->