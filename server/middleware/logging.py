"""Request/response logging middleware.

Logs one line per request:
    {METHOD} {path} → {status_code} ({duration_ms}ms)
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("server.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code, and duration for every HTTP request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
