import logging
import threading
from typing import Any, Dict, Iterable, List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from .config import RAGConfig
from .embeddings import get_embedding_model

logger = logging.getLogger(__name__)


def build_where(user_id: int, search_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Chroma metadata filter scoping retrieval to one user's reviews, plus an optional extra condition."""
    owner = {"user_id": user_id}
    return {"$and": [owner, search_filter]} if search_filter else owner


class VectorStoreManager:
    """All ChromaDB access goes through here. Every document carries a `user_id`
    in its metadata so one tenant's reviews are never retrieved for another."""

    def __init__(self):
        self.embedding_model = get_embedding_model()
        self._vectorstore = None
        self._init_lock = threading.Lock()

    @property
    def vectorstore(self) -> Chroma:
        if self._vectorstore is None:
            # Chroma's client registry isn't safe to initialize from two threads at once
            # (e.g. an upload's background sync racing a chat request).
            with self._init_lock:
                if self._vectorstore is None:
                    self._vectorstore = self._connect()
        return self._vectorstore

    def _connect(self) -> Chroma:
        if RAGConfig.USE_REMOTE_CHROMA:
            import chromadb
            logger.info(f"Connecting to remote ChromaDB at {RAGConfig.CHROMA_HOST}:{RAGConfig.CHROMA_PORT}")
            client = chromadb.HttpClient(host=RAGConfig.CHROMA_HOST, port=RAGConfig.CHROMA_PORT)
            return Chroma(
                client=client,
                collection_name=RAGConfig.COLLECTION_NAME,
                embedding_function=self.embedding_model,
            )
        return Chroma(
            persist_directory=RAGConfig.CHROMA_PERSIST_DIR,
            collection_name=RAGConfig.COLLECTION_NAME,
            embedding_function=self.embedding_model,
        )

    def get_retriever(self, user_id: int, search_filter: Optional[Dict[str, Any]] = None):
        """MMR retriever over a single user's reviews (diverse, relevant matches)."""
        return self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": RAGConfig.TOP_K,
                "fetch_k": 20,
                "lambda_mult": 0.4,  # 0 = more diverse, 1 = more similar
                "filter": build_where(user_id, search_filter),
            },
        )

    def has_documents(self, user_id: int) -> bool:
        result = self.vectorstore.get(where={"user_id": user_id}, limit=1, include=[])
        return bool(result and result.get("ids"))

    def count_documents(self, user_id: int) -> int:
        result = self.vectorstore.get(where={"user_id": user_id}, include=[])
        return len(result.get("ids", [])) if result else 0

    def document_ids(self, user_id: int) -> set:
        result = self.vectorstore.get(where={"user_id": user_id}, include=[])
        return set(result.get("ids", [])) if result else set()

    def delete_ids(self, ids) -> None:
        ids = list(ids)
        for start in range(0, len(ids), 1000):
            self.vectorstore.delete(ids=ids[start:start + 1000])

    def delete_user_documents(self, user_id: int) -> None:
        self.vectorstore._collection.delete(where={"user_id": user_id})

    def upsert_reviews(self, docs: Iterable[Dict[str, Any]], batch_size: int = 256) -> int:
        """Upsert review dicts with keys: id, text, sentiment, user_id, date (optional)."""
        documents: List[Document] = []
        ids: List[str] = []
        for d in docs:
            documents.append(Document(
                page_content=d["text"],
                metadata={
                    "user_id": int(d["user_id"]),
                    "sentiment": float(d["sentiment"]),
                    "date": str(d.get("date") or ""),
                },
            ))
            ids.append(d["id"])

        for start in range(0, len(documents), batch_size):
            # Chroma's add is an upsert, so deterministic ids make re-syncing idempotent.
            self.vectorstore.add_documents(documents[start:start + batch_size], ids=ids[start:start + batch_size])
        logger.info(f"Upserted {len(documents)} documents into ChromaDB")
        return len(documents)


_manager: Optional[VectorStoreManager] = None
_manager_lock = threading.Lock()


def get_vector_store_manager() -> VectorStoreManager:
    """Process-wide singleton so the embedding model and Chroma client load only once."""
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = VectorStoreManager()
    return _manager
