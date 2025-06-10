from azure.storage.blob import BlobServiceClient
from stockChunker import StockChunker
from stockEmbedder import StockEmbedder
from utils import try_parse_json_or_text
from dotenv import load_dotenv
import os

# Load env vars
load_dotenv()
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_BLOB_NAME")

# Azure client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client(container_name)

# Get first blob
blob_list = list(container_client.list_blobs())
if not blob_list:
    print("❌ No blobs found in container.")
    exit()

first_blob = blob_list[1].name
print(f"📄 Downloading blob: {first_blob}")

blob_client = container_client.get_blob_client(first_blob)
raw_data = blob_client.download_blob().readall().decode('utf-8')

# Try to parse as JSON → fallback to raw text
text_data = try_parse_json_or_text(raw_data)

if not text_data.strip():
    print("❌ No usable text data.")
    exit()

print(f"\n📜 Raw text (first 500 chars):\n{text_data[:500]}")

# Chunk
chunker = StockChunker()
chunks = chunker.chunk([text_data])
print(f"\n🧩 Chunked into {len(chunks)} pieces.")

if not chunks:
    print("⚠️ No chunks generated.")
    exit()

for i, c in enumerate(chunks):
    print(f"\n--- Chunk {i} ---\n{c.page_content}")

# Embed
embedder = StockEmbedder()
texts = [c.page_content for c in chunks]
embeddings = embedder.embed(texts)

print(f"\n🧠 Generated {len(embeddings)} embeddings of size {len(embeddings[0])}.")
print(f"\n🔎 Sample embedding vector:\n{embeddings[0][:10]}...")