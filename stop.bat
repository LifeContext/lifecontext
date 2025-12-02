@echo off
chcp 65001 >nul
echo ============================================================
echo  🛑 LifeContext Stop Services Script (Windows)
echo ============================================================
echo.

echo Stopping all LifeContext services...
echo.

:: Stop backend service
echo [1/2] Stopping backend service...
for /f "tokens=2" %%i in ('tasklist /FI "WINDOWTITLE eq LifeContext Backend*" /NH 2^>NUL ^| find "cmd.exe"') do (
    taskkill /PID %%i /T /F >nul 2>&1
)
echo ✅ Backend service stopped

:: Stop frontend service
echo [2/2] Stopping frontend service...
for /f "tokens=2" %%i in ('tasklist /FI "WINDOWTITLE eq LifeContext Frontend*" /NH 2^>NUL ^| find "cmd.exe"') do (
    taskkill /PID %%i /T /F >nul 2>&1
)
echo ✅ Frontend service stopped

echo.
echo ============================================================
echo ✅ All services stopped
echo ============================================================
echo.
pause

