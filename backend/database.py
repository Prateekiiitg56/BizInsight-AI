import logging
import bcrypt
import os
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Dual-Mode Database Configuration ────────────────────────────────────────
# When DATABASE_URL is set → PostgreSQL (production / Google Cloud SQL)
# When not set → SQLite (local development, zero setup)

DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    logger.info("Database mode: PostgreSQL (production)")
    # Parameter placeholder for PostgreSQL
    P = "%s"
else:
    import sqlite3
    logger.info("Database mode: SQLite (local development)")
    # Parameter placeholder for SQLite
    P = "?"

# SQLite fallback path
DB_NAME = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "bizinsight.db"))


@contextmanager
def get_connection():
    """Yield a DB-API 2.0 connection — PostgreSQL or SQLite based on environment."""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(DB_NAME)
        try:
            yield conn
        finally:
            conn.close()


# ─── Schema Initialization ───────────────────────────────────────────────────

def initialize_database():
    with get_connection() as conn:
        cursor = conn.cursor()

        if USE_POSTGRES:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                review TEXT NOT NULL,
                sentiment REAL NOT NULL,
                user_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        else:
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
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)
            # Legacy migration: add user_id column if missing (SQLite only)
            try:
                cursor.execute("ALTER TABLE feedback ADD COLUMN user_id INTEGER REFERENCES users(id)")
                conn.commit()
            except sqlite3.OperationalError:
                pass

        conn.commit()


def no_users_exist():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        return count == 0


# ─── User Functions ───────────────────────────────────────────────────────────

def create_user(username, email, password, role="user"):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO users (username,email,password_hash,role) VALUES ({P},{P},{P},{P})",
                (username, email, hashed, role)
            )
            conn.commit()
            return True
    except Exception as e:
        error_message = str(e).lower()

        if "unique" in error_message or "duplicate" in error_message or "integrity" in error_message:
            if "username" in error_message:
                return "USERNAME_EXISTS"
            if "email" in error_message:
                return "EMAIL_EXISTS"
            # Generic unique constraint violation
            return "USERNAME_EXISTS"

        logger.error(f"Create User Error: {e}")
        return False


def get_user_by_username(username):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT id, username, email, password_hash, role
                FROM users
                WHERE username = {P}
                """,
                (username.strip(),)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "password_hash": row[3],
                    "role": row[4]
                }
            return None
    except Exception as e:
        logger.error(f"Get User Error: {e}")
        return None

def get_user_email(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT email FROM users WHERE id={P}",
                (user_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"Get Email Error: {e}")
        return None

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_user_by_email(email):
    """Look up a user by email address (used for Google OAuth)."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT id, username, email, password_hash, role
                FROM users
                WHERE LOWER(email) = LOWER({P})
                """,
                (email.strip(),)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "password_hash": row[3],
                    "role": row[4],
                }
            return None
    except Exception as e:
        logger.error(f"Get User By Email Error: {e}")
        return None


def create_google_user(username, email, role="user"):
    """Create a user from Google OAuth (no password required)."""
    try:
        placeholder_hash = "GOOGLE_OAUTH_USER"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO users (username, email, password_hash, role) VALUES ({P}, {P}, {P}, {P})",
                (username, email, placeholder_hash, role)
            )
            conn.commit()
            return True
    except Exception as e:
        error_message = str(e).lower()
        if "unique" in error_message or "duplicate" in error_message or "integrity" in error_message:
            if "username" in error_message:
                return "USERNAME_EXISTS"
            if "email" in error_message:
                return "EMAIL_EXISTS"
            return "USERNAME_EXISTS"
        logger.error(f"Create Google User Error: {e}")
        return False


def fetch_all_users():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.role, u.created_at,
                       COUNT(f.id) as review_count
                FROM users u
                LEFT JOIN feedback f ON f.user_id = u.id
                GROUP BY u.id, u.username, u.role, u.created_at
                ORDER BY u.created_at DESC
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Fetch All Users Error: {e}")
        return []


def delete_user(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM feedback WHERE user_id = {P}", (user_id,))
            cursor.execute(f"DELETE FROM users WHERE id = {P}", (user_id,))
            conn.commit()
            return True
    except Exception as e:
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
                f"INSERT INTO feedback (review, sentiment, user_id) VALUES ({P}, {P}, {P})",
                (str(review), sentiment, user_id)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Insert Error: {e}")
        raise

def insert_feedback_bulk(reviews_data, user_id):   
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if USE_POSTGRES:
                # PostgreSQL: use executemany with %s placeholders
                psycopg2.extras.execute_batch(
                    cursor,
                    "INSERT INTO feedback (review, sentiment, user_id) VALUES (%s, %s, %s)",
                    [(review, sentiment, user_id) for review, sentiment in reviews_data]
                )
            else:
                cursor.executemany(
                    "INSERT INTO feedback (review, sentiment, user_id) VALUES (?, ?, ?)",
                    [(review, sentiment, user_id) for review, sentiment in reviews_data]
                )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Bulk Insert Error: {e}")
        raise


def fetch_feedback(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT review, sentiment, created_at
                FROM feedback
                WHERE user_id = {P}
                ORDER BY created_at DESC, id DESC
            """, (user_id,))
            return cursor.fetchall()
    except Exception as e:
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
    except Exception as e:
        logger.error(f"Fetch All Feedback Error: {e}")
        return []


def clear_data(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM feedback WHERE user_id = {P}", (user_id,))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Clear Error: {e}")
        raise
