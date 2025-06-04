"""
Main service module for the Embeddings service.

This module handles the gRPC server and service implementation.
"""

import logging
import time
import grpc
from concurrent import futures
from typing import List, Dict, Any

from . import embeddings_pb2
from . import embeddings_pb2_grpc
from .database import ClickHouseDatabase
from .embeddings import get_embeddings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddingsService(embeddings_pb2_grpc.EmbeddingsServiceServicer):
    """gRPC service for handling embedding operations."""

    def __init__(self):
        """Initialize the service with database connection."""
        logger.info("Initializing Embeddings service")
        self.db = ClickHouseDatabase()
        logger.info("Successfully initialized database connection")

    def GetEmbeddings(self, request, context):
        """Handle GetEmbeddings gRPC request."""
        logger.info(f"Received GetEmbeddings request for text: {request.text[:100]}...")
        start_time = time.time()

        try:
            # Generate embeddings
            embeddings = get_embeddings(request.text)
            logger.info(f"Generated embeddings of dimension: {len(embeddings)}")

            # Create response
            response = embeddings_pb2.EmbeddingsResponse(
                embeddings=embeddings
            )

            duration = time.time() - start_time
            logger.info(f"Successfully processed GetEmbeddings request in {duration:.2f}s")
            return response

        except Exception as e:
            logger.error(f"Error processing GetEmbeddings request: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return embeddings_pb2.EmbeddingsResponse()

    def StoreEmbeddings(self, request, context):
        """Handle StoreEmbeddings gRPC request."""
        logger.info(f"Received StoreEmbeddings request for ID: {request.id}")
        start_time = time.time()

        try:
            # Store in database
            self.db.insert_vector(
                id=request.id,
                text=request.text,
                embedding=request.embeddings,
                metadata=request.metadata
            )

            duration = time.time() - start_time
            logger.info(f"Successfully stored embeddings for ID {request.id} in {duration:.2f}s")
            return embeddings_pb2.StoreResponse(success=True)

        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return embeddings_pb2.StoreResponse(success=False)

    def SearchSimilar(self, request, context):
        """Handle SearchSimilar gRPC request."""
        logger.info(f"Received SearchSimilar request with limit: {request.limit}")
        start_time = time.time()

        try:
            # Search database
            results = self.db.search_vectors(
                query_embedding=request.embeddings,
                limit=request.limit
            )

            # Convert results to response format
            response = embeddings_pb2.SearchResponse(
                results=[
                    embeddings_pb2.SearchResult(
                        id=row[0],
                        text=row[1],
                        metadata=row[2],
                        similarity=1.0 - row[3]  # Convert distance to similarity
                    )
                    for row in results
                ]
            )

            duration = time.time() - start_time
            logger.info(f"Found {len(results)} similar vectors in {duration:.2f}s")
            return response

        except Exception as e:
            logger.error(f"Error searching similar vectors: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return embeddings_pb2.SearchResponse()

def serve():
    """Start the gRPC server."""
    logger.info("Starting Embeddings gRPC server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    embeddings_pb2_grpc.add_EmbeddingsServiceServicer_to_server(
        EmbeddingsService(), server
    )
    port = 50051
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"Server started on port {port}")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()