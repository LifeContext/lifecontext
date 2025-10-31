#!/bin/bash

echo "============================================================"
echo " 🛑 LifeContext 停止服务脚本 (Linux/macOS)"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 停止服务函数
stop_service() {
    local service_name=$1
    local pid_file=$2
    local process_pattern=$3
    
    echo "[$service_name] 正在停止..."
    
    # 尝试从 PID 文件读取
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null
            sleep 1
            # 如果进程还在运行，强制终止
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID 2>/dev/null
            fi
            echo -e "${GREEN}✅ $service_name 已停止 (PID: $PID)${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name 未运行${NC}"
        fi
        rm -f "$pid_file"
    else
        # 尝试通过进程名查找并终止
        pkill -f "$process_pattern" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ $service_name 已停止${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name 未运行${NC}"
        fi
    fi
}

# 停止后端服务
stop_service "后端服务" "logs/backend.pid" "python.*app.py"

# 停止插件服务
stop_service "插件服务" "logs/extension.pid" "node.*server.js"

# 停止前端服务
stop_service "前端服务" "logs/frontend.pid" "vite"

echo ""
echo "============================================================"
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo "============================================================"
echo ""

