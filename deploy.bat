@echo off
chcp 65001 >nul
echo ============================================================
echo  🚀 LifeContext One-Click Deployment Script (Windows)
echo ============================================================
echo.

:: Check if services are already running
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [Warning] Python processes detected, services may already be running
    echo.
)

:: 1. Start backend service
echo [1/3] Starting backend service...
echo ============================================================
start "LifeContext Backend" cmd /k "cd backend && echo Activating conda environment... && conda activate lifecontext && echo Starting backend service... && python app.py"
timeout /t 3 >nul

:: 2. Start extension service
echo [2/3] Starting extension service...
echo ============================================================
start "LifeContext Extension" cmd /k "cd Extension && echo Installing dependencies... && if not exist node_modules (npm install && echo Dependencies installed successfully) else (echo Dependencies already installed) && echo Starting extension server... && node server.js"
timeout /t 3 >nul

:: 3. Start frontend service
echo [3/3] Starting frontend service...
echo ============================================================
start "LifeContext Frontend" cmd /k "cd frontend && echo Installing dependencies... && if not exist node_modules (npm install && echo Dependencies installed successfully) else (echo Dependencies already installed) && echo Starting frontend service... && npm run dev"
timeout /t 3 >nul

echo.
echo ============================================================
echo ✅ All services started successfully!
echo ============================================================
echo.
echo 📝 Service List:
echo    • Backend Service:   http://localhost:8000
echo    • Frontend UI:       http://localhost:3000
echo    • Extension Service: http://localhost:3001
echo.
echo 💡 Tips:
echo    1. For first run, ensure conda environment is created:
echo       conda env create -f backend/environment.yml
echo.
echo    2. Configure API Key in backend/config.py
echo.
echo    3. Browser extension installation steps:
echo       - Open browser extension management page
echo       - Enable developer mode
echo       - Load Extension/extension folder
echo.
echo    4. To stop all services: Close the corresponding command windows
echo.
echo ============================================================
echo Press any key to exit this window (services will continue running)...
pause >nul

