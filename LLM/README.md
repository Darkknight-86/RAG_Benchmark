# LLM Microservice
_Query → Retrieve vectors → Generate answer_

> **Note:** This service is optimized for Apple Silicon GPUs with full MPS (Metal Performance Shaders) support.

---

## 🍎 Apple Silicon GPU Support

**Native MPS Acceleration** - Fully compatible with Apple M1/M2/M3/M4 chips:

### **Optimized Dependencies for MPS**
| Package | Version | Purpose |
|---------|---------|---------|
| `torch` | `2.3.0` | PyTorch with Apple MPS backend support |
| `transformers` | `4.41.0` | **Avoids `torch.isin` MPS bug** found in 4.42+ |
| `accelerate` | `1.6.0` | Enhanced MPS device mapping and memory management |
| `safetensors` | `0.4.3` | Fast, safe model serialization |

### **MPS Compatibility Features**
- ✅ **Native GPU acceleration** for Llama models on Apple Silicon
- ✅ **Float16 precision** for optimal performance and memory usage
- ✅ **No CPU fallback required** - runs entirely on Apple GPU
- ✅ **Custom padding tokens** to avoid MPS tensor comparison issues
- ✅ **Optimized tokenization** with explicit attention masks

### **Performance Benefits**
- **10x faster** inference compared to CPU-only execution
- **Native Metal Performance Shaders** utilization
- **Reduced memory footprint** with float16 precision
- **Stable performance** without MPS fallback warnings

---

## 🎯 What It Does
1. Accept **Query** RPCs with natural-language input
2. Retrieve top-K relevant vectors from the Embeddings service / vector DB
3. Craft a prompt and call the selected LLM (`Llama-3.2-1B-Instruct` by default via `transformers`)
4. Return answer plus sources & metadata
5. Emit latency / token metrics (`prometheus-client`)

## 🛠️ Tech Stack (MPS-Optimized)
| Layer | Library | Version | MPS Compatibility |
|-------|---------|---------|-------------------|
| Retrieval | FAISS index wrapper (`faiss-cpu`), ChromaDB optional | - | ✅ |
| LLM | `transformers` (MPS-compatible) | `4.41.0` | ✅ **Avoids torch.isin bug** |
| Acceleration | `accelerate` (Apple Silicon optimized) | `1.6.0` | ✅ **Enhanced MPS support** |
| PyTorch | `torch` with MPS backend | `2.3.0` | ✅ **Native Apple GPU** |
| Model Loading | `safetensors` | `0.4.3` | ✅ **Fast serialization** |
| API | `grpclib` server + FastAPI health route | - | ✅ |
| Metrics | `prometheus-client` | - | ✅ |

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
| `DEFAULT_LLM_MODEL` | `meta-llama/Llama-3.2-1B-Instruct` | HF model id |
| `DEFAULT_TOP_K` | `5` | default number of vectors |
| `VECTOR_HOST` | `embeddings:50052` | GRPC target to retrieve vectors |
| `HUGGINGFACE_HUB_TOKEN` | - | Required for Llama models |

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

## 📊 Query Performance Metrics

### **🎯 Optimized LLM Query Analytics**

The LLM service now includes **comprehensive query performance tracking** with automated CSV export every 30 seconds:

**Essential 10-Column Structure** for RAG benchmarking:
```csv
timestamp,query_type,success,vector_latency_ms,llm_latency_ms,total_time_ms,tokens_used,docs_found,avg_relevance_score,model_name
```

### **High-Impact Metrics Tracked**
- **🔍 Vector Search Performance**: Retrieval speed and effectiveness
- **🧠 LLM Generation Performance**: Response generation timing
- **⏱️ End-to-End Query Time**: Complete user experience measurement
- **💰 Resource Consumption**: Token usage and cost tracking
- **📊 Retrieval Quality**: Documents found and relevance scoring
- **🎯 Model Performance**: Comparative analysis across different models

### **Automated Export Location**
```bash
API_Gateway/Data/query_metrics/
└── llm_query_metrics.csv    # Automated export every 30 seconds
```

### **Performance Troubleshooting**
Based on dashboard metrics, monitor for:

| **Issue** | **Metric** | **Threshold** | **Action** |
|-----------|------------|---------------|------------|
| **Poor Retrieval** | `avg_relevance_score` | <0.5 | Check vector search configuration |
| **Slow Responses** | `total_time_ms` | >5000ms | Investigate model or vector latency |
| **No Documents Found** | `docs_found` | =0 | Review vector database content |
| **High Token Usage** | `tokens_used` | >500 tokens | Optimize prompt engineering |

### **Real-time Monitoring**
Query metrics are automatically collected during RAG operations and exported to support:
- **Dashboard Integration**: Live performance visualization
- **Performance Analysis**: Historical trend analysis
- **Optimization**: Data-driven improvements to retrieval and generation

## 🧪 Tests
```bash
poetry run pytest tests -v
```

## 📜 License
MIT
