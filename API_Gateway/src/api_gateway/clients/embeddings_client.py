from __future__ import annotations

import grpc

# Use RAG service interface for embeddings queries (NOT for document ingestion)
from api_gateway.proto import rag_service_pb2 as pb2
from api_gateway.proto import rag_service_pb2_grpc as pb2_grpc


class EmbeddingsClient:
    """gRPC client wrapper for the Embeddings micro-service (Query + Benchmark only)."""

    def __init__(self, host: str = "localhost", port: int = 50051) -> None:
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

    def query(self, query: str, top_k: int = 5, temperature: float = 0.7, max_tokens: int = 200):
        """Send RAG query to embeddings service for vector search."""
        if not self.stub:
            raise RuntimeError("EmbeddingsClient not initialised (use with-statement)")
        request = pb2.QueryRequest(
            query=query,
            top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return self.stub.Query(request)

    def benchmark(self, test_queries: list[str]):
        """Run benchmark tests on embeddings service."""
        if not self.stub:
            raise RuntimeError("EmbeddingsClient not initialised (use with-statement)")
        request = pb2.BenchmarkRequest(test_queries=test_queries)
        return self.stub.Benchmark(request)