import os
import uuid
import logging
import traceback
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from dotenv import load_dotenv
import clickhouse_connect
import numpy as np
from langchain.schema import Document
# Optional import for sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

from .VectorStoreAdapter import VectorStoreAdapter


# Load environment variables once at import time so they are available when the
# class is instantiated from anywhere in the service.
load_dotenv()

logger = logging.getLogger(__name__)

# Configure logging for production use
logging.basicConfig(level=logging.INFO)


class ClickHouseAdapter(VectorStoreAdapter):
    def __init__(self, embedding_model=None):
        self.client = self.get_clickhouse_client()
        self.create_table_if_not_exists(self.client)
        # Initialize sentence transformer for embeddings if available and not provided
        if embedding_model:
            self.embedding_model = embedding_model
        elif HAS_SENTENCE_TRANSFORMERS:
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        else:
            self.embedding_model = None
            print("Warning: sentence_transformers not available. You'll need to provide embeddings manually.")

    def create_table_if_not_exists(self, client):
        """Create table with optimized schema based on ClickHouse best practices."""
        client.command("""
            CREATE TABLE IF NOT EXISTS rag_chunks_v2 (
                -- Primary key fields
                id String,
                timestamp DateTime,
                source String,

                -- Content and embedding
                chunk String,
                embedding Array(Float32),

                -- Numeric metrics with minimal precision
                price Decimal64(2),  -- Using Decimal64 for precise price values
                change_percent Decimal32(2),  -- Using Decimal32 for percentage
                volume UInt32,  -- Using UInt32 for volume (always positive)

                -- Metadata with LowCardinality for efficient storage
                security LowCardinality(String),
                chunk_index UInt16  -- Using UInt16 for chunk index (small range)
            ) ENGINE = MergeTree()
            -- Order by timestamp first for time-based queries, then by security and id for uniqueness
            ORDER BY (timestamp, security, id)
            -- Partition by month for efficient time-based queries
            PARTITION BY toYYYYMM(timestamp);
        """)

    def get_clickhouse_client(self):
        try:
            # Check if API key authentication is available (preferred method)
            api_key = os.getenv('CLICKHOUSE_API_KEY')
            api_secret = os.getenv('CLICKHOUSE_API_SECRET')

            if api_key and api_secret:
                # Use API key authentication (new method)
                host = os.getenv('CLICKHOUSE_HOST', 'localhost')
                port = int(os.getenv('CLICKHOUSE_PORT', 8443))
                database = os.getenv('CLICKHOUSE_DATABASE', 'default')
                secure = os.getenv('CLICKHOUSE_SECURE', 'true').lower() == 'true'

                logger.info(f"Connecting to ClickHouse at {host}:{port} using API key authentication (secure={secure})")

                return clickhouse_connect.get_client(
                    host=host,
                    port=port,
                    username=api_key,  # API key is used as username
                    password=api_secret,  # API secret is used as password
                    database=database,
                    secure=secure,
                    connect_timeout=30,
                    send_receive_timeout=30,
                    compression=True
                )
            else:
                # Fall back to username/password authentication (old method)
                host = os.getenv('CLICKHOUSE_HOST', 'localhost')
                port = int(os.getenv('CLICKHOUSE_PORT', 8443))
                username = os.getenv('CLICKHOUSE_USER', 'default')
                password = os.getenv('CLICKHOUSE_PASSWORD', '')
                database = os.getenv('CLICKHOUSE_DATABASE', 'default')
                secure = os.getenv('CLICKHOUSE_SECURE', 'true').lower() == 'true'

                logger.info(f"Connecting to ClickHouse at {host}:{port} with user {username} (secure={secure})")

                return clickhouse_connect.get_client(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    database=database,
                    secure=secure,
                    connect_timeout=30,
                    send_receive_timeout=30,
                    compression=True
                )
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {str(e)}")
            raise

    def add_embedding(self, vector: List[float], text: str, metadata: Dict[str, Any]):
        """Add a single embedding with metadata."""
        try:
            # Convert timestamp to DateTime (use current time if not provided)
            timestamp = datetime.now()
            if "timestamp" in metadata:
                timestamp = datetime.fromtimestamp(metadata["timestamp"] / 1000.0)

            # Ensure text is a string
            if hasattr(text, 'page_content'):  # If it's a Document object
                text = text.page_content
            text = str(text)  # Convert to string if it's not already

            # Prepare row with optimized types
            row = (
                str(uuid.uuid4()),  # id: UUID
                timestamp,  # timestamp: DateTime
                metadata.get("source", "unknown"),  # source: String
                text,  # chunk: String
                [float(x) for x in vector],  # embedding: Array(Float32)
                float(metadata.get("price", 0.0)),  # price: Decimal64(2)
                float(metadata.get("change_percent", 0.0)),  # change_percent: Decimal32(2)
                int(metadata.get("volume", 0)),  # volume: UInt32
                str(metadata.get("ticker", "unknown")),  # security: LowCardinality(String)
                int(metadata.get("chunk_index", 0))  # chunk_index: UInt16
            )

            self.client.insert(
                "rag_chunks_v2",
                [row],
                column_names=[
                    "id",
                    "timestamp",
                    "source",
                    "chunk",
                    "embedding",
                    "price",
                    "change_percent",
                    "volume",
                    "security",
                    "chunk_index"
                ],
            )
            return True
        except Exception as e:
            logger.error(f"Error inserting into ClickHouse: {str(e)}")
            logger.debug(f"Row that failed: {row}")
            return False

    def add_documents(self, documents: List[Document], ids: Optional[List[str]] = None, embeddings: Optional[List[List[float]]] = None) -> List[str]:
        """Add documents to the vector store. Compatible with LangChain interface."""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        if len(documents) != len(ids):
            raise ValueError("Number of documents must match number of ids")

        # Generate embeddings for all documents if not provided
        if embeddings is None:
            if self.embedding_model is None:
                raise ValueError("No embedding model available and no embeddings provided. Please provide embeddings or initialize with an embedding model.")
            texts = [doc.page_content for doc in documents]
            embeddings = self.embedding_model.encode(texts).tolist()

        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")

        # Insert each document
        successful_ids = []
        for i, (doc, doc_id, embedding) in enumerate(zip(documents, ids, embeddings)):
            try:
                timestamp = datetime.now()

                # Prepare row with optimized types
                row = (
                    doc_id,  # id: UUID
                    timestamp,  # timestamp: DateTime
                    doc.metadata.get("source", "unknown"),  # source: String
                    doc.page_content,  # chunk: String
                    [float(x) for x in embedding],  # embedding: Array(Float32)
                    float(doc.metadata.get("price", 0.0)),  # price: Decimal64(2)
                    float(doc.metadata.get("change_percent", 0.0)),  # change_percent: Decimal32(2)
                    int(doc.metadata.get("volume", 0)),  # volume: UInt32
                    str(doc.metadata.get("ticker", doc.metadata.get("security", "unknown"))),  # security: LowCardinality(String)
                    int(doc.metadata.get("chunk_index", 0))  # chunk_index: UInt16
                )

                self.client.insert(
                    "rag_chunks_v2",
                    [row],
                    column_names=[
                        "id",
                        "timestamp",
                        "source",
                        "chunk",
                        "embedding",
                        "price",
                        "change_percent",
                        "volume",
                        "security",
                        "chunk_index"
                    ],
                )
                successful_ids.append(doc_id)
                logger.debug(f"Inserted document {i+1}/{len(documents)}")
            except Exception as e:
                logger.warning(f"Failed to insert document {i+1}: {str(e)}")

        if len(successful_ids) == len(documents):
            logger.info(f"Successfully inserted {len(successful_ids)} documents")
        else:
            logger.warning(f"Inserted {len(successful_ids)}/{len(documents)} documents (some failed)")
        return successful_ids

    def similarity_search(self, query: str, k: int = 4, **kwargs) -> List[Document]:
        """Perform similarity search and return Document objects."""
        results = self.similarity_search_with_score(query, k, **kwargs)
        return [doc for doc, score in results]

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs) -> List[Tuple[Document, float]]:
        """Perform similarity search and return Document objects with scores."""
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode([query])[0].tolist()

            # Perform similarity search using cosine similarity
            results = self.client.query(f"""
                SELECT
                    id,
                    chunk,
                    source,
                    price,
                    change_percent,
                    volume,
                    security,
                    chunk_index,
                    timestamp,
                    cosineDistance(embedding, {query_embedding}) as distance
                FROM rag_chunks_v2
                ORDER BY distance ASC
                LIMIT {k}
            """)

            documents_with_scores = []
            for row in results.result_rows:
                doc_id, content, source, price, change_percent, volume, security, chunk_index, timestamp, distance = row

                # Convert distance to similarity score (1 - distance for cosine)
                similarity_score = 1.0 - distance

                metadata = {
                    "id": str(doc_id),
                    "source": source,
                    "price": float(price),
                    "change_percent": float(change_percent),
                    "volume": int(volume),
                    "security": security,
                    "chunk_index": int(chunk_index),
                    "timestamp": timestamp
                }

                doc = Document(page_content=content, metadata=metadata)
                documents_with_scores.append((doc, similarity_score))

            return documents_with_scores
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}")
            return []

    def delete(self, ids: Optional[List[str]] = None) -> bool:
        """Delete documents by IDs."""
        if not ids:
            return True

        try:
            # Convert list of IDs to a format suitable for ClickHouse IN clause
            ids_str = "', '".join(ids)

            result = self.client.command(f"""
                ALTER TABLE rag_chunks_v2
                DELETE WHERE id IN ('{ids_str}')
            """)

            print(f"Successfully deleted {len(ids)} documents")
            return True
        except Exception as e:
            print(f"Error deleting documents: {str(e)}")
            traceback.print_exc()
            return False

    def verify_data_insertion(self):
        """Verify data insertion by checking recent records."""
        try:
            # Get total count
            total_count = self.client.command("SELECT count() FROM rag_chunks_v2")
            print(f"\nTotal records in rag_chunks_v2: {total_count}")

            # Get latest records
            latest_records = self.client.query("""
                SELECT
                    timestamp,
                    security,
                    price,
                    change_percent,
                    volume
                FROM rag_chunks_v2
                ORDER BY timestamp DESC
                LIMIT 5
            """)

            print("\nLatest 5 records:")
            for row in latest_records.result_rows:
                print(f"Time: {row[0]}, Security: {row[1]}, Price: {row[2]}, Change: {row[3]}%, Volume: {row[4]}")

            # Get records by security
            securities = self.client.query("""
                SELECT
                    security,
                    count() as record_count,
                    min(timestamp) as first_seen,
                    max(timestamp) as last_seen
                FROM rag_chunks_v2
                GROUP BY security
                ORDER BY record_count DESC
                LIMIT 5
            """)

            print("\nRecords by security:")
            for row in securities.result_rows:
                print(f"Security: {row[0]}, Count: {row[1]}, First: {row[2]}, Last: {row[3]}")

            return True
        except Exception as e:
            print(f"Error verifying data: {str(e)}")
            traceback.print_exc()
            return False

    def get_table_stats(self):
        """Get table statistics."""
        try:
            stats = self.client.query("""
                SELECT
                    name,
                    total_rows,
                    total_bytes
                FROM system.tables
                WHERE database = 'default' AND name = 'rag_chunks_v2'
            """)

            print("\nTable Statistics:")
            for row in stats.result_rows:
                print(f"Table: {row[0]}")
                print(f"Total Rows: {row[1]}")
                print(f"Total Bytes: {row[2]}")

            return True
        except Exception as e:
            print(f"Error getting table stats: {str(e)}")
            traceback.print_exc()
            return False

    def check_table_schema(self):
        """Check the current table schema and compare with expected schema."""
        try:
            # Get current table structure
            result = self.client.query("DESCRIBE TABLE rag_chunks_v2")

            print("Current table schema:")
            existing_columns = []
            for row in result.result_rows:
                print(f"  {row[0]}: {row[1]}")
                existing_columns.append(row[0])

            # Expected columns from your create_table_if_not_exists method
            expected_columns = [
                'id', 'timestamp', 'source', 'chunk', 'embedding',
                'price', 'change_percent', 'volume', 'security', 'chunk_index'
            ]

            # Check for missing columns
            missing_columns = [col for col in expected_columns if col not in existing_columns]
            extra_columns = [col for col in existing_columns if col not in expected_columns]

            if missing_columns:
                print(f"\n❌ Missing columns: {missing_columns}")
            if extra_columns:
                print(f"\n⚠️  Extra columns: {extra_columns}")

            if not missing_columns and not extra_columns:
                print("\n✅ Table schema matches expected schema")

            return existing_columns, missing_columns, extra_columns

        except Exception as e:
            print(f"Error checking table schema: {str(e)}")
            traceback.print_exc()
            return [], [], []

    def recreate_table(self):
        """Drop and recreate the table with the correct schema."""
        try:
            # Check if table exists and get record count
            try:
                count_result = self.client.command("SELECT count() FROM rag_chunks_v2")
                print(f"Current table has {count_result} records")

                # Ask for confirmation if table has data
                if count_result > 0:
                    response = input(f"Table has {count_result} records. Are you sure you want to drop it? (yes/no): ")
                    if response.lower() != 'yes':
                        print("Operation cancelled")
                        return False
            except:
                print("Table doesn't exist or is empty")

            # Drop the table
            print("Dropping existing table...")
            self.client.command("DROP TABLE IF EXISTS rag_chunks_v2")

            # Recreate with correct schema
            print("Creating table with correct schema...")
            self.create_table_if_not_exists(self.client)

            # Verify the new table
            print("Verifying new table schema...")
            self.check_table_schema()

            print("✅ Table recreated successfully")
            return True

        except Exception as e:
            print(f"Error recreating table: {str(e)}")
            traceback.print_exc()
            return False