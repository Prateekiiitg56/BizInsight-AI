import logging
import os
import threading
from typing import List

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384


class LightweightEmbeddings:
    """
    Sentence embeddings with graceful degradation:

    1. FastEmbed (ONNX runtime, BAAI/bge-small-en-v1.5) — small memory footprint.
    2. HuggingFace all-MiniLM-L6-v2 via sentence-transformers.
    3. Stateless hashing vectorizer — always available, consistent across calls.
    """

    def __init__(self):
        try:
            from fastembed import TextEmbedding
            logger.info("Initializing FastEmbed (ONNX runtime) embedding engine...")
            cache_dir = os.getenv("FASTEMBED_CACHE_PATH", "./.cache/fastembed")
            self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=cache_dir)
            self._type = "fastembed"
            return
        except Exception as e:
            logger.warning(f"FastEmbed unavailable ({e}); trying HuggingFaceEmbeddings.")

        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self._model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            self._type = "hf"
            return
        except Exception as e:
            logger.warning(f"HuggingFaceEmbeddings unavailable ({e}); using hashing vectorizer.")

        from sklearn.feature_extraction.text import HashingVectorizer
        self._model = HashingVectorizer(
            n_features=EMBEDDING_DIM, alternate_sign=False, norm="l2", ngram_range=(1, 2)
        )
        self._type = "hashing"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._type == "fastembed":
            return [[float(x) for x in e] for e in self._model.embed(texts)]
        if self._type == "hf":
            return self._model.embed_documents(texts)
        return self._model.transform(texts).toarray().tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0] if text else [0.0] * EMBEDDING_DIM


_embedding_model = None
_lock = threading.Lock()


def get_embedding_model() -> LightweightEmbeddings:
    """Load the embedding model once and reuse it across the application."""
    global _embedding_model
    if _embedding_model is None:
        with _lock:
            if _embedding_model is None:
                _embedding_model = LightweightEmbeddings()
    return _embedding_model
