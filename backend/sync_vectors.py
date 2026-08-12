#!/usr/bin/env python
"""
Sync reviews from the database (SQLite or PostgreSQL) to ChromaDB (local or remote).
Automatically uses the same database and vector store backends as the RAG API,
controlled by environment variables (DATABASE_URL, CHROMA_HOST).
"""
import logging
import os
import sys

# Add parent directory to path so we can import rag_api and database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_chroma import Chroma
from langchain_core.documents import Document
from rag_api.embeddings import get_embedding_model
from rag_api.config import RAGConfig
from database import get_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_reviews(clear_existing=True):
    # 1. Fetch reviews from database (SQLite or PostgreSQL — handled by database.py)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, review, sentiment, created_at FROM feedback")
        rows = cursor.fetchall()

    if not rows:
        logger.warning("No reviews found. Upload a CSV first.")
        return

    # Use deterministic IDs based on row ID to prevent duplicates on re-sync
    documents = []
    for row_id, review, sentiment, date in rows:
        documents.append(Document(
            page_content=review,
            metadata={
                "sentiment": sentiment,
                "date": str(date) if date else None,
                "rowid": row_id
            },
            id=f"review_{row_id}"  # Deterministic ID prevents duplicate entries
        ))

    # CRITICAL: Use the SAME embedding model as the RAG API to avoid vector space mismatch
    embeddings = get_embedding_model()

    # 2. Create ChromaDB client — remote HTTP or local, matching the RAG API config
    if RAGConfig.USE_REMOTE_CHROMA:
        import chromadb
        logger.info(f"Connecting to remote ChromaDB at {RAGConfig.CHROMA_HOST}:{RAGConfig.CHROMA_PORT}")
        client = chromadb.HttpClient(
            host=RAGConfig.CHROMA_HOST,
            port=RAGConfig.CHROMA_PORT
        )
        vectorstore_kwargs = {
            "client": client,
            "collection_name": RAGConfig.COLLECTION_NAME,
            "embedding_function": embeddings,
        }
    else:
        vectorstore_kwargs = {
            "persist_directory": RAGConfig.CHROMA_PERSIST_DIR,
            "collection_name": RAGConfig.COLLECTION_NAME,
            "embedding_function": embeddings,
        }

    # 3. If clear_existing, delete DOCUMENTS instead of the whole collection
    if clear_existing:
        try:
            temp_client = Chroma(**vectorstore_kwargs)
            existing_data = temp_client.get()
            if existing_data and existing_data["ids"]:
                temp_client.delete(ids=existing_data["ids"])
                logger.info(f"Cleared {len(existing_data['ids'])} existing documents from collection")
        except Exception as e:
            logger.error(f"Cannot clear collection: {e}")
            raise RuntimeError("Vector store locked or unreachable.") from e

    # 4. Create fresh collection with documents
    if RAGConfig.USE_REMOTE_CHROMA:
        import chromadb
        client = chromadb.HttpClient(
            host=RAGConfig.CHROMA_HOST,
            port=RAGConfig.CHROMA_PORT
        )
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            client=client,
            collection_name=RAGConfig.COLLECTION_NAME
        )
    else:
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=RAGConfig.CHROMA_PERSIST_DIR,
            collection_name=RAGConfig.COLLECTION_NAME
        )
    logger.info(f"Synced {len(documents)} reviews to ChromaDB")

if __name__ == "__main__":
    sync_reviews(clear_existing=True)