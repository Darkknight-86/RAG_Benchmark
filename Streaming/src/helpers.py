from datetime import datetime, time
from azure.storage.blob import BlobServiceClient
import json
import pytz
import os
from dotenv import load_dotenv
from pathlib import Path
from config import AZURE_CONNECTION_STRING, AZURE_CONTAINER_NAME

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize blob service client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

# Create container if it doesn't exist
try:
    container_client.create_container()
except Exception:
    pass  # Container already exists

def is_asx_open():
    """
    Check if the Australian Securities Exchange (ASX) is currently open.
    ASX Regular Trading Hours: 10:00 AM - 4:00 PM Sydney time
    Closed on weekends and public holidays.
    
    Returns:
        dict: {
            'is_open': bool,
            'status': str (pre_market, open, post_market, closed, weekend),
            'current_time': str,
            'next_open': str (when market opens next)
        }
    """
    # Get current Sydney time
    sydney_tz = pytz.timezone('Australia/Sydney')
    now = datetime.now(sydney_tz)
    current_time = now.strftime('%Y-%m-%d %H:%M:%S %Z')
    
    # Check if weekend
    if now.weekday() in [5, 6]:  # Saturday = 5, Sunday = 6
        return {
            'is_open': False,
            'status': 'weekend',
            'current_time': current_time,
            'message': 'Market closed - Weekend'
        }
    
    # Define market hours
    market_open = time(10, 0)   # 10:00 AM
    market_close = time(16, 0)  # 4:00 PM
    pre_market_start = time(7, 0)  # 7:00 AM
    post_market_end = time(17, 0)  # 5:00 PM
    
    current_time_only = now.time()
    
    # Determine market status
    if current_time_only < pre_market_start:
        return {
            'is_open': False,
            'status': 'closed',
            'current_time': current_time,
            'message': 'Market closed - Before pre-market'
        }
    elif pre_market_start <= current_time_only < market_open:
        return {
            'is_open': False,
            'status': 'pre_market',
            'current_time': current_time,
            'message': f'Pre-market - Opens at {market_open.strftime("%H:%M")}'
        }
    elif market_open <= current_time_only < market_close:
        return {
            'is_open': True,
            'status': 'open',
            'current_time': current_time,
            'message': f'Market open - Closes at {market_close.strftime("%H:%M")}'
        }
    elif market_close <= current_time_only < post_market_end:
        return {
            'is_open': False,
            'status': 'post_market',
            'current_time': current_time,
            'message': 'Post-market trading'
        }
    else:
        return {
            'is_open': False,
            'status': 'closed',
            'current_time': current_time,
            'message': 'Market closed - After hours'
        }


def upload_to_blob(file_name, contents):
    """
    Upload file contents to Azure Blob Storage (renamed from S3 for compatibility).
    
    Args:
        file_name: Name of the file (e.g., 'data.json')
        contents: File contents (can be string, bytes, or dict/list for JSON)
        
    Returns:
        dict: Response from Azure upload operation
        
    Raises:
        Exception: If upload fails
    """
    # Construct the blob path
    blob_name = f"streamed/{file_name}"
    
    # Handle different content types
    if isinstance(contents, (dict, list)):
        # Convert dict/list to JSON string
        body = json.dumps(contents, indent=2)
    elif isinstance(contents, str):
        body = contents
    elif isinstance(contents, bytes):
        body = contents
    else:
        raise ValueError(f"Unsupported content type: {type(contents)}")
    
    try:
        # Get blob client
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload to Azure - simplified without content_settings
        response = blob_client.upload_blob(
            body,
            overwrite=True
        )
        
        print(f"Successfully uploaded {file_name} to Azure container {AZURE_CONTAINER_NAME}/{blob_name}")
        return {
            'etag': response.get('etag', ''),
            'last_modified': response.get('last_modified', ''),
            'blob_name': blob_name
        }
        
    except Exception as e:
        print(f"Error uploading {file_name} to Azure: {str(e)}")
        raise
    
def epoch_to_json_date(epoch_ms):
    """
    Convert epoch timestamp in milliseconds to ISO 8601 date string.
    
    Args:
        epoch_ms: Unix timestamp in milliseconds
        
    Returns:
        ISO 8601 formatted date string (JSON compatible)
    """
    # Convert milliseconds to seconds
    epoch_seconds = epoch_ms / 1000
    
    # Create datetime object
    dt = datetime.fromtimestamp(epoch_seconds)
    
    # Return ISO 8601 format string
    return dt.isoformat()