import logging 
from typing import List, Dict, Any
from langchain_chroma import Chroma   
from .embeddings import get_embedding_model
from .config import RAGConfig

logger = logging.getLogger(__name__)

# The VectorStoreManager class is responsible for managing interactions with the ChromaDB vector store. It initializes the embedding model and provides methods to get retrievers with specific filters and to add new documents to the vector store. 
class VectorStoreManager:
    def __init__(self):
        # Initialize the embedding model using the get_embedding_model function, which ensures that we only load the model once and reuse it across the application for efficiency.
        self.embedding_model = get_embedding_model()
        self._vectorstore = None

    # The vectorstore property lazily initializes the Chroma vector store when it is first accessed. 
    @property
    def vectorstore(self):
        if self._vectorstore is None:
            # We create a Chroma vector store instance, specifying the persist directory, collection name, and embedding function. 
            self._vectorstore = Chroma(
                persist_directory=RAGConfig.CHROMA_PERSIST_DIR,
                collection_name=RAGConfig.COLLECTION_NAME,
                embedding_function=self.embedding_model,
            )
        return self._vectorstore
    
    # The get_retriever method returns a retriever object that can be used to query the vector store. 
    def get_retriever(self, search_filter=None, where_document=None):
        search_kwargs = {
            "k": RAGConfig.TOP_K,     # final docs returned by vector stage
            "fetch_k": 30,            # bigger pool for diversity selection
            "lambda_mult": 0.5        # 0=more diverse, 1=more similar
        }

        # We can apply a metadata filter to the retriever to only retrieve documents that match certain criteria (e.g., sentiment). 
        if search_filter:
            search_kwargs["filter"] = search_filter
        # Additionally, we can apply a document-level filter to exclude certain documents based on their content or metadata.
        if where_document:
            search_kwargs["where_document"] = where_document

        # We use Maximal Marginal Relevance (MMR) search to retrieve documents that are not only relevant to the query but also diverse among themselves, which can help provide richer context for the LLM when generating answers.
        return self.vectorstore.as_retriever(
            search_type="mmr",       
            search_kwargs=search_kwargs
        )
    
    # The add_documents method allows us to add new documents to the vector store. It first clears existing documents to avoid duplicates, then prepares the new documents in the required format and adds them to ChromaDB. 
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store."""
        from langchain_core.documents import Document
        
        # 1. Clear existing documents so we don't get duplicates on re-upload
        try:
            existing_data = self.vectorstore.get()
            if existing_data and existing_data["ids"]:
                self.vectorstore.delete(ids=existing_data["ids"])
                logger.info(f"Cleared {len(existing_data['ids'])} old documents.")
        except Exception as e:
            logger.warning(f"Could not clear old documents: {e}")

        # 2. Prepare the new documents in the format required by ChromaDB, which includes page_content, metadata, and an optional ID. 
        docs = [
            Document(
                page_content=doc["page_content"],
                metadata=doc.get("metadata", {}),
                id=doc.get("id")
            )
            for doc in documents
        ]

        # 3. Add to ChromaDB and log the count of added documents for debugging purposes. 
        self.vectorstore.add_documents(docs)
        logger.info(f"Added {len(docs)} documents to ChromaDB")

    # The delete_collection method allows us to delete the entire collection from ChromaDB, which can be useful for resyncing the vector store with new data. 
    def delete_collection(self):
        """Delete entire collection (used for resync)"""
        try:
            self.vectorstore.delete_collection()
            self._vectorstore = None
            logger.info("Deleted existing collection")
        except Exception as e:
            logger.warning(f"Failed to delete collection: {e}")