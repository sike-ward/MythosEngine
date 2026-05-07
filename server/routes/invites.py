"""
Invite code management endpoints (admin only).

GET /invites — list all invite codes
POST /invites — generate a new invite code
DELETE /invites/{id} — revoke an invite code
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.deps import get_ctx, require_permission

router = APIRouter()


# ============================================================================
# Request/Response models
# ============================================================================


class InviteListItem(BaseModel):
    """Invite code item in list response"""

    id: str
    code: str
    created_by: str
    created_at: datetime
    expires_at: datetime
    is_active: bool
    use_count: int
    max_uses: int
    used_by: str | None
    status: str


class GenerateInviteResponse(BaseModel):
    """Response body for POST /invites"""

    code: str
    expires_at: datetime
    max_uses: int
    message: str


class GenerateInviteRequest(BaseModel):
    ttl_days: int = 7
    max_uses: int = 1


# ============================================================================
# Invite management endpoints
# ============================================================================


@router.get("/", response_model=List[InviteListItem])
async def list_invites(
    ctx: AppContext = Depends(get_ctx),
    admin: User = require_permission("admin"),
):
    """
    List all invite codes.

    Requires admin role. Shows active and inactive invites with usage information.
    """
    try:
        invites = ctx.storage.list_invites() or []

        return [
            InviteListItem(
                id=inv.id,
                code=inv.code,
                created_by=inv.created_by,
                created_at=inv.created_at,
                expires_at=inv.expires_at,
                is_active=inv.is_active,
                use_count=inv.use_count,
                used_by=inv.used_by,
                max_uses=inv.max_uses,
                status=inv.status,
            )
            for inv in invites
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list invites: {str(e)}",
        )


@router.post("/", response_model=GenerateInviteResponse)
async def generate_invite(
    body: GenerateInviteRequest,
    ctx: AppContext = Depends(get_ctx),
    admin: User = require_permission("admin"),
):
    """
    Generate a new invite code.

    Requires admin role. Returns a 12-character code in the format XXXX-XXXX-XXXX.
    The code expires in 7 days.
    """
    try:
        invite = ctx.invites.generate_with_expiry(
            created_by_user_id=admin.id,
            expiry_days=body.ttl_days,
            max_uses=body.max_uses,
        )

        return GenerateInviteResponse(
            code=invite.code,
            expires_at=invite.expires_at,
            max_uses=invite.max_uses,
            message=f"Invite code {invite.code} generated successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invite: {str(e)}",
        )


@router.delete("/{invite_id}")
async def revoke_invite(
    invite_id: str,
    ctx: AppContext = Depends(get_ctx),
    admin: User = require_permission("admin"),
):
    """
    Revoke an invite code (mark as inactive).

    Requires admin role. The invite code can no longer be used after revocation.
    """
    try:
        invite = ctx.storage.get_invite_by_id(invite_id)
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invite not found",
            )

        ctx.invites.revoke(invite_id)

        return {"message": "Invite revoked successfully", "invite_id": invite_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke invite: {str(e)}",
        )
