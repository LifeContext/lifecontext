#!/bin/bash

echo "============================================================"
echo " 🚀 LifeContext 一键部署脚本 (Linux/macOS)"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查依赖
check_dependencies() {
    echo "🔍 检查依赖环境..."
    
    # 检查 conda
    if ! command -v conda &> /dev/null; then
        echo -e "${RED}❌ 未找到 conda，请先安装 Miniconda 或 Anaconda${NC}"
        exit 1
    fi
    
    # 检查 node
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ 未找到 Node.js，请先安装 Node.js${NC}"
        exit 1
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ 未找到 npm，请先安装 npm${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 依赖检查通过${NC}"
    echo ""
}

# 检查 conda 环境
check_conda_env() {
    echo "🔍 检查 conda 环境..."
    
    if conda env list | grep -q "lifecontext"; then
        echo -e "${GREEN}✅ 找到 lifecontext 环境${NC}"
    else
        echo -e "${YELLOW}⚠️  未找到 lifecontext 环境，正在创建...${NC}"
        cd backend
        conda env create -f environment.yml
        cd ..
        echo -e "${GREEN}✅ 环境创建完成${NC}"
    fi
    echo ""
}

# 创建日志目录
mkdir -p logs

# 检查依赖
check_dependencies

# 检查 conda 环境
check_conda_env

# 终止之前的进程
echo "🧹 清理旧进程..."
pkill -f "python.*app.py" 2>/dev/null
pkill -f "node.*server.js" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# 1. 启动后端服务
echo "[1/3] 启动后端服务..."
echo "============================================================"
cd backend
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate lifecontext
nohup python app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
cd ..
sleep 3

# 2. 启动浏览器插件服务
echo "[2/3] 启动浏览器插件服务..."
echo "============================================================"
cd Extension
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装依赖..."
    npm install
fi
nohup node server.js > ../logs/extension.log 2>&1 &
EXTENSION_PID=$!
echo -e "${GREEN}✅ 插件服务已启动 (PID: $EXTENSION_PID)${NC}"
cd ..
sleep 3

# 3. 启动前端服务
echo "[3/3] 启动前端服务..."
echo "============================================================"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装依赖..."
    npm install
    # macOS 权限处理
    if [[ "$OSTYPE" == "darwin"* ]]; then
        chmod +x node_modules/.bin/vite
    fi
fi
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
cd ..
sleep 5

echo ""
echo "============================================================"
echo -e "${GREEN}✅ 所有服务启动完成！${NC}"
echo "============================================================"
echo ""
echo "📝 服务列表："
echo "   • 后端服务:   http://localhost:8000  (PID: $BACKEND_PID)"
echo "   • 前端界面:   http://localhost:3000  (PID: $FRONTEND_PID)"
echo "   • 插件服务:   运行中              (PID: $EXTENSION_PID)"
echo ""
echo "📊 日志文件："
echo "   • 后端日志:   logs/backend.log"
echo "   • 插件日志:   logs/extension.log"
echo "   • 前端日志:   logs/frontend.log"
echo ""
echo "💡 提示："
echo "   1. 需要配置 backend/config.py 中的 API Key"
echo ""
echo "   2. 浏览器插件安装步骤："
echo "      - 打开浏览器扩展管理页面"
echo "      - 启用开发者模式"
echo "      - 加载 Extension/extension 文件夹"
echo ""
echo "   3. 查看实时日志："
echo "      tail -f logs/backend.log"
echo "      tail -f logs/extension.log"
echo "      tail -f logs/frontend.log"
echo ""
echo "   4. 停止所有服务："
echo "      ./stop.sh"
echo "      或手动执行: kill $BACKEND_PID $EXTENSION_PID $FRONTEND_PID"
echo ""
echo "============================================================"

# 保存 PID 到文件，方便后续停止
echo "$BACKEND_PID" > logs/backend.pid
echo "$EXTENSION_PID" > logs/extension.pid
echo "$FRONTEND_PID" > logs/frontend.pid

# 等待用户按键
echo ""
echo "按 Ctrl+C 退出此脚本（服务将继续在后台运行）"
echo "或等待 10 秒自动退出..."
sleep 10 || true

echo ""
echo -e "${GREEN}脚本执行完成，服务正在后台运行${NC}"

