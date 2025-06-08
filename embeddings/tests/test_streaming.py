import asyncio
import logging
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from Adapters.ClickHouseAdapter import ClickHouseAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_clickhouse_connection():
    try:
        # Initialize ClickHouse adapter
        logger.info("Testing ClickHouse connection...")
        vector_store = ClickHouseAdapter()

        # Test data
        test_data = {
            "symbol": "AAPL",
            "price": 150.25,
            "change_percent": 1.5,
            "volume": 1000000,
            "timestamp": datetime.now().isoformat(),
            "text": "Test streaming data for Apple stock price at $150.25 with 1.5% change"
        }

        # Generate embedding for the text
        logger.info("Generating embedding for test data...")
        if vector_store.embedding_model is None:
            logger.error("No embedding model available")
            return

        embedding = vector_store.embedding_model.encode([test_data["text"]])[0].tolist()
        logger.info(f"Generated embedding with {len(embedding)} dimensions")

        # Try to insert test data with embedding
        logger.info("Inserting test data...")
        success = vector_store.add_embedding(
            vector=embedding,
            text=test_data["text"],
            metadata={
                "ticker": test_data["symbol"],
                "price": test_data["price"],
                "change_percent": test_data["change_percent"],
                "volume": test_data["volume"],
                "source": "test_streaming"
            }
        )

        if success:
            logger.info("✅ Successfully inserted test data")
        else:
            logger.error("❌ Failed to insert test data")
            return

        # Try to read it back
        logger.info("Reading back test data...")
        results = vector_store.client.query(
            "SELECT * FROM rag_chunks_v2 WHERE source = 'test_streaming' ORDER BY timestamp DESC LIMIT 1"
        )

        if results.result_rows:
            logger.info("✅ Successfully read back data:")
            for row in results.result_rows:
                logger.info(f"Row: {row}")
        else:
            logger.warning("❌ No data found in query results")

        # Test similarity search
        logger.info("Testing similarity search...")
        search_results = vector_store.similarity_search("Apple stock price", k=1)
        if search_results:
            logger.info("✅ Similarity search working:")
            for doc in search_results:
                logger.info(f"Found: {doc.page_content[:100]}...")
                logger.info(f"Metadata: {doc.metadata}")
        else:
            logger.warning("❌ No similarity search results")

        logger.info("🎉 ClickHouse connection test completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error during ClickHouse test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_clickhouse_connection())