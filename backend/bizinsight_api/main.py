"""
BizInsight AI — Unified FastAPI Application
============================================
Combines the existing RAG chatbot API with new routes for auth,
reviews, dashboard, clustering, and admin management.

Run with:
    python -m bizinsight_api.main
    # or
    uvicorn bizinsight_api.main:app --host 0.0.0.0 --port 8001 --reload
"""

import os
import sys

# Ensure the project root is on the Python path so we can import
# database.py, sentiment.py, clustering/, rag_api/ etc.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import initialize_database

# Import route modules
from bizinsight_api.routes.auth import router as auth_router
from bizinsight_api.routes.reviews import router as reviews_router
from bizinsight_api.routes.dashboard import router as dashboard_router
from bizinsight_api.routes.clustering import router as clustering_router
from bizinsight_api.routes.admin import router as admin_router

# NOTE: We do NOT import rag_api.api at module load time anymore.
# That import chain pulls in torch/transformers/sentence-transformers/
# langchain/chromadb, which alone can eat 300-400MB+ of RAM just from
# `import`-ing them (before any model weights are even loaded). On
# Render's free tier (512MB RAM) that was enough to push the process
# over the limit on boot, causing an OOM-kill -> restart -> OOM-kill
# crash loop that looked like "the backend never finishes starting".
#
# Instead we lazy-load the RAG sub-app the first time /api/rag/* is
# actually hit, via LazyASGIApp below. Auth/dashboard/reviews/
# clustering traffic never pays that memory cost.

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BizInsight AI API",
    description="AI-powered customer feedback analytics — REST API",
    version="2.0.0",
)

# CORS — allow Next.js frontend (dev + prod Vercel deployments)
allow_all = os.getenv("ALLOW_ALL_ORIGINS", "true").lower() == "true"
allowed_origins = ["*"] if allow_all else [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8501",
    "https://biz-insight-ai-eight.vercel.app",
]

frontend_env = os.getenv("FRONTEND_URL")
if frontend_env and frontend_env != "*" and not allow_all:
    allowed_origins.append(frontend_env.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if not allow_all else ["*"],
    allow_origin_regex=None if allow_all else r"https://.*\.vercel\.app",
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Initialize Database ─────────────────────────────────────────────────────

initialize_database()

# ─── Mount Routers ────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(reviews_router)
app.include_router(dashboard_router)
app.include_router(clustering_router)
app.include_router(admin_router)

# Mount the existing RAG chat/sync/health endpoints under /api prefix,
# but only import/build the heavy RAG app on first use (see note above).

class LazyASGIApp:
    """Wraps an ASGI app so the (expensive) import happens on first call,
    not at process startup. Safe under concurrent requests: if two
    requests race to import at the same time, both may build the app,
    but only one instance is kept and both requests still work."""

    def __init__(self, loader):
        self._loader = loader
        self._app = None

    async def __call__(self, scope, receive, send):
        if self._app is None:
            self._app = self._loader()
        await self._app(scope, receive, send)


def _load_rag_app():
    from rag_api.api import app as rag_app
    return rag_app


app.mount("/api/rag", LazyASGIApp(_load_rag_app))


# ─── Root Health Check ────────────────────────────────────────────────────────

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "ok", "service": "bizinsight-api", "version": "2.0.0", "docs": "/docs"}

@app.api_route("/api/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok", "service": "bizinsight-api", "version": "2.0.0"}



# ─── Run Directly ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(
        "bizinsight_api.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )