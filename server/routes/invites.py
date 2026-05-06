"""
Invite code routes for MythosEngine FastAPI server (admin only).

Endpoints
---------
GET    /invites       — list all invite codes
POST   /invites       — generate a new invite code
DELETE /invites/{id}  — revoke an invite code
"""

from fastapi import APIRouter, Depends, HTTPException, status

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.dependencies import get_ctx, require_admin

router = APIRouter(prefix="/invites", tags=["invites"])


def _invite_dict(invite) -> dict:
    return {
        "id": invite.id,
        "code": invite.code,
        "created_by": invite.created_by,
        "used_by": invite.used_by,
        "expires_at": invite.expires_at.isoformat(),
        "use_count": invite.use_count,
        "max_uses": invite.max_uses,
        "is_active": invite.is_active,
        "status": invite.status,
    }


@router.get("")
def list_invites(
    ctx: AppContext = Depends(get_ctx),
    _admin: User = Depends(require_admin),
):
    invites = ctx.invites.list_all()
    return {"invites": [_invite_dict(i) for i in invites]}


@router.post("", status_code=status.HTTP_201_CREATED)
def generate_invite(
    ctx: AppContext = Depends(get_ctx),
    admin: User = Depends(require_admin),
):
    invite = ctx.invites.generate(admin.id)
    return _invite_dict(invite)


@router.delete("/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite(
    invite_id: str,
    ctx: AppContext = Depends(get_ctx),
    _admin: User = Depends(require_admin),
):
    invite = ctx.storage.get_invite_by_id(invite_id)
    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found.")
    ctx.invites.revoke(invite_id)
