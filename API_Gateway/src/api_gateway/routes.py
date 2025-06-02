"""
API Routes for the RAG Gateway.

This module defines REST endpoints that proxy requests to the gRPC microservices.
"""

from flask import Blueprint, request, jsonify
from .clients import LLMClient, EmbeddingsClient, IngestionClient
import logging

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
        "top_k": 5  # optional, defaults to 5
    }
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Query field is required"}), 400

        query_text = data['query']
        top_k = data.get('top_k', 5)

        logger.info(f"Processing query: {query_text}")

        # Use the LLM client to process the query
        with LLMClient() as client:
            response = client.query(query_text, top_k)

            # Convert gRPC response to JSON
            result = {
                "response": response.response,
                "sources": [
                    {
                        "content": source.content,
                        "score": source.score,
                        "metadata": dict(source.metadata)
                    }
                    for source in response.sources
                ],
                "metadata": {
                    "latency": response.metadata.latency,
                    "tokens_used": response.metadata.tokens_used,
                    "additional": dict(response.metadata.additional_metadata)
                }
            }

            return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
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