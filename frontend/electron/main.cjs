const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow;
let apiProcess = null;

const isDev = !app.isPackaged;
const API_PORT = 8741;
const API_URL = `http://127.0.0.1:${API_PORT}`;

// ── Launch the FastAPI backend ──────────────────────────────────────────────
function startBackend() {
  // Run uvicorn from the project root (MythosEngine/) so that
  // `from server.routes import ...` and `from MythosEngine.* import ...` both work.
  const projectRoot = isDev
    ? path.join(__dirname, "..", "..")
    : path.join(process.resourcesPath);

  const pythonCmd = process.platform === "win32" ? "python" : "python3";

  apiProcess = spawn(
    pythonCmd,
    ["-m", "uvicorn", "server.app:app", "--host", "127.0.0.1", "--port", String(API_PORT)],
    {
      cwd: projectRoot,
      stdio: ["ignore", "pipe", "pipe"],
    }
  );

  apiProcess.stdout.on("data", (d) => console.log(`[API] ${d}`));
  apiProcess.stderr.on("data", (d) => console.error(`[API] ${d}`));
  apiProcess.on("close", (code) => {
    console.log(`[API] exited with code ${code}`);
  });
}

// ── Wait for the API to become ready ────────────────────────────────────────
async function waitForApi(retries = 30, delay = 500) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(`${API_URL}/health`);
      if (res.ok) return true;
    } catch {
      // not ready yet
    }
    await new Promise((r) => setTimeout(r, delay));
  }
  throw new Error("FastAPI backend did not start in time");
}

// ── Create the main browser window ──────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: "#0D0D14",
    titleBarStyle: "hiddenInset",
    frame: process.platform !== "darwin",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools({ mode: "detach" });
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── App lifecycle ───────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  // In dev mode, check if the API is already running (e.g. started by Launch_MythosEngine.bat).
  // Only start our own backend if it's not already up.
  let apiAlreadyRunning = false;
  try {
    const res = await fetch(`${API_URL}/health`);
    if (res.ok) apiAlreadyRunning = true;
  } catch {
    // not running
  }

  if (!apiAlreadyRunning) {
    startBackend();
  } else {
    console.log("[Electron] API already running, skipping backend start");
  }

  try {
    await waitForApi();
    console.log("[Electron] API is ready");
  } catch (err) {
    console.error("[Electron]", err.message);
  }

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    if (apiProcess) apiProcess.kill();
    app.quit();
  }
});

app.on("before-quit", () => {
  if (apiProcess) apiProcess.kill();
});

// ── IPC: expose API_URL to renderer ─────────────────────────────────────────
ipcMain.handle("get-api-url", () => API_URL);
