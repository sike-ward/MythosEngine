@echo off
echo Pulling latest MythosEngine updates from GitHub...
cd /d "%~dp0"
git checkout main
git pull origin main
git worktree prune
echo.
echo Done! Your local files are now up to date.
pause
