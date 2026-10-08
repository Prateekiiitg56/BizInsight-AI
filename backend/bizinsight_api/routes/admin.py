"""
Admin routes — user management (admin only) and clearing your own data.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from database import clear_data, delete_user, fetch_all_users
from bizinsight_api.routes.auth import get_current_user
from bizinsight_api.models.schemas import AdminUserItem, AdminUsersResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency that enforces admin-only access."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


def _remove_vectors(user_id: int) -> None:
    try:
        from rag_api.indexing import remove_user_reviews
        remove_user_reviews(user_id)
    except Exception as e:
        logger.warning(f"Vector cleanup skipped for user {user_id}: {e}")


@router.get("/users", response_model=AdminUsersResponse)
def list_users(current_user: dict = Depends(require_admin)):
    """List all registered users with review counts."""
    users = fetch_all_users()
    items = [
        AdminUserItem(id=u[0], username=u[1], role=u[2], created_at=str(u[3]), review_count=u[4])
        for u in users
    ]
    return AdminUsersResponse(users=items)


@router.delete("/users/{user_id}")
def remove_user(user_id: int, current_user: dict = Depends(require_admin)):
    """Delete a user and all their feedback data."""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    if not delete_user(user_id):
        raise HTTPException(status_code=500, detail="Failed to delete user.")
    _remove_vectors(user_id)
    return {"status": "success", "message": f"User {user_id} and their data have been deleted."}


@router.delete("/reviews")
def clear_my_data(current_user: dict = Depends(get_current_user)):
    """Delete all of the current user's reviews (and only theirs)."""
    try:
        clear_data(user_id=current_user["id"])
    except Exception:
        logger.exception("Failed to clear reviews")
        raise HTTPException(status_code=500, detail="Could not clear your reviews. Please try again.")
    _remove_vectors(current_user["id"])
    return {"status": "success", "message": "All your review data has been removed."}
