"""MythosEngine FastAPI backend server.

Wraps the existing Python backend (AppContext) and exposes it as REST endpoints
for the Electron/React frontend.

Usage:
    cd MythosEngine
    python -m uvicorn server.app:app --host 127.0.0.1 --port 8741

IMPORTANT: AppContext imports AuthManager which inherits QObject (PyQt6).
We need a QCoreApplication instance for QObject to work. We create a headless
one at startup so the existing backend code works without modification.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory so MythosEngine package is importable
_parent = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_parent))

# AppContext imports AuthManager which inherits QObject.
# QObject needs a QCoreApplication — create a headless one for the API server.
try:
    from PyQt6.QtCore import QCoreApplication
    _qt_app = QCoreApplication.instance()
    if _qt_app is None:
        _qt_app = QCoreApplication(sys.argv)
except ImportError:
    _qt_app = None

from MythosEngine.config.config import Config
from MythosEngine.context.app_context import AppContext

from server.middleware.logging import LoggingMiddleware
from server.routes import ai, auth, dashboard, health, invites, notes, settings, users

logger = logging.getLogger(__name__)

DEV_MODE = os.getenv("DEV_MODE", "true").lower() in ("1", "true", "yes")


# ============================================================================
# App startup / shutdown
# ============================================================================


async def _init_app_context() -> AppContext:
    """Initialise AppContext on startup, mirroring what main.py does."""
    config = Config()
    ctx = AppContext(config)

    try:
        from MythosEngine.ai.core.model_router import ModelRouter
        ctx.ai = ModelRouter(ctx.config, storage=ctx.storage)
    except Exception as exc:
        logger.warning("[server] AI engine not available: %s", exc)

    return ctx


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and graceful shutdown."""
    ctx = await _init_app_context()
    app.state.ctx = ctx

    # Expose the token store on app.state so AuthMiddleware can resolve tokens
    # without a full FastAPI dependency chain.
    from server.deps import get_token_store, TokenStore
    engine = getattr(ctx.storage, "engine", None)
    app.state.token_store = TokenStore(engine=engine)

    logger.info("[server] MythosEngine API ready (dev_mode=%s)", DEV_MODE)
    yield
    logger.info("[server] MythosEngine API shutting down")


# ============================================================================
# FastAPI app factory
# ============================================================================

app = FastAPI(
    title="MythosEngine API",
    description="FastAPI backend for MythosEngine (Electron/React frontend)",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if DEV_MODE else None,
    redoc_url="/redoc" if DEV_MODE else None,
    openapi_url="/openapi.json" if DEV_MODE else None,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow Vite dev server, CRA dev server, and Electron renderer (app://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "app://*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Logging middleware ────────────────────────────────────────────────────────
# Logs: {method} {path} → {status_code} ({duration_ms}ms)
app.add_middleware(LoggingMiddleware)


# ============================================================================
# Route registration
# ============================================================================

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(invites.router, prefix="/invites", tags=["invites"])


# ============================================================================
# Root endpoint
# ============================================================================


@app.get("/")
async def root():
    """API information and available documentation links."""
    return {
        "name": "MythosEngine API",
        "version": "0.1.0",
        "docs": "/docs" if DEV_MODE else None,
        "openapi": "/openapi.json" if DEV_MODE else None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8741)
