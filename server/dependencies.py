"""Backward-compatible re-exports for dependency helpers."""

from server.deps import get_ctx, get_current_user, require_admin, set_app_context

__all__ = [
    "get_ctx",
    "get_current_user",
    "require_admin",
    "set_app_context",
]
