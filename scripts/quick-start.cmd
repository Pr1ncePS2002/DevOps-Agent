@echo off
REM ============================================================
REM AI DevOps Commander — Quick Start (Windows)
REM Usage: scripts\quick-start.cmd
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════╗
echo ║     AI DevOps Commander — Quick Start    ║
echo ╚══════════════════════════════════════════╝
echo.

REM Change to repo root (parent of scripts\)
cd /d "%~dp0.."

REM ── [1/4] Check prerequisites ─────────────────────────────
echo [1/4] Checking prerequisites...

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Install from https://docs.docker.com/get-docker/
    exit /b 1
)
echo [OK] Docker found

docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose not found. Update Docker Desktop.
        exit /b 1
    )
    set COMPOSE_CMD=docker-compose
) else (
    set COMPOSE_CMD=docker compose
)
echo [OK] Docker Compose found

REM ── [2/4] Set up environment ──────────────────────────────
echo.
echo [2/4] Setting up environment...

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [WARN] .env created from .env.example
    echo        Add your API keys to .env:
    echo          GEMINI_API_KEY=  (recommended - free at aistudio.google.com)
    echo          or OPENAI_API_KEY=
    echo.
) else (
    echo [OK] .env already exists
)

REM ── [3/4] Build and start ────────────────────────────────
echo.
echo [3/4] Building and starting services...
echo       (First build may take 3-5 minutes)
echo.

%COMPOSE_CMD% up --build -d
if errorlevel 1 (
    echo [ERROR] docker compose failed. Check the output above.
    exit /b 1
)

REM ── [4/4] Wait for health ─────────────────────────────────
echo.
echo [4/4] Waiting for backend to be ready...

set COUNT=0
:HEALTH_LOOP
set /a COUNT+=1
if %COUNT% gtr 30 (
    echo [ERROR] Backend did not start in time.
    echo         Check logs: %COMPOSE_CMD% logs backend
    exit /b 1
)
curl -sf http://localhost:3001/health >nul 2>&1
if errorlevel 1 (
    echo   Attempt %COUNT%/30...
    timeout /t 3 /nobreak >nul
    goto HEALTH_LOOP
)
echo [OK] Backend is healthy

REM ── Done ─────────────────────────────────────────────────
echo.
echo ╔══════════════════════════════════════════╗
echo ║         Stack is up and running!         ║
echo ╚══════════════════════════════════════════╝
echo.
echo   Dashboard:  http://localhost:3000
echo   API:        http://localhost:3001
echo   API Docs:   http://localhost:3001/docs
echo.
echo   To stop: %COMPOSE_CMD% down
echo   Logs:    %COMPOSE_CMD% logs -f
echo.

endlocal
