"""
Dependency injection for FastAPI endpoints.

Provides:
- get_ctx: Access to AppContext
- get_current_user: Current authenticated user (requires Bearer JWT)
- require_permission: Route-level permission-check dependency factory
"""

from fastapi import Depends, HTTPException, Request, status

from MythosEngine.auth.permission_checker import PermissionChecker as _PC
from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User

from server.auth_utils import decode_jwt


def get_ctx(request: Request) -> AppContext:
    """
    Extract and return the AppContext from the request.
    Raises 500 if context is not available.
    """
    ctx = getattr(request.app.state, "ctx", None)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="App context not initialized",
        )
    return ctx


def get_current_user(
    request: Request,
    ctx: AppContext = Depends(get_ctx),
) -> User:
    """
    Extract Authorization Bearer JWT, decode it, and return the User.

    Raises 401 if:
    - No Authorization header
    - Token is invalid or expired
    - User not found in storage
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    payload = decode_jwt(token)  # raises 401 if invalid/expired
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = ctx.users.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_permission(permission: str):
    """
    Dependency factory for route-level permission checks.

    Usage::

        @router.get("/admin-only")
        async def endpoint(admin: User = require_permission("admin")):
            ...
    """
    def dependency(user: User = Depends(get_current_user)) -> User:
        checker = _PC()
        if permission not in (user.roles or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user
    return Depends(dependency)
