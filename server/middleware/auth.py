"""JWT/token auth middleware.

Pre-validates the Bearer token on every protected request and attaches
the resolved User to request.state.user so downstream route handlers
can read it without repeating the lookup.

Public paths listed in _PUBLIC_PATHS bypass token validation entirely.
The route-level get_current_user() dependency still performs its own
lookup — this middleware is an additional layer, not a replacement.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

_PUBLIC_PATHS = frozenset({
    "/health",
    "/auth/status",
    "/auth/setup",
    "/auth/login",
    "/auth/register",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/",
})

_PUBLIC_PREFIXES = ("/docs", "/redoc", "/static")


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that resolves Bearer tokens to User objects.

    On success: attaches the User to request.state.user and continues.
    On failure for protected paths: returns 401 immediately.
    Public paths pass through without any token check.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if self._is_public(path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]

        try:
            token_store = getattr(request.app.state, "token_store", None)
            ctx = getattr(request.app.state, "ctx", None)

            if token_store is not None and ctx is not None:
                user_id = token_store.get_user_id(token)
                if not user_id:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid or expired token"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                user = ctx.users.get_user(user_id)
                if not user:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "User not found"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                request.state.user = user
        except Exception as exc:
            logger.warning("AuthMiddleware error for %s: %s", path, exc)

        return await call_next(request)

    def _is_public(self, path: str) -> bool:
        if path in _PUBLIC_PATHS:
            return True
        return any(path.startswith(prefix) for prefix in _PUBLIC_PREFIXES)
