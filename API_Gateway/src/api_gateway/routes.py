"""
API Routes for the RAG Gateway.

This module defines REST endpoints that proxy requests to the gRPC microservices.
"""

from flask import Blueprint, request, jsonify  # type: ignore[import-not-found]
from .clients import LLMClient, EmbeddingsClient, IngestionClient
from .metrics import metrics_collector
from .grpc import rag_service_pb2_grpc as pb2_grpc
import logging
import time
import grpc
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Create blueprint for API routes
api = Blueprint('api', __name__)

@api.route('/query', methods=['POST'])
def query():
    """
    Process a query through the RAG pipeline.

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
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Query field is required"}), 400

        # Get parameters with defaults
        query_text = data['query']
        model_name = data.get('model_name', os.getenv("DEFAULT_LLM_MODEL", "google/flan-t5-small"))
        top_k = data.get('top_k', int(os.getenv("DEFAULT_TOP_K", "5")))
        temperature = data.get('temperature', float(os.getenv("DEFAULT_TEMPERATURE", "0.7")))
        max_tokens = data.get('max_tokens', int(os.getenv("DEFAULT_MAX_TOKENS", "200")))

        logger.info(f"Processing query: {query_text}")

        # Use the LLM client to process the query
        with LLMClient() as client:
            response = client.query(
                query_text=query_text,
                model_name=model_name,
                top_k=top_k,
                temperature=temperature,
                max_tokens=max_tokens
            )

            total_time = time.time() - start_time

            # Record metrics
            metrics_collector.record_query(
                query=query_text,
                response=response.answer,
                vector_latency=response.metrics.vector_latency,
                llm_latency=response.metrics.llm_latency,
                total_time=total_time,
                tokens_used=response.metrics.tokens_used,
                vector_store_type="unknown",  # Not available in response
                status="success"
            )

            # Convert gRPC response to JSON
            result = {
                "response": response.answer,
                "metrics": {
                    "vector_latency": response.metrics.vector_latency,
                    "llm_latency": response.metrics.llm_latency,
                    "total_time": total_time,
                    "tokens_used": response.metrics.tokens_used,
                    "model_name": response.metrics.model_name
                }
            }

            return jsonify(result), 200

    except Exception as e:
        total_time = time.time() - start_time
        error_msg = str(e)
        logger.error(f"Error processing query: {error_msg}")

        # Record error metrics
        metrics_collector.record_query(
            query=query_text if 'query_text' in locals() else "unknown",
            response="",
            vector_latency=0,
            llm_latency=0,
            total_time=total_time,
            tokens_used=0,
            vector_store_type="unknown",
            status="error",
            error=error_msg
        )

        return jsonify({"error": error_msg}), 500

@api.route('/metrics/export', methods=['GET'])
def export_metrics():
    """Export collected metrics to a file."""
    try:
        format = request.args.get('format', 'csv')
        filepath = metrics_collector.export_metrics(format)
        return jsonify({
            "status": "success",
            "filepath": filepath
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/metrics/summary', methods=['GET'])
def metrics_summary():
    """Get a summary of collected metrics."""
    try:
        summary = metrics_collector.get_metrics_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/ingest', methods=['POST'])
def ingest():
    """
    Ingest documents into the RAG system.

    Expected JSON body:
    {
        "document_urls": ["url1", "url2", ...],
        "processing_options": {
            "chunk_size": 512,
            "chunk_strategy": "sliding_window"
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'document_urls' not in data:
            return jsonify({"error": "document_urls field is required"}), 400

        # Use the Ingestion client
        with IngestionClient() as client:
            # Note: This would need to be implemented in the ingestion client
            # For now, return a placeholder
            return jsonify({
                "status": "Not implemented yet",
                "message": "Ingestion endpoint needs to be connected to the ingestion service"
            }), 501

    except Exception as e:
        logger.error(f"Error during ingestion: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

def register_routes(app):
    """Register all API routes with the Flask application."""
    app.register_blueprint(api, url_prefix='/api')