from .VectorStoreAdapter import VectorStoreAdapter
import uuid
from langchain.schema import Document
import clickhouse_connect

import traceback


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
                chunk_index Int32
            ) ENGINE = MergeTree()
            ORDER BY id;
        """)

    def get_clickhouse_client(self):
        return clickhouse_connect.get_client(
            host='localhost', port=8123, username='default', password='MyStrongPassword123', database='default'
    )

    def add_embedding(self, vectors, text: list[Document], metadata: list[dict]):
        rows = []
        for i, (chunk, vector) in enumerate(zip(text, vectors)):
            try: 
                rows.append((
                    uuid.uuid4(), # "id" 
                    chunk, # "chunk"
                    list(vector), # "embedding"
                    metadata[i]["source"], # "source"
                    metadata[i]["chunk_index"] # "chunk_index"
                ))
            except Exception as e:
                print(f"Clickhouse Error processing chunk {i}: {e}")

        try:
            self.client.insert("rag_chunks", rows, column_names=["id", "chunk", "embedding", "source", "chunk_index"])
        except Exception as e:
            print(f"Error inserting into ClickHouse: {e} \n")
            traceback.print_exc()
