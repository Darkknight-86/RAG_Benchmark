import json
import os
from azure.storage.blob import BlobServiceClient
from pathlib import Path

def upload_dict_as_json(blob_name: str, data_dict: dict, connection_string: str, container_name: str):
    # Convert dict to JSON string
    json_str = json.dumps(data_dict)

    # Connect to Azure Blob Storage
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Create container if it doesn't exist
    try:
        container_client.create_container()
    except Exception:
        pass

    # Upload JSON string as blob
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(json_str, overwrite=True)
    print(f'Uploaded JSON blob "{blob_name}" successfully.')

if __name__ == "__main__":
    from dotenv import load_dotenv
    # Load the .env file from the root
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=env_path)


    CONN_STR = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    CONTAINER = os.getenv('AZURE_BLOB_NAME')

    sample_dict = {"hi": 123, "ho": "text"}
    upload_dict_as_json("sample.json", sample_dict, CONN_STR, CONTAINER)
