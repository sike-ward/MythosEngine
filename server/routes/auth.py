"""
Authentication endpoints.

GET /auth/status — check if setup is needed (no users exist)
POST /auth/setup — create initial admin account (only works when 0 users)
POST /auth/login — authenticate with email/password
POST /auth/logout — invalidate session (client drops token)
GET /auth/me — get current user info
POST /auth/change-password — change password
POST /auth/register — create new account with invite code

NOTE: We bypass AuthManager here because it inherits QObject (PyQt6),
which is unavailable in the headless FastAPI server context. Instead we
use UserManager directly for credential verification.
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User

from server.auth_utils import create_jwt
from server.deps import get_ctx, get_current_user


# ============================================================================
# Rate limiter — prevents brute-force login attempts
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter. Tracks attempts per key (email)."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def is_blocked(self, key: str) -> bool:
        """Check if a key is currently rate-limited."""
        now = time.time()
        attempts = self._attempts[key]
        # Prune old attempts outside the window
        self._attempts[key] = [t for t in attempts if now - t < self.window]
        return len(self._attempts[key]) >= self.max_attempts

    def record(self, key: str) -> None:
        """Record a failed attempt."""
        self._attempts[key].append(time.time())

    def reset(self, key: str) -> None:
        """Reset attempts after successful login."""
        self._attempts.pop(key, None)


_login_limiter = RateLimiter(max_attempts=5, window_seconds=900)  # 5 per 15 min


# ============================================================================
# Password strength validation
# ============================================================================

def validate_password_strength(password: str) -> str:
    """Validate password meets minimum strength requirements."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isalpha() for c in password):
        raise ValueError("Password must contain at least one letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one number")
    return password


router = APIRouter()


# ============================================================================
# Request/Response models
# ============================================================================


class LoginRequest(BaseModel):
    """Request body for POST /auth/login"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response body for successful login"""
    access_token: str
    token_type: str = "bearer"
    exp: datetime
    user: dict


class UserResponse(BaseModel):
    """User info response"""
    id: str
    username: str
    email: str
    roles: list[str]
    is_active: bool


class ChangePasswordRequest(BaseModel):
    """Request body for POST /auth/change-password"""
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, v):
        return validate_password_strength(v)


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register"""
    email: EmailStr
    username: str
    password: str
    invite_code: str

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return validate_password_strength(v)


class RegisterResponse(BaseModel):
    """Response body for successful registration (auto-login)"""
    access_token: str
    token_type: str = "bearer"
    exp: datetime
    user: dict


class SetupRequest(BaseModel):
    """Request body for POST /auth/setup (first-run admin creation)"""
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return validate_password_strength(v)


class SetupResponse(BaseModel):
    """Response body for successful setup (auto-login as admin)"""
    access_token: str
    token_type: str = "bearer"
    exp: datetime
    user: dict


# ============================================================================
# Helper: count users via SQLAlchemy
# ============================================================================


def _count_users(ctx: AppContext) -> int:
    """Return the total number of users in the database."""
    try:
        storage = ctx.storage
        if hasattr(storage, "engine"):
            from sqlalchemy.orm import Session as SASession
            from MythosEngine.storage.sqlite_backend import UserRecord
            with SASession(storage.engine) as session:
                return session.query(UserRecord).count()
    except Exception:
        pass
    return -1  # unknown


# ============================================================================
# Auth endpoints
# ============================================================================


@router.get("/status")
async def auth_status(
    ctx: AppContext = Depends(get_ctx),
):
    """
    Check if the app needs initial setup.
    Returns {needs_setup: true} when no users exist in the database.
    This endpoint is public (no auth required).
    """
    count = _count_users(ctx)
    return {"needs_setup": count == 0}


@router.post("/setup", response_model=SetupResponse)
async def setup_admin(
    req: SetupRequest,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Create the initial admin account. Only works when the database has zero users.
    After the first admin is created, this endpoint is permanently disabled.
    """
    count = _count_users(ctx)
    if count != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup already completed. Use login or invite codes.",
        )

    try:
        user = ctx.users.create_user(
            email=req.email,
            username=req.username,
            password=req.password,
            roles=["admin", "gm"],
        )

        ctx.storage.set_user_context(
            user.id, is_admin=True, is_gm=True,
        )

        role = user.roles[0] if user.roles else "admin"
        token = create_jwt(user.id, user.email, role)
        exp = datetime.utcnow() + timedelta(hours=8)

        return SetupResponse(
            access_token=token,
            token_type="bearer",
            exp=exp,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": user.roles,
                "is_active": user.is_active,
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Setup failed: {str(e)}",
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Authenticate with email and password.
    Returns a signed JWT bearer token and user info on success.
    Rate-limited: max 5 failed attempts per email per 15 minutes.
    """
    # Rate limit check
    email_key = req.email.lower()
    if _login_limiter.is_blocked(email_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in 15 minutes.",
        )

    try:
        # Look up user by email
        user = ctx.users.get_user_by_email(req.email)
        if not user or not user.is_active:
            _login_limiter.record(email_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password using UserManager
        if not ctx.users.verify_password(req.password, user.password_hash):
            _login_limiter.record(email_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Login successful — reset rate limiter for this email
        _login_limiter.reset(email_key)

        # Set user context on storage for permission checks
        ctx.storage.set_user_context(
            user.id,
            is_admin="admin" in (user.roles or []),
            is_gm="gm" in (user.roles or []),
        )

        # Update last_login
        user.last_login = datetime.utcnow()
        ctx.users.update_user(user)

        role = user.roles[0] if user.roles else "player"
        token = create_jwt(user.id, user.email, role)
        exp = datetime.utcnow() + timedelta(hours=8)

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            exp=exp,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": user.roles,
                "is_active": user.is_active,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )


@router.post("/logout")
async def logout(
    user: User = Depends(get_current_user),
):
    """
    Logout the current user. JWTs are stateless so the client is responsible
    for discarding the token. This endpoint confirms the token was valid.
    """
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(
    user: User = Depends(get_current_user),
):
    """
    Get the current user's info.
    Returns nested {user: {...}} to match what the frontend expects.
    """
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "is_active": user.is_active,
        }
    }


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    ctx: AppContext = Depends(get_ctx),
    user: User = Depends(get_current_user),
):
    """
    Change the current user's password.
    """
    try:
        ctx.users.change_password(user.id, req.current_password, req.new_password)
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}",
        )


@router.post("/register", response_model=RegisterResponse)
async def register(
    req: RegisterRequest,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Register a new user with an invite code, then auto-login.
    Returns a JWT + user dict so the frontend can start a session immediately.
    """
    try:
        # Validate invite code
        invite = ctx.invites.validate(req.invite_code)
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invite code",
            )

        # Create the user
        user = ctx.users.create_user(
            email=req.email,
            username=req.username,
            password=req.password,
            roles=["player"],
        )

        # Redeem the invite
        ctx.invites.redeem(req.invite_code, user.id)

        role = user.roles[0] if user.roles else "player"
        token = create_jwt(user.id, user.email, role)
        exp = datetime.utcnow() + timedelta(hours=8)

        return RegisterResponse(
            access_token=token,
            token_type="bearer",
            exp=exp,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": user.roles or ["player"],
                "is_active": user.is_active,
            },
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )
