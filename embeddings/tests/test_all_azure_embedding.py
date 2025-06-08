import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from stockChunker import StockChunker
from stockEmbedder import StockEmbedder
from utils import try_parse_json_or_text

# Setup
load_dotenv()
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_BLOB_NAME")

blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client(container_name)

chunker = StockChunker()
embedder = StockEmbedder()

blob_list = container_client.list_blobs()
blob_count = 0
total_chunks = 0
total_embeddings = 0

print(f"\n📦 Scanning Azure Blob Container: {container_name}\n")

for blob in blob_list:
    blob_count += 1
    print(f"📄 Downloading blob: {blob.name}")
    blob_client = container_client.get_blob_client(blob.name)
    raw_data = blob_client.download_blob().readall().decode('utf-8')

    try:
        text_data = try_parse_json_or_text(raw_data)
    except Exception as e:
        print(f"⚠️ Skipping invalid blob {blob.name}: {e}")
        continue

    # --- Chunk ---
    chunks = chunker.chunk([text_data])
    print(f"🧩 {len(chunks)} chunks from {blob.name}")
    total_chunks += len(chunks)

    # --- Embed ---
    chunk_texts = [doc.page_content for doc in chunks]
    if chunk_texts:
        embeddings = embedder.embed(chunk_texts)
        print(f"🧠 {len(embeddings)} embeddings generated.\n")
        total_embeddings += len(embeddings)
    else:
        print("⚠️ No valid chunks to embed.\n")

print(f"\n✅ Finished processing {blob_count} blobs.")
print(f"📊 Total chunks: {total_chunks}")
print(f"🧠 Total embeddings: {total_embeddings}")