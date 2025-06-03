from .VectorStoreAdapter import VectorStoreAdapter

# class PostgresAdapter(VectorStoreAdapter):
#     def add_embedding(self, vector, text, metadata):
#         pass


import os
import time
import fitz  # PyMuPDF
import psycopg2
from sentence_transformers import SentenceTransformer

# Load sentence-transformer model
# model = SentenceTransformer("all-MiniLM-L6-v2")

# PostgreSQL connection (for Docker on port 5433)
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="yourpassword",  # change if needed
    dbname="postgres"
)
cur = conn.cursor()

# Create the table if it doesn't exist
cur.execute("""
CREATE TABLE IF NOT EXISTS pdf_chunks (
    id SERIAL PRIMARY KEY,
    file_name TEXT,
    chunk TEXT,
    embedding VECTOR(384)
);
""")
conn.commit()

PDF_DIR = "pdfs"

def insert_chunk(file_name, chunk_text, embedding):
    cur.execute(
        "INSERT INTO pdf_chunks (file_name, chunk, embedding) VALUES (%s, %s, %s)",
        (file_name, chunk_text, embedding)
    )

def process_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if not text:
            continue

        start = time.time()
        embedding = model.encode(text).tolist()
        duration = time.time() - start

        insert_chunk(os.path.basename(pdf_path), text, embedding)
        print(f"Embedded page {i+1} of {os.path.basename(pdf_path)} in {duration:.2f} seconds")


def run_all():
    for file in os.listdir(PDF_DIR):
        if file.endswith(".pdf"):
            process_pdf(os.path.join(PDF_DIR, file))
    conn.commit()
    print("All chunks inserted into pgvector!")

if __name__ == "__main__":
    run_all()
