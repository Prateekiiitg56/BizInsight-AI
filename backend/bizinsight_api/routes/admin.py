"""
Admin routes — user management (list, delete).
Only accessible by users with admin role.
"""

import os
from fastapi import APIRouter, HTTPException, Depends

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database import fetch_all_users, delete_user, clear_data, fetch_all_feedback
from bizinsight_api.routes.auth import get_current_user
from bizinsight_api.models.schemas import AdminUsersResponse, AdminUserItem

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency that enforces admin-only access."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@router.get("/users", response_model=AdminUsersResponse)
def list_users(current_user: dict = Depends(require_admin)):
    """List all registered users with review counts."""
    users = fetch_all_users()
    items = [
        AdminUserItem(
            id=u[0],
            username=u[1],
            role=u[2],
            created_at=str(u[3]),
            review_count=u[4],
        )
        for u in users
    ]
    return AdminUsersResponse(users=items)


@router.delete("/users/{user_id}")
def remove_user(user_id: int, current_user: dict = Depends(require_admin)):
    """Delete a user and all their feedback data."""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")

    success = delete_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user.")

    return {"status": "success", "message": f"User {user_id} and their data have been deleted."}


@router.delete("/reviews")
def clear_my_data(current_user: dict = Depends(get_current_user)):
    """Clear all feedback data for the current user."""
    try:
        clear_data(user_id=current_user["id"])
        try:
            from rag_api.api import get_chain_manager
            cm = get_chain_manager()
            cm.vector_store_manager.delete_collection()
        except Exception as e:
            print(f"ChromaDB clear collection skipped: {e}")
        return {"status": "success", "message": "All your review data has been removed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
