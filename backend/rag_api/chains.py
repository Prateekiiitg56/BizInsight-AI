import logging
import threading
from collections import OrderedDict

from langchain_classic.chains import ConversationalRetrievalChain, RetrievalQA
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from .config import RAGConfig
from .vector_store import get_vector_store_manager

logger = logging.getLogger(__name__)

# A structured format (Summary → Key Themes → Notable Quotes) keeps answers grounded
# and prevents raw review dumps and fabricated statistics.
CUSTOM_PROMPT = PromptTemplate(
    template="""You are a senior Business Intelligence analyst answering questions about customer feedback.

Customer Reviews Retrieved:
{context}

User's Question:
{question}

Answer using ONLY the reviews above. Follow this format strictly:

## Summary
A concise 2-3 sentence answer to the question based on the reviews.

## Key Themes
List the main themes found, with how many of the retrieved reviews mention each:
- **Theme name**: X out of N reviews — brief description

## Notable Quotes
Up to 3 representative quotes from different reviews (no duplicates):
- "quote text"

Rules:
- ONLY use data from the Customer Reviews above. Do NOT invent statistics or numbers.
- If the reviews do not contain relevant information, say exactly: "The customer reviews do not contain information about this topic."
- Never repeat the same review text multiple times.
- Keep the response concise and professional.
""",
    input_variables=["context", "question"],
)


class RAGChainManager:
    """Builds retrieval chains: multi-query expansion → optional cross-encoder re-ranking → LLM."""

    def __init__(self):
        self.vector_store_manager = get_vector_store_manager()
        self._llm = None
        self._conv_chains: "OrderedDict[str, ConversationalRetrievalChain]" = OrderedDict()
        self._conv_lock = threading.Lock()
        self._compressor = None

    @property
    def llm(self) -> ChatOpenAI:
        """Created on first use so retrieval-only mode works without an API key."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                api_key=RAGConfig.get_api_key(),
                base_url=RAGConfig.LLM_BASE_URL,
                model=RAGConfig.LLM_MODEL,
                temperature=RAGConfig.LLM_TEMPERATURE,
                max_tokens=RAGConfig.LLM_MAX_TOKENS,
                max_retries=2,
                timeout=60,
                default_headers={"X-Title": "BizInsight AI"},
            )
        return self._llm

    @property
    def compressor(self):
        """Cross-encoder re-ranker, loaded lazily. Returns None if it can't be loaded."""
        if self._compressor is None:
            try:
                from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
                from langchain_community.cross_encoders import HuggingFaceCrossEncoder
                logger.info("Loading cross-encoder re-ranker...")
                model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
                self._compressor = CrossEncoderReranker(model=model, top_n=8)
            except Exception as e:
                logger.warning(f"Re-ranker unavailable ({e}); continuing without re-ranking.")
                self._compressor = False  # don't retry on every request
        return self._compressor or None

    def _build_retriever(self, user_id: int, search_filter=None):
        base = self.vector_store_manager.get_retriever(user_id, search_filter=search_filter)
        retriever = MultiQueryRetriever.from_llm(retriever=base, llm=self.llm)
        if self.compressor is not None:
            from langchain_classic.retrievers import ContextualCompressionRetriever
            retriever = ContextualCompressionRetriever(base_compressor=self.compressor, base_retriever=retriever)
        return retriever

    def get_qa_chain(self, user_id: int, search_filter=None):
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self._build_retriever(user_id, search_filter),
            return_source_documents=True,
            chain_type_kwargs={"prompt": CUSTOM_PROMPT},
        )

    def get_conversational_chain(self, user_id: int, session_id: str, search_filter=None):
        key = f"{user_id}:{session_id}:{search_filter}"
        with self._conv_lock:
            chain = self._conv_chains.get(key)
            if chain is not None:
                self._conv_chains.move_to_end(key)
                return chain

        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self._build_retriever(user_id, search_filter),
            memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="answer"),
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": CUSTOM_PROMPT},
        )
        with self._conv_lock:
            self._conv_chains[key] = chain
            while len(self._conv_chains) > RAGConfig.MAX_CHAT_SESSIONS:
                self._conv_chains.popitem(last=False)
        return chain
