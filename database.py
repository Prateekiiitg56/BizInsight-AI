import sqlite3
import logging
import bcrypt
from contextlib import contextmanager

DB_NAME = "bizinsight.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)

    # Enforce SQLite foreign key constraints for all connections
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
    finally:
        conn.close()


def initialize_database():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review TEXT NOT NULL,
            sentiment REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chat_history_session
        ON chat_history (session_id, created_at)
        """)
        conn.commit()
        # Workspace support

        try:
            cursor.execute(
                "ALTER TABLE feedback ADD COLUMN user_id INTEGER REFERENCES users(id)"
            )
            conn.commit()

        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("user_id column already exists in feedback table")
            else:
                logger.exception("Unexpected database migration failure")
                raise


def save_chat_turn(session_id, human_msg, ai_msg):
    """Persist one conversation turn (human question + AI answer)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, "human", human_msg),
        )
        cursor.execute(
            "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, "ai", ai_msg),
        )
        conn.commit()


def load_chat_history(session_id, window=None):
    """Load chat turns for a session in chronological order.

    If window is set, returns only the most recent `window` turns
    (a turn = one human + one ai message, so 2 * window rows).
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if window:
            # newest 2*window rows, then re-sort ascending for replay
            rows = cursor.execute(
                """
                SELECT role, content FROM (
                    SELECT id, role, content FROM chat_history
                    WHERE session_id = ?
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                ) ORDER BY id ASC
                """,
                (session_id, window * 2),
            ).fetchall()
        else:
            rows = cursor.execute(
                "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY created_at ASC, id ASC",
                (session_id,),
            ).fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]


def no_users_exist():
    with get_connection() as conn:
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        return count == 0


# ─── User Functions ───────────────────────────────────────────────────────────


def create_user(
    username, email, password, role="user", workspace_type="personal", workspace_id=None
):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password_hash,
                    role,
                    workspace_type,
                    workspace_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, email, hashed, role, workspace_type, workspace_id),
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError as e:

        error_message = str(e).lower()

        if "username" in error_message:
            return "USERNAME_EXISTS"

        if "email" in error_message:
            return "EMAIL_EXISTS"

        return False  # username already taken
    except sqlite3.Error as e:
        logger.error(f"Create User Error: {e}")
        return False


def get_user_by_username(username):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    password_hash,
                    role,
                    workspace_type,
                    workspace_id
                FROM users
                WHERE username = ?
                """,
                (username.strip(),),
            )

            row = cursor.fetchone()

            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "password_hash": row[3],
                    "role": row[4],
                    "workspace_type": row[5],
                    "workspace_id": row[6],
                }

            return None

    except sqlite3.Error as e:
        logger.error(f"Get User Error: {e}")
        return None


def get_user_email(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT email FROM users WHERE id=?", (user_id,))

            row = cursor.fetchone()

            return row[0] if row else None

    except sqlite3.Error as e:
        logger.error(f"Get Email Error: {e}")
        return None


def get_user_workspace(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT workspace_type, workspace_id
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            )

            row = cursor.fetchone()

            if row:
                return {"workspace_type": row[0], "workspace_id": row[1]}

            return None

    except sqlite3.Error as e:
        logger.error(f"Workspace Fetch Error: {e}")
        return None


def get_workspace_feedback(workspace_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    f.review,
                    f.sentiment,
                    f.created_at
                FROM feedback f
                INNER JOIN users u
                    ON f.user_id = u.id
                WHERE u.workspace_id = ?
                ORDER BY f.created_at DESC
                """,
                (workspace_id,),
            )

            return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Workspace Fetch Error: {e}")
        return []


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def fetch_all_users():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.role, u.created_at,
                       COUNT(f.id) as review_count
                FROM users u
                LEFT JOIN feedback f ON f.user_id = u.id
                GROUP BY u.id
                ORDER BY u.created_at DESC
            """)
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Fetch All Users Error: {e}")
        return []


def delete_user(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Delete User Error: {e}")
        return False


# ─── Feedback Functions ───────────────────────────────────────────────────────


def insert_feedback(review, sentiment, user_id):
    if review is None or str(review).strip() == "":
        raise ValueError("Review cannot be empty.")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback (review, sentiment, user_id) VALUES (?, ?, ?)",
                (str(review), sentiment, user_id),
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Insert Error: {e}")
        raise sqlite3.Error(f"Insert Error: {e}")


def insert_feedback_bulk(reviews_data, user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO feedback (review, sentiment, user_id) VALUES (?, ?, ?)",
                [(review, sentiment, user_id) for review, sentiment in reviews_data],
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Bulk Insert Error: {e}")
        raise sqlite3.Error(f"Bulk Insert Error: {e}")


def fetch_feedback(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT review, sentiment, created_at
                FROM feedback
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
            """,
                (user_id,),
            )
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Fetch Error: {e}")
        return []


def fetch_all_feedback():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.review, f.sentiment, f.created_at, u.username
                FROM feedback f
                LEFT JOIN users u ON f.user_id = u.id
                ORDER BY f.created_at DESC
            """)
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Fetch All Feedback Error: {e}")
        return []


def clear_data(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Clear Error: {e}")
        raise sqlite3.Error(f"Clear Error: {e}")
