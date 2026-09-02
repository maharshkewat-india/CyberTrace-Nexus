@echo off
REM ============================================================================
REM CyberTrace Nexus - AI-Assisted Digital Incident Reconstruction Platform
REM Starts both FastAPI backend and Next.js frontend in separate windows
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "VENV_DIR=%PROJECT_ROOT%.venv"

echo.
echo ============================================================
echo   CyberTrace Nexus
echo   AI-Assisted Digital Incident Reconstruction Platform
echo ============================================================
echo.

REM ----- Step 1: Set up Python virtual environment -----
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [1/5] Creating Python virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/5] Virtual environment found.
)

REM ----- Step 2: Install backend dependencies -----
echo [2/5] Installing backend dependencies...
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
python -m pip install -r "%BACKEND_DIR%\requirements.txt" --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies.
    pause
    exit /b 1
)
call deactivate

REM ----- Step 3: Initialize database -----
echo [3/5] Initializing database...
call "%VENV_DIR%\Scripts\activate.bat"
python -m backend.app.database.database
if errorlevel 1 (
    echo [WARN] Database init returned non-zero. Continuing...
)
call deactivate

REM ----- Step 4: Check Node.js dependencies -----
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [4/5] Installing frontend dependencies...
    cd /d "%FRONTEND_DIR%"
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies.
        pause
        exit /b 1
    )
) else (
    echo [4/5] Frontend dependencies found.
)

REM ----- Step 5: Start backend and frontend -----
echo [5/5] Starting services...
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo.
echo   Default credentials: admin / Admin@123
echo.
echo   Press Ctrl+C in each window to stop services.
echo ============================================================
echo.

REM Start backend in a new window
start "CyberTrace - Backend (FastAPI)" cmd /k "cd /d ""%PROJECT_ROOT%"" && ""%VENV_DIR%\Scripts\python.exe"" -m backend.app.main"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
start "CyberTrace - Frontend (Next.js)" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev"

REM Wait and open browser
timeout /t 5 /nobreak >nul
start "" "http://localhost:3000"

echo [OK] Both services started. This window can be closed.
echo.
pause
