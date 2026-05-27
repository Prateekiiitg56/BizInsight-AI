import sqlite3
import logging
from contextlib import contextmanager

DB_NAME = "bizinsight.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
    finally:
        conn.close()


def initialize_database():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_review TEXT NOT NULL,
            cleaned_review TEXT NOT NULL,
            sentiment REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()


def insert_feedback(original_review, cleaned_review, sentiment):
    """Insert a review with both original and cleaned text."""
    if original_review is None or str(original_review).strip() == "":
        raise ValueError("Review cannot be empty.")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO feedback (original_review, cleaned_review, sentiment)
                VALUES (?, ?, ?)
                """,
                (str(original_review), str(cleaned_review), sentiment)
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Insert Error: {e}")
        raise


def fetch_feedback():
    """Return all rows: original_review, cleaned_review, sentiment, created_at."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT original_review, cleaned_review, sentiment, created_at
                FROM feedback
                ORDER BY created_at DESC, id DESC
            """)
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Fetch Error: {e}")
        return []


def clear_data():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feedback")
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Delete Error: {e}")
        raise

# ... rest of the file ...

# Create table when module loads
initialize_database()
