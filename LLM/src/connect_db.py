import sys
import os

# Add the embeddings path to sys.path to import ClickHouseAdapter
sys.path.append(os.path.join(os.path.dirname(__file__), '../../Embeddings/src'))

try:
    from Adapters.ClickHouseAdapter import ClickHouseAdapter
    CLICKHOUSE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import ClickHouseAdapter: {e}")
    CLICKHOUSE_AVAILABLE = False

def get_vector_db():
    """
    Get ClickHouse vector database connection.
    Returns configured ClickHouseAdapter instance.
    """
    if not CLICKHOUSE_AVAILABLE:
        print("❌ ClickHouse adapter not available")
        return None

    try:
        adapter = ClickHouseAdapter()
        print("✅ Connected to ClickHouse vector store")
        return adapter
    except Exception as e:
        print(f"❌ Failed to connect to ClickHouse: {e}")
        return None

def test_vector_connection():
    """Test the vector database connection"""
    db = get_vector_db()
    if db:
        try:
            # Test with a simple query
            results = db.similarity_search("test query", k=1)
            print(f"✅ Vector store test successful, found {len(results)} results")
            return True
        except Exception as e:
            print(f"❌ Vector store test failed: {e}")
            return False
    return False
