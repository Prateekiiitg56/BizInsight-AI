import logging
import time  
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .chains import RAGChainManager
from .config import RAGConfig

logging.basicConfig(level=RAGConfig.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="BizInsight RAG API", version="1.0.0")

# CORS setup to allow Streamlit frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:8502"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the RAG Chain Manager which sets up the vector store, LLM, and chains
chain_manager = RAGChainManager()

# Define request and response models for better type checking and documentation
class ChatRequest(BaseModel):
    question: str # The user's question or query
    session_id: Optional[str] = None # An optional session ID for conversational context
    use_memory: bool = False # Whether to use conversational memory (True for follow-up questions, False for standalone queries)

# This response model includes the AI's answer, the sources it retrieved, and an optional session ID for tracking conversations.
class ChatResponse(BaseModel):
    answer: str # The AI-generated answer to the user's question
    sources: List[str] # A list of source documents that the AI used to generate its answer
    session_id: Optional[str] = None # Echo back the session ID if provided, so the frontend can maintain conversation state

# This model is used for syncing documents to the vector store. It expects a list of documents, where each document is a dictionary containing the page content and optional metadata.
class SyncRequest(BaseModel):
    documents: List[Dict[str, Any]] # A list of documents to be added to the vector store, each with 'page_content' and optional 'metadata' and 'id'

# This model is used for the health check endpoint, returning the status of the API and optionally the count of vectors in the store.
class HealthResponse(BaseModel):
    status: str # "ok" if the API is healthy, "error" if there was an issue
    vector_count: Optional[int] = None # The number of vectors currently in the vector store, useful for monitoring and debugging

# --- API ENDPOINTS ---
# The /health endpoint allows us to check if the API is running and can connect to the vector store. It returns "ok" and the count of vectors if successful, or "error" if there was an issue.
@app.get("/health", response_model=HealthResponse) 
async def health_check():
    try:
        count = chain_manager.vector_store_manager.vectorstore._collection.count() # Access the internal collection to get the count of vectors
        return HealthResponse(status="ok", vector_count=count) 
    except Exception as e: 
        logger.error(f"Health check failed: {e}") # Log the error for debugging purposes
        return HealthResponse(status="error")

# The /chat endpoint is the main entry point for the chatbot functionality. It accepts a ChatRequest, processes it through the appropriate RAG chain (with or without memory), and returns a ChatResponse containing the AI's answer and the sources it used. It also includes a retry mechanism to handle transient issues with the LLM provider, and it implements a smart metadata router to filter retrieved documents based on the sentiment of the user's question (positive or negative intent).
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    max_retries = 4  # Number of retry attempts for LLM calls in case of failure, with exponential backoff

    # --- SMART METADATA ROUTER ---
    question_lower = request.question.lower()
    search_filter = None

    # If they ask about negative things, only filter for negative reviews in ChromaDB. 
    if any(word in question_lower for word in ["issue", "problem", "bad", "complaint", "wrong", "broken"]):
        search_filter = {"sentiment": {"$lt": 0}}
        print("🚦 ROUTER: Negative intent detected. Filtering for sentiment < 0")
        
    # If they ask about positive things, only filter for positive reviews in ChromaDB.
    elif any(word in question_lower for word in ["good", "great", "best", "love", "awesome", "perfect"]):
        search_filter = {"sentiment": {"$gt": 0}}
        print("🚦 ROUTER: Positive intent detected. Filtering for sentiment > 0")
    
    # If no clear intent is detected, we don't apply any sentiment filter and let the retriever search across all documents.
    for attempt in range(max_retries): 
        try:
            # Depending on whether the user wants to use memory and has provided a session ID, we either invoke a conversational chain (which maintains context across messages) or a standard QA chain (which treats each message independently). The chains will use the search_filter determined by the smart metadata router to fetch relevant documents from the vector store.
            if request.use_memory and request.session_id: 
                chain = chain_manager.get_conversational_chain(request.session_id, search_filter=search_filter)
                result = chain.invoke({"question": request.question})
                answer = result.get("answer", "")
                sources = [doc.page_content for doc in result.get("source_documents", [])]
            else:
                chain = chain_manager.get_qa_chain(search_filter=search_filter)
                result = chain.invoke({"query": request.question})
                answer = result.get("result", result.get("answer", ""))
                sources = [doc.page_content for doc in result.get("source_documents", [])]

            # Debug logs to inspect the raw AI result and the retrieved sources, which can help in understanding how the smart metadata router is influencing the results.
            if request.use_memory and request.session_id:
                chain = chain_manager.get_conversational_chain(request.session_id, search_filter=search_filter)
                result = chain.invoke({"question": request.question})
                print("🤖 RAW AI RESULT:", result)  
                answer = result.get("answer", "")
                sources = [doc.page_content for doc in result.get("source_documents", [])]
                print("🔍 Retrieved sources:", sources) 

            # Return the AI's answer along with the sources it used. The frontend can use this information to display the answer and optionally show the sources to the user for transparency.
            return ChatResponse(
                answer=answer,
                sources=sources[:RAGConfig.TOP_K],
                session_id=request.session_id
            )
            
        except Exception as e:
            logger.warning(f"LLM Call failed on attempt {attempt + 1}: {str(e)}")
            
            # Implementing exponential backoff before retrying the LLM call. This helps to mitigate issues with rate limits or temporary instability of the LLM provider. The wait time doubles with each attempt (2 seconds, 4 seconds, 8 seconds, etc.).
            if attempt == max_retries - 1: # If we've exhausted all retry attempts, we log the error and return a 502 Bad Gateway response indicating that the AI provider is currently unstable.
                logger.error("All retry attempts exhausted.")
                raise HTTPException(
                    status_code=502, 
                    detail="The AI provider is currently unstable. Please try sending your message again."
                )
            
            # Wait before retrying (exponential backoff)
            time.sleep(2 ** attempt)

# The /sync endpoint allows us to upload new documents to the vector store. It accepts a SyncRequest containing a list of documents, which are then added to the ChromaDB vector store. This endpoint is typically used after uploading new reviews from a CSV file, and it ensures that the vector store is updated with the latest data for accurate retrieval during chat interactions. The endpoint also includes error handling to catch any issues during the syncing process and returns an appropriate HTTP response in case of failure.
@app.post("/sync")
async def sync_documents(request: SyncRequest):
    try:
        # We call the add_documents method of the VectorStoreManager to add the new documents to ChromaDB. This method also handles clearing old documents to prevent duplicates. If the syncing process is successful, we return a success message along with the count of added documents. 
        chain_manager.vector_store_manager.add_documents(request.documents)
        return {"status": "success", "added_count": len(request.documents)}
    except Exception as e:
        # If there is an error during syncing (e.g., issues with ChromaDB, invalid document format), we log the exception and return a 500 Internal Server Error response with the error details.
        logger.exception("Sync failed")
        raise HTTPException(status_code=500, detail=str(e))