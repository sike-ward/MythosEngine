"""
Auth routes for MythosEngine FastAPI server.

Endpoints
---------
GET  /auth/status         — check if first-run setup is needed
POST /auth/setup          — create the first admin account
POST /auth/login          — email + password → session token
POST /auth/logout         — revoke current session
GET  /auth/me             — return current user profile
POST /auth/register       — create account with invite code
POST /auth/change-password — self-service password change
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User
from server.dependencies import get_ctx, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Pydantic request/response schemas ────────────────────────────────────────


class SetupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    invite_code: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def _user_response(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "roles": user.roles,
        "groups": user.groups,
    }


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/status")
def auth_status(ctx: AppContext = Depends(get_ctx)):
    """Return whether first-time setup is required (no users exist yet)."""
    try:
        any_user = _any_user_exists(ctx)
    except Exception:
        any_user = False
    return {"needs_setup": not any_user}


def _any_user_exists(ctx: AppContext) -> bool:
    """Return True if at least one user record exists in storage."""
    # HybridStorage exposes a private dict via _load_global; SQLite via ORM.
    # We use the public interface: try to find a user by scanning known IDs.
    # The cleanest approach is to check HybridStorage's global users file
    # or SQLite's users table.  Both backends work via the same path below.
    storage = ctx.storage
    # Try a known sentinel — if the storage has any user we can look one up.
    # Since we don't have a list_users() on the abstract interface, we read
    # the underlying data differently per backend type.
    try:
        from MythosEngine.storage.hybrid_storage import HybridStorage

        if isinstance(storage, HybridStorage):
            return bool(storage._load_global("user"))
    except Exception:
        pass
    try:
        from MythosEngine.storage.sqlite_backend import SQLiteBackend, UserRecord

        if isinstance(storage, SQLiteBackend):
            with storage._session() as s:
                return s.query(UserRecord).first() is not None
    except Exception:
        pass
    return False


@router.post("/setup", status_code=status.HTTP_201_CREATED)
def setup(body: SetupRequest, ctx: AppContext = Depends(get_ctx)):
    """Create the first admin account. Fails if any user already exists."""
    if _any_user_exists(ctx):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Setup already complete.",
        )
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters.",
        )
    user = ctx.users.create_user(
        email=body.email,
        username=body.username,
        password=body.password,
        roles=["admin"],
    )
    token = ctx.auth.start_session(user)
    return {"token": token, "user": _user_response(user)}


@router.post("/login")
def login(body: LoginRequest, ctx: AppContext = Depends(get_ctx)):
    """Authenticate with email + password and return a session token."""
    user = ctx.auth.login(body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    token = ctx.auth.start_session(user)
    return {"token": token, "user": _user_response(user)}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user),
    ctx: AppContext = Depends(get_ctx),
):
    """Revoke the current session."""
    ctx.auth.logout(current_user.id)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return {"user": _user_response(current_user)}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, ctx: AppContext = Depends(get_ctx)):
    """Register a new account using an invite code."""
    invite = ctx.invites.validate(body.invite_code)
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite code is invalid, expired, or already used.",
        )
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters.",
        )
    try:
        user = ctx.users.create_user(
            email=body.email,
            username=body.username,
            password=body.password,
            roles=["player"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    ctx.invites.redeem(body.invite_code, user.id)
    token = ctx.auth.start_session(user)
    return {"token": token, "user": _user_response(user)}


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    ctx: AppContext = Depends(get_ctx),
):
    """Change the current user's password."""
    try:
        ctx.users.change_password(current_user.id, body.current_password, body.new_password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
