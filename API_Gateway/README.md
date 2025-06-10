# API Gateway for RAG Benchmarking Platform

Central API Gateway for the RAG Benchmarking Platform with unified metrics collection and real-time analytics.

## 🎯 Features

- **🚀 FastAPI Framework**: Modern async API with automatic documentation
- **📊 Unified Metrics System**: Single enhanced metrics collector for all components
- **🧠 LLM Query Analytics**: Comprehensive query performance tracking
- **📈 Real-time Streaming**: WebSocket metrics broadcasting
- **💾 Automated CSV Export**: Continuous metrics export every 30 seconds
- **💰 Financial Query Support**: Specialized endpoints for financial data queries

## 🏗️ Architecture

The API Gateway serves as the central entry point with a **single unified metrics system**:

```
FastAPI Server (Port 8000)
├── Enhanced Metrics Collector (Unified System)
│   ├── LLM Query Analytics
│   ├── Real-time WebSocket Streaming
│   ├── Automated CSV Export
│   └── Performance Classification
├── LLM Service Client (gRPC)
├── Embeddings Service Client (gRPC)
└── Streamlit Dashboard (Port 8502)
```

## 📡 Core API Endpoints

### **Query Processing**
- `POST /api/query` - General RAG pipeline queries
- `POST /api/financial/query` - Financial-specific queries with market context
- `GET /api/financial/tickers` - List of active financial tickers

### **Metrics & Analytics**
- `GET /api/metrics/current` - Real-time metrics snapshot
- `POST /api/metrics/export` - Export LLM query performance to CSV
- `WebSocket /ws/metrics` - Live metrics streaming
- `GET /api/health` - System health check with service connectivity

### **Documentation**
- `GET /docs` - Interactive OpenAPI documentation
- `GET /redoc` - Alternative API documentation

## 🚀 Quick Start

```bash
# Install dependencies
poetry install

# Start the API Gateway
poetry run python src/api_gateway/fastapi_server.py

# Access interactive documentation
open http://localhost:8000/docs

# Start the dashboard
poetry run streamlit run src/dashboard/enhanced_streamlit_dashboard.py --server.port 8502
```

## 📊 Unified Metrics System

### **Enhanced Metrics Collector**
The platform uses a **single unified metrics system** (`enhanced_metrics.py`) that handles:

- **LLM Query Performance**: Latency, token usage, model performance
- **Real-time Analytics**: Live WebSocket streaming to dashboards
- **Automated Export**: CSV generation every 30 seconds
- **Performance Classification**: Automatic categorization of metrics
- **Error Tracking**: Comprehensive error monitoring and analysis

### **Organized CSV Exports** - **UPDATED**
All metrics are automatically exported to organized directories:

```
API_Gateway/Data/
├── streaming_metrics/              # Real-time pipeline performance
│   ├── vector_db_metrics.csv      # OPTIMIZED: 12 essential columns
│   ├── chunking_metrics.csv       # OPTIMIZED: 7 essential columns
│   ├── streaming_data_metrics.csv # Data ingestion performance
│   └── embedding_metrics.csv      # AI model benchmarks
└── query_metrics/                  # LLM query analysis
    └── llm_query_metrics.csv      # NEW: 10 essential RAG columns
```

### **🎯 Dashboard Performance Integration**
The dashboard now displays **optimized metrics** with enhanced troubleshooting:

| **Dashboard Metric** | **CSV Source** | **Performance Threshold** |
|---------------------|----------------|---------------------------|
| **Vector DB Retrieval** | `streaming_metrics/vector_db_metrics.csv` | <1000ms = Good |
| **LLM Processing** | `query_metrics/llm_query_metrics.csv` | <3000ms = Good |
| **Average Relevance** | `avg_relevance_score` | >0.5 = Good Quality |
| **High-Quality Sources** | `docs_found` + relevance | >50% = Good Retrieval |

### **Real-time Streaming**
- **WebSocket Support**: Live metrics broadcast to connected clients
- **Dashboard Integration**: Real-time updates without polling
- **Performance Monitoring**: Instant visibility into system health

## 🔧 Development

### **Structure**
```
src/
├── api_gateway/
│   ├── fastapi_server.py          # Main FastAPI application
│   ├── routes.py                  # Legacy Flask routes (deprecated)
│   └── clients/                   # gRPC service clients
├── monitoring/
│   └── enhanced_metrics.py        # UNIFIED metrics system
└── dashboard/
    └── enhanced_streamlit_dashboard.py  # Active dashboard
```

### **Testing**
```bash
# Run all tests
poetry run pytest

# Test metrics system
poetry run pytest tests/test_metrics.py

# Test API endpoints
poetry run pytest tests/test_api.py
```

### **Utilities**
Manual testing utilities are available in `utils/`:
- `utils/manual_export.py` - Development/testing script for benchmarks
- `utils/README.md` - Utility documentation

## 🌟 Migration Notes

**Consolidated Systems:**
- ✅ **Enhanced Metrics** - Single unified metrics system (active)
- ❌ **Basic Metrics** - Deprecated and removed
- ❌ **RAGBenchmarks** - Moved to utilities (development only)
- ❌ **Old Dashboard** - Replaced with enhanced version

**Automated Features:**
- Streaming metrics export directly to CSV (no manual intervention)
- Real-time WebSocket broadcasting
- Automatic performance classification
- Continuous health monitoring

## 📈 Performance Monitoring

The unified metrics system provides:

| Metric Type | Frequency | Export Format | Purpose |
|-------------|-----------|---------------|---------|
| **LLM Queries** | Real-time | CSV + WebSocket | Query performance analysis |
| **Component Metrics** | 30-second intervals | CSV | System health monitoring |
| **Error Tracking** | Real-time | Logs + CSV | Troubleshooting |
| **Health Checks** | On-demand | JSON | Service connectivity |

## 🔗 Integration

- **LLM Service**: gRPC client for query processing
- **Embeddings Service**: gRPC client for vector operations
- **ClickHouse**: Vector database for financial data
- **Streamlit Dashboard**: Real-time visualization
- **WebSocket Clients**: Live metrics streaming

---

Built with FastAPI, enhanced metrics collection, and real-time analytics for comprehensive RAG pipeline monitoring.