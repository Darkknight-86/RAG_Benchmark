from .VectorStoreAdapter import VectorStoreAdapter
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement
from cassandra.auth import PlainTextAuthProvider
from langchain.schema import Document
import uuid
import traceback
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'localhost')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', 9042))
CASSANDRA_USERNAME = os.getenv('CASSANDRA_USERNAME')
CASSANDRA_PASSWORD = os.getenv('CASSANDRA_PASSWORD')


class CassandraAdapter(VectorStoreAdapter):
    def __init__(self):
        self.session = self.get_cassandra_session()
        self.create_table_if_not_exists()

    def get_cassandra_session(self):
        if CASSANDRA_USERNAME and CASSANDRA_PASSWORD:
            auth_provider = PlainTextAuthProvider(username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD)
            cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT, auth_provider=auth_provider)
        else:
            cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
        session = cluster.connect()
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS rag
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        session.set_keyspace('rag')
        return session

    def create_table_if_not_exists(self):
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id UUID PRIMARY KEY,
                chunk TEXT,
                embedding list<float>,
                source TEXT,
                chunk_index int
            );
        """)

    def add_embedding(self, vectors, text: list[Document], metadata: list[dict]):
        insert_query = self.session.prepare("""
            INSERT INTO rag_chunks (id, chunk, embedding, source, chunk_index)
            VALUES (?, ?, ?, ?, ?)
        """)
        batch_size = 20
        batch = BatchStatement()
        for i, (chunk, vector) in enumerate(zip(text, vectors)):
            try:
                # Standardize to float32
                float32_vector = list(np.array(vector, dtype=np.float32))
                batch.add(insert_query, (
                    uuid.uuid4(),
                    chunk.page_content,
                    float32_vector,
                    metadata[i]["source"],
                    metadata[i]["chunk_index"]
                ))
            except Exception as e:
                print(f"Error preparing chunk {i} for batch: {e}")
                traceback.print_exc()
            # If batch is full or it's the last item, execute it
            if (i + 1) % batch_size == 0 or i == len(text) - 1:
                try:
                    self.session.execute(batch)
                except Exception as e:
                    print(f"Error executing batch ending at chunk {i}: {e}")
                    traceback.print_exc()
                batch = BatchStatement()  # Start new batch

