@echo off
chcp 65001 >nul
echo ============================================================
echo  🚀 LifeContext 一键部署脚本 (Windows)
echo ============================================================
echo.

:: 检查是否已经启动
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [警告] 检测到 Python 进程已在运行，可能已有服务启动
    echo.
)

:: 1. 启动后端服务
echo [1/3] 启动后端服务...
echo ============================================================
start "LifeContext Backend" cmd /k "cd backend && echo 正在激活 conda 环境... && conda activate lifecontext && echo 启动后端服务... && python app.py"
timeout /t 3 >nul

:: 2. 启动浏览器插件服务
echo [2/3] 启动浏览器插件服务...
echo ============================================================
start "LifeContext Extension" cmd /k "cd Extension && echo 安装依赖... && if not exist node_modules (npm install) && echo 启动插件服务器... && node server.js"
timeout /t 3 >nul

:: 3. 启动前端服务
echo [3/3] 启动前端服务...
echo ============================================================
start "LifeContext Frontend" cmd /k "cd frontend && echo 安装依赖... && if not exist node_modules (npm install) && echo 启动前端服务... && npm run dev"
timeout /t 3 >nul

echo.
echo ============================================================
echo ✅ 所有服务启动完成！
echo ============================================================
echo.
echo 📝 服务列表：
echo    • 后端服务:   http://localhost:8000
echo    • 前端界面:   http://localhost:3000
echo    • 插件服务:   运行中
echo.
echo 💡 提示：
echo    1. 首次运行需要确保已创建 conda 环境：
echo       conda env create -f backend/environment.yml
echo.
echo    2. 需要配置 backend/config.py 中的 API Key
echo.
echo    3. 浏览器插件安装步骤：
echo       - 打开浏览器扩展管理页面
echo       - 启用开发者模式
echo       - 加载 Extension/extension 文件夹
echo.
echo    4. 关闭所有服务：关闭对应的命令行窗口即可
echo.
echo ============================================================
echo 按任意键退出此窗口（服务将继续运行）...
pause >nul

