@echo off
chcp 65001 >nul
echo ============================================================
echo  🛑 LifeContext Stop Services Script (Windows)
echo ============================================================
echo.

echo Stopping all LifeContext services...
echo.

REM Stop backend service
echo [1/3] Stopping backend service...
for /f "tokens=2" %%i in ('tasklist /FI "WINDOWTITLE eq LifeContext Backend*" /NH 2^>NUL ^| find "cmd.exe"') do (
    taskkill /PID %%i /T /F >nul 2>&1
)
echo ✅ Backend service stopped

REM Stop extension service
echo [2/3] Stopping extension service...
for /f "tokens=2" %%i in ('tasklist /FI "WINDOWTITLE eq LifeContext Extension*" /NH 2^>NUL ^| find "cmd.exe"') do (
    taskkill /PID %%i /T /F >nul 2>&1
)
echo ✅ Extension service stopped

REM Stop frontend service
echo [3/3] Stopping frontend service...
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

