@echo off
chcp 65001 >nul
echo ============================================================
echo  🛑 LifeContext 停止服务脚本 (Windows)
echo ============================================================
echo.

echo 正在停止所有 LifeContext 服务...
echo.

:: 停止后端服务
echo [1/3] 停止后端服务...
for /f "tokens=2" %%i in ('tasklist /FI "WINDOWTITLE eq LifeContext Backend*" /NH 2^>NUL ^| find "cmd.exe"') do (
    taskkill /PID %%i /T /F >nul 2>&1
)
echo ✅ 后端服务已停止

:: 停止插件服务
echo [2/3] 停止插件服务...
for /f "tokens=2" %%i in ('tasklist /FI "WINDOWTITLE eq LifeContext Extension*" /NH 2^>NUL ^| find "cmd.exe"') do (
    taskkill /PID %%i /T /F >nul 2>&1
)
echo ✅ 插件服务已停止

:: 停止前端服务
echo [3/3] 停止前端服务...
for /f "tokens=2" %%i in ('tasklist /FI "WINDOWTITLE eq LifeContext Frontend*" /NH 2^>NUL ^| find "cmd.exe"') do (
    taskkill /PID %%i /T /F >nul 2>&1
)
echo ✅ 前端服务已停止

echo.
echo ============================================================
echo ✅ 所有服务已停止
echo ============================================================
echo.
pause

