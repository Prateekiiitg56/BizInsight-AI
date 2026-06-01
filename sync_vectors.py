#!/usr/bin/env python
import sqlite3
import logging
import shutil
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_reviews(clear_existing=True):
    # 1. Fetch reviews from SQLite
    conn = sqlite3.connect("bizinsight.db")
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, original_review, sentiment, created_at FROM feedback")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        logger.warning("No reviews found. Upload a CSV first.")
        return

    documents = []
    for rowid, review, sentiment, date in rows:
        documents.append(Document(
            page_content=review,
            metadata={
                "sentiment": sentiment,
                "date": str(date) if date else None,
                "rowid": rowid
            },
            id=str(rowid)
        ))

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    persist_dir = "./chroma_db"
    collection_name = "bizinsight_reviews"

    # 2. If clear_existing, delete DOCUMENTS instead of the whole collection
    if clear_existing:
        try:
            # Create a temporary client to clear documents
            temp_client = Chroma(
                persist_directory=persist_dir,
                embedding_function=embeddings,
                collection_name=collection_name
            )
            
            # Find all existing document IDs
            existing_data = temp_client.get()
            if existing_data and existing_data["ids"]:
                # Delete only the documents, keeping the collection ID intact
                temp_client.delete(ids=existing_data["ids"])
                logger.info(f"Cleared {len(existing_data['ids'])} existing documents from collection")
                
        except Exception as e:
            logger.error(f"Cannot clear collection (API server may be running): {e}")
            logger.error("Please stop the FastAPI server and try again.")
            raise RuntimeError("Vector store locked. Stop the RAG API server before uploading.") from e

    # 3. Create fresh collection
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name=collection_name
    )
    logger.info(f"Synced {len(documents)} reviews to ChromaDB")

if __name__ == "__main__":
    sync_reviews(clear_existing=True)