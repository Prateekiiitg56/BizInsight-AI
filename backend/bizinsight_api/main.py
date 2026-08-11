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

# Import the existing RAG API routes to mount alongside the new routes
from rag_api.api import app as rag_app

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BizInsight AI API",
    description="AI-powered customer feedback analytics — REST API",
    version="2.0.0",
)

# CORS — allow Next.js frontend (dev + prod Vercel deployments)
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8501",
    os.getenv("FRONTEND_URL", "*"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ALLOW_ALL_ORIGINS", "true").lower() == "true" else allowed_origins,
    allow_credentials=True,
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

# Mount the existing RAG chat/sync/health endpoints under /api prefix
app.mount("/api/rag", rag_app)


# ─── Root Health Check ────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "bizinsight-api", "version": "2.0.0", "docs": "/docs"}

@app.get("/api/health")
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
