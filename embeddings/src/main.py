"""
Main gRPC service for the Embeddings microservice.

This service provides:
- On-demand embedding generation for API Gateway
- Vector storage and retrieval
- Metrics collection for monitoring
- Health checks

Runs alongside streaming.py for complete functionality.
Uses HuggingFaceEmbeddings consistently with streaming service.
"""

import os
# Fix protobuf compatibility issues
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Import global warning suppression for production
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
import warnings_suppression

import logging
import time
import grpc
from concurrent import futures
from typing import List, Dict, Any
import os

# Add proto directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'proto'))

# Use RAGService interface (Query + Benchmark, NOT IngestDocuments)
# Local protobuf files for RAG service interface
import rag_service_pb2
import rag_service_pb2_grpc

# Import service components (modular architecture)
from database import Database
from config import config
from langchain_community.embeddings import HuggingFaceEmbeddings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddingsRAGService(rag_service_pb2_grpc.RAGServiceServicer):
    """RAG service implementation for embeddings and queries (NOT document ingestion)."""

    def __init__(self):
        """Initialize the service with modular database connection."""
        logger.info("Initializing Embeddings RAG service")
        try:
            # Use modular database that can swap adapters via environment variable
            self.db = Database()  # Defaults to ClickHouse, can be changed via VECTOR_DB_ADAPTER env var
            logger.info(f"Successfully initialized database connection with {self.db.primary_adapter_type} adapter")

            # Initialize embeddings using same approach as streaming (consistent!)
            main_config = config.get_main_config()
            self.embedder = HuggingFaceEmbeddings(model_name=main_config["embedding_model"])
            logger.info(f"Initialized embedding model: {main_config['embedding_model']}")

        except Exception as e:
            logger.error(f"Failed to initialize service: {str(e)}")
            raise

    def Query(self, request, context):
        """Handle RAG Query requests - search vectors and return relevant results."""
        logger.info(f"Received Query request: {request.query[:100]}...")
        start_time = time.time()

        try:
            # Generate embeddings for the query (consistent with streaming service)
            query_embeddings = self.embedder.embed_query(request.query)
            logger.info(f"Generated query embeddings of dimension: {len(query_embeddings)}")

            # Search for similar vectors in database
            top_k = request.top_k if request.top_k > 0 else 5
            results = self.db.search_vectors(
                query_embedding=query_embeddings,
                limit=top_k
            )

            # Convert results to protobuf format
            sources = []
            for row in results:
                source = rag_service_pb2.Source(
                    content=str(row[1]),  # text content
                    score=1.0 - float(row[3]),  # Convert distance to similarity score
                    metadata={
                        "id": str(row[0]),
                        "source": "financial_streaming"
                    }
                )
                sources.append(source)

            # Create metrics
            duration = time.time() - start_time
            metrics = rag_service_pb2.Metrics(
                vector_latency=duration,
                llm_latency=0.0,  # No LLM processing in embeddings service
                total_time=duration,
                tokens_used=0,  # No tokens used for vector search
                model_name=self.embedder.model_name
            )

            # Create response (embeddings service provides vectors, LLM service provides final answer)
            response = rag_service_pb2.QueryResponse(
                answer=f"Found {len(sources)} relevant financial data points. Processing by LLM service required for final answer.",
                sources=sources,
                metrics=metrics
            )

            logger.info(f"Successfully processed Query in {duration:.2f}s, found {len(sources)} results")
            return response

        except Exception as e:
            logger.error(f"Error processing Query request: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to process query: {str(e)}")
            return rag_service_pb2.QueryResponse(
                answer="Error processing query",
                sources=[],
                metrics=rag_service_pb2.Metrics()
            )

    def Benchmark(self, request, context):
        """Handle Benchmark requests - performance testing of vector operations."""
        logger.info(f"Received Benchmark request with {len(request.test_queries)} test queries")
        start_time = time.time()

        try:
            results = []
            total_latency = 0.0
            successful_queries = 0

            # Process each test query
            for i, test_query in enumerate(request.test_queries):
                query_start = time.time()

                try:
                    # Generate embeddings and search (consistent with streaming service)
                    query_embeddings = self.embedder.embed_query(test_query)
                    search_results = self.db.search_vectors(
                        query_embedding=query_embeddings,
                        limit=5
                    )

                    query_latency = time.time() - query_start
                    total_latency += query_latency
                    successful_queries += 1

                    # Create benchmark result
                    benchmark_result = rag_service_pb2.BenchmarkResult(
                        query=test_query,
                        config=rag_service_pb2.BenchmarkConfig(
                            model=self.embedder.model_name,
                            retrieval_options=rag_service_pb2.RetrievalOptions(top_k=5),
                            llm_options=rag_service_pb2.LLMOptions(model="none")
                        ),
                        result=rag_service_pb2.QueryResponse(
                            answer=f"Benchmark query {i+1}",
                            sources=[],
                            metrics=rag_service_pb2.Metrics(
                                vector_latency=query_latency,
                                total_time=query_latency
                            )
                        ),
                        latency=query_latency,
                        timestamp=str(int(time.time()))
                    )
                    results.append(benchmark_result)

                except Exception as e:
                    logger.error(f"Benchmark query {i+1} failed: {str(e)}")

            # Calculate summary
            average_latency = total_latency / successful_queries if successful_queries > 0 else 0.0
            success_rate = successful_queries / len(request.test_queries) if request.test_queries else 0.0

            summary = rag_service_pb2.BenchmarkSummary(
                average_latency=average_latency,
                success_rate=success_rate,
                metrics={
                    "total_queries": float(len(request.test_queries)),
                    "successful_queries": float(successful_queries),
                    "failed_queries": float(len(request.test_queries) - successful_queries)
                }
            )

            response = rag_service_pb2.BenchmarkResponse(
                benchmark_id=f"embedding_benchmark_{int(time.time())}",
                results=results,
                summary=summary
            )

            duration = time.time() - start_time
            logger.info(f"Completed benchmark in {duration:.2f}s: {successful_queries}/{len(request.test_queries)} successful")
            return response

        except Exception as e:
            logger.error(f"Error processing Benchmark request: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to process benchmark: {str(e)}")
            return rag_service_pb2.BenchmarkResponse()

def serve():
    """Start the gRPC server."""
    logger.info("Starting Embeddings RAG gRPC server")

    # Create server with thread pool
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add RAG service implementation (Query + Benchmark, NOT IngestDocuments)
    rag_service_pb2_grpc.add_RAGServiceServicer_to_server(
        EmbeddingsRAGService(), server
    )

    # Configure port (50051 for embeddings service)
    port = 50051
    server.add_insecure_port(f'[::]:{port}')

    # Start server
    server.start()
    logger.info(f"🚀 Embeddings RAG gRPC server started on port {port}")
    logger.info("📊 Ready to serve Query and Benchmark requests from API Gateway")
    logger.info("🔄 Live streaming service should run separately via streaming.py")
    logger.info("📥 IngestDocuments handled by separate Ingestion microservice")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        server.stop(0)

if __name__ == '__main__':
    serve()