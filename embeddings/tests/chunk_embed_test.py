import boto3
from RAG.src.rag.chunker import SpecterChunker
from RAG.src.rag.embedder import SpecterEmbedder
from dotenv import load_dotenv
import os

# Setup
object_key = "scores.txt"
bucket_name = "ragproject-store"

# Load environment variables
load_dotenv()

# Common S3 setup
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# Get test object
response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
text_data = response['Body'].read().decode('utf-8')

# Chunk the document
chunker = SpecterChunker()
chunks = chunker.chunk([text_data])
print(f"\nChunked into {len(chunks)} pieces.")
for i, c in enumerate(chunks[:3]):
    print(f"\n--- Chunk {i} ---\n{c.page_content[:300]}...\n")


# --- Step 3: Embed chunks ---
embedder = SpecterEmbedder()
texts = [doc.page_content for doc in chunks]
embeddings = embedder.embed(texts)
print(f"\nGenerated {len(embeddings)} embeddings of size {len(embeddings[0])} each.")

# --- Step 4: Debug check ---
print(f"\nSample embedding vector:\n{embeddings[0][:10]}...")