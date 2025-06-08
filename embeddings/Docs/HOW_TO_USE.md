# How to Use the Financial RAG Microservice

This guide provides detailed examples and use cases for the Financial RAG Microservice.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Real-time Data Streaming](#real-time-data-streaming)
5. [Semantic Search Examples](#semantic-search-examples)
6. [Data Management](#data-management)
7. [Integration Patterns](#integration-patterns)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting](#troubleshooting)

## Getting Started

### Initial Setup

1. **Install and configure the service**:
   ```bash
   # Clone and setup
   cd embeddings
   poetry install

   # Configure environment
   cp .env.example .env
   # Edit .env with your ClickHouse credentials
   ```

2. **Test the connection**:
   ```bash
   poetry run python test_schema_fix.py
   ```

3. **Initialize the vector store**:
   ```python
   from src.rag.Adapters.ClickHouseAdapter import ClickHouseAdapter

   # Create adapter instance
   adapter = ClickHouseAdapter()

   # Verify setup
   adapter.check_table_schema()
   ```

## Basic Usage

### Adding Documents

#### Single Document
```python
from langchain_core.documents import Document

# Create a document
doc = Document(
    page_content="Tesla stock jumped 8% after Q3 earnings beat analyst expectations with record revenue.",
    metadata={
        "source": "financial_news",
        "ticker": "TSLA",
        "price": 185.50,
        "change_percent": 8.2,
        "volume": 45000000
    }
)

# Add to vector store
adapter.add_documents([doc])
```

#### Multiple Documents
```python
from uuid import uuid4

# Prepare multiple documents
documents = [
    Document(
        page_content="Amazon Web Services revenue grew 20% year-over-year in Q3.",
        metadata={"source": "earnings", "ticker": "AMZN", "price": 127.80}
    ),
    Document(
        page_content="Apple iPhone 15 sales exceeded expectations in first week.",
        metadata={"source": "product_news", "ticker": "AAPL", "price": 175.20}
    ),
    Document(
        page_content="Microsoft Azure cloud revenue increased 29% compared to last quarter.",
        metadata={"source": "earnings", "ticker": "MSFT", "price": 331.90}
    )
]

# Generate unique IDs
ids = [str(uuid4()) for _ in documents]

# Add all documents
successful_ids = adapter.add_documents(documents=documents, ids=ids)
print(f"Successfully added {len(successful_ids)} documents")
```

### Searching Documents

#### Basic Similarity Search
```python
# Search for cloud-related content
results = adapter.similarity_search("cloud computing revenue growth", k=3)

for i, doc in enumerate(results):
    print(f"{i+1}. {doc.page_content}")
    print(f"   Ticker: {doc.metadata['ticker']}")
    print(f"   Price: ${doc.metadata['price']}")
    print()
```

#### Search with Similarity Scores
```python
# Search with confidence scores
results_with_scores = adapter.similarity_search_with_score(
    "technology stock performance",
    k=5
)

for doc, score in results_with_scores:
    print(f"Score: {score:.3f} | {doc.metadata['ticker']} | {doc.page_content[:100]}...")
```

## Advanced Features

### Custom Embedding Models

```python
from sentence_transformers import SentenceTransformer

# Use a financial-specific model
financial_model = SentenceTransformer('nlpaueb/sec-bert-base')

# Initialize adapter with custom model
adapter = ClickHouseAdapter(embedding_model=financial_model)

# Or use a multilingual model
multilingual_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
adapter = ClickHouseAdapter(embedding_model=multilingual_model)
```

### Batch Processing

```python
import json
from pathlib import Path

def process_financial_reports(reports_dir: str):
    """Process a directory of financial reports"""

    documents = []

    for report_file in Path(reports_dir).glob("*.json"):
        with open(report_file) as f:
            data = json.load(f)

        # Create document from report
        doc = Document(
            page_content=data['summary'],
            metadata={
                "source": "financial_report",
                "ticker": data['ticker'],
                "quarter": data['quarter'],
                "year": data['year'],
                "revenue": data['revenue'],
                "profit_margin": data['profit_margin']
            }
        )
        documents.append(doc)

    # Batch insert
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        adapter.add_documents(batch)
        print(f"Processed batch {i//batch_size + 1}")

# Usage
process_financial_reports("./financial_reports/")
```

## Real-time Data Streaming

### Starting the Live Stream

```bash
# Start the real-time financial data stream
poetry run python src/rag/streaming.py
```

The streaming service will:
- Connect to Yahoo Finance WebSocket
- Process live stock data for configured tickers
- Generate embeddings in real-time
- Store vectors in ClickHouse continuously

### Monitoring Live Data

```python
import time

def monitor_live_data():
    """Monitor incoming live data"""

    while True:
        # Check recent insertions
        adapter.verify_data_insertion()

        # Check for specific tickers
        recent_results = adapter.similarity_search("latest price update", k=10)

        print(f"Found {len(recent_results)} recent updates")
        for doc in recent_results[:3]:
            print(f"  {doc.metadata['security']}: ${doc.metadata['price']}")

        time.sleep(30)  # Check every 30 seconds

# Run monitoring
monitor_live_data()
```

## Semantic Search Examples

### Financial Query Examples

```python
# Stock performance queries
queries = [
    "technology stocks with strong earnings growth",
    "companies reporting revenue decline",
    "stocks with high trading volume",
    "positive quarterly results announcement",
    "market volatility and price movements"
]

for query in queries:
    print(f"\nQuery: {query}")
    results = adapter.similarity_search_with_score(query, k=3)

    for doc, score in results:
        ticker = doc.metadata.get('security', 'N/A')
        price = doc.metadata.get('price', 0)
        print(f"  {score:.3f} | {ticker} | ${price:.2f}")
```

### Sector Analysis

```python
def analyze_sector(sector_keywords: str, min_score: float = 0.7):
    """Analyze documents for a specific sector"""

    results = adapter.similarity_search_with_score(sector_keywords, k=20)

    sector_analysis = {
        'high_confidence': [],
        'medium_confidence': [],
        'stocks_mentioned': set()
    }

    for doc, score in results:
        ticker = doc.metadata.get('security', 'Unknown')
        sector_analysis['stocks_mentioned'].add(ticker)

        if score >= min_score:
            sector_analysis['high_confidence'].append((doc, score))
        elif score >= 0.5:
            sector_analysis['medium_confidence'].append((doc, score))

    return sector_analysis

# Analyze tech sector
tech_analysis = analyze_sector("technology software cloud computing artificial intelligence")
print(f"Tech stocks found: {list(tech_analysis['stocks_mentioned'])}")
print(f"High confidence matches: {len(tech_analysis['high_confidence'])}")
```

## Data Management

### Document Deletion

```python
# Delete specific documents
document_ids = ["doc_id_1", "doc_id_2", "doc_id_3"]
success = adapter.delete(ids=document_ids)

if success:
    print(f"Successfully deleted {len(document_ids)} documents")

# Verify deletion
adapter.verify_data_insertion()
```

### Data Cleanup

```python
def cleanup_old_data(days_old: int = 30):
    """Remove data older than specified days"""

    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=days_old)

    # Note: This requires custom SQL for ClickHouse
    query = f"""
    ALTER TABLE rag_chunks_v2
    DELETE WHERE timestamp < '{cutoff_date.isoformat()}'
    """

    try:
        adapter.client.command(query)
        print(f"Cleaned up data older than {days_old} days")
    except Exception as e:
        print(f"Cleanup failed: {e}")

# Clean up old data
cleanup_old_data(days_old=7)
```

### Schema Migration

```python
def migrate_schema():
    """Migrate to latest schema if needed"""

    existing_cols, missing_cols, extra_cols = adapter.check_table_schema()

    if missing_cols or extra_cols:
        print("Schema mismatch detected!")
        print(f"Missing columns: {missing_cols}")
        print(f"Extra columns: {extra_cols}")

        response = input("Recreate table with correct schema? (yes/no): ")
        if response.lower() == 'yes':
            success = adapter.recreate_table()
            if success:
                print("✅ Schema migration completed")
            else:
                print("❌ Schema migration failed")
    else:
        print("✅ Schema is up to date")

migrate_schema()
```

## Integration Patterns

### REST API Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Financial RAG API")

class SearchRequest(BaseModel):
    query: str
    k: int = 5
    min_score: Optional[float] = None

class DocumentRequest(BaseModel):
    content: str
    metadata: dict

class SearchResult(BaseModel):
    content: str
    metadata: dict
    score: float

@app.post("/search", response_model=List[SearchResult])
async def search_documents(request: SearchRequest):
    try:
        results = adapter.similarity_search_with_score(request.query, k=request.k)

        response = []
        for doc, score in results:
            if request.min_score is None or score >= request.min_score:
                response.append(SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=score
                ))

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents")
async def add_document(request: DocumentRequest):
    try:
        doc = Document(
            page_content=request.content,
            metadata=request.metadata
        )

        ids = adapter.add_documents([doc])
        return {"status": "success", "document_id": ids[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn integration:app --reload
```

### Scheduled Analytics

```python
import schedule
import time
from datetime import datetime

def daily_analytics():
    """Run daily analytics on stored data"""

    print(f"Running daily analytics - {datetime.now()}")

    # Get table statistics
    adapter.get_table_stats()

    # Analyze trending topics
    trending_queries = [
        "earnings report",
        "stock price increase",
        "market volatility",
        "dividend announcement"
    ]

    for query in trending_queries:
        results = adapter.similarity_search_with_score(query, k=5)
        print(f"\nTrending: {query}")
        print(f"Found {len(results)} relevant documents")

def weekly_maintenance():
    """Weekly maintenance tasks"""

    print("Running weekly maintenance...")

    # Verify data integrity
    adapter.verify_data_insertion()

    # Get comprehensive stats
    adapter.get_table_stats()

# Schedule jobs
schedule.every().day.at("09:00").do(daily_analytics)
schedule.every().sunday.at("02:00").do(weekly_maintenance)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Performance Optimization

### Optimized Queries

```python
def optimized_search(query: str, filters: dict = None):
    """Perform optimized search with filtering"""

    # Generate embedding once
    query_embedding = adapter.embedding_model.encode([query])[0].tolist()

    # Build SQL with filters
    where_clause = ""
    if filters:
        conditions = []
        if 'ticker' in filters:
            conditions.append(f"security = '{filters['ticker']}'")
        if 'min_price' in filters:
            conditions.append(f"price >= {filters['min_price']}")
        if 'source' in filters:
            conditions.append(f"source = '{filters['source']}'")

        if conditions:
            where_clause = "AND " + " AND ".join(conditions)

    # Execute optimized query
    query_sql = f"""
    SELECT
        id, chunk, source, price, change_percent, volume, security,
        cosineDistance(embedding, {query_embedding}) as distance
    FROM rag_chunks_v2
    WHERE 1=1 {where_clause}
    ORDER BY distance ASC
    LIMIT 10
    """

    results = adapter.client.query(query_sql)
    return results.result_rows

# Usage
results = optimized_search(
    "cloud revenue growth",
    filters={'min_price': 100, 'source': 'earnings'}
)
```

### Batch Operations

```python
def bulk_similarity_search(queries: List[str], k: int = 5):
    """Perform multiple searches efficiently"""

    # Generate all embeddings at once
    embeddings = adapter.embedding_model.encode(queries).tolist()

    results = {}
    for i, (query, embedding) in enumerate(zip(queries, embeddings)):
        # Use pre-computed embedding
        query_sql = f"""
        SELECT chunk, security, price,
               cosineDistance(embedding, {embedding}) as distance
        FROM rag_chunks_v2
        ORDER BY distance ASC
        LIMIT {k}
        """

        search_results = adapter.client.query(query_sql)
        results[query] = search_results.result_rows

    return results

# Bulk search
queries = [
    "technology earnings",
    "financial performance",
    "market trends"
]
bulk_results = bulk_similarity_search(queries)
```

## Troubleshooting

### Common Issues and Solutions

#### Connection Problems
```python
def test_connection():
    """Test ClickHouse connection"""
    try:
        adapter.client.command("SELECT 1")
        print("✅ ClickHouse connection successful")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

# Test before operations
if not test_connection():
    print("Please check your ClickHouse configuration")
    exit(1)
```

#### Schema Issues
```python
def diagnose_schema():
    """Diagnose schema-related issues"""

    try:
        # Check if table exists
        result = adapter.client.query("""
            SELECT name FROM system.tables
            WHERE database = 'default' AND name = 'rag_chunks_v2'
        """)

        if not result.result_rows:
            print("❌ Table 'rag_chunks_v2' does not exist")
            print("Run adapter.recreate_table() to create it")
            return False

        # Check schema
        existing_cols, missing_cols, extra_cols = adapter.check_table_schema()

        if missing_cols or extra_cols:
            print(f"❌ Schema mismatch: missing={missing_cols}, extra={extra_cols}")
            return False

        print("✅ Schema is correct")
        return True

    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False

diagnose_schema()
```

#### Performance Issues
```python
def performance_diagnostics():
    """Check performance metrics"""

    # Check table size
    result = adapter.client.query("""
        SELECT
            formatReadableSize(total_bytes) as size,
            total_rows,
            formatReadableSize(total_bytes/total_rows) as avg_row_size
        FROM system.tables
        WHERE database = 'default' AND name = 'rag_chunks_v2'
    """)

    if result.result_rows:
        size, rows, avg_size = result.result_rows[0]
        print(f"Table size: {size}")
        print(f"Total rows: {rows}")
        print(f"Average row size: {avg_size}")

    # Check recent query performance
    result = adapter.client.query("""
        SELECT
            query_duration_ms,
            read_rows,
            read_bytes
        FROM system.query_log
        WHERE type = 'QueryFinish'
        AND query LIKE '%rag_chunks_v2%'
        ORDER BY event_time DESC
        LIMIT 5
    """)

    if result.result_rows:
        print("\nRecent query performance:")
        for duration, rows, bytes_read in result.result_rows:
            print(f"  Duration: {duration}ms, Rows: {rows}, Bytes: {bytes_read}")

performance_diagnostics()
```

This guide covers the most common use cases and advanced features of the Financial RAG Microservice. For additional help, refer to the main [README.md](README.md) or create an issue on the project repository.