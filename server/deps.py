"""
Dependency injection for FastAPI endpoints.

Provides:
- get_ctx: Access to AppContext
- get_current_user: Current authenticated user (requires Bearer token)
- require_admin: Dependency that enforces admin role
- PermissionChecker: Callable dependency for checking named permissions
- TokenStore: SQLite-backed token persistence (survives server restarts)
"""

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import Column, String, DateTime, create_engine, delete, select
from sqlalchemy.orm import Session as SASession, declarative_base

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.user import User


# ============================================================================
# Token store — SQLite-backed, survives server restarts
# ============================================================================

TokenBase = declarative_base()


class TokenRecord(TokenBase):
    """SQLAlchemy model for persistent token storage."""
    __tablename__ = "api_tokens"

    token = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class TokenStore:
    """
    SQLite-backed token store. Persists tokens across server restarts.
    Falls back to in-memory dict if no engine is available.
    """

    def __init__(self, engine=None, token_ttl_days: int = 30):
        self._engine = engine
        self._token_ttl = timedelta(days=token_ttl_days)
        self._memory = {}  # fallback

        if self._engine:
            TokenBase.metadata.create_all(self._engine)

    def _use_db(self) -> bool:
        return self._engine is not None

    def store(self, token: str, user_id: str) -> None:
        """Store a token mapping to a user."""
        if self._use_db():
            with SASession(self._engine) as session:
                record = TokenRecord(
                    token=token,
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + self._token_ttl,
                )
                session.merge(record)
                session.commit()
        else:
            self._memory[token] = user_id

    def get_user_id(self, token: str) -> str | None:
        """Retrieve user_id for a token, or None if not found/expired."""
        if self._use_db():
            with SASession(self._engine) as session:
                record = session.get(TokenRecord, token)
                if not record:
                    return None
                # Check expiry
                if record.expires_at and record.expires_at < datetime.utcnow():
                    session.delete(record)
                    session.commit()
                    return None
                return record.user_id
        else:
            return self._memory.get(token)

    def revoke(self, token: str) -> None:
        """Revoke a token."""
        if self._use_db():
            with SASession(self._engine) as session:
                record = session.get(TokenRecord, token)
                if record:
                    session.delete(record)
                    session.commit()
        else:
            self._memory.pop(token, None)

    def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke all tokens for a user (logout everywhere)."""
        if self._use_db():
            with SASession(self._engine) as session:
                session.execute(
                    delete(TokenRecord).where(TokenRecord.user_id == user_id)
                )
                session.commit()
        else:
            tokens_to_revoke = [
                t for t, uid in self._memory.items() if uid == user_id
            ]
            for t in tokens_to_revoke:
                self._memory.pop(t, None)

    def cleanup_expired(self) -> int:
        """Remove expired tokens. Returns count of removed tokens."""
        if self._use_db():
            with SASession(self._engine) as session:
                result = session.execute(
                    delete(TokenRecord).where(
                        TokenRecord.expires_at < datetime.utcnow()
                    )
                )
                session.commit()
                return result.rowcount
        return 0


# Global token store — initialized lazily with engine from AppContext
_token_store: TokenStore | None = None


# ============================================================================
# Dependency functions
# ============================================================================


def get_ctx(request: Request) -> AppContext:
    """
    Extract and return the AppContext from the request.
    Raises 500 if context is not available.
    """
    ctx = getattr(request.app.state, "ctx", None)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="App context not initialized",
        )
    return ctx


def get_token_store(ctx: AppContext = Depends(get_ctx)) -> TokenStore:
    """
    Get the token store, initializing with SQLite engine on first call.
    """
    global _token_store
    if _token_store is None:
        engine = getattr(ctx.storage, "engine", None)
        _token_store = TokenStore(engine=engine)
    return _token_store


def get_current_user(
    request: Request,
    ctx: AppContext = Depends(get_ctx),
    token_store: TokenStore = Depends(get_token_store),
) -> User:
    """
    Extract Authorization Bearer token, resolve it to a User, and return the User.

    Raises 401 if:
    - No Authorization header
    - Token is invalid or expired
    - User not found in storage
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    user_id = token_store.get_user_id(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = ctx.users.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency that raises 403 if the authenticated user is not an admin."""
    if "admin" not in (user.roles or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


class PermissionChecker:
    """Callable dependency factory that checks whether a user has a named permission.

    Usage::

        @router.get("/example")
        async def example(user: User = Depends(PermissionChecker("notes:write"))):
            ...

    Admins always pass. Other users pass only if the permission string
    appears in their roles list (simple role-based check; extend as needed).
    """

    def __init__(self, permission: str) -> None:
        self.permission = permission

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if "admin" in (user.roles or []):
            return user
        if self.permission in (user.roles or []):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {self.permission}",
        )
