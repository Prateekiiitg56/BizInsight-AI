import os
import sys
import tempfile

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Isolated SQLite database and vector store for the test run (set before app import).
_tmp = tempfile.mkdtemp(prefix="bizinsight-tests-")
os.environ["DB_PATH"] = os.path.join(_tmp, "test.db")
os.environ["CHROMA_PERSIST_DIR"] = os.path.join(_tmp, "chroma")
os.environ.pop("DATABASE_URL", None)
os.environ.pop("CHROMA_HOST", None)
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-32-bytes-long"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from bizinsight_api.main import app

    return TestClient(app)


_counter = {"n": 0}


@pytest.fixture
def make_user(client):
    def _make():
        _counter["n"] += 1
        name = f"user{_counter['n']}"
        res = client.post(
            "/api/auth/register",
            json={"username": name, "email": f"{name}@example.com", "password": "password123", "confirm_password": "password123"},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        return {"headers": {"Authorization": f"Bearer {body['token']}"}, **body["user"]}

    return _make


def upload(client, user, text, filename: str = "reviews.csv"):
    return client.post(
        "/api/reviews/upload",
        headers=user["headers"],
        files={"file": (filename, text if isinstance(text, bytes) else text.encode(), "text/csv")},
    )
