import logging
from .config import RAGConfig

logger = logging.getLogger(__name__)

# We use a global variable to hold the embedding model instance so that we only load it once and reuse it across the application. 
_embedding_model = None

# The get_embedding_model function checks if the embedding model has already been loaded. If not, it initializes a new HuggingFaceEmbeddings instance with the specified model name and configuration from RAGConfig.  
class LightweightEmbeddings:
    """
    Ultra-lightweight sentence embedding model using ONNX runtime (< 20 MB RAM).
    Eliminates PyTorch tensor memory allocations on 512 MB RAM servers.
    """
    def __init__(self):
        self._type = "tfidf"
        try:
            from fastembed import TextEmbedding
            logger.info("Initializing FastEmbed (ONNX Runtime) embedding engine...")
            cache_dir = os.getenv("FASTEMBED_CACHE_PATH", "./.cache/fastembed")
            self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=cache_dir)
            self._type = "fastembed"
        except Exception as e1:
            try:
                logger.warning(f"FastEmbed failed ({e1}), falling back to HuggingFaceEmbeddings (all-MiniLM-L6-v2)...")
                from langchain_huggingface import HuggingFaceEmbeddings
                self._model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                self._type = "hf"
            except Exception as e2:
                logger.warning(f"HuggingFaceEmbeddings fallback to TF-IDF vectorizer ({e2})")
                self._type = "tfidf"
                from sklearn.feature_extraction.text import TfidfVectorizer
                self._vectorizer = TfidfVectorizer(max_features=384)

    def embed_documents(self, texts: list) -> list:
        if not texts:
            return []
        if self._type == "fastembed":
            return [[float(x) for x in e] for e in self._model.embed(texts)]
        if self._type == "hf":
            return self._model.embed_documents(texts)
        import numpy as np
        X = self._vectorizer.fit_transform(texts).toarray()
        if X.shape[1] < 384:
            X = np.pad(X, ((0,0), (0, 384 - X.shape[1])))
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return [[float(x) for x in row] for row in (X / norms)]

    def embed_query(self, text: str) -> list:
        return self.embed_documents([text])[0] if text else [0.0] * 384


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            _embedding_model = LightweightEmbeddings()
        except Exception as e:
            logger.warning(f"LightweightEmbeddings fallback: {e}")
            from langchain_community.embeddings import FakeEmbeddings
            _embedding_model = FakeEmbeddings(size=384)
    return _embedding_model