"""Health check endpoint.

GET /health → { status, version, timestamp }

Used by the Electron launcher to poll until the FastAPI server is ready.
This endpoint is intentionally unauthenticated.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Liveness probe — returns ok with current ISO-8601 timestamp."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
