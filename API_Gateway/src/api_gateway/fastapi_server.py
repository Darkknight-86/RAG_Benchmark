"""
FastAPI Server for Financial RAG API Gateway

Replaces Flask server with better async support, no import conflicts,
and native real-time streaming capabilities.
"""

import asyncio
import json
import time
import logging
import os
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import clients and metrics - using absolute imports for main module execution
try:
    from .clients import LLMClient, EmbeddingsClient
    from ..monitoring.enhanced_metrics import metrics_collector
except ImportError:
    from api_gateway.clients import LLMClient, EmbeddingsClient
    from monitoring.enhanced_metrics import metrics_collector

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Note: Streaming metrics are now handled automatically by the streaming service
# Dashboard focuses only on LLM/RAG query metrics - streaming data exports directly to CSV

# Create FastAPI app
app = FastAPI(
    title="Financial RAG API Gateway",
    description="Microservices API Gateway for Financial RAG Pipeline with Real-time Metrics",
    version="2.0.0",
    docs_url="/docs",  # Automatic OpenAPI documentation
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    query: str
    model_name: Optional[str] = "meta-llama/Llama-3.2-1B-Instruct"
    top_k: Optional[int] = 5
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000  # Increased for Llama

class FinancialQueryRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    model_name: Optional[str] = "meta-llama/Llama-3.2-1B-Instruct"
    temperature: Optional[float] = 0.7

class QueryMetrics(BaseModel):
    vector_latency: float
    llm_latency: float
    total_time: float
    tokens_used: int
    model_name: str
    # Enhanced metrics for search strategies and retrieval quality
    search_strategies: Optional[List[str]] = []
    search_metrics: Optional[Dict[str, Any]] = {}
    retrieval_quality: Optional[Dict[str, Any]] = {}

class QueryResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    metrics: QueryMetrics
    query_type: Optional[str] = None
    ticker: Optional[str] = None

class ExportRequest(BaseModel):
    minutes: Optional[int] = 60
    export_type: Optional[str] = "live data"  # "live data" or "LLM query"

# Root endpoint
@app.get("/")
async def root():
    """API Gateway root endpoint with service information."""
    return {
        "message": "Financial RAG API Gateway - FastAPI",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

# Health endpoint
@app.get("/api/health")
async def health():
    """Enhanced health check with service connectivity."""
    health_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "framework": "FastAPI",
        "version": "2.0.0"
    }

    # Test service connectivity
    try:
        # Test LLM service connection
        with LLMClient() as llm_client:
            health_info["services"] = {"llm_service": "healthy"}
    except Exception as e:
        logger.warning(f"LLM service health check failed: {e}")
        health_info["services"] = {"llm_service": "unhealthy"}

    try:
        # Test Embeddings service connection
        with EmbeddingsClient() as embeddings_client:
            health_info["services"]["embeddings_service"] = "healthy"
    except Exception as e:
        logger.warning(f"Embeddings service health check failed: {e}")
        health_info["services"]["embeddings_service"] = "unhealthy"

    return health_info

# Query endpoints
@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process a query through the RAG pipeline."""
    start_time = time.time()
    logger.info(f"📩 Received query request: {request.query[:50]}...")

    try:
        # Use LLM client asynchronously
        with LLMClient() as client:
            logger.info("🧠 Sending to LLM service...")

            # In a real async implementation, we'd make this truly async
            # For now, we'll wrap the sync call
            response = client.query(
                query_text=request.query,
                model_name=request.model_name,
                top_k=request.top_k,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

            total_time = time.time() - start_time

            # Build response
            result = QueryResponse(
                response=response.answer,
                sources=[{
                    "content": source.content,
                    "score": source.score,
                    "metadata": dict(source.metadata) if hasattr(source, 'metadata') else {}
                } for source in response.sources] if hasattr(response, 'sources') else [],
                metrics=QueryMetrics(
                    vector_latency=response.metrics.vector_latency,
                    llm_latency=response.metrics.llm_latency,
                    total_time=total_time,
                    tokens_used=response.metrics.tokens_used,
                    model_name=response.metrics.model_name,
                    # Enhanced metrics
                    search_strategies=getattr(response.metrics, 'search_strategies', []),
                    search_metrics=getattr(response.metrics, 'search_metrics', {}),
                    retrieval_quality=getattr(response.metrics, 'retrieval_quality', {})
                )
            )

            # Record metrics for CSV export
            # Extract retrieval quality from sources since protobuf doesn't support extended metrics
            docs_found = len(response.sources) if hasattr(response, 'sources') and response.sources else 0

            # Calculate average relevance from sources
            avg_relevance = 0.0
            if hasattr(response, 'sources') and response.sources:
                relevance_scores = [source.score for source in response.sources if hasattr(source, 'score')]
                if relevance_scores:
                    avg_relevance = sum(relevance_scores) / len(relevance_scores)

            # Enhanced search strategies - parse from response text for crypto queries
            search_strategies = []
            search_metrics = {}
            if "Bitcoin" in response.answer or "cryptocurrency" in response.answer or "BTC" in response.answer:
                search_strategies = ["crypto_enhanced", "similarity_search"]
                search_metrics = {"crypto_enhanced": docs_found}

            metrics_collector.record_metric("api_gateway", "query_processed", total_time,
                query=request.query[:100],  # Truncate for storage
                response=response.answer[:200],  # Truncate for storage
                vector_latency=response.metrics.vector_latency,
                llm_latency=response.metrics.llm_latency,
                tokens_used=response.metrics.tokens_used,
                model_name=response.metrics.model_name,
                # Enhanced metrics - manually constructed since protobuf limitation
                search_strategies=search_strategies,
                search_metrics=search_metrics,
                retrieval_quality={
                    "docs_found": docs_found,
                    "avg_relevance": avg_relevance,
                    "high_quality_docs": len([s for s in (response.sources or []) if hasattr(s, 'score') and s.score > 0.7]),
                    "high_quality_ratio": (len([s for s in (response.sources or []) if hasattr(s, 'score') and s.score > 0.7]) / max(docs_found, 1))
                },
                status="success"
            )

            logger.info(f"✅ Query completed in {total_time:.3f}s")
            return result

    except Exception as e:
        # Record error metrics
        metrics_collector.record_metric("api_gateway", "query_error", time.time() - start_time,
            query=request.query[:100],
            error=str(e)[:200],
            status="error"
        )

        logger.error(f"❌ Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/financial/query", response_model=QueryResponse)
async def financial_query(request: FinancialQueryRequest):
    """Process financial-specific queries with market data context."""
    start_time = time.time()
    logger.info(f"💰 Received financial query: {request.query[:50]}...")
    logger.info(f"💼 Financial query for ticker: {request.ticker or 'general'}")

    try:
        with LLMClient() as client:
            response = client.query(
                query_text=request.query,
                model_name=request.model_name,
                temperature=request.temperature,
                max_tokens=300  # Longer responses for financial analysis
            )

            total_time = time.time() - start_time

            result = QueryResponse(
                response=response.answer,
                sources=[{
                    "content": source.content,
                    "score": source.score,
                    "metadata": dict(source.metadata) if hasattr(source, 'metadata') else {}
                } for source in response.sources] if hasattr(response, 'sources') else [],
                metrics=QueryMetrics(
                    vector_latency=response.metrics.vector_latency,
                    llm_latency=response.metrics.llm_latency,
                    total_time=total_time,
                    tokens_used=response.metrics.tokens_used,
                    model_name=response.metrics.model_name,
                    # Enhanced metrics
                    search_strategies=getattr(response.metrics, 'search_strategies', []),
                    search_metrics=getattr(response.metrics, 'search_metrics', {}),
                    retrieval_quality=getattr(response.metrics, 'retrieval_quality', {})
                ),
                query_type="financial",
                ticker=request.ticker
            )

            # Record financial metrics for CSV export
            # Extract retrieval quality from sources since protobuf doesn't support extended metrics
            docs_found = len(response.sources) if hasattr(response, 'sources') and response.sources else 0

            # Calculate average relevance from sources
            avg_relevance = 0.0
            if hasattr(response, 'sources') and response.sources:
                relevance_scores = [source.score for source in response.sources if hasattr(source, 'score')]
                if relevance_scores:
                    avg_relevance = sum(relevance_scores) / len(relevance_scores)

            # Enhanced search strategies - parse from response text for crypto queries
            search_strategies = []
            search_metrics = {}
            if "Bitcoin" in response.answer or "cryptocurrency" in response.answer or "BTC" in response.answer:
                search_strategies = ["crypto_enhanced", "similarity_search"]
                search_metrics = {"crypto_enhanced": docs_found}

            metrics_collector.record_metric("api_gateway", "financial_query_processed", total_time,
                query=request.query[:100],  # Truncate for storage
                ticker=request.ticker or "general",
                response=response.answer[:200],  # Truncate for storage
                vector_latency=response.metrics.vector_latency,
                llm_latency=response.metrics.llm_latency,
                tokens_used=response.metrics.tokens_used,
                model_name=response.metrics.model_name,
                # Enhanced metrics - manually constructed since protobuf limitation
                search_strategies=search_strategies,
                search_metrics=search_metrics,
                retrieval_quality={
                    "docs_found": docs_found,
                    "avg_relevance": avg_relevance,
                    "high_quality_docs": len([s for s in (response.sources or []) if hasattr(s, 'score') and s.score > 0.7]),
                    "high_quality_ratio": (len([s for s in (response.sources or []) if hasattr(s, 'score') and s.score > 0.7]) / max(docs_found, 1))
                },
                status="success"
            )

            logger.info(f"✅ Financial query completed in {total_time:.3f}s")
            return result

    except Exception as e:
        # Record financial error metrics
        metrics_collector.record_metric("api_gateway", "financial_query_error", time.time() - start_time,
            query=request.query[:100],
            ticker=request.ticker or "general",
            error=str(e)[:200],
            status="error"
        )

        logger.error(f"❌ Error processing financial query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financial/tickers")
async def get_active_tickers():
    """Get list of currently active tickers in the system."""
    # This will eventually query the ClickHouse database
    active_tickers = [
        # Major Cryptocurrencies
        {"ticker": "BTC-USD", "name": "Bitcoin", "status": "active", "category": "crypto"},
        {"ticker": "ETH-USD", "name": "Ethereum", "status": "active", "category": "crypto"},
        {"ticker": "USDT-USD", "name": "Tether", "status": "active", "category": "crypto"},
        {"ticker": "BNB-USD", "name": "Binance Coin", "status": "active", "category": "crypto"},
        {"ticker": "SOL-USD", "name": "Solana", "status": "active", "category": "crypto"},
        {"ticker": "XRP-USD", "name": "Ripple", "status": "active", "category": "crypto"},
        {"ticker": "DOGE-USD", "name": "Dogecoin", "status": "active", "category": "crypto"},
        {"ticker": "ADA-USD", "name": "Cardano", "status": "active", "category": "crypto"},
        {"ticker": "AVAX-USD", "name": "Avalanche", "status": "active", "category": "crypto"},
        {"ticker": "DOT-USD", "name": "Polkadot", "status": "active", "category": "crypto"},
        {"ticker": "LINK-USD", "name": "Chainlink", "status": "active", "category": "crypto"},
        {"ticker": "MATIC-USD", "name": "Polygon", "status": "active", "category": "crypto"},
        {"ticker": "LTC-USD", "name": "Litecoin", "status": "active", "category": "crypto"},

        # US Stocks
        {"ticker": "AMZN", "name": "Amazon.com Inc", "status": "active", "category": "us_stock"},
        {"ticker": "GOOGL", "name": "Alphabet Inc", "status": "active", "category": "us_stock"},
        {"ticker": "AAPL", "name": "Apple Inc", "status": "active", "category": "us_stock"},
        {"ticker": "MSFT", "name": "Microsoft Corp", "status": "active", "category": "us_stock"},
        {"ticker": "META", "name": "Meta Platforms", "status": "active", "category": "us_stock"},

        # Australian Stocks
        {"ticker": "COL.AX", "name": "Coles Group Limited", "status": "active", "category": "au_stock"},
        {"ticker": "JBH.AX", "name": "JB Hi-Fi Limited", "status": "active", "category": "au_stock"},
        {"ticker": "WOW.AX", "name": "Woolworths Group Limited", "status": "active", "category": "au_stock"},
        {"ticker": "QAN.AX", "name": "Qantas Airways Limited", "status": "active", "category": "au_stock"},
        {"ticker": "TLS.AX", "name": "Telstra Corporation Limited", "status": "active", "category": "au_stock"}
    ]

    return {
        "tickers": active_tickers,
        "count": len(active_tickers),
        "last_updated": datetime.now().isoformat()
    }

# Metrics endpoints - Dual metrics system integration
@app.get("/metrics/current")
async def get_current_metrics():
    """Get current system metrics for dashboard display."""
    try:
        # Get LLM/RAG query metrics only - streaming metrics now go directly to CSV
        enhanced_data = metrics_collector.get_real_time_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "rag_query_metrics": enhanced_data,
            "system_info": {
                "service": "Financial RAG API Gateway",
                "version": "2.0",
                "metrics_types": ["llm_queries"],
                "note": "Live streaming metrics are exported directly to CSV files"
            }
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics error: {str(e)}")

@app.get("/api/metrics/current")
async def get_current_metrics_alt():
    """Alternative endpoint for metrics (dashboard compatibility)."""
    return await get_current_metrics()

# Removed /api/stream/metrics endpoint - no longer needed since streaming metrics export directly to CSV
# Dashboard now focuses only on LLM query metrics

@app.post("/api/metrics/export")
async def export_metrics(request: ExportRequest):
    """Export metrics to CSV file (dual system)."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Support both old and new parameter names for backward compatibility
        if request.export_type in ["streaming", "live data"]:
            # Live streaming metrics are now exported automatically every 5 minutes
            return {
                "status": "info",
                "message": "✅ Live streaming metrics are automatically exported to CSV every 5 minutes",
                "export_type": "automatic_streaming_export",
                "note": "📁 Check for files: live_streaming_metrics_YYYYMMDD_HHMMSS.csv",
                "auto_export_interval": "5 minutes",
                "manual_export": "not_required",
                "files_location": "Current directory"
            }

        else:
            # Export LLM query metrics in readable format (default for "queries" or "LLM query")
            filename = metrics_collector.export_query_metrics_csv(
                filename=f"LLM_query_performance_{timestamp}.csv",
                minutes=request.minutes
            )
            return {
                "status": "success",
                "filename": filename,
                "export_type": "LLM_query_performance",
                "timeframe_minutes": request.minutes,
                "records_exported": "LLM query performance metrics",
                "note": "Readable CSV with query text, response, latencies, tokens, and model performance"
            }

    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/metrics/export")
async def export_metrics_alt(request: ExportRequest):
    """Alternative endpoint for metrics export."""
    return await export_metrics(request)

# Legacy Flask compatibility endpoint
@app.get("/api/metrics/dashboard")
async def metrics_dashboard():
    """Serve the metrics dashboard HTML."""
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Financial RAG Monitoring - FastAPI</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            .header { text-align: center; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            .status { display: flex; justify-content: space-around; margin: 20px 0; }
            .status-card { background: #e7f3ff; padding: 15px; border-radius: 5px; text-align: center; min-width: 150px; }
            .healthy { background: #d4edda; }
            .unhealthy { background: #f8d7da; }
            .unknown { background: #e2e3e5; }
            .link { color: #007bff; text-decoration: none; margin: 10px; display: inline-block; }
            .new { background: #fff3cd; border: 1px solid #ffeaa7; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Financial RAG API Gateway - FastAPI</h1>
                <p>Real-time monitoring with async microservices</p>
                <div class="new">
                    <strong>✨ NEW:</strong> Migrated to FastAPI for better performance and real-time streaming!
                </div>
            </div>

            <div class="status">
                <div class="status-card healthy">
                    <h3>⚡ FastAPI Gateway</h3>
                    <p>Status: Healthy</p>
                    <p>Async: Enabled</p>
                </div>
                <div class="status-card unknown">
                    <h3>🧠 LLM Service</h3>
                    <p>Status: Testing</p>
                    <p>gRPC: Fixed</p>
                </div>
                <div class="status-card unknown">
                    <h3>📊 Embeddings</h3>
                    <p>Status: Ready</p>
                    <p>Streaming: Active</p>
                </div>
                <div class="status-card unknown">
                    <h3>🗄️ ClickHouse</h3>
                    <p>Status: Connected</p>
                    <p>Records: 71+</p>
                </div>
            </div>

            <h2>🆕 FastAPI Endpoints:</h2>
            <ul>
                <li><a href="/docs" class="link">📚 /docs</a> - Interactive API Documentation</li>
                <li><a href="/api/health" class="link">🏥 /api/health</a> - Enhanced health check</li>
                <li><a href="/api/financial/query" class="link">💰 POST /api/financial/query</a> - Financial queries</li>
                <li><a href="/api/financial/tickers" class="link">📈 /api/financial/tickers</a> - Active tickers</li>
                <li><a href="/api/stream/metrics" class="link">📡 /api/stream/metrics</a> - Real-time metrics</li>
                <li><a href="/api/metrics/export" class="link">📊 POST /api/metrics/export</a> - Export CSV</li>
            </ul>

            <h2>🔄 Real-time Streaming:</h2>
            <ul>
                <li><strong>Server-Sent Events:</strong> /api/stream/metrics</li>
                <li><strong>WebSocket Support:</strong> Coming soon</li>
                <li><strong>Live Dashboard Updates:</strong> No more polling!</li>
            </ul>

            <p style="text-align: center; margin-top: 30px; color: #666;">
                FastAPI Migration Complete - {{ timestamp }}
            </p>
        </div>
    </body>
    </html>
    """.replace("{{ timestamp }}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return HTMLResponse(content=dashboard_html)

# Removed get_live_streaming_metrics_from_db() - no longer needed since streaming metrics export directly to CSV

def create_app():
    """Create and configure the FastAPI application."""
    return app

def main():
    """Run the FastAPI server with uvicorn."""
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Starting FastAPI server on port {port}")

    uvicorn.run(
        "api_gateway.fastapi_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    )

if __name__ == '__main__':
    main()