import os
import glob
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import shutil
import time
import re
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configuration
RAW_DATA_DIR = "./raw"
CHROMA_DB_DIR = "./chroma_db"
EMBEDDING_MODEL = "text-embedding-3-small"

def parse_metadata(file_path):
    """
    Extracts scheme_name, document_name, and date from the file path.
    Variants:
    1. <scheme_name>_<document_name>_<Month>_<year>.pdf
    2. <scheme_name>_<document_name>_<date>_<month>_<year>.pdf
    3. <scheme_name>_<document_name>.pdf
    """
    filename = os.path.basename(file_path)
    parent_folder = os.path.basename(os.path.dirname(file_path))
    name_no_ext = os.path.splitext(filename)[0]
    
    metadata = {
        "file_name": filename,
        "scheme_name": parent_folder.replace('_', ' '),
        "document_name": "Unknown",
        "date_of_the_document": "Unknown"
    }

    # Common months for regex (non-capturing)
    months = "(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)"
    
    # Variant 2: <scheme>_<doc>_<date>_<month>_<year>
    # Example: HDFC_BalancedAdvantage_KIM_21_Nov_2025
    match2 = re.search(rf'^(.*?)_(.*?)_(\d{{1,2}})_({months})_(\d{{4}})$', name_no_ext, re.IGNORECASE)
    if match2:
        # We prefer the folder name for scheme, but let's try to get a clean doc name
        # If the first part matches a known scheme prefix, the middle is the doc
        metadata["document_name"] = match2.group(2).replace('_', ' ')
        metadata["date_of_the_document"] = f"{match2.group(3)} {match2.group(4)} {match2.group(5)}"
        return metadata

    # Variant 1: <scheme>_<doc>_<Month>_<year>
    # Example: HDFC_BalancedAdvantage_Fund_Facts_Jan_2026
    match1 = re.search(rf'^(.*?)_(.*?)_({months})_(\d{{4}})$', name_no_ext, re.IGNORECASE)
    if match1:
        metadata["document_name"] = match1.group(2).replace('_', ' ')
        metadata["date_of_the_document"] = f"{match1.group(3)} {match1.group(4)}"
        return metadata

    # Variant 3: <scheme>_<doc>
    # Try to find a known doc type in the name
    doc_types = ["KIM", "SID", "Factsheet", "Fund_Facts", "Leaflet", "Presentation", "ProductPage", "SCHEME_SUMMARY_DOCUMENT", "Fact_Sheet"]
    for dt in doc_types:
        if dt.lower() in name_no_ext.lower():
            metadata["document_name"] = dt.replace('_', ' ')
            return metadata

    # Default: Try to separate from scheme if name starts with scheme-like string
    # Assuming scheme part might be the first part.
    metadata["document_name"] = name_no_ext.replace('_', ' ')
    
    return metadata

def ingest_data():
    """
    Ingests PDF files from RAW_DATA_DIR, chunks them, and stores embeddings in ChromaDB.
    """
    # 1. Check if raw directory exists
    if not os.path.exists(RAW_DATA_DIR):
        print(f"Error: Raw data directory '{RAW_DATA_DIR}' not found.")
        return

    # 2. Load PDF files
    # Recursive search for PDFs using os.walk
    pdf_files = []
    for root, dirs, files in os.walk(RAW_DATA_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))

    if not pdf_files:
        print(f"No PDF files found in '{RAW_DATA_DIR}' or its subdirectories.")
        return

    print(f"Found {len(pdf_files)} PDF files. Loading...")

    documents = []
    for pdf_path in pdf_files:
        try:
            loader = PyMuPDFLoader(pdf_path)
            docs = loader.load()
            
            # Enrich metadata
            filename = os.path.basename(pdf_path)
            file_meta = parse_metadata(pdf_path)
            for doc in docs:
                doc.metadata.update(file_meta)
                
            documents.extend(docs)
            print(f"Loaded {len(docs)} pages from {filename}")
        except Exception as e:
            print(f"Failed to load {pdf_path}: {e}")

    print(f"Total documents loaded: {len(documents)}")

    if not documents:
        print("No documents loaded to process.")
        return

    # 3. Split Text
    print("Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    
    # Enrichment: Prepend detailed metadata to content for better retrieval
    for chunk in chunks:
        meta = chunk.metadata
        header = f"File: {meta.get('file_name')}\nScheme: {meta.get('scheme_name')}\nDocument: {meta.get('document_name')}\nDate: {meta.get('date_of_the_document')}\n"
        chunk.page_content = f"{header}Content: {chunk.page_content}"
    
    print(f"Created {len(chunks)} enriched chunks.")

    # 4. Initialize Embeddings
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        return

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=api_key
    )

    # 5. Create/Update Vector Store
    print(f"Creating/Updating ChromaDB at '{CHROMA_DB_DIR}'...")
    
    try:

        batch_size = 50
        delay = 2 # seconds

        # We can't easily initialize an empty Chroma like FAISS without documents or a collection name.
        # But we can look for existing DB.
        
        # For simplicity, we initialize with first batch or load existing.
        # If we use Chroma(persist_directory=...) it loads existing.
        
        vector_store = Chroma(
            collection_name="hdfc_mutual_fund",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR
        )

        # Process batches
        print(f"Ingesting {len(chunks)} chunks in batches of {batch_size}...")
        for i in tqdm(range(0, len(chunks), batch_size), desc="Ingesting batches"):
            batch = chunks[i : i + batch_size]
            try:
                vector_store.add_documents(batch)
                time.sleep(delay)
            except Exception as e:
                print(f"Error adding batch {i}: {e}")
                time.sleep(10)
                try:
                     vector_store.add_documents(batch)
                except:
                    print(f"Skipping batch {i} after retry.")

        print("Ingestion complete. Data stored in ChromaDB.")
        
    except Exception as e:
        print(f"Error creating ChromaDB: {e}")

if __name__ == "__main__":
    ingest_data()
