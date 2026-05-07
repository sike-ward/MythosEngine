"""
Dashboard routes for MythosEngine FastAPI server.

Endpoints
---------
GET /dashboard/stats  — note/character/session counts
GET /dashboard/recent — most-recently-modified notes
"""

from fastapi import APIRouter, Depends

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.dependencies import get_ctx, get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    notes = ctx.storage.list_notes()
    folders = ctx.storage.list_folders()

    # Characters, sessions — count JSON files via storage if available
    characters = _count_meta(ctx, "characters")
    sessions = _count_meta(ctx, "sessions")
    timeline_events = _count_timeline(ctx)

    return {
        "notes": len(notes),
        "folders": len(folders),
        "characters": characters,
        "quests": 0,  # Quest model not yet implemented
        "timeline_events": timeline_events,
        "sessions": sessions,
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


def _count_meta(ctx: AppContext, subfolder: str) -> int:
    """Count JSON files in a .dnd_meta subfolder (HybridStorage / SQLiteBackend)."""
    try:
        from pathlib import Path

        vault_path = getattr(ctx.storage, "vault_path", None)
        if vault_path:
            d = Path(vault_path) / ".dnd_meta" / subfolder
            if d.is_dir():
                return len(list(d.glob("*.json")))
    except Exception:
        pass
    return 0


def _count_timeline(ctx: AppContext) -> int:
    """Count timeline events if the storage supports it."""
    try:
        events = ctx.storage.read_timeline()
        return len(events)
    except Exception:
        return 0
