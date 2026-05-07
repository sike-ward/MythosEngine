"""API route modules.

All routers are imported and re-exported here so app.py can register them
with a single import statement per router.
"""

from server.routes import ai, auth, dashboard, health, invites, notes, settings, users

__all__ = ["ai", "auth", "dashboard", "health", "invites", "notes", "settings", "users"]
