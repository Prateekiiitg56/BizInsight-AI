"""
Review routes — CSV upload with sentiment scoring, review listing, CSV export.
"""

import csv
import io
import logging
import threading

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from database import fetch_feedback, fetch_feedback_page, insert_feedback_bulk
from sentiment import get_sentiment
from bizinsight_api.config import HIGH_RISK_THRESHOLD, MAX_UPLOAD_BYTES, MAX_UPLOAD_MB
from bizinsight_api.routes.auth import get_current_user
from bizinsight_api.models.schemas import ReviewItem, ReviewsResponse, UploadSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


def _sync_vectors_in_background(user_id: int) -> None:
    """Refresh the user's RAG index without blocking the upload response."""
    def _run():
        try:
            from rag_api.indexing import sync_user_reviews
            sync_user_reviews(user_id)
        except Exception as e:
            logger.warning(f"Vector sync skipped for user {user_id}: {e}")

    threading.Thread(target=_run, daemon=True).start()


def _read_csv(contents: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(contents), encoding=encoding)
        except UnicodeDecodeError:
            continue
        except Exception:
            break
    raise HTTPException(status_code=400, detail="Could not parse the file. Make sure it is a valid CSV.")


@router.post("/upload", response_model=UploadSummary)
async def upload_reviews(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Accept a CSV with a 'review' column, score sentiment, store it, and return summary stats."""
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File is too large. The limit is {MAX_UPLOAD_MB} MB.")
    if not contents.strip():
        raise HTTPException(status_code=400, detail="The file is empty.")

    df = _read_csv(contents)

    review_col = next((c for c in df.columns if str(c).strip().lower() == "review"), None)
    if review_col is None:
        raise HTTPException(
            status_code=400,
            detail="The CSV needs a column named 'review'. Rename your review text column and try again.",
        )

    reviews = df[review_col].dropna().astype(str).str.strip()
    reviews = reviews[reviews != ""]
    if reviews.empty:
        raise HTTPException(status_code=400, detail="No reviews found in the 'review' column.")

    scores = reviews.apply(get_sentiment)
    insert_feedback_bulk([(r, float(s)) for r, s in zip(reviews, scores)], user_id=current_user["id"])
    _sync_vectors_in_background(current_user["id"])

    total = len(scores)
    positive = int((scores > 0).sum())
    negative = int((scores < 0).sum())
    negative_percent = round(negative / total * 100, 2)

    return UploadSummary(
        total_processed=total,
        positive=positive,
        negative=negative,
        neutral=total - positive - negative,
        negative_percent=negative_percent,
        alert_triggered=negative_percent >= HIGH_RISK_THRESHOLD,
    )


@router.get("", response_model=ReviewsResponse)
def list_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """Paginated review list for the current user, newest first."""
    rows, total = fetch_feedback_page(current_user["id"], limit=page_size, offset=(page - 1) * page_size)
    reviews = [ReviewItem(review=r[0], sentiment=r[1], date=str(r[2])) for r in rows]
    return ReviewsResponse(reviews=reviews, total=total, page=page, page_size=page_size)


@router.get("/export")
def export_csv(current_user: dict = Depends(get_current_user)):
    """Download the current user's scored reviews as CSV."""
    data = fetch_feedback(user_id=current_user["id"])
    if not data:
        raise HTTPException(status_code=404, detail="No reviews to export yet. Upload a CSV first.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["review", "sentiment", "date"])
    writer.writerows(data)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bizinsight_reviews.csv"},
    )
