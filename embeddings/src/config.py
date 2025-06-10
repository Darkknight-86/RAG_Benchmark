"""
Configuration module for the Embeddings service.

Handles database adapter selection and configuration for both:
- streaming.py (live financial data streaming)
- main.py (gRPC service for API Gateway)

Supports multiple databases simultaneously if configured.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class EmbeddingsConfig:
    """Configuration for the Embeddings service."""

    def __init__(self):
        """Initialize configuration from environment variables."""

        # Streaming service database configuration
        self.streaming_adapters = self._parse_adapter_list(
            os.getenv("STREAMING_DB_ADAPTERS", "clickhouse")
        )

        # Main gRPC service database configuration (can be different from streaming)
        self.main_adapters = self._parse_adapter_list(
            os.getenv("MAIN_DB_ADAPTERS", "clickhouse")
        )

        # Available adapter types
        self.available_adapters = ["clickhouse", "cassandra", "postgres", "opensearch"]

        # Embedding model configuration
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

        # Streaming configuration
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

        # gRPC service configuration
        self.grpc_port = int(os.getenv("EMBEDDINGS_GRPC_PORT", "50051"))

        # Validate configuration
        self._validate_config()

    def _parse_adapter_list(self, adapter_string: str) -> List[str]:
        """Parse comma-separated adapter list from environment variable."""
        adapters = [adapter.strip().lower() for adapter in adapter_string.split(",")]
        return [adapter for adapter in adapters if adapter]

    def _validate_config(self):
        """Validate configuration settings."""
        # Check streaming adapters
        for adapter in self.streaming_adapters:
            if adapter not in self.available_adapters:
                raise ValueError(f"Invalid streaming adapter: {adapter}. Available: {self.available_adapters}")

        # Check main service adapters
        for adapter in self.main_adapters:
            if adapter not in self.available_adapters:
                raise ValueError(f"Invalid main service adapter: {adapter}. Available: {self.available_adapters}")

        logger.info(f"Configuration validated:")
        logger.info(f"  Streaming adapters: {self.streaming_adapters}")
        logger.info(f"  Main service adapters: {self.main_adapters}")
        logger.info(f"  Embedding model: {self.embedding_model}")

    def get_streaming_config(self) -> Dict[str, Any]:
        """Get configuration for streaming service."""
        return {
            "adapters": self.streaming_adapters,
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }

    def get_main_config(self) -> Dict[str, Any]:
        """Get configuration for main gRPC service."""
        return {
            "adapters": self.main_adapters,
            "embedding_model": self.embedding_model,
            "grpc_port": self.grpc_port
        }

    def supports_multi_database(self) -> bool:
        """Check if multiple databases are configured."""
        return len(self.streaming_adapters) > 1 or len(self.main_adapters) > 1

# Global configuration instance
config = EmbeddingsConfig()

# Example usage configurations:
"""
# Single database (current setup):
STREAMING_DB_ADAPTERS=clickhouse
MAIN_DB_ADAPTERS=clickhouse

# Different databases for streaming vs main:
STREAMING_DB_ADAPTERS=clickhouse
MAIN_DB_ADAPTERS=postgres

# Multiple databases for streaming (write to all):
STREAMING_DB_ADAPTERS=clickhouse,postgres,opensearch
MAIN_DB_ADAPTERS=clickhouse

# Multiple databases for both (maximum flexibility):
STREAMING_DB_ADAPTERS=clickhouse,postgres
MAIN_DB_ADAPTERS=clickhouse,cassandra,opensearch
"""