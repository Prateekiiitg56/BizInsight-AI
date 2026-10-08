"""
Pydantic request/response models for the BizInsight API.
All endpoints return typed JSON through these schemas.
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., max_length=50)
    email: str = Field(..., max_length=254)
    password: str = Field(..., max_length=128)
    confirm_password: str = Field(..., max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=128)


class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    role: str


class AuthResponse(BaseModel):
    token: str
    user: UserInfo


class GoogleAuthRequest(BaseModel):
    id_token: str


# ─── Reviews ──────────────────────────────────────────────────────────────────

class ReviewItem(BaseModel):
    review: str
    sentiment: float
    date: str


class UploadSummary(BaseModel):
    total_processed: int
    positive: int
    negative: int
    neutral: int
    negative_percent: float
    alert_triggered: bool = False


class ReviewsResponse(BaseModel):
    reviews: List[ReviewItem]
    total: int
    page: int
    page_size: int


# ─── Dashboard ────────────────────────────────────────────────────────────────

class TrendPoint(BaseModel):
    date: str
    avg_sentiment: float


class KeywordItem(BaseModel):
    keyword: str
    frequency: int


class DashboardSummary(BaseModel):
    total_reviews: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percent: float
    negative_percent: float
    neutral_percent: float
    avg_sentiment: float
    trend: List[TrendPoint]
    top_keywords: List[KeywordItem]


# ─── Alerts ───────────────────────────────────────────────────────────────────

class AlertStatus(BaseModel):
    risk_level: str  # "low", "medium", "high"
    negative_percent: float
    total_reviews: int
    top_issues: List[str]
    threshold: float = 40.0


# ─── Clustering ───────────────────────────────────────────────────────────────

class ClusteringRequest(BaseModel):
    mode: Literal["negative", "positive"] = "negative"


class ClusterItem(BaseModel):
    id: int
    name: str
    count: int
    percentage: float
    example_reviews: List[str]


class ClusteringJobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    message: Optional[str] = None


class ClusteringResult(BaseModel):
    success: bool
    message: str
    total_reviews: int
    n_clusters: int
    noise_percentage: float
    clusters: List[ClusterItem]


# ─── Admin ────────────────────────────────────────────────────────────────────

class AdminUserItem(BaseModel):
    id: int
    username: str
    role: str
    created_at: str
    review_count: int


class AdminUsersResponse(BaseModel):
    users: List[AdminUserItem]

