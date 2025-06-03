from .VectorStoreAdapter import VectorStoreAdapter
import uuid
from langchain.schema import Document
import psycopg2
from psycopg2.extras import execute_batch
import traceback


class PostgresAdapter(VectorStoreAdapter):
    def __init__(self):
        """
        Initialize the PostgreSQL adapter.
        
        Creates database connection, initializes cursor, and sets up the required
        table structure with pgvector extension if not already present.
        
        Raises:
            psycopg2.Error: If connection to database fails
        """
        self.conn = self.get_postgres_connection()
        self.cur = self.conn.cursor()
        self.create_table_if_not_exists()
    
    def create_table_if_not_exists(self):
        """
        Create the rag_chunks table and necessary indexes if they don't exist.
        
        This method:
        1. Enables the pgvector extension (required for vector operations)
        2. Creates the rag_chunks table with the following schema:
           - id: UUID primary key
           - chunk: TEXT for storing document content
           - embedding: VECTOR(384) for storing 384-dimensional embeddings
           - source: TEXT for document source identification
           - chunk_index: INT for chunk ordering within documents
        3. Creates an IVFFlat index for efficient similarity searches

            The vector dimension is fixed at 384 to match common embedding models
            like sentence-transformers/all-MiniLM-L6-v2
        """
        try:
            # Enable pgvector extension
            self.cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create table 
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    id UUID PRIMARY KEY,
                    chunk TEXT,
                    embedding VECTOR(384),
                    source TEXT,
                    chunk_index INT
                );
            """)
            
            # Create index for similarity search
            self.cur.execute("""
                CREATE INDEX IF NOT EXISTS rag_chunks_embedding_idx 
                ON rag_chunks USING ivfflat (embedding vector_cosine_ops);
            """)
            
            self.conn.commit()
        except Exception as e:
            print(f"Error creating table: {e}")
            self.conn.rollback()
    
    def get_postgres_connection(self):
        """Get PostgreSQL connection matching the original pattern."""
        return psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='yourpassword',  # change if needed to match your password
            dbname='postgres'
        )
    
    def add_embedding(self, vectors, text: list[Document], metadata: list[dict]):
        """Add embeddings"""
        rows = []
        for i, (chunk, vector) in enumerate(zip(text, vectors)):
            try:
                # Extract text content from Document object
                chunk_text = chunk.page_content if hasattr(chunk, 'page_content') else str(chunk)
                
                # Convert vector to PostgreSQL array format
                vector_str = '[' + ','.join(map(str, vector)) + ']'
                
                rows.append((
                    str(uuid.uuid4()),  # "id"
                    chunk_text,  # "chunk"
                    vector_str,  # "embedding"
                    metadata[i]["source"],  # "source"
                    metadata[i]["chunk_index"]  # "chunk_index"
                ))
            except Exception as e:
                print(f"PostgreSQL Error processing chunk {i}: {e}")
        
        try:
            # Batch insert for better performance
            execute_batch(
                self.cur,
                """
                INSERT INTO rag_chunks (id, chunk, embedding, source, chunk_index) 
                VALUES (%s, %s, %s::vector, %s, %s)
                """,
                rows
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error inserting into PostgreSQL: {e} \n")
            traceback.print_exc()
            self.conn.rollback()
    
    def query_similar(self, query_vector, top_k=10):
        """
        Query similar vectors
        """
        try:
            vector_str = '[' + ','.join(map(str, query_vector)) + ']'
            
            self.cur.execute("""
                SELECT id, chunk, source, chunk_index,
                       1 - (embedding <=> %s::vector) as similarity
                FROM rag_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (vector_str, vector_str, top_k))
            
            results = []
            for row in self.cur.fetchall():
                results.append({
                    'id': row[0],
                    'chunk': row[1],
                    'source': row[2],
                    'chunk_index': row[3],
                    'similarity': row[4]
                })
            
            return results
        except Exception as e:
            print(f"Error querying PostgreSQL: {e}")
            traceback.print_exc()
            return []
    
    def get_chunk_count(self):
        """Get total number of chunks in the database."""
        try:
            self.cur.execute("SELECT COUNT(*) FROM rag_chunks")
            return self.cur.fetchone()[0]
        except Exception as e:
            print(f"Error counting chunks: {e}")
            return 0
    
    def close(self):
        """Close database connections."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()