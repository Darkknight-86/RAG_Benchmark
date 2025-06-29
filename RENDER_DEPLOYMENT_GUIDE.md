# 🚀 RAG Benchmarking Platform - Render.com Deployment Guide

## Overview
This guide walks you through deploying the complete RAG Benchmarking Platform (12k+ lines, 4 microservices) on Render.com using our optimized Docker configuration.

## 🏗️ Architecture
**Single Container Deployment** - All microservices run in one optimized container:
- **🌐 Streamlit Dashboard** (Port 8502) - Main UI with user credential input
- **⚡ FastAPI Gateway** (Port 8000) - REST API endpoints
- **📊 Embeddings Service** (Port 50051) - gRPC + Live streaming
- **🤖 LLM Service** (Port 50054) - gRPC + RAG pipeline

## 📋 Prerequisites

### 1. ClickHouse Cloud Database (Optional but Recommended)
```bash
# Create account at https://clickhouse.cloud/
# Note your connection details:
# - Host: your-instance.us-east-1.aws.clickhouse.cloud
# - Port: 8443 (secure)
# - User: default
# - Password: [your-password]
# - Database: default
```

### 2. HuggingFace Account (Optional but Recommended)
```bash
# Create account at https://huggingface.co/
# Generate access token at https://huggingface.co/settings/tokens
# Token enables LLM features (Llama 3.2 models)
```

## 🚀 Deployment Steps

### Step 1: Connect Repository to Render
1. Fork/clone this repository to your GitHub account
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New" → "Web Service"
4. Connect your GitHub repository

### Step 2: Configure Service
```yaml
# Render will auto-detect render.yaml configuration
Service Name: rag-benchmarking-platform
Environment: Docker
Dockerfile Path: ./Dockerfile.render
Plan: Starter (can upgrade to Standard for better performance)
Health Check Path: /
```

### Step 3: Set Environment Variables
**Required Variables:**
```bash
PORT=8502
ENVIRONMENT=production
```

**Optional Database Variables (for full functionality):**
```bash
CLICKHOUSE_HOST=your-instance.us-east-1.aws.clickhouse.cloud
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=[your-secure-password]
CLICKHOUSE_DATABASE=default
CLICKHOUSE_PORT=8443
CLICKHOUSE_SECURE=true
```

**Optional LLM Variables (for AI features):**
```bash
HUGGINGFACE_HUB_TOKEN=[your-hf-token]
DEFAULT_LLM_MODEL=meta-llama/Llama-3.2-1B-Instruct
```

### Step 4: Deploy
1. Click "Create Web Service"
2. Wait for build to complete (~5-10 minutes)
3. Service will be available at your Render URL

## 🔧 Configuration Options

### Environment Variables Reference
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8502 | Main dashboard port |
| `ENVIRONMENT` | production | Deployment environment |
| `CLICKHOUSE_HOST` | "" | ClickHouse server hostname |
| `CLICKHOUSE_USER` | default | Database username |
| `CLICKHOUSE_PASSWORD` | "" | Database password |
| `CLICKHOUSE_DATABASE` | default | Database name |
| `CLICKHOUSE_PORT` | 8443 | Database port |
| `CLICKHOUSE_SECURE` | true | Use SSL/TLS |
| `HUGGINGFACE_HUB_TOKEN` | "" | HF access token |
| `DEFAULT_LLM_MODEL` | meta-llama/Llama-3.2-1B-Instruct | LLM model |

### User Credential Input (Demo Mode)
If environment variables are not set, users can input credentials directly in the dashboard:
- ClickHouse connection details
- HuggingFace token
- Credentials are session-based (not persistent)

## 🌟 Features Available After Deployment

### Core Features
- ✅ **Enhanced Streamlit Dashboard** - Beautiful UI for system monitoring
- ✅ **FastAPI REST Endpoints** - `/api/health`, `/api/query`, `/api/benchmark`
- ✅ **Real-time Financial Data Streaming** - Live yfinance data processing
- ✅ **Vector Database Integration** - ClickHouse with embeddings
- ✅ **LLM RAG Pipeline** - Llama 3.2 with retrieval augmentation

### Performance Metrics
- 📊 **Live Streaming Metrics** - Real-time data processing stats
- 📈 **Query Performance** - Vector search and LLM response times
- 💾 **Database Metrics** - Connection health and query latency
- 📋 **CSV Export** - Download metrics for analysis

### API Endpoints
```bash
# Health Check
GET https://your-app.onrender.com/api/health

# Query RAG System
POST https://your-app.onrender.com/api/query
{
  "query": "What is the latest financial data?",
  "top_k": 5
}

# Benchmark Performance
POST https://your-app.onrender.com/api/benchmark
{
  "test_queries": ["query1", "query2"],
  "iterations": 10
}
```

## 🔍 Monitoring & Debugging

### Health Checks
- **Dashboard**: `https://your-app.onrender.com/`
- **API Health**: `https://your-app.onrender.com/api/health`
- **Render Logs**: Available in Render dashboard

### Common Issues & Solutions

**1. Build Failures**
```bash
# Check Dockerfile.render syntax
# Ensure all dependencies in pyproject.toml files
# Verify Poetry lock files are up to date
```

**2. Service Connection Issues**
```bash
# Check environment variables are set correctly
# Verify ClickHouse credentials and network access
# Confirm HuggingFace token has proper permissions
```

**3. Performance Issues**
```bash
# Upgrade from Starter to Standard plan
# Optimize ClickHouse queries
# Consider model size vs. available memory
```

## 🚀 Scaling Options

### Plan Upgrades
- **Starter**: 512MB RAM, 0.5 CPU - Good for demos
- **Standard**: 2GB RAM, 1 CPU - Recommended for production
- **Pro**: 4GB RAM, 2 CPU - High performance

### Optimization Tips
1. **Database**: Use ClickHouse Cloud for better performance
2. **Models**: Consider smaller LLM models for faster responses
3. **Caching**: HuggingFace models are cached between deployments
4. **Monitoring**: Use built-in metrics to identify bottlenecks

## 📞 Support

### Documentation
- [Complete System README](./Docs/COMPLETE_SYSTEM_README.md)
- [Project Status](./Docs/PROJECT_STATUS.md)
- [Deployment Summary](./DEPLOYMENT_SUMMARY.md)

### Troubleshooting
1. Check Render logs for detailed error messages
2. Verify environment variables are set correctly
3. Test database connections independently
4. Monitor resource usage in Render dashboard

---

## 🎯 Quick Start Checklist

- [ ] Repository connected to Render
- [ ] Environment variables configured
- [ ] ClickHouse database setup (optional)
- [ ] HuggingFace token generated (optional)
- [ ] Service deployed and healthy
- [ ] Dashboard accessible at Render URL
- [ ] API endpoints responding
- [ ] Streaming metrics active

**🎉 Your RAG Benchmarking Platform is now live on Render!**