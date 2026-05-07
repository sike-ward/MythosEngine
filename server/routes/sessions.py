"""
Session Log endpoints — D&D campaign session tracking.

GET    /sessions?vault_id=&skip=&limit=  — paginated list
GET    /sessions/{id}                    — get single session log
POST   /sessions                         — create session log
PUT    /sessions/{id}                    — update session log
DELETE /sessions/{id}                    — soft delete
POST   /sessions/{id}/recap              — generate AI recap from raw_notes
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.deps import get_ctx, get_current_user
from server.vault_access import resolve_vault

router = APIRouter()


# ============================================================================
# Request / Response models
# ============================================================================


class SessionLogCreate(BaseModel):
    vault_id: str
    title: str
    session_date: str = ""
    summary: str = ""
    raw_notes: str = ""
    participants: str = ""
    xp_gained: int = 0
    loot_notes: str = ""


class SessionLogUpdate(BaseModel):
    title: Optional[str] = None
    session_date: Optional[str] = None
    summary: Optional[str] = None
    raw_notes: Optional[str] = None
    ai_recap: Optional[str] = None
    participants: Optional[str] = None
    xp_gained: Optional[int] = None
    loot_notes: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================


@router.get("")
async def list_sessions(
    vault_id: str,
    skip: int = 0,
    limit: int = 50,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    vault_id = resolve_vault(ctx, user, vault_id).id
    items, total = ctx.storage.list_session_logs(vault_id, skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    session = ctx.storage.get_session_log(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("", status_code=201)
async def create_session(
    body: SessionLogCreate,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    data = body.model_dump()
    data["vault_id"] = resolve_vault(ctx, user, body.vault_id).id
    data["owner_id"] = user.id
    session_id = ctx.storage.save_session_log(data)
    return ctx.storage.get_session_log(session_id)


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    body: SessionLogUpdate,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    if ctx.storage.get_session_log(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    update = {k: v for k, v in body.model_dump().items() if v is not None}
    update["id"] = session_id
    ctx.storage.save_session_log(update)
    return ctx.storage.get_session_log(session_id)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    if ctx.storage.get_session_log(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    ctx.storage.soft_delete_session_log(session_id)
    return None


@router.post("/{session_id}/recap")
async def generate_recap(
    session_id: str,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    session = ctx.storage.get_session_log(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not ctx.has_ai():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI engine not available",
        )

    raw_notes = session.get("raw_notes", "").strip()
    if not raw_notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No raw notes to summarize",
        )

    try:
        ai = ctx.require_ai()
        prompt = (
            "You are a D&D session chronicler. Summarize the following session notes "
            f"into a vivid, narrative-style recap for players: {raw_notes}"
        )
        response, _, _ = ai.ask(prompt)
        ctx.storage.save_session_log({"id": session_id, "ai_recap": response})
        return {"ai_recap": response}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recap generation failed: {str(e)}",
        )
