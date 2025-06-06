import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()  # Load variables from a .env file located in project root if present

from rag.Adapters.ClickHouseAdapter import ClickHouseAdapter
from rag.specterChunker import SpecterChunker
from sentence_transformers import SentenceTransformer

# If API_Gateway metrics are available, import them; otherwise, create a noop fallback
try:
    from api_gateway.metrics.streaming_metrics import streaming_metrics  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    class _DummyMetrics:  # noqa: D101
        def record_message_processing(self, *args, **kwargs):
            pass

    streaming_metrics = _DummyMetrics()  # type: ignore

logger = logging.getLogger(__name__)

class StreamProcessor:
    def __init__(self):
        logger.info("Initializing StreamProcessor components...")
        try:
            # Initialise chunker and embedding model
            self.chunker = SpecterChunker()
            logger.info("SpecterChunker ready")

            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer model loaded")

            # Vector database adapter
            self.vector_store = ClickHouseAdapter()
            logger.info("Connected to ClickHouse")

            self.processing_queue = asyncio.Queue()
            self.is_processing = True
            logger.info("StreamProcessor initialization complete")
        except Exception as e:
            logger.error(f"Error initializing StreamProcessor: {str(e)}", exc_info=True)
            raise

    async def process_message(self, message: Dict[str, Any]):
        """Process a single WebSocket message."""
        start_time = time.time()
        try:
            logger.info(f"Processing message: {message}")

            # Format the ticker data
            ts = datetime.fromtimestamp(message['timestamp'] / 1000)
            timestamp_str = ts.strftime('%Y-%m-%d %H:%M:%S')

            formatted_data = {
                'security': str(message['id']),
                'price': round(message['price'], message['priceHint']),
                'changePercent': round(message['changePercent'], int(message['priceHint'])),
                'tradeVolume': int(message['dayVolume']),
                'timestamp': timestamp_str  # human-readable string for chunk text
            }

            # Convert the formatted dict to a textual representation for chunking.
            text_blob = json.dumps(formatted_data)

            # --- Chunking ---
            chunks = self.chunker.chunk([text_blob])
            chunk_texts = [doc.page_content for doc in chunks]
            logger.info(f"Created {len(chunk_texts)} chunks for {formatted_data['security']}")

            # --- Embedding ---
            embeddings = self.embedding_model.encode(chunk_texts)
            logger.info(f"Generated {len(embeddings)} embeddings for {formatted_data['security']}")

            # --- Persist ---
            metadata = [
                {
                    "source": f"stream_{message['id']}",
                    "chunk_index": idx,
                    "timestamp": ts,  # native datetime for ClickHouse column
                    "price": formatted_data['price'],
                    "change_percent": formatted_data['changePercent'],
                    "volume": formatted_data['tradeVolume']
                }
                for idx in range(len(chunk_texts))
            ]

            self.vector_store.add_embedding(embeddings, chunk_texts, metadata)
            logger.info(f"Successfully stored {len(embeddings)} embeddings for {formatted_data['security']}")

            # --- Metrics ---
            processing_time = time.time() - start_time
            streaming_metrics.record_message_processing(
                message_id=formatted_data['security'],
                processing_time=processing_time,
                chunks_generated=len(chunk_texts),
                embeddings_generated=len(embeddings),
                queue_size=self.processing_queue.qsize(),
                status='success'
            )
            return True

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            streaming_metrics.record_message_processing(
                message_id=message.get('id', 'unknown'),
                processing_time=processing_time,
                chunks_generated=0,
                embeddings_generated=0,
                queue_size=self.processing_queue.qsize(),
                status='error',
                error=str(e)
            )
            return False

    async def start_processing(self):
        """Start the processing loop."""
        logger.info("Starting message processing loop")
        while self.is_processing:
            try:
                message = await self.processing_queue.get()
                await self.process_message(message)
                self.processing_queue.task_done()
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}", exc_info=True)

    async def stop_processing(self):
        """Stop the processing loop."""
        logger.info("Stopping message processing")
        self.is_processing = False
        await self.processing_queue.join()
        logger.info("Processing stopped")
