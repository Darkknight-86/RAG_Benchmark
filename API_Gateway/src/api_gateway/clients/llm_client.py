"""
LLM Client for the RAG Gateway.

This module provides a client for communicating with the LLM service.
"""

from __future__ import annotations

import grpc
from api_gateway.grpc import rag_service_pb2 as pb2  # type: ignore
from api_gateway.grpc import rag_service_pb2_grpc as pb2_grpc  # type: ignore

class LLMClient:
    """gRPC client wrapper for the LLM micro-service."""

    def __init__(self, host: str = "llm", port: int = 50054) -> None:
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

    def query(self, query_text: str, model_name: str = "google/flan-t5-small", top_k: int = 5, temperature: float = 0.7, max_tokens: int = 200):
        if not self.stub:
            raise RuntimeError("LLMClient not initialised (use with-statement)")
        request = pb2.QueryRequest(
            query=query_text,
            model_name=model_name,
            top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens
        )
        response = self.stub.Query(request)
        return response