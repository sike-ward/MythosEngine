# Building MythosEngine for Distribution

## Prerequisites

- **Node.js 20+** and **npm**
- **Python 3.11+** with all dependencies installed:
  ```bash
  pip install -r requirements.txt
  ```
- Platform icon files in `frontend/build-resources/` (see that folder's README)

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

## Production Build

> **Note:** The packaged app requires Python 3.11+ to be installed on the target machine.
> The Python backend is bundled as source files in `resources/`; the installer
> does not embed a Python interpreter.

```bash
cd frontend
npm install

# Windows (produces dist-electron/MythosEngine Setup x.x.x.exe)
npm run electron:build:win

# macOS (produces dist-electron/MythosEngine-x.x.x.dmg)
npm run electron:build:mac

# Linux (produces dist-electron/MythosEngine-x.x.x.AppImage)
npm run electron:build:linux
```

The Electron main process (`electron/main.cjs`) will:
1. Open the app window immediately showing a startup splash
2. Spawn `python -m uvicorn server.app:app` from `process.resourcesPath`
3. Wait up to 20 seconds for the API to respond on port 8741
4. Show an error screen with a Retry button if startup fails

## Distributing to Testers

Share the installer from `frontend/dist-electron/`. Testers must have:

1. **Python 3.11+** — <https://www.python.org/downloads/>
2. Run once before first launch:
   ```bash
   pip install -r requirements.txt
   ```
   (The `requirements.txt` is included next to the app in `resources/`)

A future release will bundle a self-contained Python runtime to eliminate this step.
