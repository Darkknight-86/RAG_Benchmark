"""
LLM Service - Main server module for the LLM service.

This module sets up and runs the LLM service, handling query requests from the API Gateway.
"""

import grpc
from concurrent import futures
import time
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag import query
from rag.llm_manager import llm_manager

# Import generated gRPC code
from rag.proto import rag_service_pb2
from rag.proto import rag_service_pb2_grpc

class RAGServiceServicer(rag_service_pb2_grpc.RAGServiceServicer):
    def Query(self, request, context):
        """Handle query requests from the API Gateway."""
        start_time = time.time()
        logger.info(f"[LLM] Received query: {request.query}")
        try:
            # Get parameters from request
            model_name = request.model_name if request.model_name else None
            temperature = request.temperature if request.temperature else 0.7
            max_tokens = request.max_tokens if request.max_tokens else 200

            logger.info(f"[LLM] Processing with model: {model_name}, temperature: {temperature}, max_tokens: {max_tokens}")

            # Process query using query module
            logger.info("[LLM] Starting query processing...")
            response_text, metrics = query.process_query(
                user_query=request.query,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info("[LLM] Query processing completed")

            # Build response
            response = rag_service_pb2.QueryResponse()
            response.answer = response_text

            # Add metrics
            response.metrics.vector_latency = metrics["vector_latency"]
            response.metrics.llm_latency = metrics["llm_latency"]
            response.metrics.total_time = metrics["total_time"]
            response.metrics.tokens_used = metrics["tokens_used"]
            response.metrics.model_name = metrics["model_name"]

            total_time = time.time() - start_time
            logger.info(f"[LLM] Request completed in {total_time:.2f} seconds")
            return response

        except Exception as e:
            logger.error(f"[LLM] Error processing query: {str(e)}", exc_info=True)
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return rag_service_pb2.QueryResponse()

def serve():
    """Start the gRPC server."""
    logger.info("[LLM] Starting gRPC server...")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rag_service_pb2_grpc.add_RAGServiceServicer_to_server(RAGServiceServicer(), server)
    port = 50054
    server.add_insecure_port(f'[::]:{port}')
    logger.info(f"[LLM] gRPC server started on port {port}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()