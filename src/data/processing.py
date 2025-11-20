import os
import json
from langchain_core.documents import Document
from typing import List, Any # Assuming List is needed for type hinting

def load_documents_from_json(file_path: str) -> List[Document]:
    """Loads documents from a JSON file, manually extracting content and metadata."""
    documents = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Case 1: JSON structure is a top-level object with a 'chunks' key
        if isinstance(data, dict) and 'chunks' in data and isinstance(data['chunks'], list):
            for record in data['chunks']:
                content = record.get("content")
                if content:
                    metadata = {
                        "source": record.get("source_url", os.path.basename(file_path)),
                        "title": record.get("title"),
                        "date": record.get("date"),
                        "region": record.get("region"),
                        "category": record.get("category"),
                        "source_type": record.get("source_type")
                    }
                    metadata = {k: v for k, v in metadata.items() if v is not None}
                    documents.append(Document(page_content=content, metadata=metadata))
        
        # Case 2: JSON structure is a top-level list of objects
        elif isinstance(data, list):
            for record in data:
                content = record.get("post") # Assuming 'post' contains the main text content
                if content:
                    metadata = {
                        "source": record.get("URL imagen/video", os.path.basename(file_path)),
                        "user": record.get("user"),
                        "tiempo": record.get("tiempo"),
                        "reacciones": record.get("Reacciones"),
                        "interacciones": record.get("Interacciones")
                    }
                    metadata = {k: v for k, v in metadata.items() if v is not None}
                    documents.append(Document(page_content=content, metadata=metadata))

        # Case 3: Other dictionary structure, trying direct content extraction
        elif isinstance(data, dict):
            content = data.get("text") or data.get("content") or data.get("post")
            if content:
                metadata = {"source": os.path.basename(file_path)}
                documents.append(Document(page_content=content, metadata=metadata))
        else:
            print(f"Warning: Unexpected top-level JSON structure in '{file_path}'. No documents extracted directly.")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while loading {file_path}: {e}")
    
    return documents