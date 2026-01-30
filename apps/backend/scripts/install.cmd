@echo off
setlocal
cd /d %~dp0\..

REM Creates a virtual environment and installs backend dependencies.
REM Requires Python 3.11+ installed and available on PATH.

set "PYTHON_EXE="
set "PYTHON_ARGS="

REM Allow caller override: set PYTHON_EXE=C:\Path\to\python.exe
REM Example:
REM   set PYTHON_EXE=C:\Users\me\AppData\Local\Programs\Python\Python312\python.exe
REM   scripts\install.cmd
if not "%PYTHON_EXE%"=="" goto python_selected

REM Prefer python if available
where python >nul 2>nul
if %errorlevel%==0 set "PYTHON_EXE=python"

REM Fallback to py launcher
if "%PYTHON_EXE%"=="" (
  where py >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3"
  )
)

REM Fallback to python3
if "%PYTHON_EXE%"=="" (
  where python3 >nul 2>nul
  if %errorlevel%==0 set "PYTHON_EXE=python3"
)

if "%PYTHON_EXE%"=="" (
  echo ERROR: Python not found on PATH.
  echo - Install Python 3.11+ from https://www.python.org/downloads/
  echo - During install, enable: "Add python.exe to PATH"
  echo - Then close and re-open your terminal.
  exit /b 1
)

:python_selected

echo Using Python launcher: %PYTHON_EXE% %PYTHON_ARGS%
%PYTHON_EXE% %PYTHON_ARGS% -V

if not exist .venv (
  %PYTHON_EXE% %PYTHON_ARGS% -m venv .venv
  if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    exit /b 1
  )
)

.venv\Scripts\python.exe -m pip install --upgrade pip
if %errorlevel% neq 0 (
  echo ERROR: pip upgrade failed.
  exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo ERROR: dependency install failed.
  exit /b 1
)

echo.
echo Backend dependencies installed.
