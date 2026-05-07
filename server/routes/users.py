"""
User management routes for MythosEngine FastAPI server (admin only).

Endpoints
---------
GET  /users               — list all users
GET  /users/{id}          — get a single user
PUT  /users/{id}/roles    — update roles
POST /users/{id}/disable  — disable account
POST /users/{id}/enable   — enable account
POST /users/{id}/reset-password — admin password reset
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.dependencies import get_ctx, require_admin

router = APIRouter(prefix="/users", tags=["users"])


class UpdateRolesRequest(BaseModel):
    roles: List[str]


class ResetPasswordRequest(BaseModel):
    new_password: str


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "roles": user.roles,
        "groups": user.groups,
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


def _list_all_users(ctx: AppContext):
    """Return all User objects. Works for both HybridStorage and SQLiteBackend."""
    try:
        from MythosEngine.storage.hybrid_storage import HybridStorage

        if isinstance(ctx.storage, HybridStorage):
            raw = ctx.storage._load_global("user")
            return [User.model_validate(v) for v in raw.values()]
    except Exception:
        pass
    try:
        from MythosEngine.storage.sqlite_backend import SQLiteBackend, UserRecord

        if isinstance(ctx.storage, SQLiteBackend):
            with ctx.storage._session() as s:
                return [User.model_validate_json(r.data) for r in s.query(UserRecord).all()]
    except Exception:
        pass
    return []


@router.get("")
def list_users(
    ctx: AppContext = Depends(get_ctx),
    _admin: User = Depends(require_admin),
):
    users = _list_all_users(ctx)
    return {"users": [_user_dict(u) for u in users]}


@router.get("/{user_id}")
def get_user(
    user_id: str,
    ctx: AppContext = Depends(get_ctx),
    _admin: User = Depends(require_admin),
):
    user = ctx.users.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return _user_dict(user)


@router.put("/{user_id}/roles")
def update_roles(
    user_id: str,
    body: UpdateRolesRequest,
    ctx: AppContext = Depends(get_ctx),
    _admin: User = Depends(require_admin),
):
    user = ctx.users.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.roles = body.roles
    ctx.users.update_user(user)
    return _user_dict(user)


@router.post("/{user_id}/disable", status_code=status.HTTP_204_NO_CONTENT)
def disable_user(
    user_id: str,
    ctx: AppContext = Depends(get_ctx),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account.",
        )
    user = ctx.users.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.is_active = False
    ctx.users.update_user(user)


@router.post("/{user_id}/enable", status_code=status.HTTP_204_NO_CONTENT)
def enable_user(
    user_id: str,
    ctx: AppContext = Depends(get_ctx),
    _admin: User = Depends(require_admin),
):
    user = ctx.users.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.is_active = True
    ctx.users.update_user(user)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: str,
    body: ResetPasswordRequest,
    ctx: AppContext = Depends(get_ctx),
    _admin: User = Depends(require_admin),
):
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters.",
        )
    user = ctx.users.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    import bcrypt

    user.password_hash = bcrypt.hashpw(
        body.new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    ctx.users.update_user(user)
