"""AI endpoints.

POST /ai/ask          — ask the AI a question with vault context
POST /ai/summarize    — summarize text
POST /ai/suggest-tags — suggest tags for text
POST /ai/propose-links — suggest internal links for a note
GET  /ai/status       — check if the AI engine is ready
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User

from server.deps import get_ctx, get_current_user


router = APIRouter()


# ============================================================================
# Request/Response models
# ============================================================================


class AskRequest(BaseModel):
    """Request body for POST /ai/ask"""
    prompt: str
    vault_id: Optional[str] = None


class AskResponse(BaseModel):
    """Response body for POST /ai/ask"""
    response: str
    prompt_tokens: int
    completion_tokens: int


class SummarizeRequest(BaseModel):
    """Request body for POST /ai/summarize"""
    text: str


class SummarizeResponse(BaseModel):
    """Response body for POST /ai/summarize"""
    summary: str
    prompt_tokens: int
    completion_tokens: int


class SuggestTagsRequest(BaseModel):
    """Request body for POST /ai/suggest-tags"""
    text: str
    existing_tags: List[str] = []


class SuggestTagsResponse(BaseModel):
    """Response body for POST /ai/suggest-tags"""
    tags: List[str]
    prompt_tokens: int
    completion_tokens: int


class ProposeLinksRequest(BaseModel):
    """Request body for POST /ai/propose-links"""
    note_id: str


class ProposeLinksResponse(BaseModel):
    """Response body for POST /ai/propose-links"""
    links: List[str]
    prompt_tokens: int
    completion_tokens: int


class AIStatusResponse(BaseModel):
    """Response body for GET /ai/status"""
    ready: bool
    index_built: bool


# ============================================================================
# AI endpoints
# ============================================================================


@router.post("/ask", response_model=AskResponse)
async def ask(
    req: AskRequest,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    """Ask the AI a question, optionally with vault context.

    Returns 503 if the AI engine has not been initialised.
    """
    try:
        if not ctx.has_ai():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI engine not available",
            )

        ai = ctx.require_ai()
        response, prompt_tokens, completion_tokens = ai.ask(req.prompt)

        return AskResponse(
            response=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI request failed: {str(e)}",
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    req: SummarizeRequest,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    """Summarize the provided text using the AI engine."""
    try:
        if not ctx.has_ai():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI engine not available",
            )

        ai = ctx.require_ai()
        summary, prompt_tokens, completion_tokens = ai.summarize(req.text)

        return SummarizeResponse(
            summary=summary,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}",
        )


@router.post("/suggest-tags", response_model=SuggestTagsResponse)
async def suggest_tags(
    req: SuggestTagsRequest,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    """Suggest tags for text using the AI engine.

    Optionally pass existing_tags to avoid duplicates.
    The AI backend returns a comma-separated string; this endpoint splits
    and normalises the result into a list.
    """
    try:
        if not ctx.has_ai():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI engine not available",
            )

        ai = ctx.require_ai()
        raw_tags, prompt_tokens, completion_tokens = ai.suggest_tags(req.text)

        # Backend returns comma-separated string; split into a clean list.
        if isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        else:
            tags = list(raw_tags)

        # Deduplicate against caller-supplied existing tags
        if req.existing_tags:
            existing_lower = {t.lower() for t in req.existing_tags}
            tags = [t for t in tags if t.lower() not in existing_lower]

        return SuggestTagsResponse(
            tags=tags,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tag suggestion failed: {str(e)}",
        )


@router.post("/propose-links", response_model=ProposeLinksResponse)
async def propose_links(
    req: ProposeLinksRequest,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    """Suggest internal wiki-style links for a note.

    Loads the note by ID, fetches all note titles as candidates, and asks the
    AI backend to propose links. Returns a list of suggested note titles.
    """
    try:
        if not ctx.has_ai():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI engine not available",
            )

        note = ctx.notes.get_note(req.note_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

        # Collect candidate note titles for the link proposal
        try:
            all_notes = ctx.storage.search_notes("", top_k=500)
            note_names = [
                n.title for n in all_notes
                if n.id != req.note_id and not getattr(n, "is_deleted", False)
            ]
        except Exception:
            note_names = []

        ai = ctx.require_ai()
        raw_links, prompt_tokens, completion_tokens = ai.propose_links(
            note.content, note_names
        )

        # Backend returns comma-separated string; split into a clean list.
        if isinstance(raw_links, str):
            links = [l.strip() for l in raw_links.split(",") if l.strip()]
        else:
            links = list(raw_links)

        return ProposeLinksResponse(
            links=links,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Link proposal failed: {str(e)}",
        )


@router.get("/status", response_model=AIStatusResponse)
async def ai_status(
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    """Return whether the AI engine is initialised and its index is built."""
    ready = ctx.has_ai()
    index_built = False

    if ready:
        ai = ctx.ai
        index_mgr = getattr(ai, "_index_manager", None)
        if index_mgr is not None:
            index_built = getattr(index_mgr, "_index_built", False) or (
                getattr(index_mgr, "index", None) is not None
            )

    return AIStatusResponse(ready=ready, index_built=index_built)
