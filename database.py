import sqlite3
import logging
import math
from contextlib import contextmanager

DB_NAME = "bizinsight.db"

# Configure logging
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
            review TEXT NOT NULL,
            sentiment REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()


def insert_feedback(review, sentiment):

    # Handle None / NaN / empty reviews safely
    if review is None or str(review).strip() == "":
        raise ValueError("Review cannot be empty.")

    # Handle NaN sentiment values
    if sentiment is None or (isinstance(sentiment, float) and math.isnan(sentiment)):
        sentiment = 0.0

    try:
        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO feedback (review, sentiment)
                VALUES (?, ?)
                """,
                (str(review).strip(), float(sentiment))
            )

            conn.commit()

            return True

    except sqlite3.Error as e:

        logger.error(f"Insert Error: {e}")

        raise sqlite3.Error(f"Insert Error: {e}")


def insert_feedback_bulk(records):
    """Insert multiple feedback records efficiently using executemany.

    Args:
        records: List of (review, sentiment) tuples.

    Returns:
        tuple: (insert_count, skip_count) indicating how many were inserted vs skipped.
    """
    valid_records = []
    skip_count = 0

    for review, sentiment in records:
        # Skip None / empty reviews
        if review is None or str(review).strip() == "":
            skip_count += 1
            continue

        # Sanitize NaN sentiment values
        if sentiment is None or (isinstance(sentiment, float) and math.isnan(sentiment)):
            sentiment = 0.0

        valid_records.append((str(review).strip(), float(sentiment)))

    if not valid_records:
        return 0, skip_count

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO feedback (review, sentiment) VALUES (?, ?)",
                valid_records
            )
            conn.commit()
            return len(valid_records), skip_count

    except sqlite3.Error as e:
        logger.error(f"Bulk Insert Error: {e}")
        raise sqlite3.Error(f"Bulk Insert Error: {e}")


def fetch_feedback():

    try:
        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT review, sentiment, created_at
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

        raise sqlite3.Error(f"Delete Error: {e}")


# Auto-initialize database on module import to prevent
# "no such table: feedback" errors (fixes issue #56)
initialize_database()