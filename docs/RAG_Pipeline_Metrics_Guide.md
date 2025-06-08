# RAG Pipeline Metrics Comprehensive Guide

## 📊 Overview

This guide explains the complete metrics system for the Financial RAG Pipeline, including real-time streaming metrics and LLM query performance tracking. The system exports metrics to component-specific CSV files every 30 seconds for detailed analysis.

## 🏗️ Architecture

### **Metrics Collection Flow:**
```
📡 Live Data Stream → ✂️ Chunking → 🧠 Embedding → 🗄️ Vector DB (ClickHouse)
        ↓               ↓            ↓               ↓
   Data Metrics    Chunk Metrics  Embedding    VectorDB Metrics
                                  Metrics
        ↓               ↓            ↓               ↓
📁 streaming_data_metrics.csv → chunking_metrics.csv → embedding_metrics.csv → vector_db_metrics.csv
```

### **Export Schedule:**
- **Frequency**: Every 30 seconds
- **Data Window**: Last 5 minutes of activity
- **File Location**: `API_Gateway/Data/` (automatically created)
- **Append Mode**: Continuous data accumulation

---

## 📈 Component Metrics Breakdown

### **1. 📡 Data Streaming Metrics** (`streaming_data_metrics.csv`)

**Purpose**: Tracks live financial data ingestion from yliveticker

**Columns:**
- `timestamp` - ISO format timestamp of ingestion
- `ticker` - Financial symbol (BTC-USD, AAPL, etc.)
- `success` - Boolean ingestion success
- `ingestion_latency_ms` - Time to receive data from stream
- `data_size_bytes` - Size of raw financial data
- `source` - Data source (yliveticker)
- `throughput_bps` - Bytes per second ingestion rate

**Normal Ranges:**
- **Latency**: 0.1-2.0ms (network dependent)
- **Data Size**: 200-400 bytes per ticker update
- **Throughput**: 100K-1M+ bytes/second
- **Success Rate**: >99%

**What Triggers High Latency:**
- Network congestion
- Market volatility (more frequent updates)
- yliveticker service issues

---

### **2. ✂️ Chunking Metrics** (`chunking_metrics.csv`)

**Purpose**: Measures text chunking performance using LangChain RecursiveCharacterTextSplitter

**Columns:**
- `timestamp` - When chunking occurred
- `ticker` - Source ticker symbol
- `original_text_size` - Size of raw financial data
- `chunk_count` - Number of chunks created (usually 1 for financial data)
- `avg_chunk_size` - Average size per chunk
- `min_chunk_size` / `max_chunk_size` - Chunk size range
- `chunking_latency_ms` - Time to split text
- `chunking_efficiency` - Ratio of original size to chunks
- `chunk_size_variance` - Difference between min/max chunk sizes
- `chunker_config` - JSON of chunking configuration

**Normal Ranges:**
- **Latency**: 0.01-1.0ms (very fast operation)
- **Chunk Count**: 1 (financial data is typically <1000 chars)
- **Efficiency**: High (near 1:1 ratio)

**Configuration:**
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters
- **Separators**: `["\n\n", "\n", " ", ""]`

**What Triggers Multiple Chunks:**
- Large financial news articles (rare)
- Detailed earnings reports
- Configuration changes

---

### **3. 🧠 Embedding Metrics** (`embedding_metrics.csv`)

**Purpose**: Tracks AI model performance for vector generation

**Columns:**
- `timestamp` - When embedding was generated
- `success` - Boolean generation success
- `embedding_latency_ms` - Time for model inference
- `text_length` - Input text character count
- `embedding_dimension` - Vector size (384 for MiniLM-L6-v2)
- `model_name` - AI model used
- `tokens_per_second` - Processing speed estimate
- `embedding_throughput` - Vectors generated per second

**Normal Ranges:**
- **Latency**: 20-500ms (model dependent)
- **Dimension**: 384 (MiniLM-L6-v2)
- **Throughput**: 500-2000 tokens/second
- **Success Rate**: >98%

**Model Performance Tiers:**
- **Excellent**: <50ms
- **Good**: 50-200ms
- **Acceptable**: 200-500ms
- **Slow**: >500ms

**What Affects Performance:**
- Text length (longer = slower)
- Model size (larger = slower, more accurate)
- Hardware (GPU vs CPU)
- Concurrent requests

---

### **4. 🗄️ Vector Database Metrics** (`vector_db_metrics.csv`)

**Purpose**: Monitors ClickHouse vector operations and reindexing detection

**Columns:**
- `timestamp` - Operation timestamp
- `operation` - Database operation type
- `operation_type` - Classified operation category
- `table` - Target table name
- `success` - Boolean operation success
- `vd_latency_ms` - Vector database latency
- `records_affected` - Number of records processed
- `throughput_records_per_second` - Operation speed
- `performance_tier` - Categorized performance level

**Operation Types (ClickHouse MergeTree Reality):**

#### **🟢 Normal Operations:**
- **`indexing`** - New vector insertions (most common)
  - *Latency*: 50-200ms
  - *Frequency*: Continuous with streaming data

#### **🟡 Reindexing Operations:**
- **`background_merge`** - Automatic ClickHouse part merging
  - *Latency*: 500-2000ms
  - *Frequency*: Every few hours automatically
  - *Triggers*: Multiple data parts accumulation

- **`manual_optimize`** - Manual OPTIMIZE TABLE FINAL commands
  - *Latency*: 2000-10000ms
  - *Frequency*: Manual/scheduled maintenance
  - *Triggers*: `OPTIMIZE TABLE financial_embeddings FINAL`

- **`schema_reindex`** - Schema changes forcing reindexing
  - *Latency*: 1000-5000ms
  - *Frequency*: Rare (schema updates)
  - *Triggers*: ALTER TABLE commands

- **`suspected_background_merge`** - High-latency operations (detected automatically)
  - *Latency*: >2000ms
  - *Detection*: Latency-based classification

#### **🔴 Other Operations:**
- **`bulk_insert`** - Large batch insertions
- **`data_update`** - Record updates (rare in streaming)
- **`deletion`** - Record deletions

**Performance Tiers:**
- **Excellent**: <50ms (optimal)
- **Good**: 50-150ms (normal)
- **Slow**: >150ms (may indicate reindexing)

---

## 🔍 ClickHouse Integration Details

### **MergeTree Behavior:**
ClickHouse uses MergeTree engine with automatic background operations:

1. **Data Parts**: Each insert creates a data part
2. **Background Merging**: ClickHouse automatically merges parts
3. **Per-Part Indexes**: Each part has its own indexes
4. **Incremental Reindexing**: No global reindex, only part-level

### **When Reindexing Occurs:**

#### **🤖 Automatic (Background):**
- **Part Count Threshold**: >100 parts triggers merging
- **Size Threshold**: Large parts get merged
- **Time-Based**: Every 8-12 hours during low activity
- **Detection**: `background_merge` in metrics

#### **📋 Manual:**
- **OPTIMIZE FINAL**: Forces immediate merging
- **Schema Changes**: ALTER TABLE operations
- **Detection**: `manual_optimize` or `schema_reindex`

#### **📊 Volume-Triggered:**
- **Bulk Inserts**: Large batches may trigger immediate merging
- **High Frequency**: Rapid inserts create many parts
- **Detection**: Increased latencies, `bulk_insert` operations

### **Expected Patterns:**

**Normal Day:**
```
indexing: 95% of operations (50-200ms)
background_merge: 3% of operations (500-2000ms)
manual_optimize: 1% of operations (2000+ms)
other: 1% of operations
```

**Heavy Load Day:**
```
indexing: 85% of operations
background_merge: 10% of operations (more frequent)
bulk_insert: 4% of operations
manual_optimize: 1% of operations
```

---

## 📋 Interpreting Metrics

### **🟢 Healthy System Indicators:**
- **Streaming Latency**: <2ms consistently
- **Chunking Latency**: <1ms
- **Embedding Latency**: <200ms average
- **VD Latency**: <150ms for 90% of operations
- **Success Rates**: >98% across all components

### **🟡 Performance Concerns:**
- **Streaming Latency**: >5ms (network issues)
- **Embedding Latency**: >500ms (model overload)
- **VD Latency**: >300ms for normal inserts (reindexing activity)
- **Success Rates**: <95% (investigate errors)

### **🔴 Critical Issues:**
- **Any Latency**: >10x normal values
- **Success Rates**: <90%
- **Frequent Manual Optimizes**: Database maintenance needed
- **No Background Merging**: ClickHouse configuration issue

### **📈 Volume Analysis:**
- **Records/Hour**: 200-1000 normal, >2000 high volume
- **Parts Growth**: Monitor part count increases
- **Merge Frequency**: Should happen every few hours

---

## 🚀 Optimization Recommendations

### **Streaming Performance:**
- Monitor network latency patterns
- Alert on >5ms ingestion delays
- Track ticker-specific performance

### **Embedding Performance:**
- Consider GPU acceleration for >1000 embeds/hour
- Monitor model memory usage
- Batch processing for efficiency

### **ClickHouse Optimization:**
- Schedule OPTIMIZE during low-traffic periods
- Monitor part count growth
- Alert on excessive manual optimizations needed

### **Alert Thresholds:**
```yaml
streaming_latency_alert: >10ms
embedding_latency_alert: >1000ms
vd_latency_alert: >500ms (for normal inserts)
success_rate_alert: <95%
reindex_frequency_alert: >10 background_merges/hour
```

---

## 📊 CSV File Analysis

### **Quick Health Check:**
```bash
# Check recent performance
tail -100 vector_db_metrics.csv | grep -v "indexing"

# Monitor success rates
awk -F',' '{if(NR>1) total++; if($5=="True") success++} END {print "Success Rate:", (success/total)*100"%"}' vector_db_metrics.csv

# Find performance issues
awk -F',' '{if(NR>1 && $6>500) print $1, $6"ms", $9}' vector_db_metrics.csv
```

### **Trend Analysis:**
- **Load CSVs into Excel/Python** for time-series analysis
- **Graph latency trends** to identify patterns
- **Correlate high latencies** with reindexing events
- **Monitor success rate trends** over time

---

## 🔧 Troubleshooting Guide

### **High Streaming Latency:**
1. Check network connectivity to data source
2. Monitor yliveticker service status
3. Verify no rate limiting

### **High Embedding Latency:**
1. Check CPU/GPU utilization
2. Monitor memory usage
3. Consider model optimization

### **High VD Latency:**
1. Check for ongoing ClickHouse merging
2. Monitor disk I/O
3. Consider manual optimization scheduling

### **Low Success Rates:**
1. Check error logs for specific failures
2. Verify database connectivity
3. Monitor resource constraints

---

## 📁 File Management

All metrics are automatically saved to:
```
API_Gateway/Data/
├── streaming_data_metrics.csv
├── chunking_metrics.csv
├── embedding_metrics.csv
├── vector_db_metrics.csv
└── LLM_query_performance_YYYYMMDD_HHMMSS.csv
```

**Retention**: Files grow continuously - implement rotation as needed
**Backup**: Regular backup recommended for long-term analysis
**Analysis**: Import into BI tools for advanced analytics

---

*This metrics system provides complete visibility into RAG pipeline performance, enabling proactive optimization and troubleshooting.*