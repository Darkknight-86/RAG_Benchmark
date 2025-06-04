from typing import List
from langchain.schema import Document
import json

from utils import json_to_text  # adjust path as needed

class StockChunker:
    def chunk(self, json_strings: List[str]) -> List[Document]:
        """
        Converts a list of JSON strings into Documents with human-readable content.
        """
        docs = []
        for raw in json_strings:
            try:
                json_data = json.loads(raw)
                text = json_to_text(json_data)
                docs.append(Document(page_content=text, metadata={}))
            except Exception as e:
                print(f"⚠️ Skipping invalid JSON: {e}")
        return docs