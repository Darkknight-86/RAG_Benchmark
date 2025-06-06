from fastapi import FastAPI
from Adapters.CassandraAdapter import CassandraAdapter
from Adapters.ClickHouseAdapter import ClickHouseAdapter
from Adapters.OpenSearchAdapter import OpenSearchAdapter
from Adapters.PostgresAdapter import PostgresAdapter
from rag.utils import try_parse_json_or_text
from stockChunker import StockChunker
from stockEmbedder import StockEmbedder
from dotenv import load_dotenv
import os
import logging
import time
from typing import List
from sentence_transformers import SentenceTransformer
from azure.storage.blob import BlobServiceClient

app = FastAPI()
# Load environment variables
load_dotenv()

# Common Azure Blob setup
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_BLOB_NAME = os.getenv("AZURE_BLOB_NAME")
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_BLOB_NAME)

# Shared chunker, embedder, and vector store adapter list
chunker = StockChunker()
embedder = StockEmbedder()
vector_stores = [
    CassandraAdapter(),
    PostgresAdapter(),
    ClickHouseAdapter(),
    OpenSearchAdapter()
] # list[VectorStoreAdapter]

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the model
logger.info("Initializing sentence transformer model")
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Successfully loaded sentence transformer model")
except Exception as e:
    logger.error(f"Failed to load sentence transformer model: {str(e)}", exc_info=True)
    raise

def get_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for the given text.

    Args:
        text: The input text to generate embeddings for

    Returns:
        List of float values representing the embedding
    """
    logger.info(f"Generating embeddings for text: {text[:100]}...")
    start_time = time.time()

    try:
        # Generate embeddings
        embedding = model.encode(text)

        # Convert to list of floats
        result = embedding.tolist()

        duration = time.time() - start_time
        logger.info(f"Generated embeddings of dimension {len(result)} in {duration:.2f}s")
        return result

    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}", exc_info=True)
        raise

'''
Adds all data from AWS S3 to the vector databases
'''
@app.post("/add-all-data")
async def add_all_data():
    total_chunks = 0
    files_processed = 0

    try:
        blob_list = container_client.list_blobs()

        for blob in blob_list:
            blob_name = blob.name
            print(f"Processing {blob_name}...")
            files_processed += 1

            try:
                blob_client = container_client.get_blob_client(blob_name)
                raw_data = blob_client.download_blob().readall().decode('utf-8')
                text_data = try_parse_json_or_text(raw_data)

                chunks = chunker.chunk([text_data])
                chunk_texts = [doc.page_content for doc in chunks]
                embeddings = embedder.embed(chunk_texts)

                all_metadata = [{"source": blob_name, "chunk_index": i} for i in range(len(chunk_texts))]

                for store in vector_stores:
                    store.add_embedding(embeddings, chunk_texts, all_metadata)

            except Exception as key_e:
                print(f"Error processing {blob_name}: {key_e}")

    except Exception as objs_e:
        return {"message": f"Error listing blobs: {str(objs_e)}"}

    return {
        "message": f"{files_processed} blobs processed.",
        "total_chunks_added": total_chunks
    }

@app.post("/add-single-data")
async def add_single_data(blob_name: str):
    try:
        blob_client = container_client.get_blob_client(blob_name)
        raw_data = blob_client.download_blob().readall().decode('utf-8')
        text_data = try_parse_json_or_text(raw_data)

    except Exception as e:
        return {"message": f"Error retrieving blob: {str(e)}"}

    chunks = chunker.chunk([text_data])
    chunk_texts = [doc.page_content for doc in chunks]
    embeddings = embedder.embed(chunk_texts)

    for i, embedding in enumerate(embeddings):
        metadata = {"source": blob_name, "chunk_index": i}
        chunk_text = chunk_texts[i]

        for store in vector_stores:
            store.add_embedding(embedding, chunk_text, metadata)

    return {"message": f"{len(chunks)} chunks added from {blob_name}."}