"""
Keeps ChromaDB in sync with the reviews database.

Vectors are derived data: the SQL database is the source of truth, and any
user's vectors can be rebuilt from it at any time (e.g. after a fresh container
boot wipes a local chroma_db directory).
"""

import csv
import logging
import threading

from database import fetch_feedback_for_indexing

from .config import RAGConfig
from .vector_store import get_vector_store_manager

logger = logging.getLogger(__name__)

# One lock per user so concurrent uploads / chats don't rebuild the same index twice.
_user_locks: dict = {}
_user_locks_guard = threading.Lock()


def _lock_for(user_id: int) -> threading.Lock:
    with _user_locks_guard:
        return _user_locks.setdefault(user_id, threading.Lock())


def _rows_to_docs(rows):
    for row_id, review, sentiment, created_at, user_id in rows:
        yield {
            "id": f"review_{row_id}",
            "text": review,
            "sentiment": sentiment,
            "user_id": user_id,
            "date": created_at,
        }


def sync_user_reviews(user_id: int) -> int:
    """Rebuild a user's vectors from the database. Returns the number indexed."""
    with _lock_for(user_id):
        vsm = get_vector_store_manager()
        vsm.delete_user_documents(user_id)
        rows = fetch_feedback_for_indexing(user_id)
        return vsm.upsert_reviews(_rows_to_docs(rows)) if rows else 0


def ensure_user_indexed(user_id: int) -> None:
    """Index a user's reviews if the vector store has none for them yet."""
    vsm = get_vector_store_manager()
    if vsm.has_documents(user_id):
        return
    with _lock_for(user_id):
        if vsm.has_documents(user_id):
            return
        rows = fetch_feedback_for_indexing(user_id)
        if rows:
            logger.info(f"Hydrating vector store for user {user_id} ({len(rows)} reviews)")
            vsm.upsert_reviews(_rows_to_docs(rows))


def remove_user_reviews(user_id: int) -> None:
    with _lock_for(user_id):
        get_vector_store_manager().delete_user_documents(user_id)


def ensure_demo_indexed() -> None:
    """Load the bundled demo dataset used by the public (signed-out) chat sandbox."""
    demo_id = RAGConfig.DEMO_USER_ID
    vsm = get_vector_store_manager()
    if vsm.has_documents(demo_id):
        return
    with _lock_for(demo_id):
        if vsm.has_documents(demo_id):
            return
        from sentiment import get_sentiment

        with open(RAGConfig.DEMO_DATASET_PATH, newline="", encoding="utf-8") as f:
            reviews = [row["review"].strip() for row in csv.DictReader(f) if (row.get("review") or "").strip()]

        logger.info(f"Indexing {len(reviews)} demo reviews")
        vsm.upsert_reviews(
            {"id": f"demo_{i}", "text": text, "sentiment": get_sentiment(text), "user_id": demo_id}
            for i, text in enumerate(reviews)
        )


def sync_all_reviews() -> int:
    """Rebuild vectors for every user in the database. Used by sync_vectors.py."""
    rows = fetch_feedback_for_indexing()
    user_ids = sorted({row[4] for row in rows if row[4] is not None})
    return sum(sync_user_reviews(uid) for uid in user_ids)
