"""
MythosEngine FastAPI backend server.

Wraps the existing Python backend (AppContext) and exposes it as REST endpoints
for the Electron/React frontend.

Usage:
    cd MythosEngine
    python -m uvicorn server.app:app --host 127.0.0.1 --port 8741

IMPORTANT: AppContext imports AuthManager which inherits QObject (PyQt6).
We need a QCoreApplication instance for QObject to work. We create a headless
one at startup so the existing backend code works without modification.
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

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
    _qt_app = None  # PyQt6 not installed — AuthManager won't work but that's OK

from MythosEngine.config.config import Config
from MythosEngine.context.app_context import AppContext

from server.routes import auth, notes, ai, dashboard, users, settings, invites


# ============================================================================
# App startup/shutdown
# ============================================================================


async def init_app_context() -> AppContext:
    """
    Initialize the AppContext on startup.
    Mirrors what main.py does for the desktop app.
    """
    config = Config()
    ctx = AppContext(config)

    # Wire up the AI engine (optional — fails gracefully)
    try:
        from MythosEngine.ai.core.model_router import ModelRouter
        ctx.ai = ModelRouter(ctx.config, storage=ctx.storage)
    except Exception as e:
        print(f"[server] AI engine not available: {e}")

    return ctx


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage app startup and shutdown.
    """
    ctx = await init_app_context()
    app.state.ctx = ctx
    print("[server] MythosEngine API ready")
    yield
    print("[server] MythosEngine API shutting down")


# ============================================================================
# FastAPI app creation
# ============================================================================

app = FastAPI(
    title="MythosEngine API",
    description="FastAPI backend for MythosEngine (Electron/React frontend)",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Vite dev server and Electron renderer
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health check
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint — used by Electron to wait for server readiness."""
    return {"status": "ok"}


# ============================================================================
# Route modules
# ============================================================================

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
    """Root endpoint — API information."""
    return {
        "name": "MythosEngine API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8741)
