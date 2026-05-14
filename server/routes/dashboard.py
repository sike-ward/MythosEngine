"""
Dashboard routes for MythosEngine FastAPI server.

Endpoints
---------
GET /dashboard/stats  — note/character/session counts
GET /dashboard/recent — most-recently-modified notes
"""

from fastapi import APIRouter, Depends, Query

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.deps import get_ctx, get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(
    vault_id: str = Query(default=""),
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    notes_count = ctx.storage.count_notes(vault_id=vault_id)
    folders = ctx.storage.list_folders(vault_id=vault_id)
    characters = len(ctx.storage.list_characters(vault_id=vault_id))
    _, sessions_total = ctx.storage.list_session_logs(vault_id=vault_id)
    timeline_events = _count_timeline(ctx)

    return {
        "notes": notes_count,
        "folders": len(folders),
        "characters": characters,
        "quests": 0,  # Quest model not yet implemented
        "timeline_events": timeline_events,
        "sessions": sessions_total,
    }


@router.get("/recent")
def recent(
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    paths = ctx.storage.list_notes()
    items = []
    for p in paths:
        try:
            meta = ctx.storage.get_note_metadata(p)
            items.append(
                {
                    "id": p,
                    "title": p.split("/")[-1].removesuffix(".md"),
                    "modified_date": meta.get("modified"),
                }
            )
        except Exception:
            items.append({"id": p, "title": p.split("/")[-1].removesuffix(".md"), "modified_date": None})

    # Sort newest-first and return top 10
    items.sort(key=lambda x: x.get("modified_date") or "", reverse=True)
    return items[:10]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _count_timeline(ctx: AppContext) -> int:
    """Count timeline events if the storage supports it."""
    try:
        events = ctx.storage.read_timeline()
        return len(events)
    except Exception:
        return 0
