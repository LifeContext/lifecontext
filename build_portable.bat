@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════════════════════════════╗
echo ║         LifeContext 便携包构建工具 (Windows)                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 找不到 Python
    echo    请先安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

:: 检查 Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 找不到 Node.js
    echo    请先安装 Node.js 18 或更高版本
    pause
    exit /b 1
)

:: 检查 PyInstaller
python -c "import PyInstaller" >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  警告: 未安装 PyInstaller
    echo    正在安装 PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ❌ PyInstaller 安装失败
        pause
        exit /b 1
    )
)

echo.
echo ✅ 环境检查通过
echo.
echo 开始构建便携包...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:: 运行构建脚本
python build_portable.py

if %errorlevel% equ 0 (
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo ✅ 构建完成！
    echo.
    echo 📦 输出目录: LifeContext-Portable\
    echo 📦 ZIP 文件: LifeContext-Portable-win32.zip
    echo.
) else (
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo ❌ 构建失败！
    echo 请查看上方的错误信息
    echo.
)

pause

