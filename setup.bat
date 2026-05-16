@echo off
REM ============================================================
REM ScholARA — Auto Setup Script (Windows)
REM ============================================================

echo.
echo  ======================================
echo    ScholARA - AI Research Assistant
echo    Setup Script for Windows
echo  ======================================
echo.

REM Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version') do echo ^✓ Python %%v found

REM Check Node
echo [2/6] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Install from https://nodejs.org v18+
    pause
    exit /b 1
)
for /f %%v in ('node --version') do echo ^✓ Node.js %%v found

REM Create .env
echo [3/6] Setting up environment...
if not exist ".env" (
    copy .env.example .env
    echo ^✓ .env created — edit it to set your SECRET_KEY and model
) else (
    echo ^✓ .env already exists
)

REM Python venv
echo [4/6] Installing Python dependencies...
if not exist "venv" (
    python -m venv venv
    echo ^✓ Virtual environment created
)
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo ^✓ Python packages installed

REM Node deps
echo [5/6] Installing frontend dependencies...
cd frontend
call npm install --silent
cd ..
echo ^✓ Node packages installed

REM Directories
echo [6/6] Creating directories...
if not exist "uploads" mkdir uploads
if not exist "vector_db" mkdir vector_db
if not exist "logs" mkdir logs
echo ^✓ Directories ready

echo.
echo ======================================
echo  LLM Setup (Required)
echo ======================================
echo.
echo  Install Ollama from: https://ollama.ai
echo  Then run in a new terminal:
echo    ollama pull llama3.2
echo.

echo ======================================
echo   Setup Complete!
echo ======================================
echo.
echo  Start ScholARA:
echo.
echo  Terminal 1 — Ollama:
echo    ollama serve
echo.
echo  Terminal 2 — Backend:
echo    venv\Scripts\activate
echo    python -m backend.main
echo    API docs: http://localhost:8000/docs
echo.
echo  Terminal 3 — Frontend:
echo    cd frontend ^&^& npm run dev
echo    App: http://localhost:5173
echo.
pause
