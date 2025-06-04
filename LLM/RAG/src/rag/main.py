"""
Main module for the LLM service.

This module provides the gRPC server implementation for the LLM service.
"""

import grpc
import logging
import time
from concurrent import futures
from .query import process_query
from .proto import rag_service_pb2_grpc as rag_service_pb2_grpc
from .proto import rag_service_pb2 as rag_service_pb2

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGServiceServicer(rag_service_pb2_grpc.RAGServiceServicer):
    """gRPC server implementation for the RAG service."""

    def Query(self, request, context):
        """Handle query requests from the API Gateway."""
        start_time = time.time()
        logger.info(f"Received query request: {request.query[:100]}...")  # Log first 100 chars

        try:
            # Get parameters from request
            model_name = request.model_name if request.model_name else None
            temperature = request.temperature if request.temperature else 0.7
            max_tokens = request.max_tokens if request.max_tokens else 200

            logger.info(f"Processing with model: {model_name}, temperature: {temperature}, max_tokens: {max_tokens}")

            # Process query using query module
            logger.info("Starting query processing...")
            response_text, metrics = process_query(
                user_query=request.query,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info("Query processing completed")

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
            logger.info(f"Request completed in {total_time:.2f} seconds")
            return response

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return rag_service_pb2.QueryResponse()

def serve():
    """Start the gRPC server."""
    logger.info("Starting LLM service...")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rag_service_pb2_grpc.add_RAGServiceServicer_to_server(
        RAGServiceServicer(), server
    )
    port = 50054
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"LLM service started on port {port}")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()