# MythosEngine

An AI-powered assistant for managing your D&D lore. Browse notes, chat with your world, generate summaries, and manage characters, maps, timelines, and more — via an Electron + React desktop app backed by a FastAPI server.

---

## Quick Start

### Requirements
- Python 3.11+
- An OpenAI API key
- An Obsidian vault (or any folder of markdown files)

### Install

```bash
git clone https://github.com/sike-ward/Ward_DND_Campaign.git
cd Ward_DND_Campaign
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY and VAULT_PATH
```

### Run

```bash
# Start the FastAPI backend
python MythosEngine/main.py
# or with uvicorn directly
uvicorn server.app:app --host 127.0.0.1 --port 8000

# Start the Electron + React frontend (in a second terminal)
cd frontend && npm start

# Or double-click Launch_MythosEngine.bat (starts both automatically)
```

---

## Environment Configuration

The app uses `.env` files for secrets and environment-specific settings.

| File | Purpose |
|------|---------|
| `.env` | Shared secrets — **never commit this** |
| `.env.development` | Local dev overrides (optional) |
| `.env.production` | Production overrides (optional) |
| `.env.test` | Test environment overrides (optional) |
| `.env.example` | Template — safe to commit |

Set `APP_ENV=production` in your shell to switch environments.

Key variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `VAULT_PATH` | Absolute path to your Obsidian vault |
| `APP_ENV` | `development` (default), `production`, or `test` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING` (default: `INFO`) |
| `COMPLETION_MODEL` | OpenAI model for chat (default: `gpt-4o`) |
| `EMBEDDING_MODEL` | OpenAI model for embeddings (default: `text-embedding-3-small`) |

All other settings live in `Ward_DND_AI/config/settings.json` and can be changed from the Settings tab inside the app.

---

## Project Structure

```
MythosEngine/
├── MythosEngine/
│   ├── ai/           # AI engines (OpenAI, LoreAI RAG)
│   ├── auth/         # PermissionChecker, session management
│   ├── config/       # Config loader, settings.json, templates
│   ├── context/      # AppContext — central service locator
│   ├── managers/     # Business logic layer (one per model type)
│   ├── models/       # Pydantic data models
│   ├── storage/      # StorageBackend interface + SQLite backend
│   ├── tests/        # pytest test suite
│   ├── utils/        # Audit logger, helpers
│   └── main.py       # uvicorn launcher (entry point)
├── server/           # FastAPI app, routes, deps
├── frontend/         # Electron + React + Vite + Tailwind
├── migrations/       # Alembic migrations
├── docs/             # Architecture and operational docs
├── logs/             # app.log, audit.log
├── .env.example      # Environment variable template
├── mypy.ini          # Type checking config
├── TECH_DEBT.md      # Known issues and deferred work
└── requirements.txt  # Python dependencies
```

---

## Architecture Overview

- **Backend**: FastAPI (Python) — `server/` directory, started via `python MythosEngine/main.py` or `uvicorn server.app:app`
- **Frontend**: Electron + React — `frontend/` directory
- **Database**: SQLite via SQLAlchemy
- **AI**: OpenAI GPT-4o (configurable)

> PyQt6 GUI has been removed as of this commit. The sole UI layer is the Electron + React app.

The backend follows a layered design with dependency injection:

- **Models** (`MythosEngine/models/`) — Pydantic v2
- **Storage** (`MythosEngine/storage/`) — SQLAlchemy + SQLite
- **Managers** (`MythosEngine/managers/`) — Business logic; one manager per model type
- **AppContext** (`MythosEngine/context/app_context.py`) — Central service locator: config, storage, AI engine, managers, permissions
- **API** (`server/`) — FastAPI routes; all client interaction goes through the REST API

### Multiuser Design

Every model record carries `owner_id` and a `permissions` dict. `PermissionChecker` (`auth/permission_checker.py`) enforces read/write/admin access. `AppContext.current_user_id` identifies the acting user. When a database backend is added, swap `HybridStorage` for a new `StorageBackend` implementation in `AppContext.__init__` — nothing else needs to change.

---

## Docs

- [Configuration Reference](docs/config-reference.md)
- [Permissions Model](docs/permissions-model.md)
- [Backup & Restore](docs/backup-restore.md)
- [Migration & Upgrade Guide](docs/migration-upgrade.md)

---

## Development

```bash
# Lint + format
ruff check .
ruff format .

# Tests
pytest MythosEngine/tests/

# Type check
mypy MythosEngine/models/ MythosEngine/managers/ MythosEngine/storage/
```

Pre-commit hooks run ruff automatically on every commit.

---

## License

Private project — all rights reserved.
