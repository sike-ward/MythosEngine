"""
MythosEngine FastAPI application.

Creates the FastAPI app, wires up AppContext, and registers all route
modules.  Uvicorn points at ``server.app:app``.

Start from the project root (the directory containing both
``MythosEngine/`` and ``server/``):

    uvicorn server.app:app --host 127.0.0.1 --port 8741 --reload

The Electron ``main.cjs`` starts this automatically in production.
"""

import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from MythosEngine.config.config import Config
from MythosEngine.context.app_context import AppContext
from server.dependencies import set_app_context
from server.routes import ai, auth, dashboard, invites, notes, settings, users

logger = logging.getLogger(__name__)


# ── App lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Bootstrap AppContext and logging once at server startup."""
    # Initialise file + in-memory logging before anything else so all
    # startup messages land in the log file.
    try:
        from MythosEngine.utils.logging_setup import (  # noqa: F401
            APP_SESSION_LOG_HANDLER,
            file_handler,
        )
        root = logging.getLogger()
        if not any(isinstance(h, type(file_handler)) for h in root.handlers):
            root.addHandler(file_handler)
            root.addHandler(APP_SESSION_LOG_HANDLER)
    except Exception as exc:
        logging.basicConfig(level=logging.INFO)
        logger.warning("Could not configure file logging: %s", exc)

    cfg = Config()
    ctx = AppContext(cfg)

    # Wire up AI engine if an API key is present
    api_key = getattr(cfg, "OPENAI_API_KEY", "")
    if api_key:
        try:
            from MythosEngine.ai.core.model_router import get_model_backend

            ctx.ai = get_model_backend(cfg, storage=ctx.storage)
            logger.info("AI engine initialised.")
        except Exception as exc:
            logger.warning("AI engine failed to initialise: %s", exc)

    set_app_context(ctx)
    logger.info("MythosEngine server ready. Vault: %s", getattr(cfg, "VAULT_PATH", "?"))
    yield
    logger.info("MythosEngine server shutting down.")


# ── FastAPI instance ──────────────────────────────────────────────────────────

app = FastAPI(
    title="MythosEngine API",
    version="1.0.0",
    description="REST API for the MythosEngine D&D campaign management platform.",
    lifespan=lifespan,
)

# Allow the Vite dev server (port 5173) and production Electron renderer
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8741",
        "http://127.0.0.1:8741",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global unhandled exception handler ───────────────────────────────────────


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for any exception that escapes a route.

    Logs the full traceback to the app log file so crashes are never
    silently swallowed, then returns a safe JSON 500 to the client.
    """
    logger.error(
        "Unhandled exception on %s %s\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. See the server log for details."
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(ai.router)
app.include_router(dashboard.router)
app.include_router(settings.router)
app.include_router(users.router)
app.include_router(invites.router)


# ── Health check ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["health"])
def health():
    """Liveness probe used by the Electron launcher to detect API readiness."""
    return {"status": "ok", "service": "MythosEngine"}
