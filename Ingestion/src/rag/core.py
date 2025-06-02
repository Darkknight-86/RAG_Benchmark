import os
import csv
import time
import xml.etree.ElementTree as ET

import config
from utils import (
    sanitize_filename, clean_existing_files,
    s3_key_exists, upload_to_s3_with_encoding,
    is_within_date_range, extract_paper_metadata,
    make_arxiv_request, download_file,
    safe_parse_pdf, get_text_preview,
    format_paper_row, ARXIV_CSV_HEADERS
)


# ==================== PDF Processing Functions ====================

def parse_pdf_and_get_description(pdf_path):
    """Parse PDF and return truncated description."""
    success, content = safe_parse_pdf(pdf_path, config.LLAMA_PARSER)
    if success:
        return get_text_preview(content, num_lines=5)
    return content  # Return error message


def upload_to_s3(content, key):
    """Upload content to S3 bucket."""
    # Check if dry run mode
    if config.IS_DRY_RUN:
        print(f"[DRY RUN] Would upload to S3: {key}")
        print(f"[DRY RUN] Content size: {len(str(content))} characters")
        return True
    
    # Check if key already exists
    if s3_key_exists(config.S3_CLIENT, config.BUCKET_NAME, key):
        print(f"Warning: Key {key} already exists in S3, skipping upload...")
        return False
    
    # Upload the object
    success = upload_to_s3_with_encoding(
        config.S3_CLIENT, 
        content, 
        key, 
        config.BUCKET_NAME
    )
    
    if success:
        print(f"Uploaded to S3: {key}")
    
    return success


def process_csv_and_pdfs(csv_filename):
    """Process CSV file and parse/upload PDFs to S3."""
    if not os.path.exists(csv_filename):
        print(f"Error: CSV file '{csv_filename}' not found!")
        return

    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for idx, row in enumerate(reader, 1):
            title = row['title']
            authors = row['author(s)']
            original_description = row['description']
            file_location = row['file_location']

            print(f"\n{'='*80}")
            print(f"Processing paper {idx}: {title[:50]}...")

            full_text = ""
            if not os.path.exists(file_location):
                print(f"Warning: PDF file not found at {file_location}")
                llama_description = "PDF file not found"
            else:
                print("Parsing PDF with LlamaParse...")
                success, full_text = safe_parse_pdf(file_location, config.LLAMA_PARSER)
                if success:
                    llama_description = get_text_preview(full_text, num_lines=5)
                else:
                    llama_description = full_text  # Error message

            # Upload full text only
            if full_text and not full_text.startswith("Error:"):
                pdf_name = os.path.splitext(os.path.basename(file_location))[0]
                fulltext_key = f"papers/{pdf_name}.txt"
                
                if config.IS_DRY_RUN:
                    print(f"[DRY RUN] Would upload full text to S3: {fulltext_key}")
                    print(f"[DRY RUN] Full text size: {len(full_text)} characters")
                else:
                    # Use existing S3 check in upload_to_s3
                    upload_to_s3(full_text, fulltext_key)

            print("\n--- PAPER INFO ---")
            print(f"Title: {title}")
            print(f"Authors: {authors}")
            print(f"\nOriginal arXiv Description:\n{original_description}")
            print(f"\nLlamaParse Extracted Description:\n{llama_description}")

            time.sleep(1)


# ==================== arXiv Scraping Functions ====================

def scrape_arxiv_papers(years=None, max_results=None, output_dir=None, 
                       csv_filename=None, clean_existing=True):
    """
    Main function to scrape arXiv papers and download PDFs.
    
    Args:
        years: Number of years to look back for papers
        max_results: Maximum number of results to fetch
        output_dir: Directory to save PDFs
        csv_filename: Name of the CSV file to save metadata
        clean_existing: Whether to remove existing files before starting
    
    Returns:
        dict: Summary statistics of the scraping process
    """
    # Use config defaults if not provided
    years = years or config.DEFAULT_YEAR_DIFF
    max_results = max_results or config.DEFAULT_MAX_RESULTS
    output_dir = output_dir or config.DEFAULT_OUTPUT_DIR
    csv_filename = csv_filename or config.DEFAULT_CSV_FILE
    
    # Clean existing data if requested
    if clean_existing:
        clean_existing_files(output_dir, csv_filename)
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Define the arXiv query URL
    arxiv_url = f'{config.DEFAULT_API_ENDPOINT}/api/query?search_query=all:economics&start=0&max_results={max_results}'
    
    # Send request to arXiv API
    print(f"Fetching metadata from arXiv for {max_results} results within the last {years} years")
    response = make_arxiv_request(arxiv_url)
    
    if not response:
        return {"error": "Failed to retrieve metadata"}
    
    print("Successfully retrieved metadata from arXiv!")
    
    # Parse the XML response
    root = ET.fromstring(response.content)
    
    # Statistics
    attempted_downloads = 0
    successful_downloads = 0
    download_start_time = time.time()
    
    # Open CSV file for writing
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=ARXIV_CSV_HEADERS)
        writer.writeheader()
        
        # Process each entry
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            # Extract metadata
            metadata = extract_paper_metadata(entry)
            
            # Check if paper is within date range
            if not is_within_date_range(metadata['updated'], metadata['published'], years):
                continue
            
            attempted_downloads += 1
            
            if metadata['pdf_link']:
                # Create filename
                filename = sanitize_filename(metadata['title'])
                pdf_path = os.path.join(output_dir, filename)
                absolute_pdf_path = os.path.abspath(pdf_path)
                
                # Download PDF if it doesn't exist
                if not os.path.exists(pdf_path):
                    success, download_time = download_file(metadata['pdf_link'], pdf_path)
                    if success:
                        print(f"Downloaded: {filename} (Time: {download_time:.2f} seconds)")
                        successful_downloads += 1
                    else:
                        print(f"Failed to download PDF for: {metadata['title']}")
                        continue
                else:
                    print(f"Skipped (already exists): {filename}")
                    successful_downloads += 1
                
                # Write to CSV
                row_data = format_paper_row(
                    metadata['title'],
                    metadata['authors_str'],
                    metadata['published'],
                    metadata['updated'],
                    metadata['summary'],
                    absolute_pdf_path
                )
                writer.writerow(row_data)
            else:
                print(f"No PDF link found for: {metadata['title']}")
    
    # Calculate statistics
    download_end_time = time.time()
    total_time = download_end_time - download_start_time
    
    # Print summary
    print(f"\nSummary:")
    print(f"Attempted downloads: {attempted_downloads}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"CSV file created: {csv_filename}")
    print(f"Time taken: {total_time:.2f} seconds")
    
    if successful_downloads > 0:
        print(f"Average time per document: {total_time / successful_downloads:.2f} seconds")
    
    # Return statistics
    return {
        "attempted_downloads": attempted_downloads,
        "successful_downloads": successful_downloads,
        "csv_filename": csv_filename,
        "output_dir": output_dir,
        "total_time": total_time
    }