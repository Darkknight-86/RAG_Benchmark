import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import asyncio
import logging
import yliveticker
import sys
from queue import Queue

from rag.streaming import StreamingProcessor
from rag.stockChunker import StockChunker
from rag.stockEmbedder import StockEmbedder
from rag.Adapters.ClickHouseAdapter import ClickHouseAdapter

__all__ = ["main"]

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("Initializing components...")
        # Initialize components
        chunker = StockChunker()
        embedder = StockEmbedder()
        clickhouse = ClickHouseAdapter()

        # Initialize stream processor
        stream_processor = StreamingProcessor(chunker, embedder, clickhouse)
        logger.info("Stream processor initialized successfully")

        # Create processing queue
        processing_queue = Queue()
        stream_processor.processing_queue = processing_queue

        # Start the processing loop
        logger.info("Starting processing loop...")
        processing_task = asyncio.create_task(stream_processor.process_messages(processing_queue))
        logger.info("Processing loop started")

        # Grab the running event loop for thread-safe callbacks
        loop = asyncio.get_running_loop()

        # Start WebSocket connection
        logger.info("Connecting to WebSocket...")

        def on_ticker(ws, msg):
            # Thread-safe hand-off to the asyncio event loop
            asyncio.run_coroutine_threadsafe(
                stream_processor.processing_queue.put(msg), loop
            )

        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")

        # Initialize WebSocket connection
        ticker = yliveticker.YLiveTicker(
            on_ticker=on_ticker,
            on_error=on_error,
            on_close=on_close,
            ticker_names=[
                # Australian stocks
                "QAN.AX", "WOW.AX", "COL.AX", "TLS.AX", "JBH.AX",
                # US stocks
                "AAPL", "MSFT", "GOOGL", "AMZN", "META",
                # London stocks
                "HSBA.L", "BP.L", "VOD.L", "GSK.L", "BARC.L",
                # Additional active London stocks
                "LLOY.L", "RKT.L", "VOD.L", "BHP.L", "RIO.L", "AAL.L", "CRH.L", "PRU.L", "REL.L", "SHEL.L"
            ]
        )
        logger.info("WebSocket connection established")

        try:
            # Keep the main task running
            logger.info("Stream processor is running. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            # Clean shutdown
            logger.info("Shutting down stream processor...")
            processing_task.cancel()
            logger.info("Stream processor stopped")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
