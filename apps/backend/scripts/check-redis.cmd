@echo off
setlocal
cd /d "%~dp0\.."

REM Checks whether Redis is reachable based on REDIS_URL.
REM Exits 0 if reachable, 1 otherwise.

REM Prefer using the backend venv + settings loader so this checks the same
REM REDIS_URL the app will actually use (loaded from ../../.env).
if exist .venv\Scripts\python.exe goto :CHECK_WITH_VENV
goto :FALLBACK_TCP

:CHECK_WITH_VENV
.venv\Scripts\python.exe -c "from app.common.settings import settings; from redis import Redis; r=Redis.from_url(settings.redis_url, decode_responses=False); r.ping()" >nul 2>nul
if errorlevel 1 goto :VENV_FAIL
exit /b 0

:VENV_FAIL
echo ERROR: Cannot connect to Redis using app setting REDIS_URL.
echo.
.venv\Scripts\python.exe -c "from app.common.settings import settings; print(settings.redis_url)" 2>nul
echo.
echo Fix options:
echo   1^) If Redis is in WSL, set REDIS_URL to the WSL IP (Option A).
echo   2^) If Redis is local Windows, ensure it is listening on 6379.
echo.
exit /b 1

:FALLBACK_TCP
REM Fallback: no venv found, do a raw TCP connect using REDIS_URL env var.
if "%REDIS_URL%"=="" set "REDIS_URL=redis://localhost:6379"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$u=[Uri]$env:REDIS_URL; $redisHost=$u.Host; $redisPort=$u.Port; if($redisPort -le 0){$redisPort=6379}; try { $c = New-Object System.Net.Sockets.TcpClient; $c.Connect($redisHost,$redisPort); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Cannot connect to Redis at %REDIS_URL%.
  echo.
  echo Fix options:
  echo   1^) Start Redis with Docker Desktop:
  echo      - Start Docker Desktop
  echo      - Run: docker run --name redis -p 6379:6379 -d redis:7
  echo   2^) Or install Memurai on Windows and keep REDIS_URL as-is.
  echo.
  exit /b 1
)

exit /b 0
