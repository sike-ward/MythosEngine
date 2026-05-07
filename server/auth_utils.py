"""JWT utilities for the MythosEngine API server."""

import datetime
import os

from fastapi import HTTPException
from jose import JWTError, jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"


def create_jwt(user_id: str, email: str, role: str, expires_hours: int = 8) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
