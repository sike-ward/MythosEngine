# How to Build MythosEngine for Testers

Every time you want to send a new build to testers, follow these steps.
The result is one `.exe` file they double-click to install — no Python or Node required on their end.

Total time: about 5–10 minutes once everything is set up.

---

## Before you start

Make sure you have pulled the latest code from GitHub:

```
update.bat
```

Make sure your `.venv` is set up and your `.env` file has the right values.
If you have not done the first-time setup, see the README.

---

## Step 1 — Freeze the Python server

Open a terminal in the MythosEngine folder (or double-click `Dev_Console.bat`).

Run this command:

```
scripts\build-backend.bat
```

This will take **2–5 minutes**. You will see a lot of output scroll by — that is normal.

When it is done you should see:

```
[build-backend] Done.  Frozen backend at: dist\server\server.exe
```

If it says `ERROR` instead, see the Troubleshooting section at the bottom.

---

## Step 2 — Build the Windows installer

In the same terminal, run these two commands one at a time:

```
cd frontend
npm run build:win
```

This will take **1–3 minutes**.

When it is done you will see something like:

```
  • building        target=NSIS name=MythosEngine file=MythosEngine Setup 1.0.0.exe
  • done
```

---

## Step 3 — Find your installer file

Your installer is at:

```
frontend\dist-electron\MythosEngine Setup 1.0.0.exe
```

(The version number may differ.)

That is the file you send to testers.

---

## Step 4 — Test it yourself first

Before sending to anyone:

1. Run `MythosEngine Setup 1.0.0.exe` on your own machine
2. Click through the install wizard
3. Launch MythosEngine from the Start Menu
4. Make sure the startup splash screen appears and the app loads

If the app opens and you can log in, it is good to ship.

---

## Step 5 — Send to testers

Send testers:
- The `.exe` file
- The `TESTER_GUIDE.md` file (in the project root)

Testers need to create their own `.env` file before first launch. The TESTER_GUIDE walks them through it.

---

## Troubleshooting

**Step 1 fails with "ModuleNotFoundError" or similar**

Your venv may be missing a package. Run:
```
.venv\Scripts\activate
pip install -r requirements.txt
```
Then try Step 1 again.

**Step 1 fails with "PyInstaller not found"**

```
.venv\Scripts\activate
pip install pyinstaller
```

**Step 2 fails with "cannot find dist\server"**

Step 1 did not finish successfully. Go back and fix Step 1 first.

**Step 2 fails with npm errors**

```
cd frontend
npm install
npm run build:win
```

**The installed app opens but shows a server error**

```
set MYTHOS_DATA_DIR=%APPDATA%\MythosEngine
dist\server\server.exe
```

**The installed app works on your machine but crashes for testers**

Check if their machine is Windows 10 or later (64-bit).
Ask them to send you the log file from: `%APPDATA%\MythosEngine\logs\app.log`

---

## Quick reference — the two commands

From the project root:

```
scripts\build-backend.bat
cd frontend && npm run build:win
```

Output file: `frontend\dist-electron\MythosEngine Setup x.x.x.exe`
