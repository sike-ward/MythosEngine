"""
AI endpoints.

GET  /ai/status       — readiness check (always available, no auth required)
POST /ai/ask          — ask the AI a question with vault context
POST /ai/summarize    — summarize text
POST /ai/suggest-tags — suggest tags for text
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User

from server.deps import get_ctx, get_current_user
from server.limiter import limiter


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
    existing_tags: list[str] = []


class SuggestTagsResponse(BaseModel):
    """Response body for POST /ai/suggest-tags"""
    tags: list[str]
    prompt_tokens: int
    completion_tokens: int


# ============================================================================
# Dependencies
# ============================================================================


def require_index_ready(ctx: AppContext = Depends(get_ctx)) -> None:
    """Raise 503 if the AI vector index is still being built."""
    if not getattr(ctx.ai, "_index_ready", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI index is still building. Try again shortly.",
        )


# ============================================================================
# AI endpoints
# ============================================================================


@router.get("/status")
async def ai_status(
    ctx: AppContext = Depends(get_ctx),
):
    """Return AI engine and index readiness status. Always available."""
    return {
        "ready": ctx.has_ai(),
        "index_built": getattr(ctx.ai, "_index_ready", False) if ctx.has_ai() else False,
    }


@router.post("/ask", response_model=AskResponse)
@limiter.limit("20/minute")
async def ask(
    request: Request,
    req: AskRequest,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
    _: None = Depends(require_index_ready),
):
    """
    Ask the AI a question, optionally with vault context.

    If vault_id is provided, the AI will include relevant notes from that vault
    in its context for a more informed response.

    Requires authentication, an initialised AI engine, and a built index.
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
@limiter.limit("20/minute")
async def summarize(
    request: Request,
    req: SummarizeRequest,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
    _: None = Depends(require_index_ready),
):
    """
    Summarize the provided text using the AI engine.

    Requires authentication, an initialised AI engine, and a built index.
    """
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
@limiter.limit("20/minute")
async def suggest_tags(
    request: Request,
    req: SuggestTagsRequest,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
    _: None = Depends(require_index_ready),
):
    """
    Suggest tags for text using the AI engine.

    Optionally pass existing_tags to avoid duplicates and maintain consistency.

    Requires authentication, an initialised AI engine, and a built index.
    """
    try:
        if not ctx.has_ai():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI engine not available",
            )

        ai = ctx.require_ai()
        tags, prompt_tokens, completion_tokens = ai.suggest_tags(req.text)

        # Filter out existing tags if any
        if req.existing_tags:
            existing_lower = {tag.lower() for tag in req.existing_tags}
            tags = [tag for tag in tags if tag.lower() not in existing_lower]

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
