"""
Independent Financial Data Streaming Service

Streams live financial data from yliveticker, processes it through
configurable embedding models, and stores it in configurable databases.

Can run completely independently of the gRPC service with its own database configuration.
"""

import os
# Fix yliveticker protobuf compatibility issue
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import yliveticker
import json
import logging
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

# Import our modular components
from config import config
from database import MultiDatabase
from streaming_metrics import streaming_metrics
import threading
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def periodic_csv_export():
    """Export streaming metrics to component-specific CSVs every 30 seconds."""
    while True:
        try:
            time.sleep(30)  # Wait 30 seconds

            # Export last 5 minutes of data to component-specific CSV files
            exported_files = streaming_metrics.export_component_csvs(minutes=5)

            if exported_files:
                logger.info(f"🗄️ Auto-exported component metrics:")
                for component, filename in exported_files.items():
                    logger.info(f"  📊 {component}: {filename}")
            else:
                logger.info("🗄️ No new metrics to export")

        except Exception as e:
            logger.error(f"Failed to auto-export streaming metrics: {e}")

# Export the streaming_metrics for external access (for dashboard)
__all__ = ['streaming_metrics', 'FinancialDataStreamer', 'start_streaming']

class FinancialDataStreamer:
    """Independent financial data streaming service with configurable databases."""

    def __init__(self):
        """Initialize the streaming service with configuration."""
        logger.info("🚀 Initializing Financial Data Streaming Service")

        # Get streaming configuration
        streaming_config = config.get_streaming_config()

        # Initialize embedding components
        self.chunker = RecursiveCharacterTextSplitter(
            chunk_size=streaming_config["chunk_size"],
            chunk_overlap=streaming_config["chunk_overlap"]
        )

        self.embedder = HuggingFaceEmbeddings(
            model_name=streaming_config["embedding_model"]
        )

        # Initialize multi-database support
        self.database = MultiDatabase(streaming_config["adapters"])

        # Ticker list
        self.ticker_names = [
            # Major Forex Pairs (24/7 trading for continuous data)
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X",
            "AUDUSD=X", "USDCAD=X", "NZDUSD=X", "EURGBP=X",
            "EURJPY=X", "GBPJPY=X", "EURCHF=X", "GBPCHF=X",

            # Cryptocurrency (24/7 trading) - SIGNIFICANTLY EXPANDED
            # Major Cryptocurrencies (Top 10 by market cap)
            "BTC-USD",   # Bitcoin
            "ETH-USD",   # Ethereum
            "USDT-USD",  # Tether
            "BNB-USD",   # Binance Coin
            "SOL-USD",   # Solana
            "USDC-USD",  # USD Coin
            "XRP-USD",   # Ripple
            "TON11419-USD", # Toncoin
            "DOGE-USD",  # Dogecoin
            "ADA-USD",   # Cardano

            # Popular Altcoins (Next tier)
            "AVAX-USD",  # Avalanche
            "SHIB-USD",  # Shiba Inu
            "DOT-USD",   # Polkadot
            "TRX-USD",   # TRON
            "LINK-USD",  # Chainlink
            "MATIC-USD", # Polygon
            "LTC-USD",   # Litecoin
            "BCH-USD",   # Bitcoin Cash
            "NEAR-USD",  # NEAR Protocol
            "UNI3-USD",  # Uniswap

            # DeFi & Layer 2 Tokens
            "ATOM-USD",  # Cosmos
            "FIL-USD",   # Filecoin
            "VET-USD",   # VeChain
            "ICP-USD",   # Internet Computer
            "APT21794-USD", # Aptos
            "ARB11841-USD", # Arbitrum
            "OP-USD",    # Optimism
            "IMX10603-USD", # Immutable X
            "AAVE-USD",  # Aave
            "MKR-USD",   # Maker

            # Meme & Community Coins
            "PEPE24478-USD", # Pepe
            "FLOKI-USD",     # Floki Inu
            "BONK-USD",      # Bonk
            "WIF-USD",       # dogwifhat

            # Enterprise & Utility Tokens
            "XLM-USD",   # Stellar
            "ALGO-USD",  # Algorand
            "HBAR-USD",  # Hedera
            "FLOW-USD",  # Flow
            "SAND-USD",  # The Sandbox
            "MANA-USD",  # Decentraland
            "ENJ-USD",   # Enjin Coin
            "CHZ-USD",   # Chiliz

            # Stablecoins & Wrapped Assets
            "DAI-USD",   # Dai
            "BUSD-USD",  # Binance USD
            "TUSD-USD",  # TrueUSD

            # Emerging & High Potential
            "SUI20947-USD", # Sui
            "SEI22457-USD", # Sei
            "INJ-USD",      # Injective
            "TIA22861-USD", # Celestia
            "PYTH-USD",     # Pyth Network
            "JUP23095-USD", # Jupiter

            # Australian stocks
            "QAN.AX", "WOW.AX", "COL.AX", "TLS.AX", "JBH.AX",
            # US stocks
            "AAPL", "MSFT", "GOOGL", "AMZN", "META",
            # London stocks
            "HSBA.L", "BP.L", "VOD.L", "GSK.L", "BARC.L",
            # Additional active London stocks
            "LLOY.L", "RKT.L", "BHP.L", "RIO.L", "AAL.L", "CRH.L", "PRU.L", "REL.L", "SHEL.L"
        ]

        logger.info(f"✅ Streaming service initialized:")
        logger.info(f"  📊 Database adapters: {self.database.get_available_adapters()}")
        logger.info(f"  🤖 Embedding model: {streaming_config['embedding_model']}")
        logger.info(f"  📦 Chunk size: {streaming_config['chunk_size']}")
        logger.info(f"  🔄 Chunk overlap: {streaming_config['chunk_overlap']}")

# Initialize the global streamer
streamer = FinancialDataStreamer()

def on_ticker(ws, msg):
    """Process incoming ticker messages using the configured streamer with metrics tracking."""
    ingestion_start = time.time()

    try:
        # Convert message to string and format it nicely
        if isinstance(msg, dict):
            text = json.dumps(msg, indent=2)
            ticker_id = msg.get('id', 'unknown')
        else:
            text = str(msg)
            ticker_id = 'unknown'

        logger.debug(f"Processing raw text for ticker {ticker_id}")

        # METRICS: Record data ingestion timing
        ingestion_latency = (time.time() - ingestion_start) * 1000  # Convert to ms
        streaming_metrics.record_data_ingestion(
            ticker=ticker_id,
            success=True,
            latency_ms=ingestion_latency,
            data_size=len(text),
            metadata={"source": "yliveticker"}
        )

        # METRICS: Track chunking operation timing
        chunking_start = time.time()

        # Chunk the message using configured chunker
        chunks = streamer.chunker.split_text(text)

        # METRICS: Record chunking performance
        chunking_latency = (time.time() - chunking_start) * 1000  # Convert to ms
        streaming_metrics.record_chunking_operation(
            ticker=ticker_id,
            original_text=text,
            chunks=chunks,
            latency_ms=chunking_latency,
            chunker_config={
                "chunk_size": streamer.chunker._chunk_size,
                "chunk_overlap": streamer.chunker._chunk_overlap,
                "length_function": str(streamer.chunker._length_function),
                "separators": streamer.chunker._separators
            }
        )

        logger.debug(f"Processing {len(chunks)} chunks for ticker {ticker_id} (chunking: {chunking_latency:.2f}ms)")

        if not chunks:
            return

        # METRICS: Track embedding generation timing
        embedding_start = time.time()
        embeddings = streamer.embedder.embed_documents(chunks)
        embedding_latency = (time.time() - embedding_start) * 1000  # Convert to ms

        logger.debug(f"Generated {len(embeddings)} embeddings for ticker {ticker_id}")

        # Record embedding metrics
        streaming_metrics.record_embedding_generation(
            text=text,
            success=True,
            latency_ms=embedding_latency,
            embedding_dim=len(embeddings[0]) if embeddings else 0,
            model_name=streamer.embedder.model_name
        )

        # Process each chunk and its embedding
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            try:
                # METRICS: Track Vector Database load time
                vd_start = time.time()

                # Store in ALL configured databases
                success = streamer.database.insert_vector(
                    id=f"{ticker_id}_chunk_{i}_{int(time.time())}",  # Unique ID
                    text=chunk,
                    embedding=embedding,
                    metadata={
                        "source": "yliveticker",
                        "chunk_index": i,
                        "ticker": ticker_id,
                        "timestamp": time.time()
                    }
                )

                # METRICS: Record Vector Database load time
                vd_latency = (time.time() - vd_start) * 1000  # Convert to ms
                streaming_metrics.record_database_operation(
                    operation="vector_insert",
                    table="financial_vectors",
                    success=success,
                    latency_ms=vd_latency,
                    records_affected=1
                )

                if success:
                    logger.debug(f"✅ Successfully processed chunk {i} for ticker {ticker_id} (VD load: {vd_latency:.2f}ms)")
                else:
                    logger.warning(f"⚠️ Failed to process chunk {i} for ticker {ticker_id}")

            except Exception as e:
                logger.error(f"❌ Error processing chunk {i} for ticker {ticker_id}: {str(e)}")
                # Record the error
                streaming_metrics.record_error(
                    error_type="database_insert_error",
                    error_message=str(e),
                    component="clickhouse",
                    ticker=ticker_id
                )

    except Exception as e:
        logger.error(f"❌ Error processing message for ticker: {str(e)}")
        # Record ingestion error
        streaming_metrics.record_data_ingestion(
            ticker=ticker_id if 'ticker_id' in locals() else 'unknown',
            success=False,
            latency_ms=(time.time() - ingestion_start) * 1000,
            data_size=len(str(msg)),
            metadata={"error": str(e)}
        )

def on_error(ws, error):
    """Handle WebSocket errors."""
    logger.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code=None, close_msg=None):
    """Handle WebSocket close."""
    logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")

def start_streaming():
    """Start the financial data streaming service."""
    logger.info("🚀 Starting financial data streaming service")

    # Display configuration
    stats = streamer.database.get_stats()
    logger.info(f"📊 Database configuration:")
    for adapter_name in stats["available_adapters"]:
        logger.info(f"  • {adapter_name}: ready")

    # Start automatic CSV export thread
    csv_thread = threading.Thread(target=periodic_csv_export, daemon=True)
    csv_thread.start()
    logger.info("🗄️ Started automatic component CSV export (every 30 seconds → 4 pipeline CSV files)")

    ticker = yliveticker.YLiveTicker(
        on_ticker=on_ticker,
        on_error=on_error,
        on_close=on_close,
        ticker_names=streamer.ticker_names
    )

    logger.info("📡 Live streaming started. Press Ctrl+C to stop.")
    logger.info(f"📈 Monitoring {len(streamer.ticker_names)} financial instruments")

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Streaming stopped by user")

if __name__ == "__main__":
    start_streaming()
