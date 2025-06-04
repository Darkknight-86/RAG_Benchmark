from fastapi import FastAPI
from Adapters.CassandraAdapter import CassandraAdapter
from Adapters.ClickHouseAdapter import ClickHouseAdapter
from Adapters.OpenSearchAdapter import OpenSearchAdapter
from Adapters.PostgresAdapter import PostgresAdapter
from chunker import SpecterChunker
from embedder import SpecterEmbedder
from dotenv import load_dotenv
import os
import boto3

app = FastAPI()
# Load environment variables
load_dotenv()

# Common S3 setup
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)
bucket_name = 'ragproject-store'

# Shared chunker, embedder, and vector store adapter list
chunker = SpecterChunker()
embedder = SpecterEmbedder()
vector_stores = [
    CassandraAdapter(),
    #PostgresAdapter(),
    #ClickHouseAdapter(),
    OpenSearchAdapter()
] # list[VectorStoreAdapter]

'''
Adds all data from AWS S3 to the vector databases
'''
@app.post("/add-all-data")
async def add_all_data():
    prefix = ''
    total_chunks = 0
    files_processed = 0

    try:
        # All data
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        if 'Contents' not in response:
            return {"message": "No data found."}

        # Iterate through each object in the bucket
        for obj in response['Contents']:
            # Get the key
            key = obj['Key']
            print(f"Processing {key}...")
            files_processed += 1

            # Process obj
            try:
                # Get the single file
                s3_object = s3_client.get_object(Bucket=bucket_name, Key=key)
                text_data = s3_object['Body'].read().decode('utf-8')

                # Chunk and embed this file
                chunks = chunker.chunk([text_data])

                chunk_texts = [doc.page_content for doc in chunks]

                embeddings = embedder.embed(chunk_texts)

                all_metadata = [{"source": key, "chunk_index": i} for i in range(len(chunk_texts))]

                for store in vector_stores:
                    store.add_embedding(embeddings, chunk_texts, all_metadata)

            except Exception as key_e:
                print(f"Error processing {key}: {key_e}")

    except Exception as objs_e:
        return {"message": f"Error listing S3 objects: {str(objs_e)}"}

    return {
        "message": f"{files_processed} files processed.",
        "total_chunks_added": total_chunks
    }


'''
Given a Key, adds that single data point to the vector databases
'''
@app.post("/add-single-data")
async def add_single_data(object_key: str):

    try:
        s3_object = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        text_data = s3_object['Body'].read().decode('utf-8')

    except Exception as e:
        return {"message": f"Error retrieving object: {str(e)}"}

    chunks = chunker.chunk([text_data])
    chunk_texts = [doc.page_content for doc in chunks]
    embeddings = embedder.embed(chunk_texts)

    for i, embedding in enumerate(embeddings):
        metadata = {"source": object_key, "chunk_index": i}
        chunk_text = chunk_texts[i]

        for store in vector_stores:
            store.add_embedding(embedding, chunk_text, metadata)

    return {"message": f"{len(chunks)} chunks added from {object_key}."}