"""
AI routes for MythosEngine FastAPI server.

Endpoints
---------
GET  /ai/status       — readiness check (always available, no auth required)
POST /ai/ask          — ask a question about vault lore
POST /ai/summarize    — summarize a block of text
POST /ai/suggest-tags — suggest tags for a note
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.deps import get_ctx, get_current_user
from server.limiter import limiter


router = APIRouter(prefix="/ai", tags=["ai"])


class AskRequest(BaseModel):
    prompt: str


class AskResponse(BaseModel):
    response: str
    prompt_tokens: int
    completion_tokens: int


class SummarizeRequest(BaseModel):
    text: str


class SummarizeResponse(BaseModel):
    summary: str
    prompt_tokens: int
    completion_tokens: int


class SuggestTagsRequest(BaseModel):
    """Request body for POST /ai/suggest-tags"""
    text: str
    existing_tags: list[str] = Field(default_factory=list)


class SuggestTagsResponse(BaseModel):
    """Response body for POST /ai/suggest-tags"""
    tags: list[str]
    prompt_tokens: int
    completion_tokens: int


def require_index_ready(ctx: AppContext = Depends(get_ctx)) -> None:
    """Raise 503 if the AI vector index is still being built."""
    if not getattr(ctx.ai, "_index_ready", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI index is still building. Try again shortly.",
        )


@router.get("/status")
async def ai_status(ctx: AppContext = Depends(get_ctx)):
    return {
        "ready": ctx.has_ai(),
        "index_built": getattr(ctx.ai, "_index_ready", False) if ctx.has_ai() else False,
    }


@router.post("/ask", response_model=AskResponse)
@limiter.limit("20/minute")
async def ask(
    request: Request,
    body: AskRequest,
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
    _: None = Depends(require_index_ready),
):
    if not ctx.has_ai():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI engine is not configured. Set OPENAI_API_KEY in .env.",
        )
    answer, prompt_tokens, completion_tokens = ctx.ai.ask(body.prompt)
    return {
        "response": answer,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }


@router.post("/summarize", response_model=SummarizeResponse)
@limiter.limit("20/minute")
async def summarize(
    request: Request,
    body: SummarizeRequest,
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
    _: None = Depends(require_index_ready),
):
    if not ctx.has_ai():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI engine is not configured. Set OPENAI_API_KEY in .env.",
        )
    summary, prompt_tokens, completion_tokens = ctx.ai.summarize(body.text)
    return {
        "summary": summary,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }


@router.post("/suggest-tags", response_model=SuggestTagsResponse)
@limiter.limit("20/minute")
async def suggest_tags(
    request: Request,
    body: SuggestTagsRequest,
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
    _: None = Depends(require_index_ready),
):
    if not ctx.has_ai():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI engine is not configured. Set OPENAI_API_KEY in .env.",
        )
    tags, prompt_tokens, completion_tokens = ctx.ai.suggest_tags(body.text)
    if body.existing_tags:
        existing_lower = {tag.lower() for tag in body.existing_tags}
        tags = [tag for tag in tags if tag.lower() not in existing_lower]
    return {
        "tags": tags,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
