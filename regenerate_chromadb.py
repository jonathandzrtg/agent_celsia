import os
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
# No longer importing JSONLoader from langchain_community
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Import document loading utility
from src.data.processing import load_documents_from_json

# Load environment variables
load_dotenv()

# --- Configuration ---
CHROMA_PERSIST_DIRECTORY = "./chromadb_storage"
CHROMA_COLLECTION_NAME = "rag_collection"
SOURCE_DATA_DIRECTORY = "./data/source"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")



def regenerate_chromadb():
    print(f"Starting ChromaDB regeneration with GoogleGenerativeAIEmbeddings...")

    # Initialize GoogleGenerativeAIEmbeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # Load documents from source directory
    documents = []
    for filename in os.listdir(SOURCE_DATA_DIRECTORY):
        if filename.endswith(".json"):
            file_path = os.path.join(SOURCE_DATA_DIRECTORY, filename)
            print(f"Loading documents from {file_path}...")
            try:
                loaded_docs = load_documents_from_json(file_path)
                documents.extend(loaded_docs)
                print(f"Loaded {len(loaded_docs)} documents from {filename}.")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                continue
    
    if not documents:
        print("No documents found to process. Exiting.")
        return

    print(f"Total documents loaded: {len(documents)}")

    # Split documents into chunks (optional, if documents are already chunked, this might be redundant)
    # Based on the names (e.g., celsia_processed_..._chunks.json), they might already be chunked.
    # If they are already chunks, you might skip this step or use a splitter that ensures proper formatting.
    # For now, let's assume raw documents and apply a splitter.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.split_documents(documents)
    print(f"Split into {len(texts)} text chunks.")

    # Delete existing ChromaDB directory to ensure a clean slate
    if os.path.exists(CHROMA_PERSIST_DIRECTORY):
        import shutil
        print(f"Deleting existing ChromaDB at {CHROMA_PERSIST_DIRECTORY}...")
        shutil.rmtree(CHROMA_PERSIST_DIRECTORY)
        print("Existing ChromaDB deleted.")

    # Create and persist the new ChromaDB vector store
    print(f"Creating new ChromaDB collection '{CHROMA_COLLECTION_NAME}'...")
    db = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIRECTORY,
        collection_name=CHROMA_COLLECTION_NAME
    )
    print("New ChromaDB generated and persisted successfully.")
    print(f"Number of items in the new collection: {db._collection.count()}")

if __name__ == "__main__":
    regenerate_chromadb()

