"""
FastAPI dependency providers for MythosEngine server.

All route handlers receive AppContext and the current User via these
FastAPI dependencies, keeping routes thin and testable.
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User

# The single AppContext instance, set by app.py at startup.
_ctx: Optional[AppContext] = None


def set_app_context(ctx: AppContext) -> None:
    """Called once at startup to register the AppContext."""
    global _ctx
    _ctx = ctx


def get_ctx() -> AppContext:
    """Return the shared AppContext. Raises 503 if not initialised."""
    if _ctx is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application context not initialised.",
        )
    return _ctx


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    ctx: AppContext = Depends(get_ctx),
) -> User:
    """
    Extract and validate the Bearer token from the Authorization header.

    Returns the authenticated User or raises 401.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    session = ctx.storage.get_session_by_id(token)
    if session is None or not session.is_active or session.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid.",
        )
    user = ctx.users.get_user(session.owner_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled.",
        )
    # Propagate identity to storage layer for access-control checks
    ctx.storage.set_user_context(
        user.id,
        is_admin="admin" in user.roles,
        is_gm="gm" in user.roles,
    )
    ctx.current_user_id = user.id
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Raises 403 if the current user does not have the 'admin' role."""
    if "admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user
