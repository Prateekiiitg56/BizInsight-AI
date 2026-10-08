import logging
import re
import threading
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from bizinsight_api.routes.auth import get_optional_user

from .chains import RAGChainManager
from .config import RAGConfig
from .indexing import ensure_demo_indexed, ensure_user_indexed

logging.basicConfig(level=RAGConfig.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="BizInsight RAG API", version="2.0.0")

_chain_manager: Optional[RAGChainManager] = None
_chain_manager_key: Optional[str] = None
_chain_manager_lock = threading.Lock()


def get_chain_manager() -> RAGChainManager:
    """Lazy singleton; rebuilt if the API key changes at runtime."""
    global _chain_manager, _chain_manager_key
    key = RAGConfig.get_api_key()
    with _chain_manager_lock:
        if _chain_manager is None or _chain_manager_key != key:
            logger.info("Initializing RAG chain manager...")
            _chain_manager = RAGChainManager()
            _chain_manager_key = key
        return _chain_manager


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, max_length=100)
    use_memory: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: Optional[str] = None
    demo: bool = False


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool


NEGATIVE_WORDS = {
    "issue", "issues", "problem", "problems", "bad", "complaint", "complaints", "wrong", "broken",
    "negative", "worst", "terrible", "horrible", "hate", "angry", "disappointed", "frustrating",
    "slow", "delay", "delays", "late", "bug", "bugs", "crash", "crashes", "error", "errors",
    "fail", "failure", "refund", "damage", "damaged", "poor", "awful",
}
POSITIVE_WORDS = {
    "good", "great", "best", "love", "awesome", "perfect", "positive", "happy", "excellent",
    "amazing", "fast", "helpful", "recommend", "satisfied", "impressed", "premium",
    "outstanding", "fantastic", "wonderful", "like", "praise",
}


def sentiment_filter_for(question: str) -> Optional[dict]:
    """Route clearly negative/positive questions to reviews with matching sentiment."""
    words = set(re.findall(r"[a-z]+", question.lower()))
    negative, positive = bool(words & NEGATIVE_WORDS), bool(words & POSITIVE_WORDS)
    if negative and not positive:
        return {"sentiment": {"$lt": 0}}
    if positive and not negative:
        return {"sentiment": {"$gt": 0}}
    return None


def _dedupe(items: List[str]) -> List[str]:
    return list(dict.fromkeys(items))


def _retrieval_only_answer(cm: RAGChainManager, user_id: int, question: str, search_filter) -> ChatResponse:
    """Answer without an LLM: list the most relevant reviews (used when no API key is set)."""
    docs = cm.vector_store_manager.get_retriever(user_id, search_filter).invoke(question)
    if not docs and search_filter:
        docs = cm.vector_store_manager.get_retriever(user_id).invoke(question)
    sources = _dedupe([d.page_content for d in docs])

    if sources:
        bullets = "\n".join(f"- {s}" for s in sources[:RAGConfig.TOP_K])
        noun = "review" if len(sources) == 1 else "reviews"
        answer = f"## Most relevant reviews\nFound {len(sources)} matching {noun}:\n\n{bullets}"
    else:
        answer = "No matching reviews found. Upload a CSV of customer reviews to get started."
    answer += "\n\n> AI summaries are disabled because no LLM API key is configured on the server."
    return ChatResponse(answer=answer, sources=sources[:RAGConfig.TOP_K])


def _run_chain(cm: RAGChainManager, user_id: int, request: ChatRequest, search_filter):
    if request.use_memory and request.session_id:
        chain = cm.get_conversational_chain(user_id, request.session_id, search_filter)
        result = chain.invoke({"question": request.question})
        answer = result.get("answer", "")
    else:
        chain = cm.get_qa_chain(user_id, search_filter)
        result = chain.invoke({"query": request.question})
        answer = result.get("result", "")
    sources = _dedupe([d.page_content for d in result.get("source_documents", [])])
    return answer, sources


def _chat(request: ChatRequest, user: Optional[dict]) -> ChatResponse:
    is_demo = user is None
    user_id = RAGConfig.DEMO_USER_ID if is_demo else user["id"]

    if is_demo:
        ensure_demo_indexed()
    else:
        ensure_user_indexed(user_id)

    cm = get_chain_manager()
    search_filter = sentiment_filter_for(request.question)

    if not RAGConfig.get_api_key():
        response = _retrieval_only_answer(cm, user_id, request.question, search_filter)
    else:
        answer, sources = _run_chain(cm, user_id, request, search_filter)
        if not sources and search_filter:
            # The sentiment filter was too narrow — retry over all of this user's reviews.
            answer, sources = _run_chain(cm, user_id, request, None)
        response = ChatResponse(answer=answer, sources=sources[:RAGConfig.TOP_K])

    response.session_id = request.session_id
    response.demo = is_demo
    return response


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", llm_configured=bool(RAGConfig.get_api_key()))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: Optional[dict] = Depends(get_optional_user)):
    """Answer a question grounded in the caller's reviews (or the demo dataset when signed out)."""
    try:
        return await run_in_threadpool(_chat, request, user)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=502,
            detail="The AI assistant is temporarily unavailable. Please try again in a moment.",
        )
