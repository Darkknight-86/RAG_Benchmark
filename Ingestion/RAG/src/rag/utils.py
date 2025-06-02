import os
import shutil
import requests
import time
from datetime import datetime, timedelta
from botocore.exceptions import ClientError


# ==================== Constants ====================

ARXIV_CSV_HEADERS = [
    "title", 
    "author(s)", 
    "published_date", 
    "updated_date", 
    "description", 
    "scraped_date", 
    "file_location"
]

ARXIV_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


# ==================== File System Utilities ====================

def sanitize_filename(title, max_length=255):
    """
    Convert title to valid filename by replacing invalid characters.
    
    Args:
        title: Original title string
        max_length: Maximum filename length (default 255)
    
    Returns:
        str: Sanitized filename with .pdf extension
    """
    # Replace invalid filename characters
    filename = title.replace(" ", "_").replace("/", "_").replace(":", "_").replace("?", "_")
    filename += ".pdf"
    
    # Truncate if too long
    if len(filename) > max_length:
        filename = filename[:max_length-4] + ".pdf"  # Keep .pdf extension
    
    return filename


def clean_existing_files(output_dir, csv_filename):
    """
    Remove existing output directory and CSV file.
    
    Args:
        output_dir: Directory path to remove
        csv_filename: CSV file path to remove
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    if os.path.exists(csv_filename):
        os.remove(csv_filename)


# ==================== S3 Utilities ====================

def s3_key_exists(s3_client, bucket, key):
    """
    Check if a key already exists in S3.
    
    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        key: S3 object key
    
    Returns:
        bool: True if key exists, False otherwise
    """
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            # Re-raise for other errors
            raise e


def upload_to_s3_with_encoding(s3_client, content, key, bucket, encoding='utf-8'):
    """
    Upload content to S3 with proper encoding.
    
    Args:
        s3_client: Boto3 S3 client
        content: Content to upload (string)
        key: S3 object key
        bucket: S3 bucket name
        encoding: Text encoding (default 'utf-8')
    
    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        # Encode content if it's a string
        if isinstance(content, str):
            content = content.encode(encoding)
        
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content
        )
        return True
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return False


# ==================== Date/Time Utilities ====================

def parse_arxiv_date(date_string):
    """
    Parse arXiv date format to datetime object.
    
    Args:
        date_string: Date string in arXiv format
    
    Returns:
        datetime: Parsed datetime object
    """
    return datetime.strptime(date_string, ARXIV_DATE_FORMAT)


def is_within_date_range(updated_date, published_date, years_back):
    """
    Check if paper is within specified year range.
    
    Args:
        updated_date: Paper update date string
        published_date: Paper publish date string
        years_back: Number of years to look back
    
    Returns:
        bool: True if paper is within date range
    """
    if not (updated_date or published_date):
        return True  # Include if no date info
    
    date_threshold = datetime.now() - timedelta(days=365 * years_back)
    
    updated_dt = parse_arxiv_date(updated_date) if updated_date else None
    published_dt = parse_arxiv_date(published_date) if published_date else None
    
    # Paper must be within range for both dates
    if updated_dt and updated_dt < date_threshold:
        if published_dt and published_dt < date_threshold:
            return False
    
    return True


# ==================== XML Parsing Utilities ====================

def extract_paper_metadata(entry):
    """
    Extract all metadata from a single arXiv XML entry.
    
    Args:
        entry: XML entry element
    
    Returns:
        dict: Paper metadata including title, authors, dates, summary, pdf_link
    """
    # Extract title
    title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
    title = ' '.join(title_elem.text.split()) if title_elem is not None else ""
    
    # Extract authors
    authors = []
    for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
        name_elem = author.find('{http://www.w3.org/2005/Atom}name')
        if name_elem is not None and name_elem.text:
            authors.append(name_elem.text)
    
    # Extract dates
    updated_elem = entry.find('{http://www.w3.org/2005/Atom}updated')
    published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
    updated = updated_elem.text if updated_elem is not None else None
    published = published_elem.text if published_elem is not None else None
    
    # Extract summary
    summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
    summary = ' '.join(summary_elem.text.split()) if summary_elem is not None and summary_elem.text else ""
    
    # Extract PDF link
    pdf_link = find_pdf_link(entry)
    
    return {
        'title': title,
        'authors': authors,
        'authors_str': '|'.join(authors),
        'updated': updated,
        'published': published,
        'summary': summary,
        'pdf_link': pdf_link
    }


def find_pdf_link(entry):
    """
    Find PDF link from arXiv entry links.
    
    Args:
        entry: XML entry element
    
    Returns:
        str: PDF URL or None if not found
    """
    for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
        if link.attrib.get('title') == 'pdf':
            return link.attrib.get('href')
    return None


# ==================== HTTP/Download Utilities ====================

def download_file(url, filepath, max_retries=3, timeout=30):
    """
    Download file from URL with retry logic.
    
    Args:
        url: URL to download from
        filepath: Local path to save file
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
    
    Returns:
        tuple: (success: bool, time_taken: float)
    """
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            end_time = time.time()
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True, end_time - start_time
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Failed to download after {max_retries} attempts: {e}")
                return False, 0
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return False, 0


def make_arxiv_request(query_url, timeout=30):
    """
    Make request to arXiv API with error handling.
    
    Args:
        query_url: Full arXiv API URL
        timeout: Request timeout in seconds
    
    Returns:
        requests.Response or None if failed
    """
    try:
        response = requests.get(query_url, timeout=timeout)
        if response.status_code == 200:
            return response
        else:
            print(f"arXiv API returned status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error making arXiv request: {e}")
        return None


# ==================== PDF Processing Utilities ====================

def get_text_preview(full_text, num_lines=5):
    """
    Get first N lines of text as preview.
    
    Args:
        full_text: Complete text content
        num_lines: Number of lines to include in preview
    
    Returns:
        str: Preview text
    """
    if not full_text:
        return ""
    
    lines = full_text.splitlines()
    preview_lines = lines[:num_lines]
    return "\n".join(preview_lines)


def safe_parse_pdf(pdf_path, parser):
    """
    Safely parse PDF and return full text or error message.
    
    Args:
        pdf_path: Path to PDF file
        parser: LlamaParse instance
    
    Returns:
        tuple: (success: bool, content: str)
    """
    try:
        documents = parser.load_data(pdf_path)
        full_text = "".join(doc.text + "\n" for doc in documents)
        return True, full_text
    except Exception as e:
        error_msg = f"Error: Could not parse PDF - {str(e)}"
        print(f"Error parsing {pdf_path}: {e}")
        return False, error_msg


# ==================== CSV Utilities ====================

def format_paper_row(title, authors_str, published, updated, summary, file_path):
    """
    Format paper data for CSV row.
    
    Args:
        title: Paper title
        authors_str: Pipe-separated author string
        published: Published date
        updated: Updated date
        summary: Paper summary/abstract
        file_path: Local file path
    
    Returns:
        dict: Formatted row data
    """
    return {
        "title": title,
        "author(s)": authors_str,
        "published_date": published,
        "updated_date": updated,
        "description": summary,
        "scraped_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "file_location": file_path
    }