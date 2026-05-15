import sqlite3

conn = sqlite3.connect("bizinsight.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review TEXT,
    sentiment REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


def insert_feedback(review, sentiment):
    cursor.execute("SELECT 1 FROM feedback WHERE review = ?", (review,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO feedback (review, sentiment) VALUES (?, ?)",
            (review, sentiment)
        )
        conn.commit()


def fetch_feedback():
    cursor.execute("SELECT review, sentiment, created_at FROM feedback")
    return cursor.fetchall()


def clear_data():
    cursor.execute("DELETE FROM feedback")
    conn.commit()
