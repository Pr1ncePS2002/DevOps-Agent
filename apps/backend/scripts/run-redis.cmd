@echo off
setlocal
cd /d "%~dp0\.."

REM Starts Redis using Docker (requires Docker Desktop running).

where docker >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker CLI not found.
  echo Install Docker Desktop or use Memurai.
  exit /b 1
)

REM If Docker engine isn't running, docker commands will fail.
docker info >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker engine is not reachable.
  echo Start Docker Desktop and re-run this script.
  exit /b 1
)

REM Idempotent start/create
for /f "tokens=*" %%i in ('docker ps -a --filter "name=^redis$" --format "{{.ID}}"') do set REDIS_CONTAINER_ID=%%i

if not "%REDIS_CONTAINER_ID%"=="" (
  docker start redis >nul
  echo Redis container 'redis' started.
) else (
  docker run --name redis -p 6379:6379 -d redis:7 >nul
  echo Redis container 'redis' created and started.
)

echo Verifying Redis port...
call scripts\check-redis.cmd
if errorlevel 1 exit /b 1

echo Redis is reachable at %REDIS_URL%.
exit /b 0
