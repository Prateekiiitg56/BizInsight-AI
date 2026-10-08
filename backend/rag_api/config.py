import os

from dotenv import load_dotenv

# Load .env from the working directory, the backend folder, and the project root.
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()
load_dotenv(os.path.join(_backend_dir, ".env"))
load_dotenv(os.path.join(os.path.dirname(_backend_dir), ".env"))

_API_KEY_ENV_NAMES = ("OPENROUTER_API_KEY", "OPENROUTER_KEY", "OPENAI_API_KEY", "LLM_API_KEY")


class RAGConfig:
    # ChromaDB — local persistence or remote HTTP server
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", os.path.join(_backend_dir, "chroma_db"))
    COLLECTION_NAME = "bizinsight_reviews"
    CHROMA_HOST = os.getenv("CHROMA_HOST")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
    USE_REMOTE_CHROMA = bool(CHROMA_HOST)

    # Reviews shown to visitors who are not signed in (the public /chat sandbox).
    DEMO_USER_ID = 0
    DEMO_DATASET_PATH = os.path.join(_backend_dir, "data", "demo_reviews.csv")

    # Retrieval
    TOP_K = 5

    # LLM (OpenRouter, OpenAI-compatible API)
    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    LLM_TEMPERATURE = 0.3
    LLM_MAX_TOKENS = 768

    # Conversational memory: max concurrent chat sessions kept in RAM.
    MAX_CHAT_SESSIONS = int(os.getenv("MAX_CHAT_SESSIONS", "200"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @staticmethod
    def get_api_key() -> str:
        """Return the configured LLM API key, or an empty string when none is set."""
        for name in _API_KEY_ENV_NAMES:
            val = (os.getenv(name) or "").strip()
            if val:
                return val
        return ""
