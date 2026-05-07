"""
Settings routes for MythosEngine FastAPI server.

Endpoints
---------
GET /settings   — return current app settings (safe subset)
PUT /settings   — update settings
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.dependencies import get_ctx, get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])

# Keys that must never be returned to the client
_SENSITIVE_KEYS = {"OPENAI_API_KEY"}

# Keys that clients are allowed to update
_MUTABLE_KEYS = {
    "THEME",
    "FONT_SIZE",
    "SHOW_TOOLTIPS",
    "STARTUP_TAB",
    "COMPACT_MODE",
    "COMPLETION_MODEL",
    "EMBEDDING_MODEL",
    "MAX_TOKENS",
    "LOG_LEVEL",
}


@router.get("")
def get_settings(
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    """Return the current settings, excluding sensitive values."""
    raw: Dict[str, Any] = ctx.config._data.copy()
    for key in _SENSITIVE_KEYS:
        raw.pop(key, None)
    # Mask the API key presence rather than its value
    raw["has_api_key"] = bool(getattr(ctx.config, "OPENAI_API_KEY", ""))
    return raw


@router.put("")
def update_settings(
    body: Dict[str, Any],
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    """Update allowed settings fields."""
    for key, value in body.items():
        if key in _MUTABLE_KEYS:
            setattr(ctx.config, key, value)
    return get_settings(ctx=ctx, _user=_user)
