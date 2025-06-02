import os
from dotenv import load_dotenv
import boto3
from llama_parse import LlamaParse

load_dotenv()

# Llama parsing and S3 uploader
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

if not aws_access_key_id or not aws_secret_access_key:
    raise ValueError("Error: Missing AWS credentials in environment variables.")

S3_CLIENT = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
)

BUCKET_NAME = 'ragproject-store'

LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
if not LLAMA_API_KEY:
    raise ValueError("LLAMA_API_KEY not found in environment variables.")

LLAMA_PARSER = LlamaParse(
    api_key=LLAMA_API_KEY,
    result_type="text",
    verbose=False,
    language="en"
)

# PDF Scraper
DEFAULT_OUTPUT_DIR = "arxiv_pdfs"
DEFAULT_CSV_FILE = "arxiv_papers_metadata.csv"
DEFAULT_API_ENDPOINT = "http://export.arxiv.org"
DEFAULT_YEAR_DIFF = 2
DEFAULT_MAX_RESULTS = 100

# Testing
IS_DRY_RUN = True