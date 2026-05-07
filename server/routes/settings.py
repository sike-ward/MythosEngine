"""
Settings/configuration endpoints.

GET /settings — get current settings
PUT /settings — update settings
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User

from server.deps import get_ctx, get_current_user, require_admin


router = APIRouter()


# ============================================================================
# Request/Response models
# ============================================================================


class SettingsResponse(BaseModel):
    """Current settings response"""
    theme: str
    font_size: str
    vault_path: str
    vault_type: str
    completion_model: str
    embedding_model: str
    max_tokens: int
    auto_refresh_interval: int
    enable_experimental: bool
    show_tooltips: bool
    startup_tab: str
    compact_mode: bool


class UpdateSettingsRequest(BaseModel):
    """Request body for PUT /settings"""
    theme: str | None = None
    font_size: str | None = None
    vault_path: str | None = None
    completion_model: str | None = None
    embedding_model: str | None = None
    max_tokens: int | None = None
    auto_refresh_interval: int | None = None
    enable_experimental: bool | None = None
    show_tooltips: bool | None = None
    startup_tab: str | None = None
    compact_mode: bool | None = None


# ============================================================================
# Settings endpoints
# ============================================================================


@router.get("/", response_model=SettingsResponse)
async def get_settings(
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    """
    Get current application settings.

    Requires authentication.
    """
    try:
        config = ctx.config
        return SettingsResponse(
            theme=getattr(config, "THEME", "Light"),
            font_size=getattr(config, "FONT_SIZE", "Medium"),
            vault_path=getattr(config, "VAULT_PATH", "./Obsidian"),
            vault_type=getattr(config, "VAULT_TYPE", "sqlite"),
            completion_model=getattr(config, "COMPLETION_MODEL", "gpt-4o"),
            embedding_model=getattr(config, "EMBEDDING_MODEL", "text-embedding-3-small"),
            max_tokens=getattr(config, "MAX_TOKENS", 4000),
            auto_refresh_interval=getattr(config, "AUTO_REFRESH_INTERVAL", 300),
            enable_experimental=getattr(config, "ENABLE_EXPERIMENTAL", False),
            show_tooltips=getattr(config, "SHOW_TOOLTIPS", True),
            startup_tab=getattr(config, "STARTUP_TAB", "Dashboard"),
            compact_mode=getattr(config, "COMPACT_MODE", False),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get settings: {str(e)}",
        )


@router.put("/")
async def update_settings(
    req: UpdateSettingsRequest,
    ctx: AppContext = Depends(get_ctx),
    admin: User = Depends(require_admin),
):
    """
    Update application settings. Requires admin role.

    Settings are stored in the config file and persisted across app restarts.
    """
    try:
        config = ctx.config

        # Update only the fields that were provided
        updates = {}
        if req.theme is not None:
            config.THEME = req.theme
            updates["THEME"] = req.theme
        if req.font_size is not None:
            config.FONT_SIZE = req.font_size
            updates["FONT_SIZE"] = req.font_size
        if req.vault_path is not None:
            config.VAULT_PATH = req.vault_path
            updates["VAULT_PATH"] = req.vault_path
        if req.completion_model is not None:
            config.COMPLETION_MODEL = req.completion_model
            updates["COMPLETION_MODEL"] = req.completion_model
        if req.embedding_model is not None:
            config.EMBEDDING_MODEL = req.embedding_model
            updates["EMBEDDING_MODEL"] = req.embedding_model
        if req.max_tokens is not None:
            config.MAX_TOKENS = req.max_tokens
            updates["MAX_TOKENS"] = req.max_tokens
        if req.auto_refresh_interval is not None:
            config.AUTO_REFRESH_INTERVAL = req.auto_refresh_interval
            updates["AUTO_REFRESH_INTERVAL"] = req.auto_refresh_interval
        if req.enable_experimental is not None:
            config.ENABLE_EXPERIMENTAL = req.enable_experimental
            updates["ENABLE_EXPERIMENTAL"] = req.enable_experimental
        if req.show_tooltips is not None:
            config.SHOW_TOOLTIPS = req.show_tooltips
            updates["SHOW_TOOLTIPS"] = req.show_tooltips
        if req.startup_tab is not None:
            config.STARTUP_TAB = req.startup_tab
            updates["STARTUP_TAB"] = req.startup_tab
        if req.compact_mode is not None:
            config.COMPACT_MODE = req.compact_mode
            updates["COMPACT_MODE"] = req.compact_mode

        # Save configuration
        config.save()

        return {
            "message": "Settings updated successfully",
            "updated_fields": list(updates.keys()),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}",
        )
