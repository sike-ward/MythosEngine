"""
migrations/runner.py — Programmatic Alembic runner for MythosEngine.

Wraps Alembic's Python API so that SQLiteBackend.__init__ can apply any
pending schema migrations on startup without requiring a CLI call.

Concept mapping
---------------
SchemaVersion          → Alembic's ``alembic_version`` table (auto-managed)
@migration(v0, v1)     → Alembic revision files in migrations/versions/
run_migrations(engine) → ``alembic upgrade head`` via the Python API

Fresh-database behaviour
------------------------
If create_all() has already built the tables (no alembic_version row exists),
run_migrations() stamps the database at "head" so that Alembic doesn't try to
re-create tables that are already present.  Subsequent startups apply only
migrations newer than the stamped revision.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_INI_PATH = Path(__file__).parent.parent / "alembic.ini"


def run_migrations(engine: "Engine") -> None:
    """Apply all pending Alembic migrations to *engine*.

    Call this from SQLiteBackend.__init__ after Base.metadata.create_all().
    """
    from alembic import command
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import text

    cfg = Config(str(_INI_PATH))
    cfg.set_main_option("sqlalchemy.url", str(engine.url))

    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        current = ctx.get_current_revision()

    if current is None:
        # Tables were created by create_all() but Alembic has never run.
        # Stamp to head so the next call only runs truly new migrations.
        command.stamp(cfg, "head")
    else:
        command.upgrade(cfg, "head")


# ---------------------------------------------------------------------------
# @migration decorator — thin adapter for hand-written migration callables
# ---------------------------------------------------------------------------
# This decorator lets you write inline Python migrations alongside the
# Alembic revision files.  It is NOT a replacement for Alembic; it is a
# convenience for very simple, non-DDL data migrations that don't need a
# downgrade path.
#
# Usage example (in a migrations/versions/ file or your own module):
#
#   from migrations.runner import migration
#
#   @migration(from_version="0001", to_version="0002")
#   def backfill_titles(session):
#       for row in session.execute(text("SELECT id, data FROM notes")).fetchall():
#           ...
#
# The decorator registers the function but does NOT run it automatically;
# you call it explicitly when needed.

_registry: dict[tuple[str, str], callable] = {}


def migration(from_version: str, to_version: str):
    """Register a data-migration callable for (from_version → to_version)."""

    def _decorator(fn):
        _registry[(from_version, to_version)] = fn
        fn._migration_from = from_version
        fn._migration_to = to_version
        return fn

    return _decorator
