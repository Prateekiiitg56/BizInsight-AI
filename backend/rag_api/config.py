import os
from dotenv import load_dotenv

# Load .env file from working directory, backend folder, and root project folder
load_dotenv()
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_backend_dir, ".env"))
load_dotenv(os.path.join(os.path.dirname(_backend_dir), ".env"))

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
    
    # LLM configuration (Verified 200 OK OpenRouter model slug)
    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    
    @classmethod
    def get_api_key(cls):
        # 1. Direct environment variable lookup
        for name in ["OPENROUTER_API_KEY", "OPENROUTER_KEY", "OPENAI_API_KEY", "LLM_API_KEY"]:
            val = os.getenv(name)
            if val and val.strip() and val.strip() != "NO_KEY_PROVIDED":
                return val.strip()
        
        # 2. Case-insensitive and whitespace-insensitive search over all env keys
        for k, v in os.environ.items():
            k_clean = k.strip().upper()
            if ("OPENROUTER" in k_clean or "OPENAI" in k_clean) and "KEY" in k_clean:
                if v and v.strip() and v.strip() != "NO_KEY_PROVIDED":
                    return v.strip()

        return "NO_KEY_PROVIDED"

    @property
    def OPENROUTER_API_KEY(self):
        return self.get_api_key()

    LLM_BASE_URL = "https://openrouter.ai/api/v1"
    LLM_TEMPERATURE = 0.3 # Lower temperature for more focused and deterministic answers, especially since we're relying on retrieved documents for context.
    LLM_MAX_TOKENS = 768  # Increased from 512 to allow room for structured output format

    # Logging
    LOG_LEVEL = "INFO"