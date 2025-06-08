"""
API Routes for the Financial RAG Gateway.

This module defines REST endpoints that proxy requests to the gRPC microservices,
enhanced monitoring capabilities, and financial query routing.
"""

from flask import Blueprint, request, jsonify, render_template_string  # type: ignore[import-not-found]
from flask_socketio import SocketIO, emit  # type: ignore[import-not-found]
import asyncio
import json
import time
import logging
import grpc
import os
from datetime import datetime
from dotenv import load_dotenv

# Import clients (required)
from .clients import LLMClient, EmbeddingsClient

# Import optional monitoring
try:
    from .metrics import metrics_collector
except ImportError:
    print("Warning: Basic metrics module not found")
    metrics_collector = None

# Import optional grpc pb2
try:
    from .proto import rag_service_pb2_grpc as pb2_grpc
except ImportError:
    print("Warning: gRPC pb2 module not found")
    pb2_grpc = None

# Import enhanced metrics
try:
    from ..monitoring.enhanced_metrics import metrics_collector as enhanced_metrics
except ImportError:
    print("Warning: Enhanced metrics not found, using basic metrics")
    enhanced_metrics = None

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint for API routes
api = Blueprint('api', __name__)

# Enhanced Query Endpoints
@api.route('/query', methods=['POST'])
def query():
    """
    Process a query through the RAG pipeline with enhanced monitoring.

    Expected JSON body:
    {
        "query": "Your question here",
        "model_name": "google/flan-t5-small",  # optional
        "top_k": 5,              # optional
        "temperature": 0.7,      # optional
        "max_tokens": 200        # optional
    }
    """
    start_time = time.time()
    logger.info("📩 Received query request")

    try:
        data = request.get_json()
        if not data or 'query' not in data:
            logger.error("❌ Missing query field in request")
            return jsonify({"error": "Query field is required"}), 400

        # Get parameters with defaults
        query_text = data['query']
        model_name = data.get('model_name', os.getenv("DEFAULT_LLM_MODEL", "google/flan-t5-small"))
        top_k = data.get('top_k', int(os.getenv("DEFAULT_TOP_K", "5")))
        temperature = data.get('temperature', float(os.getenv("DEFAULT_TEMPERATURE", "0.7")))
        max_tokens = data.get('max_tokens', int(os.getenv("DEFAULT_MAX_TOKENS", "200")))

        logger.info(f"🔧 Processing query: model={model_name}, temp={temperature}, tokens={max_tokens}")

        # Record initial metrics
        if enhanced_metrics:
            enhanced_metrics.record_metric("api_gateway", "query_received", 1.0,
                                          model=model_name, query_length=len(query_text))

        # Use the LLM client to process the query
        logger.info("🧠 Sending to LLM service...")
        with LLMClient() as client:
            response = client.query(
                query_text=query_text,
                model_name=model_name,
                top_k=top_k,
                temperature=temperature,
                max_tokens=max_tokens
            )

            total_time = time.time() - start_time

            # Record enhanced metrics
            if enhanced_metrics:
                enhanced_metrics.record_query_metrics({
                    "vector_latency": response.metrics.vector_latency,
                    "llm_latency": response.metrics.llm_latency,
                    "total_time": total_time,
                    "tokens_used": response.metrics.tokens_used
                })

            # Convert gRPC response to JSON
            result = {
                "response": response.answer,
                "sources": [{"content": source.content, "score": source.score}
                           for source in response.sources] if hasattr(response, 'sources') else [],
                "metrics": {
                    "vector_latency": response.metrics.vector_latency,
                    "llm_latency": response.metrics.llm_latency,
                    "total_time": total_time,
                    "tokens_used": response.metrics.tokens_used,
                    "model_name": response.metrics.model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_k": top_k
                }
            }

            logger.info(f"✅ Query completed in {total_time:.3f}s")
            return jsonify(result), 200

    except Exception as e:
        logger.error(f"❌ Error processing query: {str(e)}", exc_info=True)
        if enhanced_metrics:
            enhanced_metrics.record_metric("api_gateway", "query_error", 1.0, error=str(e))
        return jsonify({"error": str(e)}), 500

@api.route('/financial/query', methods=['POST'])
def financial_query():
    """
    Process financial-specific queries with market data context.

    Expected JSON body:
    {
        "query": "What's the performance of AAPL?",
        "ticker": "AAPL",  # optional for ticker-specific queries
        "model_name": "google/flan-t5-small",  # optional
        "temperature": 0.7  # optional
    }
    """
    start_time = time.time()
    logger.info("💰 Received financial query")

    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Query field is required"}), 400

        query_text = data['query']
        ticker = data.get('ticker')
        model_name = data.get('model_name', "google/flan-t5-small")
        temperature = data.get('temperature', 0.7)

        logger.info(f"💼 Financial query for ticker: {ticker or 'general'}")

        # Record financial query metrics
        if enhanced_metrics:
            enhanced_metrics.record_metric("api_gateway", "financial_query_received", 1.0,
                                          ticker=ticker, query_type="financial")

        # Process through LLM with financial context
        with LLMClient() as client:
            response = client.query(
                query_text=query_text,
                model_name=model_name,
                temperature=temperature,
                max_tokens=300  # Longer responses for financial analysis
            )

            total_time = time.time() - start_time

            # Enhanced response for financial queries
            result = {
                "response": response.answer,
                "ticker": ticker,
                "query_type": "financial",
                "market_context": True,
                "sources": [{"content": source.content, "score": source.score}
                           for source in response.sources] if hasattr(response, 'sources') else [],
                "metrics": {
                    "vector_latency": response.metrics.vector_latency,
                    "llm_latency": response.metrics.llm_latency,
                    "total_time": total_time,
                    "tokens_used": response.metrics.tokens_used,
                    "model_name": response.metrics.model_name
                }
            }

            logger.info(f"✅ Financial query completed in {total_time:.3f}s")
            return jsonify(result), 200

    except Exception as e:
        logger.error(f"❌ Error processing financial query: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/financial/tickers', methods=['GET'])
def get_active_tickers():
    """Get list of currently active tickers in the system."""
    try:
        # This would query the ClickHouse database for active tickers
        # For now, return the demo tickers we know are working
        active_tickers = [
            {"ticker": "AMZN", "name": "Amazon.com Inc", "status": "active"},
            {"ticker": "COL.AX", "name": "Coles Group Limited", "status": "active"},
            {"ticker": "JBH.AX", "name": "JB Hi-Fi Limited", "status": "active"},
            {"ticker": "WOW.AX", "name": "Woolworths Group Limited", "status": "active"},
            {"ticker": "QAN.AX", "name": "Qantas Airways Limited", "status": "active"},
            {"ticker": "TLS.AX", "name": "Telstra Corporation Limited", "status": "active"},
            {"ticker": "GOOGL", "name": "Alphabet Inc", "status": "active"}
        ]

        return jsonify({
            "tickers": active_tickers,
            "count": len(active_tickers),
            "last_updated": datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error fetching tickers: {e}")
        return jsonify({"error": str(e)}), 500

# Enhanced Metrics Endpoints
@api.route('/metrics/current', methods=['GET'])
def get_current_metrics():
    """Get current real-time metrics."""
    try:
        if enhanced_metrics:
            metrics_data = enhanced_metrics.get_real_time_metrics()
            return jsonify(metrics_data), 200
        else:
            # Fallback to basic metrics
            return jsonify({"error": "Enhanced metrics not available"}), 503
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return jsonify({"error": str(e)}), 500

@api.route('/metrics/export', methods=['POST'])
def export_metrics():
    """Export collected metrics to CSV file."""
    try:
        data = request.get_json() or {}
        minutes = data.get('minutes', 5)

        if enhanced_metrics:
            filename = enhanced_metrics.export_metrics_csv(minutes=minutes)
            return jsonify({
                "status": "success",
                "filename": filename,
                "exported_timeframe": f"{minutes} minutes"
            }), 200
        else:
            return jsonify({"error": "Enhanced metrics not available"}), 503

    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        return jsonify({"error": str(e)}), 500

@api.route('/metrics/health', methods=['GET'])
def service_health():
    """Get health status of all services."""
    try:
        if enhanced_metrics:
            health_data = enhanced_metrics.get_service_health()
            return jsonify(health_data), 200
        else:
            return jsonify({"api_gateway": {"status": "healthy", "enhanced_metrics": False}}), 200

    except Exception as e:
        logger.error(f"Error checking service health: {e}")
        return jsonify({"error": str(e)}), 500

@api.route('/metrics/dashboard', methods=['GET'])
def metrics_dashboard():
    """Serve the metrics dashboard."""
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Financial RAG Monitoring</title>
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Financial RAG Microservices Dashboard</h1>
                <p>Real-time monitoring and metrics for streaming financial data</p>
            </div>

            <div class="status">
                <div class="status-card healthy">
                    <h3>🏥 API Gateway</h3>
                    <p>Status: Healthy</p>
                </div>
                <div class="status-card unknown">
                    <h3>🧠 LLM Service</h3>
                    <p>Status: Check /metrics/health</p>
                </div>
                <div class="status-card unknown">
                    <h3>📊 Embeddings</h3>
                    <p>Status: Check /metrics/health</p>
                </div>
                <div class="status-card unknown">
                    <h3>🗄️ ClickHouse</h3>
                    <p>Status: Check /metrics/health</p>
                </div>
            </div>

            <h2>📈 Available Endpoints:</h2>
            <ul>
                <li><a href="/api/query" class="link">POST /api/query</a> - RAG queries</li>
                <li><a href="/api/financial/query" class="link">POST /api/financial/query</a> - Financial queries</li>
                <li><a href="/api/financial/tickers" class="link">GET /api/financial/tickers</a> - Active tickers</li>
                <li><a href="/api/metrics/current" class="link">GET /api/metrics/current</a> - Real-time metrics</li>
                <li><a href="/api/metrics/health" class="link">GET /api/metrics/health</a> - Service health</li>
                <li><a href="/api/metrics/export" class="link">POST /api/metrics/export</a> - Export metrics CSV</li>
            </ul>

            <h2>🚀 Getting Started:</h2>
            <ol>
                <li>Start the embeddings service for financial data streaming</li>
                <li>Start the LLM service for RAG queries</li>
                <li>Use the Streamlit dashboard: <code>streamlit run src/dashboard/streamlit_dashboard.py</code></li>
                <li>Send queries to <code>/api/financial/query</code> for financial analysis</li>
            </ol>

            <p style="text-align: center; margin-top: 30px; color: #666;">
                Last updated: {{ timestamp }}
            </p>
        </div>
    </body>
    </html>
    """

    return render_template_string(dashboard_html, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Legacy endpoints for backward compatibility
@api.route('/metrics/summary', methods=['GET'])
def metrics_summary():
    """Get a summary of collected metrics (legacy endpoint)."""
    try:
        if enhanced_metrics:
            metrics_data = enhanced_metrics.get_real_time_metrics()
            return jsonify(metrics_data.get('summary', {})), 200
        else:
            return jsonify({"status": "Basic metrics only"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/ingest', methods=['POST'])
def ingest():
    """
    Ingest documents into the RAG system (deprecated - use streaming instead).
    """
    return jsonify({
        "status": "deprecated",
        "message": "Document ingestion has been replaced by real-time financial data streaming. Use the embeddings service directly."
    }), 410

@api.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    health_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "features": {
            "enhanced_metrics": enhanced_metrics is not None,
            "financial_queries": True,
            "real_time_monitoring": True
        }
    }
    return jsonify(health_info), 200

def register_routes(app):
    """Register all API routes with the Flask application."""
    app.register_blueprint(api, url_prefix='/api')

    # Add a root redirect to the dashboard
    @app.route('/')
    def root():
        return jsonify({
            "message": "Financial RAG API Gateway",
            "dashboard": "/api/metrics/dashboard",
            "health": "/api/health",
            "docs": "See /api/metrics/dashboard for available endpoints"
        }), 200