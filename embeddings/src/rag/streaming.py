from dotenv import load_dotenv
import yliveticker
import json
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from rag.Adapters.ClickHouseAdapter import ClickHouseAdapter

load_dotenv()

# Ticker list
ticker_names = [
    # Australian stocks
    "QAN.AX", "WOW.AX", "COL.AX", "TLS.AX", "JBH.AX",
    # US stocks
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    # London stocks
    "HSBA.L", "BP.L", "VOD.L", "GSK.L", "BARC.L",
    # Additional active London stocks
    "LLOY.L", "RKT.L", "BHP.L", "RIO.L", "AAL.L", "CRH.L", "PRU.L", "REL.L", "SHEL.L"
]

# Initialize components
chunker = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Use your working custom ClickHouse adapter (no experimental settings)
print("Initializing ClickHouse adapter...")
clickhouse = ClickHouseAdapter()
print("ClickHouse adapter initialized successfully")

def on_ticker(ws, msg):
    try:
        # Convert message to string and format it nicely
        if isinstance(msg, dict):
            text = json.dumps(msg, indent=2)
            ticker_id = msg.get('id', 'unknown')
        else:
            text = str(msg)
            ticker_id = 'unknown'

        print(f"DEBUG: Raw text type: {type(text)}")

        # Chunk the message
        chunks = chunker.split_text(text)
        print(f"DEBUG: Processing {len(chunks)} chunks for ticker {ticker_id}")
        print(f"DEBUG: First chunk type: {type(chunks[0])}")

        if not chunks:
            return

        # Convert chunks to Document objects and then embed them
        chunk_docs = [Document(page_content=chunk) for chunk in chunks]
        print(f"DEBUG: Created {len(chunk_docs)} Document objects")

        embeddings = embedder.embed_documents(chunks)  # Pass strings, not Document objects
        print(f"DEBUG: Got {len(embeddings)} embeddings, first embedding type: {type(embeddings[0])}")

        # Process each chunk and its embedding
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            try:
                print(f"DEBUG: Processing chunk {i}, chunk type: {type(chunk)}, embedding type: {type(embedding)}")

                success = clickhouse.add_embedding(
                    vector=embedding,
                    text=chunk,  # Pass the string directly, not the Document
                    metadata={
                        "source": "yliveticker",
                        "chunk_index": i,
                        "ticker": ticker_id
                    }
                )
                if success:
                    print(f"✅ Successfully processed chunk {i} for ticker {ticker_id}")
                else:
                    print(f"❌ Failed to process chunk {i} for ticker {ticker_id}")
            except Exception as e:
                print(f"❌ Error processing chunk {i}: {str(e)}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"❌ Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code=None, close_msg=None):
    print(f"WebSocket closed: {close_status_code} - {close_msg}")

if __name__ == "__main__":
    ticker = yliveticker.YLiveTicker(
        on_ticker=on_ticker,
        on_error=on_error,
        on_close=on_close,
        ticker_names=ticker_names
    )
    print("Streaming started. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopped.")
