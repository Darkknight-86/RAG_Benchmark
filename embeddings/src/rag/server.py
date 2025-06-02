import asyncio
import logging
from concurrent import futures

import grpc
import sys, os

from rag_service_pb2 import IngestResponse  # generated at build time
import rag_service_pb2_grpc as pb2_grpc

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("embeddings.server")


class EmbeddingsServicer(pb2_grpc.RAGServiceServicer):
    """Implements only IngestDocuments RPC for MVP."""

    async def IngestDocuments(self, request, context):  # type: ignore[override]
        url_count = len(request.document_urls)
        LOGGER.info("Received ingest request for %s urls", url_count)

        # Simulate success (real logic would call chunker + embedder)
        return IngestResponse(job_id="placeholder", vectors_created=0, status="QUEUED")


async def serve() -> None:
    server = grpc.aio.server()
    pb2_grpc.add_RAGServiceServicer_to_server(EmbeddingsServicer(), server)
    server.add_insecure_port("[::]:50052")

    await server.start()
    LOGGER.info("Embeddings gRPC server started on :50052")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())