"""
MythosEngine — entry point.
Starts the FastAPI server via uvicorn.
The UI is served by Electron (frontend/).
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("DEV_MODE", "false").lower() == "true"
    uvicorn.run(
        "server.app:app",
        host="127.0.0.1",
        port=port,
        reload=reload,
        log_level="info",
    )
