import os
import csv
import time
import uuid
import boto3
from dotenv import load_dotenv
from llama_parse import LlamaParse
from fastapi import FastAPI
from botocore.exceptions import ClientError

app = FastAPI()

# Load environment variables
load_dotenv()

# Setup S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
bucket_name = 'ragproject-store'

def parse_pdf_and_get_description(pdf_path):
    try:
        api_key = os.getenv("LLAMA_API_KEY")
        if not api_key:
            raise ValueError("LLAMA_API_KEY not found in environment variables.")

        parser = LlamaParse(
            api_key=api_key,
            result_type="text",
            verbose=False,
            language="en"
        )

        documents = parser.load_data(pdf_path)
        full_text = "".join(doc.text + "\n" for doc in documents)

        # Only return the first few lines (e.g., first 5 lines)
        truncated_text = "\n".join(full_text.splitlines()[:5])
        return truncated_text
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
        return f"Error: Could not parse PDF - {str(e)}"

def upload_to_s3(content, key):
    try:
        # Check if key already exists
        try:
            s3_client.head_object(Bucket=bucket_name, Key=key)
            print(f"Warning: Key {key} already exists in S3, skipping upload...")
            return False
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Object doesn't exist, proceed with upload
                pass
            else:
                # Some other error occurred
                raise e
        
        # Upload the object
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=str(content)
        )
        print(f"Uploaded to S3: {key}")
        return True
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return False

def process_csv_and_pdfs(csv_filename):
    if not os.path.exists(csv_filename):
        print(f"Error: CSV file '{csv_filename}' not found!")
        return

    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for idx, row in enumerate(reader, 1):
            title = row['title']
            authors = row['author(s)']
            published_date = row['published_date']
            updated_date = row['updated_date']
            original_description = row['description']
            scraped_date = row['scraped_date']
            file_location = row['file_location']

            print(f"\n{'='*80}")
            print(f"Processing paper {idx}: {title[:50]}...")

            full_text = ""
            if not os.path.exists(file_location):
                print(f"Warning: PDF file not found at {file_location}")
                llama_description = "PDF file not found"
            else:
                print("Parsing PDF with LlamaParse...")
                try:
                    api_key = os.getenv("LLAMA_API_KEY")
                    parser = LlamaParse(
                        api_key=api_key,
                        result_type="text",
                        verbose=False,
                        language="en"
                    )
                    documents = parser.load_data(file_location)
                    full_text = "".join(doc.text + "\n" for doc in documents)
                    llama_description = "\n".join(full_text.splitlines()[:5])  # truncated for dashboard
                except Exception as e:
                    print(f"Error parsing {file_location}: {e}")
                    llama_description = f"Error: Could not parse PDF - {str(e)}"

            # Upload full text only
            if full_text:
                pdf_name = os.path.splitext(os.path.basename(file_location))[0]
                fulltext_key = f"papers/{pdf_name}.txt"
                try:
                    # Check if key exists before uploading
                    try:
                        s3_client.head_object(Bucket=bucket_name, Key=fulltext_key)
                        print(f"Warning: PDF {fulltext_key} already exists in S3, skipping upload...")
                    except ClientError as e:
                        if e.response['Error']['Code'] == '404':
                            # Object doesn't exist, proceed with upload
                            s3_client.put_object(
                                Bucket=bucket_name,
                                Key=fulltext_key,
                                Body=full_text.encode('utf-8')
                            )
                            print(f"Uploaded full text to S3: {fulltext_key}")
                        else:
                            # Some other error occurred
                            raise e
                except Exception as e:
                    print(f"Error uploading full text to S3: {e}")

            print("\n--- PAPER INFO ---")
            print(f"Title: {title}")
            print(f"Authors: {authors}")
            print(f"\nOriginal arXiv Description:\n{original_description}")
            print(f"\nLlamaParse Extracted Description:\n{llama_description}")

            time.sleep(1)