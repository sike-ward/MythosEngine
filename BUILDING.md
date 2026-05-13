# Building MythosEngine for Distribution

This guide produces a Windows NSIS installer (`MythosEngine Setup x.x.x.exe`)
that bundles the Electron UI and the frozen FastAPI backend.  Testers get a
double-click install with no Python required on the target machine.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Must be in PATH; used only during the build |
| Node.js | 18+ | Required for the Electron/Vite build |
| Git | any | |

The project `.venv` must exist and have all dependencies installed:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Platform icon files must be present in `frontend/build-resources/` (see that
folder's README).

---

## Development

```bash
# Start the Python backend (from project root)
python -m uvicorn server.app:app --host 127.0.0.1 --port 8741 --reload

# Start the Electron + Vite frontend (from frontend/)
cd frontend
npm install
npm run electron:dev
```

Or use the convenience launcher:
```bat
Launch_MythosEngine.bat
```

---

## Production Build

### Step 1 — Freeze the Python backend

Run from the **project root**:

```bat
scripts\build-backend.bat
```

This activates `.venv`, installs PyInstaller, and produces:

```
dist\
  server\
    server.exe      ← entry point Electron will launch
    _internal\      ← all bundled DLLs and .pyc files
```

> **Why onedir instead of onefile?**  The `--onedir` format avoids Windows
> Defender false-positives common with self-extracting `--onefile` bundles and
> starts faster (no extraction on every launch).

### Step 2 — Build the Electron installer

```bat
cd frontend
npm install
npm run build:win
```

electron-builder will:
1. Run `vite build` to compile the React UI into `frontend/dist/`.
2. Copy `dist\server\` from the project root into the app's `Resources/` dir.
3. Package everything into `frontend/dist-electron/MythosEngine Setup x.x.x.exe`.

For other platforms:

```bash
# macOS (produces dist-electron/MythosEngine-x.x.x.dmg)
npm run electron:build:mac

# Linux (produces dist-electron/MythosEngine-x.x.x.AppImage)
npm run electron:build:linux
```

### Step 3 — Test the installer

1. Run `MythosEngine Setup x.x.x.exe` and complete the wizard.
2. Launch **MythosEngine** from the Start Menu or Desktop shortcut.
3. The app should open and the API health check should pass (green status).

The Electron main process (`electron/main.cjs`) will:
1. Open the app window immediately showing a startup splash screen
2. Launch `server.exe` from `resources/server/` (packaged) or spawn uvicorn (dev)
3. Wait up to 20 seconds for the API to respond on port 8741
4. Show an error screen with details if startup fails

User data (vault, logs, `settings.json`, SQLite DB) is stored in:

```
%APPDATA%\MythosEngine\
```

---

## Troubleshooting

### PyInstaller fails with import errors
Add the missing module via `--hidden-import` in `scripts\build-backend.bat`
and re-run.

### `server.exe` crashes on launch
Run it directly in a terminal to see the traceback:

```bat
set MYTHOS_DATA_DIR=%APPDATA%\MythosEngine
dist\server\server.exe
```

### electron-builder can't find `dist\server\`
Make sure Step 1 completed successfully before running Step 2.  The path
`../dist/server` in `package.json` `extraResources` is relative to the
`frontend/` directory.

### App opens but API is unreachable
Check `%APPDATA%\MythosEngine\logs\app.log` for Python-side errors.

---

## CI / automated builds

The two steps map cleanly to separate CI jobs:

```yaml
# (pseudo-code — adapt to your CI system)
build-backend:
  runs-on: windows-latest
  steps:
    - run: scripts\build-backend.bat
    - upload-artifact: dist/server

build-electron:
  needs: build-backend
  steps:
    - download-artifact: dist/server
    - run: cd frontend && npm ci && npm run build:win
    - upload-artifact: frontend/dist-electron/*.exe
```
