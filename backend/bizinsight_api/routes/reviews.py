"""
Review routes — CSV upload with sentiment scoring, review listing, CSV export.
"""

import os
import io
import csv
import hashlib
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database import insert_feedback_bulk, fetch_feedback
from bizinsight_api.routes.auth import get_current_user
from bizinsight_api.models.schemas import (
    UploadSummary, ReviewsResponse, ReviewItem
)

# Import VADER for sentiment scoring (same as original app.py)
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

vader_analyzer = SentimentIntensityAnalyzer()

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


def get_sentiment(text: str) -> float:
    """VADER compound score — same logic as original app.py."""
    return vader_analyzer.polarity_scores(text)["compound"]


@router.post("/upload", response_model=UploadSummary)
async def upload_reviews(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Accept a CSV file with a 'review' column, run sentiment scoring,
    store in SQLite, and return summary stats.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    contents = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    if "review" not in df.columns:
        raise HTTPException(
            status_code=400,
            detail="That file doesn't have a 'review' column. Add one and upload again.",
        )

    # Clean
    df = df.dropna(subset=["review"])
    df["review"] = df["review"].astype(str).str.strip()
    df = df[df["review"] != ""]

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="No valid reviews found after cleaning. The file appears to be empty.",
        )

    # Score
    df["sentiment"] = df["review"].apply(get_sentiment)
    reviews_data = list(zip(df["review"], df["sentiment"]))
    insert_feedback_bulk(reviews_data, user_id=current_user["id"])

    # Summary
    positive = int((df["sentiment"] > 0).sum())
    negative = int((df["sentiment"] < 0).sum())
    neutral = int((df["sentiment"] == 0).sum())
    total = len(df)
    negative_percent = round((negative / total) * 100, 2) if total > 0 else 0

    return UploadSummary(
        total_processed=total,
        positive=positive,
        negative=negative,
        neutral=neutral,
        negative_percent=negative_percent,
        alert_triggered=negative_percent > 40,
    )


@router.get("", response_model=ReviewsResponse)
def list_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """Paginated review list for the current user."""
    data = fetch_feedback(user_id=current_user["id"])
    total = len(data)

    start = (page - 1) * page_size
    end = start + page_size
    page_data = data[start:end]

    reviews = [
        ReviewItem(review=row[0], sentiment=row[1], date=str(row[2]))
        for row in page_data
    ]

    return ReviewsResponse(reviews=reviews, total=total, page=page, page_size=page_size)


@router.get("/export")
def export_csv(token: str = Query(..., description="JWT token passed as query param for browser download")):
    """Stream processed reviews as a CSV file download.
    
    Uses query-param token instead of Authorization header because
    window.open() in the browser cannot set custom headers.
    """
    import jwt as pyjwt
    JWT_SECRET = os.getenv("JWT_SECRET", "bizinsight-dev-secret-change-in-production")
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        current_user = {"id": payload["user_id"], "username": payload["username"], "role": payload["role"]}
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please log in again.")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    data = fetch_feedback(user_id=current_user["id"])

    if not data:
        raise HTTPException(status_code=404, detail="No reviews to export. Upload some first.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["review", "sentiment", "date"])
    for row in data:
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bizinsight_feedback.csv"},
    )
