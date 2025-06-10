"""
LLM Client for the RAG Gateway.

This module provides a client for communicating with the LLM service.
"""

from __future__ import annotations
import logging
import grpc
from api_gateway.proto import rag_service_pb2 as pb2  # type: ignore
from api_gateway.proto import rag_service_pb2_grpc as pb2_grpc  # type: ignore

logger = logging.getLogger(__name__)

class LLMClient:
    """gRPC client wrapper for the LLM micro-service."""

    def __init__(self, host: str = "localhost", port: int = 50054) -> None:
        self.address = f"{host}:{port}"
        self.channel: grpc.Channel | None = None
        self.stub: pb2_grpc.RAGServiceStub | None = None
        logger.info(f"Initialized LLM client for {self.address}")

    def __enter__(self):
        logger.info(f"Opening gRPC channel to {self.address}")
        self.channel = grpc.insecure_channel(self.address)
        self.stub = pb2_grpc.RAGServiceStub(self.channel)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.channel:
            logger.info("Closing gRPC channel")
            self.channel.close()

    def query(self, query_text: str, model_name: str = "meta-llama/Llama-3.2-1B-Instruct", top_k: int = 5, temperature: float = 0.7, max_tokens: int = 1000):
        """Send a query to the LLM service."""
        if not self.stub:
            logger.error("LLMClient not initialized (use with-statement)")
            raise RuntimeError("LLMClient not initialised (use with-statement)")

        logger.info(f"Sending query to LLM service: model={model_name}, temp={temperature}, max_tokens={max_tokens}, top_k={top_k}")

        request = pb2.QueryRequest(
            query=query_text,
            model_name=model_name,
            top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens
        )

        try:
            logger.info("Making gRPC call to LLM service")
            response = self.stub.Query(request)
            logger.info("Received response from LLM service")
            return response
        except grpc.RpcError as e:
            logger.error(f"gRPC error: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise