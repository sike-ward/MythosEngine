@echo off
title MythosEngine
cd /d "%~dp0"

start python MythosEngine\main.py
timeout /t 2 /nobreak
cd frontend && npm start
