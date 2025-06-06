import asyncio
import logging
from datetime import datetime
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
            "text": "Test streaming data for Apple stock"
        }

        # Try to insert test data
        logger.info("Inserting test data...")
        vector_store.add_embedding(
            text=test_data["text"],
            metadata=test_data
        )

        # Try to read it back
        logger.info("Reading back test data...")
        results = vector_store.client.query(
            "SELECT * FROM rag_chunks WHERE symbol = 'AAPL' ORDER BY timestamp DESC LIMIT 1"
        )

        if results.result_rows:
            logger.info("Successfully read back data:")
            for row in results.result_rows:
                logger.info(f"Row: {row}")
        else:
            logger.warning("No data found in query results")

        logger.info("ClickHouse connection test completed successfully!")

    except Exception as e:
        logger.error(f"Error during ClickHouse test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_clickhouse_connection())