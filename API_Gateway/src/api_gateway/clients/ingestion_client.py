from __future__ import annotations

import grpc
from api_gateway.proto import rag_service_pb2 as pb2  # type: ignore
from api_gateway.proto import rag_service_pb2_grpc as pb2_grpc  # type: ignore


class IngestionClient:
    """gRPC client wrapper for the Ingestion micro-service."""

    def __init__(self, host: str = "ingestion", port: int = 50053) -> None:
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

    def ingest_documents(self, document_urls: list[str]):
        if not self.stub:
            raise RuntimeError("IngestionClient not initialised (use with-statement)")
        request = pb2.IngestRequest(document_urls=document_urls)
        return self.stub.IngestDocuments(request)