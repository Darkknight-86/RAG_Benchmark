from __future__ import annotations

import grpc

# Generated stubs will be located in api_gateway.grpc package after generate_grpc.py runs
from api_gateway.grpc import rag_service_pb2 as pb2  # type: ignore
from api_gateway.grpc import rag_service_pb2_grpc as pb2_grpc  # type: ignore


class EmbeddingsClient:
    """gRPC client wrapper for the Embeddings micro-service."""

    def __init__(self, host: str = "embeddings", port: int = 50052) -> None:
        self.address = f"{host}:{port}"
        self.channel: grpc.Channel | None = None
        self.stub: pb2_grpc.RAGServiceStub | None = None

    def __enter__(self):
        self.channel = grpc.insecure_channel(self.address)
        self.stub = pb2_grpc.RAGServiceStub(self.channel)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.channel:
            self.channel.close()

    # Example call – adjust once service implements real RPCs
    def ingest_documents(self, document_urls: list[str]):
        if not self.stub:
            raise RuntimeError("EmbeddingsClient not initialised (use with-statement)")
        request = pb2.IngestRequest(document_urls=document_urls)
        return self.stub.IngestDocuments(request)