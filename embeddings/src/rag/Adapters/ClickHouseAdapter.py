import os
import uuid
import logging
import traceback
import sys

from datetime import datetime

from dotenv import load_dotenv
import clickhouse_connect
import numpy as np
from langchain.schema import Document

from .VectorStoreAdapter import VectorStoreAdapter


# Load environment variables once at import time so they are available when the
# class is instantiated from anywhere in the service.
load_dotenv()

logger = logging.getLogger(__name__)

# Configure logging to capture all levels
logging.basicConfig(level=logging.DEBUG)


class ClickHouseAdapter(VectorStoreAdapter):
    def __init__(self):
        self.client = self.get_clickhouse_client()
        self.create_table_if_not_exists(self.client)

    def create_table_if_not_exists(self, client):
        client.command("""
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id UUID,
                chunk String,
                embedding Array(Float32),
                source String,
                timestamp DateTime,
                price Float64,
                change_percent Float64,
                volume Int64
            ) ENGINE = MergeTree()
            ORDER BY (id, timestamp);
        """)

    def get_clickhouse_client(self):
        try:
            host = os.getenv('CLICKHOUSE_HOST', 'localhost')
            port = int(os.getenv('CLICKHOUSE_PORT', 8443))
            username = os.getenv('CLICKHOUSE_USER', 'default')
            password = os.getenv('CLICKHOUSE_PASSWORD', '')
            secure = os.getenv('CLICKHOUSE_SECURE', 'true').lower() == 'true'

            print("Connecting to ClickHouse at", host, port, "with user", username, "(secure=", secure, ")", file=sys.stderr, flush=True)

            return clickhouse_connect.get_client(
                host=host,
                port=port,
                username=username,
                password=password,
                database='default',
                secure=secure,
                connect_timeout=30,
                send_receive_timeout=30,
                compression=True
            )
        except Exception as e:
            print("Failed to connect to ClickHouse:", str(e), file=sys.stderr, flush=True)
            raise

    def add_embedding(self, vectors, text: list[Document], metadata: list[dict]):
        rows = []
        print(f"we are about to enter for loop")
        for i, (chunk, vector) in enumerate(zip(text, vectors)):
            try:
                print(type([float(x) for x in vector]), file=sys.stderr)
                print("Processing chunk", i, file=sys.stderr, flush=True)
                print("Chunk:", chunk, file=sys.stderr, flush=True)
                print("Vector:", vector, file=sys.stderr, flush=True)
                rows.append(
                    (
                        str(uuid.uuid4()),  # id
                        str(chunk),
                        [float(x) for x in vector],  # ensure plain python floats
                        metadata[i]["source"],
                        datetime.fromtimestamp(metadata[i]["timestamp"] / 1000.0),  # Convert to datetime
                        float(metadata[i]["price"]),
                        float(metadata[i]["change_percent"]),
                       int(metadata[i]["volume"]),
                    )
                )
                print("Row to insert:", rows[-1], file=sys.stderr, flush=True)
            except Exception as e:
                print("Clickhouse Error processing chunk", i, ":", e)
                logger.debug(f"Index: {i}, Metadata: {metadata[i]}, Vector: {vector}")
                traceback.print_exc()
                continue

        try:
            self.client.insert(
                "rag_chunks",
                rows,
                column_names=[
                    "id",
                    "chunk",
                    "embedding",
                    "source",
                    "timestamp",
                    "price",
                    "change_percent",
                    "volume",
                ],
            )

            # Quick sanity-check: get the latest row count (cheap on MergeTree)
            try:
                total = self.client.command("SELECT count() FROM rag_chunks")
                print("Successfully inserted", len(rows), "rows. rag_chunks row_count=", total, file=sys.stderr, flush=True)
                print("Row count after insertion:", total, file=sys.stderr, flush=True)
            except Exception as count_err:  # pragma: no cover – not fatal
                print("Insert succeeded but count() failed:", count_err, file=sys.stderr, flush=True)
        except Exception as e:
            print("Error inserting into ClickHouse:", e, file=sys.stderr, flush=True)
            traceback.print_exc()
            raise
