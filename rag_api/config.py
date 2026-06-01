import os
from dotenv import load_dotenv

load_dotenv()

class RAGConfig:
    # Embedding model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # ChromaDB
    CHROMA_PERSIST_DIR = "./chroma_db"
    COLLECTION_NAME = "bizinsight_reviews"
    
    # Retrieval
    TOP_K = 15
    SEARCH_TYPE = "similarity" 
    
    # LLM configuration
    LLM_MODEL = "google/gemini-2.5-flash"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in .env")
    LLM_BASE_URL = "https://openrouter.ai/api/v1"
    LLM_TEMPERATURE = 0.3 # Lower temperature for more focused and deterministic answers, especially since we're relying on retrieved documents for context.
    LLM_MAX_TOKENS = 512

    # Logging
    LOG_LEVEL = "INFO"