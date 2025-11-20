#!/bin/bash

echo "============================================================"
echo " 🛑 LifeContext Stop Services Script (Linux/macOS)"
echo "============================================================"
echo ""

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Stop service function
stop_service() {
    local service_name=$1
    local pid_file=$2
    local process_pattern=$3
    
    echo "[$service_name] Stopping..."
    
    # Try to read from PID file
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null
            sleep 1
            # If process is still running, force kill
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID 2>/dev/null
            fi
            echo -e "${GREEN}✅ $service_name stopped (PID: $PID)${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name not running${NC}"
        fi
        rm -f "$pid_file"
    else
        # Try to find and kill by process name
        pkill -f "$process_pattern" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ $service_name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name not running${NC}"
        fi
    fi
}

# Stop backend service
stop_service "Backend Service" "$PROJECT_ROOT/logs/backend.pid" "python.*app.py"

# Stop extension service
stop_service "Extension Service" "$PROJECT_ROOT/logs/extension.pid" "node.*server.js"

# Stop frontend service
stop_service "Frontend Service" "$PROJECT_ROOT/logs/frontend.pid" "vite"

echo ""
echo "============================================================"
echo -e "${GREEN}✅ All services stopped${NC}"
echo "============================================================"
echo ""

