# Embeddings Microservice

A real-time RAG microservice that ingests live financial data, converts it to vector embeddings, and stores it in ClickHouse for semantic search and analysis.

## 🚀 Features

- **Real-time Data Ingestion**: Streams live financial data from Yahoo Finance WebSocket API
- **Vector Embeddings**: Converts financial data to high-dimensional vectors using Sentence Transformers
- **ClickHouse Vector Store**: Optimized storage and retrieval using ClickHouse with vector similarity search
- **Enhanced Native Metrics**: Combines custom metrics with ClickHouse system table insights
- **LangChain Compatible**: Full compatibility with LangChain vector store interface
- **Scalable Architecture**: Designed for high-throughput financial data processing
- **Robust Error Handling**: Comprehensive logging and monitoring
- **Advanced Analytics**: Native ClickHouse metrics for deep performance analysis

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Yahoo Finance  │───▶│   RAG Service    │───▶│   ClickHouse    │
│   WebSocket     │    │                  │    │  Vector Store   │
└─────────────────┘    │  • Data Parse    │    └─────────────────┘
                       │  • Embeddings    │
┌─────────────────┐    │  • Chunking      │    ┌─────────────────┐
│   LangChain     │◀───│  • Vector Store  │───▶│   Similarity    │
│   Interface     │    │                  │    │     Search      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- ClickHouse Cloud account or self-hosted ClickHouse instance
- Internet connection for Yahoo Finance data

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd embeddings
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your ClickHouse credentials
   ```

4. **Configure ClickHouse connection**
   ```env
   CLICKHOUSE_HOST=your-clickhouse-host
   CLICKHOUSE_PORT=8443
   CLICKHOUSE_USER=your-username
   CLICKHOUSE_PASSWORD=your-password
   CLICKHOUSE_SECURE=true
   ```

## 🚦 Quick Start

### 1. Start the streaming service
```bash
poetry run python src/rag/streaming.py
```

### 2. Use the vector store programmatically
```python
from src.rag.Adapters.ClickHouseAdapter import ClickHouseAdapter
from langchain_core.documents import Document

# Initialize the adapter
vector_store = ClickHouseAdapter()

# Add documents
documents = [
    Document(
        page_content="Apple stock surged 5% after earnings beat expectations",
        metadata={"source": "news", "ticker": "AAPL"}
    )
]
vector_store.add_documents(documents)

# Search for similar content
results = vector_store.similarity_search("tech stock performance", k=5)
```

## 🗄️ Database Schema

The service uses an optimized ClickHouse table schema:

```sql
CREATE TABLE rag_chunks_v2 (
    id String,                          -- Document ID
    timestamp DateTime,                 -- Insert timestamp
    source String,                      -- Data source (e.g., 'yliveticker')
    chunk String,                       -- Text content
    embedding Array(Float32),           -- Vector embedding
    price Decimal(18, 2),              -- Stock price
    change_percent Decimal(9, 2),       -- Price change percentage
    volume UInt32,                      -- Trading volume
    security LowCardinality(String),    -- Stock ticker
    chunk_index UInt16                  -- Chunk sequence number
) ENGINE = MergeTree()
ORDER BY (timestamp, security, id)
PARTITION BY toYYYYMM(timestamp);
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CLICKHOUSE_HOST` | ClickHouse server hostname | `localhost` |
| `CLICKHOUSE_PORT` | ClickHouse server port | `8443` |
| `CLICKHOUSE_USER` | Database username | `default` |
| `CLICKHOUSE_PASSWORD` | Database password | `` |
| `CLICKHOUSE_SECURE` | Use SSL connection | `true` |

### Embedding Model

The service uses `sentence-transformers/all-MiniLM-L6-v2` by default. You can customize this:

```python
from sentence_transformers import SentenceTransformer

custom_model = SentenceTransformer('your-preferred-model')
adapter = ClickHouseAdapter(embedding_model=custom_model)
```

## 📊 Monitoring

### Data Verification
```python
# Check insertion status
adapter.verify_data_insertion()

# Get table statistics
adapter.get_table_stats()

# Check table schema
adapter.check_table_schema()
```

### Enhanced Native ClickHouse Metrics

The service now includes **hybrid monitoring** that combines custom metrics with ClickHouse's native system table insights:

#### 🎯 **Key Benefits**
- ✅ **Real-time feedback** from custom metrics (primary performance tracking)
- ✅ **Table structure insights** from ClickHouse `system.parts` (parts count, compression)
- ✅ **Enhanced CSV exports** with 15+ new columns (mix of working and contextual data)
- ✅ **Compression analysis** - live 28%+ efficiency tracking from native ClickHouse data
- ✅ **Future-ready** for when ClickHouse operations trigger more system table entries

#### 📈 **Optimized CSV Output (12 Essential Columns)**

Your `vector_db_metrics.csv` now focuses on **high-impact benchmarking metrics only**:

**🎯 Core Performance Metrics**:
- `timestamp` - Time series analysis
- `vd_latency_ms` - **Primary performance indicator**
- `throughput_records_per_second` - **Throughput tracking**
- `performance_tier` - Quick classification (excellent/good/slow)
- `success` - Success rate monitoring

**✅ Native ClickHouse Insights**:
- `operation_type` - **Accurate classification** (using native data)
- `ch_parts_count` - **Table health** (currently ~11 parts)
- `ch_total_rows` - **Growth tracking** (17,400+ rows)
- `ch_compressed_bytes` - **Storage usage** (~23MB)
- `ch_compression_ratio` - **Compression efficiency** (1.41x)
- `compression_efficiency` - **Storage optimization** (28.9% savings)
- `merge_activity_indicator` - **System state** (idle/active)

**🗑️ Removed Low-Impact Columns**:
- Always-zero query log metrics (`ch_query_duration_ms`, `ch_inserted_rows`, etc.)
- Rarely-changing merge metrics (`ch_active_merges`, `ch_parts_being_merged`, etc.)
- Static/redundant fields (`operation`, `table`, `records_affected`)

#### 🔍 **Why Some Metrics Show Zero**

**Normal ClickHouse Behavior**:
- **Bulk Inserts**: Our streaming service uses `client.insert()` for performance, which doesn't generate `system.query_log` entries like text-based INSERTs
- **Query Log Delay**: `system.query_log` has a buffer delay (5-60 seconds) and may not capture all operations
- **No Active Merges**: `ch_active_merges` will be 0 most of the time - ClickHouse only merges parts when needed
- **Resource Metrics**: Memory/disk usage from `ProfileEvents` only appear for queries that trigger logging thresholds

**What This Means**:
- ✅ **Table structure metrics work perfectly** - real-time parts count, compression ratios
- ✅ **Your custom metrics remain primary** - for real-time latency and performance tracking
- ✅ **Native metrics provide deep insight** - when ClickHouse operations trigger system table entries
- ✅ **Compression analysis works great** - 28%+ compression efficiency visible in real-time

#### 📊 **Optimized CSV Sample**

**New 12-Column Format** (wait 30 seconds for next export):
```csv
timestamp,vd_latency_ms,throughput_records_per_second,performance_tier,success,operation_type,ch_parts_count,ch_total_rows,ch_compression_ratio,compression_efficiency,merge_activity_indicator,ch_compressed_bytes
2025-06-10T09:50:20.517251,1294.27,0.77,slow,True,indexing,11,17401,1.41,28.92,idle,22923544
```

**✅ Key Insights from Sample**:
- **Performance**: 1294ms latency, 0.77 records/sec throughput, "slow" tier
- **Accuracy**: `operation_type: indexing` matches `merge_activity_indicator: idle` ✅
- **Storage**: 17,401 rows in 11 parts, 1.41x compression (28.92% space savings)
- **Health**: ~23MB storage, system idle (optimal state)

**🎯 Benchmarking Benefits**:
- **Focused Data**: Only metrics that matter for performance analysis
- **Consistent Logic**: Native ClickHouse data drives classification
- **Clean Analysis**: No more always-zero or redundant columns
- **Faster Processing**: 12 columns vs 26 = 54% reduction in data volume
- **Organized Structure**: All metrics properly categorized in dedicated folders

#### 📁 **Organized Metrics Structure**

**`API_Gateway/Data/streaming_metrics/`** (Automated every 30 seconds):
- `vector_db_metrics.csv` - **Optimized 12-column** ClickHouse performance
- `streaming_data_metrics.csv` - Data ingestion from Yahoo Finance
- `chunking_metrics.csv` - **Optimized 7-column** text chunking performance
- `embedding_metrics.csv` - Vector embedding generation

**`API_Gateway/Data/query_metrics/`** (LLM query analysis, automated every 30 seconds):
- `llm_query_metrics.csv` - **NEW Optimized 10-column** RAG query performance

#### 🧠 **LLM Query Metrics (NEW)**

**Essential 10-Column Structure** for RAG benchmarking:
```csv
timestamp,query_type,success,vector_latency_ms,llm_latency_ms,total_time_ms,tokens_used,docs_found,avg_relevance_score,model_name
```

**🎯 High-Impact LLM Metrics**:
- `vector_latency_ms` - **Vector search performance** (retrieval speed)
- `llm_latency_ms` - **LLM generation performance** (response generation)
- `total_time_ms` - **End-to-end query time** (user experience)
- `tokens_used` - **Resource consumption** (cost tracking)
- `docs_found` - **Retrieval effectiveness** (search quality)
- `avg_relevance_score` - **Retrieval quality** (relevance tracking)
- `query_type` - RAG vs direct query classification
- `model_name` - **Model performance comparison**

**Benefits of Organization**:
- ✅ **Clean separation** between streaming vs query performance
- ✅ **Easy analysis** - focus on specific metric types
- ✅ **Automated routing** - new CSV files go to correct folders
- ✅ **Scalable structure** - ready for additional metric categories

#### 🔧 **Enhanced Operation Classification**

The system now uses **native ClickHouse data as primary source** for accurate classification:

**✅ Native Data-Driven** (uses actual ClickHouse state):
- `indexing` - Normal inserts, no active merges (`ch_active_merges: 0`)
- `indexing_with_background_merge` - Fast inserts during active merges
- `confirmed_background_merge` - Slow operations during active merges
- `indexing_high_part_count` - Normal inserts with 100+ parts (merge needed soon)
- `indexing_moderate_parts` - Normal inserts with 50+ parts

**🔧 Operation-Based** (analyzes operation type):
- `manual_optimize` - OPTIMIZE TABLE operations
- `bulk_insert` - Large batch operations
- `deletion` - DELETE/REMOVE operations

**⏱️ Latency-Based** (fallback for edge cases):
- `indexing_slow_operation` - Normal indexing but >5s latency
- `indexing_moderate_latency` - Normal indexing but >2s latency
- `indexing_compression_overhead` - Latency mismatch suggesting compression work

### Logs
The service provides detailed logging for:
- WebSocket connections
- Data processing steps
- Embedding generation
- Database operations
- Error handling
- Native ClickHouse metrics collection

## 🧪 Testing

### Run the test suite
```bash
# Test basic functionality
poetry run python test_vector_store.py

# Test schema validation
poetry run python test_schema_fix.py
```

### Test with sample data
```python
from uuid import uuid4
from langchain_core.documents import Document

# Create test documents
documents = [
    Document(page_content="Test content", metadata={"source": "test"})
]
uuids = [str(uuid4()) for _ in documents]

# Test the pipeline
vector_store.add_documents(documents=documents, ids=uuids)
results = vector_store.similarity_search("test query", k=1)
```

## 🔄 API Reference

### ClickHouseAdapter Methods

#### Core Methods
- `add_documents(documents, ids=None, embeddings=None)` - Add multiple documents
- `add_embedding(vector, text, metadata)` - Add single embedding
- `similarity_search(query, k=4)` - Find similar documents
- `similarity_search_with_score(query, k=4)` - Search with similarity scores
- `delete(ids)` - Delete documents by ID

#### Utility Methods
- `verify_data_insertion()` - Verify recent data
- `get_table_stats()` - Get table statistics
- `check_table_schema()` - Validate schema
- `recreate_table()` - Reset table with correct schema

## 🐛 Troubleshooting

### Common Issues

**Schema Mismatch**: If you see "Unrecognized column" errors:
```python
adapter.recreate_table()  # This will recreate with correct schema
```

**Connection Issues**: Check your ClickHouse credentials and network connectivity

**Memory Issues**: For large datasets, consider batch processing or increasing system resources

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [LangChain](https://github.com/langchain-ai/langchain) - Framework for LLM applications
- [ClickHouse](https://github.com/ClickHouse/ClickHouse) - Fast columnar database
- [Sentence Transformers](https://github.com/UKPLab/sentence-transformers) - Embedding models
