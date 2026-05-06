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

from server.deps import get_ctx, get_current_user


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
    used_by: str | None


class GenerateInviteRequest(BaseModel):
    """Request body for POST /invites (currently no parameters)"""
    pass


class GenerateInviteResponse(BaseModel):
    """Response body for POST /invites"""
    code: str
    expires_at: datetime
    message: str


# ============================================================================
# Helper: Require admin
# ============================================================================


def require_admin(user: User = Depends(get_current_user)):
    """Dependency that ensures the user is an admin."""
    if "admin" not in (user.roles or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# ============================================================================
# Invite management endpoints
# ============================================================================


@router.get("/", response_model=List[InviteListItem])
async def list_invites(
    ctx: AppContext = Depends(get_ctx),
    admin: User = Depends(require_admin),
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
    ctx: AppContext = Depends(get_ctx),
    admin: User = Depends(require_admin),
):
    """
    Generate a new invite code.

    Requires admin role. Returns a 12-character code in the format XXXX-XXXX-XXXX.
    The code expires in 7 days.
    """
    try:
        invite = ctx.invites.generate(created_by_user_id=admin.id)

        return GenerateInviteResponse(
            code=invite.code,
            expires_at=invite.expires_at,
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
    admin: User = Depends(require_admin),
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
