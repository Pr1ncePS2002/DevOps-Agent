@echo off
setlocal
cd /d "%~dp0\.."

REM Runs the RQ worker (background executor).
REM Ensure Redis is running and you ran scripts\install.cmd first.

if not exist .venv\Scripts\python.exe (
	echo ERROR: Backend virtualenv not found.
	echo Run: scripts\install.cmd
	exit /b 1
)

call scripts\check-redis.cmd
if errorlevel 1 (
	echo.
	echo Tip: If you want Docker-based Redis, run: scripts\run-redis.cmd
	exit /b 1
)

.venv\Scripts\python.exe -m app.queue.worker
