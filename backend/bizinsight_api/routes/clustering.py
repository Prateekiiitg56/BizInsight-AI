"""
Clustering routes — run topic clustering as a background job, poll status, fetch results.
"""

import logging
import os
import threading
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException

from database import fetch_feedback
from bizinsight_api.routes.auth import get_current_user
from bizinsight_api.models.schemas import (
    ClusterItem,
    ClusteringJobStatus,
    ClusteringRequest,
    ClusteringResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clustering", tags=["Clustering"])

MIN_REVIEWS = 10
JOB_TTL_SECONDS = 60 * 60

# In-memory job store (sufficient for a single-instance deployment).
_jobs: dict = {}
_jobs_lock = threading.Lock()

_embedding_model = None
_model_lock = threading.Lock()


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        with _model_lock:
            if _embedding_model is None:
                from sentence_transformers import SentenceTransformer
                model_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "models", "finetuned_complaint_model_final"
                )
                _embedding_model = SentenceTransformer(
                    model_path if os.path.exists(model_path) else "all-MiniLM-L6-v2"
                )
    return _embedding_model


def _prune_jobs() -> None:
    cutoff = time.time() - JOB_TTL_SECONDS
    with _jobs_lock:
        for job_id in [j for j, job in _jobs.items() if job["created_at"] < cutoff]:
            del _jobs[job_id]


def _update(job_id: str, **fields) -> None:
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(fields)


def _run_clustering_job(job_id: str, reviews: list, mode: str) -> None:
    try:
        from clustering.run_clustering import run_pipeline

        _update(job_id, status="running", message="Loading embedding model...")
        embedding_model = _get_embedding_model()

        _update(job_id, message=f"Clustering {len(reviews)} reviews...")
        result = run_pipeline(
            reviews,
            embedding_model,
            min_topic_size=max(3, len(reviews) // 5),
            similarity_threshold=0.4,
            verbose=False,
            mode=mode,
        )

        if not result["success"]:
            _update(job_id, status="failed", message=result["message"])
            return

        clusters = [
            ClusterItem(
                id=c["id"],
                name=c["name"],
                count=int(c["count"]),
                percentage=round(c["percentage"], 1),
                example_reviews=c.get("example_reviews", [])[:3],
            )
            for c in result["clusters"]
        ]
        _update(
            job_id,
            status="completed",
            message=result["message"],
            result=ClusteringResult(
                success=True,
                message=result["message"],
                total_reviews=result["total_reviews"],
                n_clusters=result["n_clusters"],
                noise_percentage=round(float(result["noise_percentage"]), 1),
                clusters=clusters,
            ),
        )
    except Exception:
        logger.exception("Clustering job failed")
        _update(job_id, status="failed", message="Clustering failed due to a server error. Please try again.")


def _get_owned_job(job_id: str, user_id: int) -> dict:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None or job["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Clustering job not found. It may have expired.")
    return job


@router.post("/run", response_model=ClusteringJobStatus)
def start_clustering(req: ClusteringRequest, current_user: dict = Depends(get_current_user)):
    """Start clustering as a background job. Returns a job_id to poll."""
    _prune_jobs()
    user_id = current_user["id"]

    with _jobs_lock:
        for job_id, job in _jobs.items():
            if job["user_id"] == user_id and job["status"] in ("pending", "running"):
                return ClusteringJobStatus(job_id=job_id, status=job["status"], message=job["message"])

    data = fetch_feedback(user_id=user_id)
    if not data:
        raise HTTPException(status_code=404, detail="No reviews found. Upload a CSV first.")

    if req.mode == "negative":
        selected = [row[0] for row in data if row[1] < 0]
    else:
        selected = [row[0] for row in data if row[1] > 0]

    if len(selected) < MIN_REVIEWS:
        raise HTTPException(
            status_code=400,
            detail=f"Only {len(selected)} {req.mode} reviews found. At least {MIN_REVIEWS} are needed to cluster.",
        )

    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "user_id": user_id,
            "status": "pending",
            "message": "Job queued...",
            "result": None,
            "created_at": time.time(),
        }

    threading.Thread(target=_run_clustering_job, args=(job_id, selected, req.mode), daemon=True).start()
    return ClusteringJobStatus(job_id=job_id, status="pending", message="Job queued...")


@router.get("/status/{job_id}", response_model=ClusteringJobStatus)
def clustering_status(job_id: str, current_user: dict = Depends(get_current_user)):
    job = _get_owned_job(job_id, current_user["id"])
    return ClusteringJobStatus(job_id=job_id, status=job["status"], message=job.get("message"))


@router.get("/results/{job_id}", response_model=ClusteringResult)
def clustering_results(job_id: str, current_user: dict = Depends(get_current_user)):
    job = _get_owned_job(job_id, current_user["id"])
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"Job is not complete yet (status: {job['status']}).")
    return job["result"]
