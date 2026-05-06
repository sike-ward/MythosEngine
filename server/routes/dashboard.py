"""
Dashboard endpoints.

GET /dashboard/stats — get dashboard statistics
GET /dashboard/recent — get recently modified notes

NOTE: storage.list_notes() returns List[str] (file paths), not Note objects.
We use search_notes("") to get actual Note objects for the recent notes list,
and len(list_notes()) / len(list_folders()) for simple counts.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User

from server.deps import get_ctx, get_current_user


router = APIRouter()


# ============================================================================
# Response models
# ============================================================================


class DashboardStats(BaseModel):
    """Dashboard statistics — counts of various entities."""
    notes: int = 0
    folders: int = 0
    characters: int = 0
    sessions: int = 0
    timeline_events: int = 0
    quests: int = 0


class RecentNote(BaseModel):
    """Recent note item for the dashboard."""
    id: str
    title: str
    folder_id: Optional[str] = None
    modified_date: Optional[datetime] = None


# ============================================================================
# Dashboard endpoints
# ============================================================================


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    """
    Get dashboard statistics: counts of notes, folders, etc.
    Only counts resources the current user has access to.
    """
    try:
        # Set user context for access control
        ctx.storage.set_user_context(
            user.id,
            is_admin="admin" in (user.roles or []),
            is_gm="gm" in (user.roles or []),
        )

        # Get all notes as objects for tag-based counting
        all_notes = ctx.storage.search_notes("", top_k=1000)

        # Exclude soft-deleted
        all_notes = [n for n in all_notes if not getattr(n, "is_deleted", False)]

        # Count by tag
        def count_with_tag(tag):
            return sum(1 for n in all_notes if tag in (getattr(n, "tags", []) or []))

        notes_count = len(all_notes)

        # Count folders
        folder_paths = ctx.storage.list_folders() or []
        folders_count = len(folder_paths)

        # Characters = notes tagged "character" or "npc"
        characters_count = count_with_tag("character") + count_with_tag("npc")

        # Timeline events
        timeline_count = count_with_tag("timeline-event")

        # Quests
        quests_count = count_with_tag("quest")

        # Sessions (game sessions) = notes tagged "session"
        sessions_count = count_with_tag("session")

        return DashboardStats(
            notes=notes_count,
            folders=folders_count,
            characters=characters_count,
            sessions=sessions_count,
            timeline_events=timeline_count,
            quests=quests_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )


@router.get("/recent", response_model=List[RecentNote])
async def get_recent_notes(
    limit: int = Query(10, ge=1, le=50, description="Number of recent notes"),
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    """
    Get recently modified notes (most recent first).
    Uses search_notes("") to get actual Note objects with metadata.
    """
    try:
        ctx.storage.set_user_context(
            user.id,
            is_admin="admin" in (user.roles or []),
            is_gm="gm" in (user.roles or []),
        )

        # search_notes with empty query returns all notes as Note objects
        all_notes = ctx.storage.search_notes("", top_k=200)

        # Sort by last_modified descending
        all_notes.sort(key=lambda n: n.last_modified, reverse=True)

        # Take the most recent ones
        recent = all_notes[:limit]

        return [
            RecentNote(
                id=n.id,
                title=n.title,
                folder_id=getattr(n, "folder_id", None),
                modified_date=n.last_modified,
            )
            for n in recent
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent notes: {str(e)}",
        )
