"""
Auth routes — registration, login, Google OAuth, JWT token generation.
"""

import datetime
import re
import secrets
from typing import Optional

import jwt
import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import (
    create_google_user,
    create_user,
    get_user_by_email,
    get_user_by_username,
    no_users_exist,
    verify_password,
)
from bizinsight_api.config import GOOGLE_CLIENT_ID, JWT_ALGORITHM, JWT_EXPIRY_HOURS, JWT_SECRET
from bizinsight_api.models.schemas import (
    AuthResponse,
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    UserInfo,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")


def create_token(user: dict) -> str:
    """Generate a JWT token for an authenticated user."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "iat": now,
        "exp": now + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode a JWT and return the user it identifies, or raise 401."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "id": payload["user_id"],
            "username": payload["username"],
            "role": payload["role"],
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Your session has expired. Please log in again.")
    except (jwt.InvalidTokenError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid authentication token.")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Require a valid Bearer token and return the user it identifies."""
    return decode_token(credentials.credentials)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[dict]:
    """Return the authenticated user, or None for anonymous requests."""
    if credentials is None:
        return None
    return decode_token(credentials.credentials)


def _auth_response(user: dict) -> AuthResponse:
    return AuthResponse(
        token=create_token(user),
        user=UserInfo(id=user["id"], username=user["username"], email=user["email"], role=user["role"]),
    )


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """Create a new user account."""
    username = req.username.strip()
    email = req.email.strip()

    if not USERNAME_PATTERN.match(username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-50 characters: letters, numbers, dots, dashes or underscores.",
        )
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    # The first account on a fresh install becomes the admin.
    role = "admin" if no_users_exist() else "user"
    result = create_user(username, email, req.password, role=role)

    if result == "USERNAME_EXISTS":
        raise HTTPException(status_code=409, detail="That username is already taken.")
    if result == "EMAIL_EXISTS":
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    if not result:
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Authenticate a user and return a JWT token."""
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return _auth_response(user)


@router.get("/me", response_model=UserInfo)
def me(current_user: dict = Depends(get_current_user)):
    """Return the current authenticated user's info."""
    user = get_user_by_username(current_user["username"])
    if not user or user["id"] != current_user["id"]:
        raise HTTPException(status_code=401, detail="Your session is no longer valid. Please log in again.")
    return UserInfo(id=user["id"], username=user["username"], email=user["email"], role=user["role"])


def _verify_google_id_token(id_token: str) -> dict:
    """Verify a Google ID token with Google's tokeninfo endpoint and return its claims."""
    try:
        resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
            timeout=10,
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Could not reach Google to verify sign-in. Please try again.")

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified.")

    claims = resp.json()
    if GOOGLE_CLIENT_ID and claims.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Google token was not issued for this application.")
    if not claims.get("email"):
        raise HTTPException(status_code=400, detail="Your Google account has no email address.")
    if claims.get("email_verified") not in (True, "true"):
        raise HTTPException(status_code=400, detail="Your Google email address is not verified.")
    return claims


def _google_username(claims: dict) -> str:
    base = re.sub(r"[^A-Za-z0-9_.-]", "", claims["email"].split("@")[0])[:40] or "user"
    return base if len(base) >= 3 else f"{base}_user"


@router.post("/google", response_model=AuthResponse)
def google_auth(req: GoogleAuthRequest):
    """Sign in (or sign up) with a verified Google ID token."""
    claims = _verify_google_id_token(req.id_token)
    email = claims["email"]

    user = get_user_by_email(email)
    if not user:
        role = "admin" if no_users_exist() else "user"
        username = _google_username(claims)
        for _ in range(5):
            result = create_google_user(username, email, role=role)
            if result == "USERNAME_EXISTS":
                username = f"{_google_username(claims)[:40]}_{secrets.token_hex(3)}"
                continue
            if not result:
                raise HTTPException(status_code=500, detail="Could not create your account. Please try again.")
            break
        user = get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=500, detail="Could not complete Google sign-in. Please try again.")
    return _auth_response(user)
