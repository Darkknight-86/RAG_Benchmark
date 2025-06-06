#!/usr/bin/env python3
"""
Test Cassandra Authentication
"""

import os
from dotenv import load_dotenv
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Load environment variables
load_dotenv()

def test_authentication():
    """Test different authentication scenarios"""
    
    host = os.getenv('CASSANDRA_HOST', 'localhost')
    port = int(os.getenv('CASSANDRA_PORT', 9042))
    custom_user = os.getenv('CASSANDRA_USERNAME', 'rag_user')
    custom_pass = os.getenv('CASSANDRA_PASSWORD', 'rag-password')
    
    print("🔐 Testing Cassandra Authentication")
    print("=" * 50)
    
    # Test 1: Default credentials
    print("1. Testing default credentials (cassandra/cassandra)...")
    try:
        auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
        cluster = Cluster([host], auth_provider=auth_provider)
        session = cluster.connect()
        
        result = session.execute("SELECT cluster_name FROM system.local")
        for row in result:
            print(f"   ✅ Connected to cluster: {row.cluster_name}")
        
        # List roles
        roles = session.execute("LIST ROLES")
        print("   Available roles:")
        for role in roles:
            print(f"     - {role.role}")
        
        cluster.shutdown()
        
    except Exception as e:
        print(f"   ❌ Default credentials failed: {e}")
    
    # Test 2: Custom credentials (if set)
    custom_user = os.getenv('CASSANDRA_USERNAME', 'rag_user')
    custom_pass = os.getenv('CASSANDRA_PASSWORD', 'rag-password')
    
    if custom_user != 'cassandra':
        print(f"\n2. Testing custom credentials ({custom_user}/****)...")
        try:
            auth_provider = PlainTextAuthProvider(username=custom_user, password=custom_pass)
            cluster = Cluster([host], auth_provider=auth_provider)
            session = cluster.connect()
            
            result = session.execute("SELECT cluster_name FROM system.local")
            for row in result:
                print(f"   ✅ Connected with custom credentials to: {row.cluster_name}")
            
            cluster.shutdown()
            
        except Exception as e:
            print(f"   ❌ Custom credentials failed: {e}")
    
    # Test 3: No authentication (should fail if auth is enabled)
    print("\n3. Testing no authentication...")
    try:
        cluster = Cluster([host])
        session = cluster.connect()
        print("   ⚠️  No authentication required (auth not enabled)")
        cluster.shutdown()
        
    except Exception as e:
        print(f"   ✅ Authentication required (as expected): {e}")

def create_secure_users():
    """Create secure users for production"""
    
    host = os.getenv('CASSANDRA_HOST', '4.237.154.242')
    
    print("\n🔒 Creating Secure Users")
    print("=" * 30)
    
    try:
        # Connect as superuser
        auth_provider = PlainTextAuthProvider(username='cassandra', password='your-secure-password-here')
        cluster = Cluster([host], auth_provider=auth_provider)
        session = cluster.connect()
        
        # Create application user
        session.execute("""
            CREATE ROLE IF NOT EXISTS rag_app 
            WITH PASSWORD = 'rag-app-secure-password' 
            AND LOGIN = true
        """)
        
        # Create read-only user
        session.execute("""
            CREATE ROLE IF NOT EXISTS rag_reader 
            WITH PASSWORD = 'rag-reader-password' 
            AND LOGIN = true
        """)
        
        # Grant permissions (after keyspaces are created)
        print("✅ Users created. Grant permissions after creating keyspaces:")
        print("   GRANT ALL ON KEYSPACE rag_vectors TO rag_app;")
        print("   GRANT SELECT ON KEYSPACE rag_vectors TO rag_reader;")
        
        cluster.shutdown()
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")

if __name__ == "__main__":
    test_authentication()
    # create_secure_users()  # Uncomment after setting superuser password