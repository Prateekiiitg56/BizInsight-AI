"""
Central runtime settings for the BizInsight API, read from environment variables.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_DEV_JWT_SECRET = "bizinsight-dev-secret-change-in-production"

JWT_SECRET = os.getenv("JWT_SECRET", _DEV_JWT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

if JWT_SECRET == _DEV_JWT_SECRET:
    logger.warning(
        "JWT_SECRET is not set — using the insecure development default. "
        "Set JWT_SECRET to a long random value in production."
    )

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("NEXT_PUBLIC_GOOGLE_CLIENT_ID")

# Upload limits
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# Risk thresholds (percentage of negative reviews)
HIGH_RISK_THRESHOLD = 40.0
MEDIUM_RISK_THRESHOLD = 25.0


def cors_origins() -> list:
    """Allowed browser origins: local dev, the production frontend, and FRONTEND_URL (comma-separated)."""
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://biz-insight-ai-eight.vercel.app",
    ]
    for origin in os.getenv("FRONTEND_URL", "").split(","):
        origin = origin.strip().rstrip("/")
        if origin and origin != "*" and origin not in origins:
            origins.append(origin)
    return origins


def allow_all_origins() -> bool:
    return os.getenv("ALLOW_ALL_ORIGINS", "false").lower() == "true"
