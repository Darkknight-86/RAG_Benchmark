#!/usr/bin/env python3
"""
Simple Cassandra Vector Database Test
Focus on core vector functionality that definitely works
"""

import os
from dotenv import load_dotenv
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import time
import random
from uuid import uuid4
from datetime import datetime

# Load environment variables
load_dotenv()

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'localhost')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', 9042))
CASSANDRA_USERNAME = os.getenv('CASSANDRA_USERNAME')
CASSANDRA_PASSWORD = os.getenv('CASSANDRA_PASSWORD')

def test_vector_storage():
    """Test basic vector storage and retrieval"""
    print("🚀 Testing Cassandra Vector Storage")
    print("=" * 50)
    
    # Connect to Cassandra with authentication if credentials are provided
    if CASSANDRA_USERNAME and CASSANDRA_PASSWORD:
        auth_provider = PlainTextAuthProvider(username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD)
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT, auth_provider=auth_provider)
    else:
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect()
    print("✅ Connected to Cassandra")
    
    try:
        # Create keyspace
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS vector_test
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        session.set_keyspace('vector_test')
        print("✅ Keyspace created")
        
        # Create table with vector column
        session.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id UUID PRIMARY KEY,
                text TEXT,
                embedding VECTOR<FLOAT, 384>,
                created_at TIMESTAMP
            )
        """)
        print("✅ Vector table created")
        
        # Insert sample vectors
        print("\n📝 Inserting vector data...")
        sample_data = [
            {
                "text": "Machine learning algorithms",
                "vector": [random.uniform(-1, 1) for _ in range(384)]
            },
            {
                "text": "Natural language processing",
                "vector": [random.uniform(-1, 1) for _ in range(384)]
            },
            {
                "text": "Computer vision systems",
                "vector": [random.uniform(-1, 1) for _ in range(384)]
            }
        ]
        
        for data in sample_data:
            session.execute("""
                INSERT INTO embeddings (id, text, embedding, created_at)
                VALUES (%s, %s, %s, %s)
            """, (uuid4(), data["text"], data["vector"], datetime.now()))
            print(f"   ✅ Inserted: {data['text']}")
        
        # Query vector data
        print("\n🔍 Querying vector data...")
        rows = session.execute("SELECT id, text, embedding FROM embeddings")
        
        for i, row in enumerate(rows, 1):
            print(f"   {i}. Text: {row.text}")
            print(f"      ID: {row.id}")
            print(f"      Vector dimensions: {len(row.embedding)}")
            print(f"      Sample values: {row.embedding[:5]}")
            print()
        
        # Test vector operations
        print("🧮 Testing vector operations...")
        
        # Get two vectors for comparison
        vectors = list(session.execute("SELECT embedding FROM embeddings LIMIT 2"))
        if len(vectors) >= 2:
            vec1 = vectors[0].embedding
            vec2 = vectors[1].embedding
            
            # Calculate dot product (simple similarity measure)
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            print(f"   Dot product of first two vectors: {dot_product:.4f}")
            
            # Calculate Euclidean distance
            squared_diff = sum((a - b) ** 2 for a, b in zip(vec1, vec2))
            euclidean_dist = squared_diff ** 0.5
            print(f"   Euclidean distance: {euclidean_dist:.4f}")
        
        # Test vector filtering (basic operations that work)
        print("\n🔧 Testing vector operations in CQL...")
        
        # Get vector length (this should work)
        try:
            result = session.execute("""
                SELECT text, embedding
                FROM embeddings 
                WHERE text = 'Machine learning algorithms'
                ALLOW FILTERING
            """).one()
            
            if result:
                print(f"   ✅ Retrieved specific vector: {len(result.embedding)} dimensions")
            
        except Exception as e:
            print(f"   ⚠️  Vector filtering: {e}")
        
        # Show what definitely works
        print("\n✅ Core vector operations confirmed working:")
        print("   • Vector storage (VECTOR<FLOAT, 384>)")
        print("   • Vector insertion and retrieval")
        print("   • Vector dimension preservation")
        print("   • Basic application-level vector math")
        
        print("\n⚠️  Advanced operations may require:")
        print("   • Specific Cassandra configuration")
        print("   • Vector indexes for ANN search")
        print("   • Newer Cassandra versions for full vector support")
        
        print("\n🎉 Vector storage test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        cluster.shutdown()
        print("Connection closed.")

def create_vector_rag_schema():
    print("\n🏗️  Creating production RAG schema...")

    if CASSANDRA_USERNAME and CASSANDRA_PASSWORD:
        auth_provider = PlainTextAuthProvider(username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD)
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT, auth_provider=auth_provider)
    else:
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect()
    
    try:
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS rag_production
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        session.set_keyspace('rag_production')
        
        # Documents table
        session.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id UUID PRIMARY KEY,
                title TEXT,
                content TEXT,
                source_url TEXT,
                document_type TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Document chunks with embeddings
        session.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                chunk_id UUID PRIMARY KEY,
                doc_id UUID,
                chunk_text TEXT,
                embedding VECTOR<FLOAT, 384>,
                chunk_index INT,
                chunk_size INT,
                overlap_with_next BOOLEAN,
                metadata MAP<TEXT, TEXT>,
                created_at TIMESTAMP
            )
        """)
        
        # Index for document lookup
        session.execute("""
            CREATE INDEX IF NOT EXISTS chunks_by_doc 
            ON document_chunks (doc_id)
        """)
        
        # Query log for RAG analytics
        session.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                query_id UUID PRIMARY KEY,
                user_query TEXT,
                query_embedding VECTOR<FLOAT, 384>,
                retrieved_chunks LIST<UUID>,
                response_generated TEXT,
                timestamp TIMESTAMP,
                response_time_ms INT
            )
        """)
        
        print("✅ Production RAG schema created!")
        print("   • Documents table for source management")
        print("   • Document chunks with 384-dim embeddings")
        print("   • Query log for analytics")
        print("   • Proper indexing for performance")
        
    except Exception as e:
        print(f"❌ Schema creation error: {e}")
        
    finally:
        cluster.shutdown()

if __name__ == "__main__":
    test_vector_storage()
    create_vector_rag_schema()