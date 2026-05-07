"""JWT utility functions for MythosEngine FastAPI server.

The main auth flow uses secrets.token_urlsafe + TokenStore (see deps.py).
These functions provide JWT-based token creation/validation for callers
that prefer signed, self-contained tokens.

JWT_SECRET is read from the JWT_SECRET environment variable.
A dev-only default is used when the variable is absent, with a logged warning.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

_DEV_SECRET = "mythos-engine-dev-secret-CHANGE-IN-PRODUCTION"
JWT_SECRET: str = os.getenv("JWT_SECRET", _DEV_SECRET)

if JWT_SECRET == _DEV_SECRET:
    logger.warning(
        "JWT_SECRET is not set — using insecure dev default. "
        "Set the JWT_SECRET environment variable in production."
    )


def create_jwt(
    user_id: str,
    email: str,
    role: str,
    secret: str = JWT_SECRET,
    expires_hours: int = 8,
) -> str:
    """Return a signed HS256 JWT for the given user identity."""
    try:
        import jwt as _jwt
    except ImportError as exc:
        raise RuntimeError("PyJWT is required: pip install PyJWT") from exc

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=expires_hours),
    }
    return _jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str = JWT_SECRET) -> dict:
    """Decode and validate a JWT.

    Raises a 401 HTTPException if the token is expired or otherwise invalid.
    Returns the decoded payload dict on success.
    """
    try:
        import jwt as _jwt
    except ImportError as exc:
        raise RuntimeError("PyJWT is required: pip install PyJWT") from exc

    try:
        return _jwt.decode(token, secret, algorithms=["HS256"])
    except _jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except _jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
