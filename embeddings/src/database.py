"""
Database interface module for the Embeddings service.

Provides a unified interface that can work with any vector database adapter:
- ClickHouseAdapter (current production)
- CassandraAdapter (alternative)
- PostgresAdapter (alternative)
- OpenSearchAdapter (alternative)

This allows easy swapping between different vector databases.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from Adapters.ClickHouseAdapter import ClickHouseAdapter
# from Adapters.CassandraAdapter import CassandraAdapter  # Future option
# from Adapters.PostgresAdapter import PostgresAdapter    # Future option
# from Adapters.OpenSearchAdapter import OpenSearchAdapter # Future option

logger = logging.getLogger(__name__)

class MultiDatabase:
    """
    Multi-database interface that can work with multiple vector database adapters simultaneously.

    Supports writing to multiple databases and reading from primary or all databases.
    """

    def __init__(self, adapter_types: Union[str, List[str]] = "clickhouse"):
        """
        Initialize database with specified adapter(s).

        Args:
            adapter_types: Single adapter type or list of adapter types
                         ("clickhouse", "cassandra", "postgres", "opensearch")
        """
        # Convert single adapter to list
        if isinstance(adapter_types, str):
            adapter_types = [adapter_types]

        self.adapter_types = adapter_types
        self.adapters = {}
        self.primary_adapter_type = adapter_types[0]  # First adapter is primary

        logger.info(f"Initializing multi-database with adapters: {adapter_types}")

        # Initialize all adapters
        for adapter_type in adapter_types:
            try:
                if adapter_type == "clickhouse":
                    self.adapters[adapter_type] = ClickHouseAdapter()
                # elif adapter_type == "cassandra":
                #     self.adapters[adapter_type] = CassandraAdapter()
                # elif adapter_type == "postgres":
                #     self.adapters[adapter_type] = PostgresAdapter()
                # elif adapter_type == "opensearch":
                #     self.adapters[adapter_type] = OpenSearchAdapter()
                else:
                    logger.warning(f"Adapter type '{adapter_type}' not implemented yet, skipping")
                    continue

                logger.info(f"Successfully initialized {adapter_type} adapter")
            except Exception as e:
                logger.error(f"Failed to initialize {adapter_type} adapter: {str(e)}")
                # Continue with other adapters

        if not self.adapters:
            raise ValueError("No database adapters could be initialized")

        logger.info(f"Multi-database initialized with {len(self.adapters)} adapters, primary: {self.primary_adapter_type}")

    @property
    def primary_adapter(self):
        """Get the primary adapter (first in list)."""
        return self.adapters.get(self.primary_adapter_type)

    def get_available_adapters(self) -> List[str]:
        """Get list of successfully initialized adapters."""
        return list(self.adapters.keys())

    def insert_vector(self, id: str, text: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        """
        Insert a vector with text and metadata into ALL configured databases.

        Args:
            id: Unique identifier for the vector
            text: Original text content
            embedding: Vector embedding
            metadata: Additional metadata

        Returns:
            bool: Success status (True if at least one adapter succeeds)
        """
        success_count = 0
        total_adapters = len(self.adapters)

        # Insert into all adapters
        for adapter_type, adapter in self.adapters.items():
            try:
                success = adapter.add_embedding(
                    vector=embedding,
                    text=text,
                    metadata=metadata or {}
                )
                if success:
                    success_count += 1
                    logger.debug(f"Successfully inserted vector for ID {id} into {adapter_type}")
                else:
                    logger.warning(f"Failed to insert vector for ID {id} into {adapter_type}")
            except Exception as e:
                logger.error(f"Error inserting vector for ID {id} into {adapter_type}: {str(e)}")

        overall_success = success_count > 0
        if success_count == total_adapters:
            logger.debug(f"Successfully inserted vector for ID {id} into all {total_adapters} databases")
        elif success_count > 0:
            logger.warning(f"Partially successful: inserted vector for ID {id} into {success_count}/{total_adapters} databases")
        else:
            logger.error(f"Failed to insert vector for ID {id} into any database")

        return overall_success

    def search_vectors(self, query_embedding: List[float], limit: int = 5) -> List[tuple]:
        """
        Search for similar vectors using the primary database.

        Args:
            query_embedding: Query vector
            limit: Maximum number of results

        Returns:
            List of tuples: (id, text, metadata, distance)
        """
        try:
            # Use primary adapter for search (first in list)
            primary = self.primary_adapter
            if not primary:
                logger.error("No primary adapter available for search")
                return []

            # Different adapters may have different search methods
            if hasattr(primary, 'search_vectors'):
                results = primary.search_vectors(query_embedding, limit)
                logger.debug(f"Search returned {len(results)} results from {self.primary_adapter_type}")
                return results
            elif hasattr(primary, 'similarity_search'):
                results = primary.similarity_search(query_embedding, limit)
                logger.debug(f"Search returned {len(results)} results from {self.primary_adapter_type}")
                return results
            else:
                logger.error(f"Primary adapter {self.primary_adapter_type} doesn't support vector search")
                return []
        except Exception as e:
            logger.error(f"Error searching vectors in {self.primary_adapter_type}: {str(e)}")
            return []

    def get_clickhouse_client(self):
        """
        Expose ClickHouse client for native metrics.

        Returns:
            ClickHouse client instance if available, None otherwise
        """
        for adapter_type, adapter in self.adapters.items():
            if adapter_type == "clickhouse" and hasattr(adapter, 'client'):
                return adapter.client
        return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics for all adapters.

        Returns:
            Dict with database stats for each adapter
        """
        try:
            stats = {
                "primary_adapter": self.primary_adapter_type,
                "total_adapters": len(self.adapters),
                "available_adapters": list(self.adapters.keys()),
                "adapters": {}
            }

            # Get stats for each adapter
            for adapter_type, adapter in self.adapters.items():
                stats["adapters"][adapter_type] = {
                    "status": "connected",
                    "supports_search": hasattr(adapter, 'search_vectors') or hasattr(adapter, 'similarity_search'),
                    "supports_insert": hasattr(adapter, 'add_embedding')
                }

            return stats
        except Exception as e:
            return {
                "primary_adapter": self.primary_adapter_type,
                "status": "error",
                "error": str(e)
            }

# Backward compatibility alias
Database = MultiDatabase

# Convenience function for database creation
def get_database(adapter_types: Union[str, List[str]] = None) -> MultiDatabase:
    """
    Get multi-database instance with specified or default adapter(s).

    Args:
        adapter_types: Single adapter type or list of adapter types
                      (defaults to environment variable or "clickhouse")

    Returns:
        MultiDatabase instance
    """
    if adapter_types is None:
        adapter_types = os.getenv("VECTOR_DB_ADAPTER", "clickhouse")

    return MultiDatabase(adapter_types)