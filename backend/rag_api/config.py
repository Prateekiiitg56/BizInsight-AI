import os
from dotenv import load_dotenv

load_dotenv()

class RAGConfig:
    # Embedding model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # ChromaDB — local persistence or remote HTTP server
    CHROMA_PERSIST_DIR = "./chroma_db"
    COLLECTION_NAME = "bizinsight_reviews"
    CHROMA_HOST = os.getenv("CHROMA_HOST")          # e.g. "chroma-server.example.com"
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
    USE_REMOTE_CHROMA = CHROMA_HOST is not None
    
    # Retrieval
    TOP_K = 5  # Reduced from 15 — fewer, higher-quality docs prevent duplicate flooding
    SEARCH_TYPE = "similarity" 
    
    # LLM configuration
    LLM_MODEL = "google/gemini-2.5-flash"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        # Fallback placeholder to prevent startup crash
        OPENROUTER_API_KEY = "NO_KEY_PROVIDED"
    LLM_BASE_URL = "https://openrouter.ai/api/v1"
    LLM_TEMPERATURE = 0.3 # Lower temperature for more focused and deterministic answers, especially since we're relying on retrieved documents for context.
    LLM_MAX_TOKENS = 768  # Increased from 512 to allow room for structured output format

    # Logging
    LOG_LEVEL = "INFO"