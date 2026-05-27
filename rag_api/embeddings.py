import logging
from langchain_huggingface import HuggingFaceEmbeddings
from .config import RAGConfig

logger = logging.getLogger(__name__)

# We use a global variable to hold the embedding model instance so that we only load it once and reuse it across the application. 
_embedding_model = None

# The get_embedding_model function checks if the embedding model has already been loaded. If not, it initializes a new HuggingFaceEmbeddings instance with the specified model name and configuration from RAGConfig.  
def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {RAGConfig.EMBEDDING_MODEL}")
        _embedding_model = HuggingFaceEmbeddings(
            model_name=RAGConfig.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},  # Use CPU for embedding generation
            encode_kwargs={'normalize_embeddings': True} # Normalize embeddings for better similarity search performance
        )
    return _embedding_model