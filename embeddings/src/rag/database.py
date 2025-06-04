"""
Database module for the Embeddings service.

This module handles all database operations for the embeddings service.
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import clickhouse_connect
from typing import Optional, Any, List
from dataclasses import dataclass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the project root directory (two levels up from this file)
project_root = Path(__file__).parent.parent.parent.parent

# Load environment variables from project root
load_dotenv(project_root / ".env")

def get_env_or_raise(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

@dataclass
class DatabaseConfig:
    host: str
    user: str
    password: str
    secure: bool = True
    port: int = 8443

class ClickHouseDatabase:
    """ClickHouse database client for vector storage."""

    def __init__(self):
        """Initialize the database connection."""
        logger.info("Initializing ClickHouse database connection")

        # Get connection details from environment variables
        self.host = os.getenv('CLICKHOUSE_HOST')
        self.user = os.getenv('CLICKHOUSE_USER')
        self.password = os.getenv('CLICKHOUSE_PASSWORD')
        self.secure = os.getenv('CLICKHOUSE_SECURE', 'true').lower() == 'true'
        self.port = int(os.getenv('CLICKHOUSE_PORT', '8443'))

        if not all([self.host, self.user, self.password]):
            logger.error("Missing required ClickHouse credentials")
            raise RuntimeError("Database configuration could not be initialized. Required environment variables are not set.")

        logger.info(f"Connecting to ClickHouse at {self.host}:{self.port}")
        try:
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                secure=self.secure
            )
            logger.info("Successfully connected to ClickHouse")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {str(e)}", exc_info=True)
            raise

    def create_tables(self):
        """Create necessary tables if they don't exist."""
        logger.info("Creating database tables if they don't exist")
        try:
            # Create vectors table
            self.client.command("""
                CREATE TABLE IF NOT EXISTS vectors (
                    id String,
                    text String,
                    embedding Array(Float32),
                    metadata Map(String, String),
                    created_at DateTime DEFAULT now()
                ) ENGINE = MergeTree()
                ORDER BY id
            """)
            logger.info("Successfully created vectors table")

            # Create vector index
            self.client.command("""
                CREATE TABLE IF NOT EXISTS vector_index (
                    id String,
                    embedding Array(Float32)
                ) ENGINE = MergeTree()
                ORDER BY id
            """)
            logger.info("Successfully created vector_index table")

        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}", exc_info=True)
            raise

    def insert_vector(self, id: str, text: str, embedding: list, metadata: dict = None):
        """Insert a vector into the database."""
        logger.info(f"Inserting vector with ID: {id}")
        try:
            self.client.insert(
                'vectors',
                [[id, text, embedding, metadata or {}]],
                column_names=['id', 'text', 'embedding', 'metadata']
            )
            logger.info(f"Successfully inserted vector {id}")
        except Exception as e:
            logger.error(f"Failed to insert vector {id}: {str(e)}", exc_info=True)
            raise

    def search_vectors(self, query_embedding: list, limit: int = 5):
        """Search for similar vectors using cosine similarity."""
        logger.info(f"Searching vectors with limit: {limit}")
        try:
            # Use cosine similarity for vector search
            result = self.client.query("""
                SELECT
                    id,
                    text,
                    metadata,
                    cosineDistance(embedding, {query_embedding:Array(Float32)}) as distance
                FROM vectors
                ORDER BY distance ASC
                LIMIT {limit:UInt32}
            """, parameters={
                'query_embedding': query_embedding,
                'limit': limit
            })

            logger.info(f"Found {len(result.result_rows)} similar vectors")
            return result.result_rows
        except Exception as e:
            logger.error(f"Failed to search vectors: {str(e)}", exc_info=True)
            raise

# Example usage:
if __name__ == '__main__':
    print("Environment variables:")
    for key, value in os.environ.items():
        if key.startswith('CLICKHOUSE_'):
            print(f"{key}={value}")

    try:
        # Initialize with default config from environment variables
        db = ClickHouseDatabase()

        # Test the connection
        if db.test_connection():
            print("Successfully connected to ClickHouse!")
        else:
            print("Failed to connect to ClickHouse")
    except Exception as e:
        print(f"Error: {str(e)}")