import logging
from langchain_classic.chains import RetrievalQA, ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_classic.retrievers.multi_query import MultiQueryRetriever

from .vector_store import VectorStoreManager
from .config import RAGConfig

logger = logging.getLogger(__name__)
logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)

# We define a custom prompt template that instructs the LLM to provide structured, accurate answers based strictly on the retrieved customer reviews. The structured format (Summary → Key Themes → Notable Quotes) prevents raw review dumps and hallucinated statistics.
custom_prompt_template = """You are a senior Business Intelligence analyst answering questions about customer feedback.

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
- Count themes only from the provided reviews, do not fabricate numbers like "184 mentions".
- Keep the response concise and professional.
"""

# By using this custom prompt, we guide the LLM to provide structured, accurate answers based on the retrieved customer reviews while preventing raw dumps and fabricated statistics.
CUSTOM_PROMPT = PromptTemplate(
    template=custom_prompt_template, 
    input_variables=["context", "question"]
)

# The RAGChainManager class is responsible for managing the retrieval-augmented generation chains used in the RAG API. It initializes the vector store manager, the LLM, and the re-ranker model. The get_qa_chain method constructs a RetrievalQA chain that incorporates multi-query expansion and re-ranking to provide accurate answers based on retrieved documents. The get_conversational_chain method creates a ConversationalRetrievalChain that maintains conversation history and also uses multi-query expansion and re-ranking for enhanced retrieval during chat interactions. Both methods utilize the custom prompt to ensure that the LLM's responses are grounded in the retrieved customer reviews.
class RAGChainManager:
    def __init__(self):
        # Initialize the Vector Store Manager, which handles interactions with ChromaDB for document retrieval. This manager provides methods to get retrievers with specific filters and to add new documents to the vector store
        self.vector_store_manager = VectorStoreManager() 
        
        # Initialize the LLM (Language Model) using ChatOpenAI, configured with the model name, API key, temperature, max tokens, and retry settings defined in RAGConfig. This LLM will be used to generate answers based on the retrieved documents and the custom prompt.
        self.llm = ChatOpenAI(
            openai_api_key=RAGConfig.OPENROUTER_API_KEY,
            openai_api_base=RAGConfig.LLM_BASE_URL,
            model_name=RAGConfig.LLM_MODEL,
            temperature=RAGConfig.LLM_TEMPERATURE,
            max_tokens=RAGConfig.LLM_MAX_TOKENS,
            max_retries=4
        )

        self._qa_chain = None
        self._conv_chains = {}  
        self._compressor = None

    @property
    def compressor(self):
        if self._compressor is None:
            from langchain_community.cross_encoders import HuggingFaceCrossEncoder
            from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
            logger.info("Loading Re-Ranker Model lazily...")
            reranker_model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
            self._compressor = CrossEncoderReranker(model=reranker_model, top_n=8)
        return self._compressor

    # The get_qa_chain method constructs a RetrievalQA chain that incorporates multi-query expansion and re-ranking to provide accurate answers based on retrieved documents. It first creates a base retriever from the vector store manager, then wraps it with a MultiQueryRetriever to generate multiple queries for better context coverage, and finally applies a ContextualCompressionRetriever with the cross-encoder re-ranker to filter down to the most relevant documents before passing them to the LLM for answer generation.
    def get_qa_chain(self, search_filter=None):
        # 1. Base Retrieval (Fetch quickly from ChromaDB)
        base_retriever = self.vector_store_manager.get_retriever(search_filter=search_filter)
        
        # 2. Multi-Query Expansion (Brainstorm 3 questions to catch more context)
        mq_retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=self.llm)
        
        # 3. Re-Ranking (Grade all results and keep only the top 8 best matches)
        from langchain_classic.retrievers import ContextualCompressionRetriever
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor,
            base_retriever=mq_retriever
        )
        
        # 4. Build the final RetrievalQA chain with the compressed retriever and custom prompt
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff", # We use "stuff" to feed all retrieved docs into the prompt
            retriever=compression_retriever, 
            return_source_documents=True, 
            chain_type_kwargs={"prompt": CUSTOM_PROMPT},
            verbose=False
        )

    # The get_conversational_chain method creates a ConversationalRetrievalChain that maintains conversation history and also uses multi-query expansion and re-ranking for enhanced retrieval during chat interactions. It constructs a unique chain key based on the session ID and search filter to manage multiple conversational chains. Each chain incorporates a ConversationBufferMemory to keep track of the chat history, and it uses the same multi-query and re-ranking retrieval strategy as the get_qa_chain method to ensure that the LLM's responses are based on the most relevant documents from the vector store.
    def get_conversational_chain(self, session_id: str, search_filter=None):
        chain_key = f"{session_id}_{str(search_filter)}" # Unique key for this conversational chain based on session and filter
        
        # If a chain for this session and filter doesn't exist, we create it. This allows us to maintain separate conversation histories and retrieval contexts for different users or different types of queries (e.g., positive vs negative sentiment).
        if chain_key not in self._conv_chains:
            # We set up a ConversationBufferMemory to keep track of the chat history for this session
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            
            # Layer 1: Base Retriever
            base_retriever = self.vector_store_manager.get_retriever(search_filter=search_filter)
            
            # Layer 2: Multi-Query
            mq_retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=self.llm)
            
            # Layer 3: Cross-Encoder Re-Ranker
            from langchain_classic.retrievers import ContextualCompressionRetriever
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=self.compressor,
                base_retriever=mq_retriever
            )
            
            # Final Chain: Conversational Retrieval Chain with memory and custom prompt
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=compression_retriever, 
                memory=memory, 
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": CUSTOM_PROMPT},
                verbose=False
            )
            self._conv_chains[chain_key] = chain # Store the chain in the dictionary with its unique key for future retrieval
        return self._conv_chains[chain_key] # Return the conversational chain for this session.