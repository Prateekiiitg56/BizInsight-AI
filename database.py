import sqlite3
import logging
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

    try:
        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO feedback (review, sentiment)
                VALUES (?, ?)
                """,
                (str(review), sentiment)
            )

            conn.commit()

            return True

    except sqlite3.Error as e:

        logger.error(f"Insert Error: {e}")

        raise sqlite3.Error(f"Insert Error: {e}")


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


if __name__ == "__main__":
    initialize_database()