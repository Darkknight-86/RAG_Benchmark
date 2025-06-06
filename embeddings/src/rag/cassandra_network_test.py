#!/usr/bin/env python3
"""
Simple Cassandra connection test
"""

import os
from dotenv import load_dotenv
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import time
import sys

# Load environment variables
load_dotenv()

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'localhost')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', 9042))
CASSANDRA_USERNAME = os.getenv('CASSANDRA_USERNAME')
CASSANDRA_PASSWORD = os.getenv('CASSANDRA_PASSWORD')

def test_cassandra_connection():
    """Test connection to Cassandra and perform basic operations"""
    
    print(f"Attempting to connect to Cassandra at {CASSANDRA_HOST}:{CASSANDRA_PORT}")
    
    try:
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
        
        # Connect with retry logic (Cassandra takes time to start)
        session = None
        max_retries = 10
        
        for attempt in range(max_retries):
            try:
                # Create a new cluster for each retry
                if attempt > 0:
                    cluster.shutdown()
                    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
                
                session = cluster.connect()
                print("✅ Successfully connected to Cassandra!")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    print("Waiting 15 seconds before retry...")
                    time.sleep(15)
                else:
                    raise
        
        if not session:
            raise Exception("Failed to establish session")
        
        # Create a test keyspace
        print("Creating test keyspace...")
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS test_keyspace
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        
        # Use the keyspace
        session.set_keyspace('test_keyspace')
        
        # Create a test table
        print("Creating test table...")
        session.execute("""
            CREATE TABLE IF NOT EXISTS hello_world (
                id UUID PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP
            )
        """)
        
        # Insert test data
        print("Inserting test data...")
        from uuid import uuid4
        from datetime import datetime
        
        session.execute("""
            INSERT INTO hello_world (id, message, created_at)
            VALUES (%s, %s, %s)
        """, (uuid4(), "Hello, Cassandra World!", datetime.now()))
        
        # Query the data
        print("Querying test data...")
        rows = session.execute("SELECT * FROM hello_world")
        
        for row in rows:
            print(f"📝 ID: {row.id}")
            print(f"📝 Message: {row.message}")
            print(f"📝 Created: {row.created_at}")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if 'cluster' in locals():
            cluster.shutdown()
            print("Connection closed.")
    
    return True

def check_container_status():
    """Check if the Cassandra container is running"""
    import subprocess
    
    try:
        result = subprocess.run([
            'az', 'container', 'show',
            '--resource-group', 'ragpipeline',
            '--name', 'cassandra',
            '--query', 'instanceView.state',
            '--output', 'tsv'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            status = result.stdout.strip()
            print(f"Container status: {status}")
            return status.lower() == 'running'
        else:
            print("Could not check container status")
            return False
            
    except FileNotFoundError:
        print("Azure CLI not found. Please install it or check container status manually.")
        return True  # Assume it's running if we can't check

if __name__ == "__main__":
    print("🚀 Cassandra Connection Test")
    print("=" * 40)
    
    # Check container status first
    if check_container_status():
        print("Container is running, proceeding with connection test...")
        success = test_cassandra_connection()
        sys.exit(0 if success else 1)
    else:
        print("❌ Container is not running. Please start it first.")
        sys.exit(1)