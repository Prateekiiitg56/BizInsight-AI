"""
BizInsight AI — Unified FastAPI Application
============================================
Auth, reviews, dashboard, clustering, admin and the RAG chatbot in one service.

Run from the backend directory with:
    uvicorn bizinsight_api.main:app --host 0.0.0.0 --port 8001 --reload
"""

import asyncio
import logging
import os
import sys

# Make database.py, sentiment.py, clustering/ and rag_api/ importable regardless of CWD.
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bizinsight_api import config
from database import initialize_database
from bizinsight_api.routes.admin import router as admin_router
from bizinsight_api.routes.auth import router as auth_router
from bizinsight_api.routes.clustering import router as clustering_router
from bizinsight_api.routes.dashboard import router as dashboard_router
from bizinsight_api.routes.reviews import router as reviews_router

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

VERSION = "2.1.0"

app = FastAPI(
    title="BizInsight AI API",
    description="AI-powered customer feedback analytics — REST API",
    version=VERSION,
)

# Auth uses Bearer tokens (not cookies), so credentials are never needed cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.allow_all_origins() else config.cors_origins(),
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX") or None,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

initialize_database()

app.include_router(auth_router)
app.include_router(reviews_router)
app.include_router(dashboard_router)
app.include_router(clustering_router)
app.include_router(admin_router)


class LazyASGIApp:
    """Defers importing an ASGI app until its first request.

    The RAG stack (langchain, chromadb, embedding models) costs hundreds of MB
    of RAM just to import. Loading it lazily keeps boot fast and lets the rest
    of the API run on small (512 MB) instances.
    """

    def __init__(self, loader):
        self._loader = loader
        self._app = None
        self._lock = asyncio.Lock()

    async def __call__(self, scope, receive, send):
        if self._app is None:
            async with self._lock:
                if self._app is None:
                    self._app = await asyncio.to_thread(self._loader)
        await self._app(scope, receive, send)


def _load_rag_app():
    from rag_api.api import app as rag_app
    return rag_app


app.mount("/api/rag", LazyASGIApp(_load_rag_app))


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "ok", "service": "bizinsight-api", "version": VERSION, "docs": "/docs"}


@app.api_route("/api/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok", "service": "bizinsight-api", "version": VERSION}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")), log_level="info")
