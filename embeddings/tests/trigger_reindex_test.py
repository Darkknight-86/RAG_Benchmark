#!/usr/bin/env python3
"""
Reindexing Test Script

This script triggers various reindexing operations to test the
reindex detection system in the RAG pipeline metrics.

Usage:
    python trigger_reindex_test.py [operation_type]

Operations:
    - optimize: Force table optimization (reindexing)
    - bulk: Insert bulk data to trigger automatic reindexing
    - schema: Modify schema to trigger reindexing
"""

import sys
import os
sys.path.append('src')

import time
import logging
from database import MultiDatabase
from streaming_metrics import streaming_metrics
from config import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReindexTester:
    """Test various reindexing scenarios."""

    def __init__(self):
        """Initialize database connections."""
        try:
            # Initialize database connection
            streaming_config = config.get_streaming_config()
            self.database = MultiDatabase(streaming_config["adapters"])
            logger.info("✅ Database connection established")

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            sys.exit(1)

    def trigger_optimize_reindex(self):
        """Trigger OPTIMIZE TABLE operation to force reindexing."""
        logger.info("🔄 Starting OPTIMIZE TABLE reindexing test...")

        try:
            # Get ClickHouse client
            clickhouse_adapter = None
            for adapter in self.database.adapters:
                if hasattr(adapter, 'client') and 'clickhouse' in str(type(adapter)).lower():
                    clickhouse_adapter = adapter
                    break

            if not clickhouse_adapter:
                logger.error("❌ ClickHouse adapter not found")
                return False

            # Use the streaming_metrics trigger method
            success = streaming_metrics.trigger_reindex_operation(
                clickhouse_adapter.client,
                "financial_embeddings"
            )

            if success:
                logger.info("✅ OPTIMIZE reindexing test completed")
                print("🎉 Reindexing operation triggered! Check vector_db_metrics.csv for 'reindexing' operations.")
            else:
                logger.error("❌ OPTIMIZE reindexing test failed")

            return success

        except Exception as e:
            logger.error(f"❌ Optimize reindex failed: {e}")
            return False

    def trigger_bulk_load_reindex(self, count: int = 50):
        """Trigger bulk data insertion to force automatic reindexing."""
        logger.info(f"📊 Starting bulk load test ({count} records)...")

        try:
            # Generate bulk test data
            from langchain_community.embeddings import HuggingFaceEmbeddings
            embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

            successful_inserts = 0
            start_time = time.time()

            for i in range(count):
                try:
                    # Generate test data
                    test_text = f"Bulk reindex test data record {i+1}: This is synthetic financial data for testing reindexing operations. Record timestamp: {time.time()}"

                    # Generate embedding
                    embedding_start = time.time()
                    embedding = embedder.embed_documents([test_text])[0]
                    embedding_time = (time.time() - embedding_start) * 1000

                    # Insert to database
                    db_start = time.time()
                    success = self.database.insert_vector(
                        id=f"REINDEX_TEST_{i+1}_{int(time.time())}",
                        text=test_text,
                        embedding=embedding,
                        metadata={
                            "test_type": "bulk_reindex",
                            "record_number": i+1,
                            "timestamp": time.time()
                        }
                    )
                    db_time = (time.time() - db_start) * 1000

                    if success:
                        successful_inserts += 1

                        # Record metrics
                        streaming_metrics.record_database_operation(
                            operation="bulk_vector_insert",
                            table="financial_embeddings",
                            success=True,
                            latency_ms=db_time,
                            records_affected=1
                        )

                    # Small delay to avoid overwhelming the system
                    time.sleep(0.1)

                    if (i + 1) % 10 == 0:
                        logger.info(f"  📈 Inserted {i+1}/{count} records...")

                except Exception as e:
                    logger.warning(f"⚠️ Failed to insert record {i+1}: {e}")

            total_time = time.time() - start_time
            logger.info(f"✅ Bulk load completed: {successful_inserts}/{count} records in {total_time:.2f}s")

            if successful_inserts > count * 0.8:  # 80% success rate
                print(f"🎉 Bulk load completed! {successful_inserts} records inserted.")
                print("📊 This volume should trigger automatic ClickHouse merging/reindexing.")
                print("Check vector_db_metrics.csv for increased latencies and potential 'optimization' operations.")
                return True
            else:
                logger.error(f"❌ Bulk load failed: only {successful_inserts}/{count} successful")
                return False

        except Exception as e:
            logger.error(f"❌ Bulk load test failed: {e}")
            return False

    def trigger_schema_reindex(self):
        """Trigger schema modification to force reindexing."""
        logger.info("🏗️ Starting schema modification reindexing test...")

        try:
            # Get ClickHouse client
            clickhouse_adapter = None
            for adapter in self.database.adapters:
                if hasattr(adapter, 'client') and 'clickhouse' in str(type(adapter)).lower():
                    clickhouse_adapter = adapter
                    break

            if not clickhouse_adapter:
                logger.error("❌ ClickHouse adapter not found")
                return False

            # Add a temporary column (this triggers reindexing)
            reindex_start = time.time()

            try:
                alter_query = "ALTER TABLE financial_embeddings ADD COLUMN IF NOT EXISTS reindex_test_column String DEFAULT ''"
                logger.info(f"🔄 Executing: {alter_query}")

                clickhouse_adapter.client.execute(alter_query)

                reindex_latency = (time.time() - reindex_start) * 1000

                # Record the schema change as reindexing
                streaming_metrics.record_database_operation(
                    operation="schema_modification",
                    table="financial_embeddings",
                    success=True,
                    latency_ms=reindex_latency,
                    records_affected=0
                )

                logger.info(f"✅ Schema modification completed in {reindex_latency:.2f}ms")

                # Remove the test column
                drop_query = "ALTER TABLE financial_embeddings DROP COLUMN IF EXISTS reindex_test_column"
                clickhouse_adapter.client.execute(drop_query)
                logger.info("🧹 Cleaned up test column")

                print("🎉 Schema modification triggered! This causes ClickHouse to reindex.")
                print("Check vector_db_metrics.csv for 'reindexing' operations.")

                return True

            except Exception as e:
                logger.error(f"❌ Schema modification failed: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ Schema reindex test failed: {e}")
            return False

def main():
    """Main function to run reindexing tests."""

    if len(sys.argv) < 2:
        print("""
🔄 Reindexing Test Script

Usage: python trigger_reindex_test.py <operation>

Available operations:
  optimize  - Force table optimization (immediate reindexing)
  bulk      - Insert bulk data (triggers automatic reindexing)
  schema    - Modify schema (forces reindexing)
  all       - Run all tests

Examples:
  python trigger_reindex_test.py optimize
  python trigger_reindex_test.py bulk
  python trigger_reindex_test.py all
        """)
        sys.exit(1)

    operation = sys.argv[1].lower()
    tester = ReindexTester()

    print(f"\n🚀 Starting reindexing test: {operation}")
    print("=" * 50)

    if operation == "optimize":
        success = tester.trigger_optimize_reindex()

    elif operation == "bulk":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        success = tester.trigger_bulk_load_reindex(count)

    elif operation == "schema":
        success = tester.trigger_schema_reindex()

    elif operation == "all":
        print("\n1️⃣ Running OPTIMIZE test...")
        success1 = tester.trigger_optimize_reindex()
        time.sleep(2)

        print("\n2️⃣ Running BULK LOAD test...")
        success2 = tester.trigger_bulk_load_reindex(30)
        time.sleep(2)

        print("\n3️⃣ Running SCHEMA test...")
        success3 = tester.trigger_schema_reindex()

        success = success1 and success2 and success3

    else:
        print(f"❌ Unknown operation: {operation}")
        sys.exit(1)

    print("\n" + "=" * 50)
    if success:
        print("✅ Reindexing test completed successfully!")
        print("\n📊 Check these CSV files for reindexing operations:")
        print("  • vector_db_metrics.csv - Look for 'reindexing' and 'optimization' operation_type")
        print("  • Check latency increases and performance_tier changes")
    else:
        print("❌ Reindexing test failed!")

    print("\n💡 Monitor the vector_db_metrics.csv file to see reindexing operations appear!")

if __name__ == "__main__":
    main()