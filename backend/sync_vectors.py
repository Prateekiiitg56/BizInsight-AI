#!/usr/bin/env python
"""
Rebuild the ChromaDB vector index from the reviews database.

Uses the same database (DATABASE_URL / SQLite) and vector store (CHROMA_HOST /
local chroma_db) as the API. Run from the backend directory:

    python sync_vectors.py
"""

import logging

from rag_api.indexing import ensure_demo_indexed, sync_all_reviews

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    count = sync_all_reviews()
    ensure_demo_indexed()
    logger.info(f"Synced {count} reviews to ChromaDB")
