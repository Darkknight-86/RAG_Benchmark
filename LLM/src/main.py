"""
Main module for the LLM service.

This module provides the gRPC server implementation for the LLM service with RAG pipeline.
"""

# Import global warning suppression for production
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
import warnings_suppression

import grpc
import asyncio
import logging
import time
from concurrent import futures
from rag_pipeline import RAGPipeline
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'proto'))
import rag_service_pb2_grpc
import rag_service_pb2

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global RAG pipeline instance
rag_pipeline = None

def initialize_rag_pipeline():
    """Initialize the RAG pipeline on startup"""
    global rag_pipeline
    try:
        logger.info("🚀 Initializing RAG Pipeline...")
        rag_pipeline = RAGPipeline()
        logger.info("✅ RAG Pipeline initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG Pipeline: {e}")
        return False

class RAGServiceServicer(rag_service_pb2_grpc.RAGServiceServicer):
    """gRPC server implementation for the RAG service."""

    def Query(self, request, context):
        """Handle query requests from the API Gateway."""
        start_time = time.time()
        logger.info(f"📩 Received query: {request.query[:100]}...")

        try:
            # Check if RAG pipeline is available
            if not rag_pipeline:
                logger.error("RAG pipeline not initialized")
                context.set_details("RAG pipeline not available")
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                return rag_service_pb2.QueryResponse()

            # Get parameters from request
            model_name = request.model_name if request.model_name else None
            temperature = request.temperature if request.temperature else 0.7
            max_tokens = request.max_tokens if request.max_tokens else 200
            top_k = request.top_k if hasattr(request, 'top_k') and request.top_k else 5

            logger.info(f"🔧 Processing with model: {model_name}, temp: {temperature}, tokens: {max_tokens}")

            # Process query using RAG pipeline (run async in thread)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    rag_pipeline.query(
                        query=request.query,
                        top_k=top_k,
                        model_name=model_name,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                )
            finally:
                loop.close()

            # Build response
            response = rag_service_pb2.QueryResponse()
            response.answer = result["answer"]

            # Add metrics
            metrics = result["metrics"]
            response.metrics.vector_latency = metrics["vector_latency"]
            response.metrics.llm_latency = metrics["llm_latency"]
            response.metrics.total_time = metrics["total_time"]
            response.metrics.tokens_used = metrics["tokens_used"]
            response.metrics.model_name = metrics["model_name"]

            # Add sources if available
            if result.get("sources"):
                for source in result["sources"][:3]:  # Limit to top 3 sources
                    source_info = response.sources.add()
                    source_info.content = source["content"]
                    source_info.score = source["score"]
                    if "metadata" in source:
                        for key, value in source["metadata"].items():
                            source_info.metadata[key] = str(value)

            total_time = time.time() - start_time
            logger.info(f"✅ Request completed in {total_time:.3f}s")
            return response

        except Exception as e:
            logger.error(f"❌ Error processing query: {str(e)}", exc_info=True)
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return rag_service_pb2.QueryResponse()

    def GetHealth(self, request, context):
        """Health check endpoint."""
        try:
            if rag_pipeline:
                health_status = rag_pipeline.get_health_status()
                response = rag_service_pb2.HealthResponse()
                response.status = health_status["overall"]
                response.vector_store_status = health_status["vector_store"]
                response.llm_status = health_status["llm_manager"]
                return response
            else:
                context.set_details("RAG pipeline not initialized")
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                return rag_service_pb2.HealthResponse()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return rag_service_pb2.HealthResponse()

def serve():
    """Start the gRPC server."""
    logger.info("🚀 Starting LLM service...")

    # Initialize RAG pipeline
    if not initialize_rag_pipeline():
        logger.error("❌ Failed to start service - RAG pipeline initialization failed")
        return

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rag_service_pb2_grpc.add_RAGServiceServicer_to_server(
        RAGServiceServicer(), server
    )
    port = 50054
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"🌟 LLM service started on port {port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down LLM service...")
        server.stop(0)

if __name__ == '__main__':
    serve()