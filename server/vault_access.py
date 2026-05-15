from __future__ import annotations

from typing import Iterable, List, Optional
from uuid import uuid4

from fastapi import HTTPException, status

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from MythosEngine.models.vault import Vault


def _storage_list_vaults(ctx: AppContext) -> List[Vault]:
    if hasattr(ctx.storage, "list_vaults"):
        try:
            return list(ctx.storage.list_vaults() or [])
        except Exception:
            return []
    return []


def _first_owned_or_member(vaults: Iterable[Vault], user: User) -> Optional[Vault]:
    active = [v for v in vaults if getattr(v, "is_active", True)]
    for vault in active:
        if vault.owner_id == user.id or user.id in (vault.members or []) or user.system_role in ("owner", "admin"):
            return vault
    return active[0] if active else None


def ensure_personal_vault(ctx: AppContext, user: User) -> Vault:
    existing = _first_owned_or_member(_storage_list_vaults(ctx), user)
    if existing:
        return existing

    preferred_id = "default"
    existing_default = getattr(ctx.storage, "get_vault_by_id", lambda _id: None)(preferred_id)
    vault = Vault(
        id=preferred_id if existing_default is None else str(uuid4()),
        owner_id=user.id,
        name="Default Vault",
        description="Personal campaign vault",
        members=[],
        permissions={},
        settings={},
        is_active=True,
    )
    ctx.storage.save_vault(vault)
    return vault


def list_accessible_vaults(ctx: AppContext, user: User) -> List[Vault]:
    ctx.storage.set_user_context(
        user.id,
        is_admin=user.system_role in ("owner", "admin"),
        is_gm=False,
    )
    vaults = [v for v in _storage_list_vaults(ctx) if getattr(v, "is_active", True)]
    if vaults:
        return vaults
    return [ensure_personal_vault(ctx, user)]


def resolve_vault(ctx: AppContext, user: User, vault_id: Optional[str]) -> Vault:
    accessible = list_accessible_vaults(ctx, user)
    if not vault_id:
        return accessible[0]
    for vault in accessible:
        if vault.id == vault_id:
            return vault
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Vault not found or access denied",
    )
