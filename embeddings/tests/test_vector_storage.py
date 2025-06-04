import numpy as np
from src.rag.database import ClickHouseDatabase
import os
import traceback

def test_vector_storage():
    # Print environment variables for debugging
    print("\nEnvironment variables:")
    for key, value in os.environ.items():
        if key.startswith('CLICKHOUSE_'):
            print(f"{key}={value}")
    print("\n")

    try:
        print("[LOG] Connecting to ClickHouse...")
        db = ClickHouseDatabase()
        print("[LOG] Connected to ClickHouse!")
    except Exception as e:
        print("[ERROR] Failed to connect to ClickHouse:")
        traceback.print_exc()
        return

    # Create test table for vectors if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS test_vectors (
        id UInt32,
        vector Array(Float32),
        metadata String
    ) ENGINE = MergeTree()
    ORDER BY id
    """
    try:
        print("[LOG] Creating table test_vectors...")
        db.execute_query(create_table_query)
        print("[LOG] Table created (or already exists).")
    except Exception as e:
        print("[ERROR] Failed to create table:")
        traceback.print_exc()
        return

    # Generate a test vector
    test_vector = np.random.rand(384).astype(np.float32).tolist()  # Using 384 dimensions as an example
    test_id = 1
    test_metadata = "test_document"

    # Insert the vector
    insert_query = """
    INSERT INTO test_vectors (id, vector, metadata)
    VALUES (%(id)s, %(vector)s, %(metadata)s)
    """
    try:
        print("[LOG] Inserting vector...")
        db.execute_query(insert_query, {
            'id': test_id,
            'vector': test_vector,
            'metadata': test_metadata
        })
        print("[LOG] Vector inserted!")
    except Exception as e:
        print("[ERROR] Failed to insert vector:")
        traceback.print_exc()
        return

    # Retrieve the vector
    select_query = """
    SELECT id, vector, metadata
    FROM test_vectors
    WHERE id = %(id)s
    """
    try:
        print("[LOG] Querying vector...")
        result = db.execute_query(select_query, {'id': test_id})
        print(f"[LOG] Query result: {result}")
    except Exception as e:
        print("[ERROR] Failed to query vector:")
        traceback.print_exc()
        return

    # Verify the results
    if result:
        retrieved_id, retrieved_vector, retrieved_metadata = result[0]
        print(f"[LOG] Successfully stored and retrieved vector with ID: {retrieved_id}")
        print(f"[LOG] Vector dimensions: {len(retrieved_vector)}")
        print(f"[LOG] Metadata: {retrieved_metadata}")

        # Verify vector values match
        if np.allclose(np.array(retrieved_vector), np.array(test_vector)):
            print("[LOG] Vector values match!")
        else:
            print("[WARN] Vector values don't match exactly")
    else:
        print("[ERROR] Failed to retrieve vector")

if __name__ == "__main__":
    test_vector_storage()