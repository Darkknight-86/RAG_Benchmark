# Financial RAG Microservice

A real-time Retrieval-Augmented Generation (RAG) microservice that ingests live financial data, converts it to vector embeddings, and stores it in ClickHouse for semantic search and analysis.

## 🚀 Features

- **Real-time Data Ingestion**: Streams live financial data from Yahoo Finance WebSocket API
- **Vector Embeddings**: Converts financial data to high-dimensional vectors using Sentence Transformers
- **ClickHouse Vector Store**: Optimized storage and retrieval using ClickHouse with vector similarity search
- **LangChain Compatible**: Full compatibility with LangChain vector store interface
- **Scalable Architecture**: Designed for high-throughput financial data processing
- **Production Ready**: Robust error handling, logging, and monitoring

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

### Logs
The service provides detailed logging for:
- WebSocket connections
- Data processing steps
- Embedding generation
- Database operations
- Error handling

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

## 🆘 Support

For questions and support:
- Create an issue on GitHub
- Check the [HOW_TO_USE.md](HOW_TO_USE.md) for detailed usage examples
- Review the troubleshooting section above

## 🔗 Related Projects

- [LangChain](https://github.com/langchain-ai/langchain) - Framework for LLM applications
- [ClickHouse](https://github.com/ClickHouse/ClickHouse) - Fast columnar database
- [Sentence Transformers](https://github.com/UKPLab/sentence-transformers) - Embedding models
