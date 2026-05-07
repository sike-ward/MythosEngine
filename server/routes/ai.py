"""
AI routes for MythosEngine FastAPI server.

Endpoints
---------
POST /ai/ask          — ask a question about vault lore
POST /ai/summarize    — summarize a block of text
POST /ai/suggest-tags — suggest tags for a note
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.dependencies import get_ctx, get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


class AskRequest(BaseModel):
    prompt: str


class SummarizeRequest(BaseModel):
    text: str


class SuggestTagsRequest(BaseModel):
    text: str


@router.post("/ask")
def ask(
    body: AskRequest,
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    if not ctx.has_ai():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI engine is not configured. Set OPENAI_API_KEY in .env.",
        )
    answer, prompt_tokens, completion_tokens = ctx.ai.ask(body.prompt)
    return {
        "answer": answer,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }


@router.post("/summarize")
def summarize(
    body: SummarizeRequest,
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
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


@router.post("/suggest-tags")
def suggest_tags(
    body: SuggestTagsRequest,
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    if not ctx.has_ai():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI engine is not configured. Set OPENAI_API_KEY in .env.",
        )
    tags_str, prompt_tokens, completion_tokens = ctx.ai.suggest_tags(body.text)
    # Parse comma-separated tags returned by the AI
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    return {
        "tags": tags,
        "raw": tags_str,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
