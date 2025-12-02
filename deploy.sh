#!/bin/bash

echo "============================================================"
echo " 🚀 LifeContext One-Click Deployment Script (Linux/macOS)"
echo "============================================================"
echo ""

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check dependencies
check_dependencies() {
    echo "🔍 Checking dependencies..."
    
    # Check conda
    if ! command -v conda &> /dev/null; then
        echo -e "${RED}❌ conda not found, please install Miniconda or Anaconda first${NC}"
        exit 1
    fi
    
    # Check node
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js not found, please install Node.js first${NC}"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm not found, please install npm first${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependency check passed${NC}"
    echo ""
}

# Check conda environment
check_conda_env() {
    echo "🔍 Checking conda environment..."
    
    if conda env list | grep -q "lifecontext"; then
        echo -e "${GREEN}✅ Found lifecontext environment${NC}"
    else
        echo -e "${YELLOW}⚠️  lifecontext environment not found, creating...${NC}"
        cd backend
        conda env create -f environment.yml
        cd ..
        echo -e "${GREEN}✅ Environment created${NC}"
    fi
    echo ""
}

# Create logs directory
mkdir -p logs

# Check dependencies
check_dependencies

# Check conda environment
check_conda_env

# Terminate previous processes
echo "🧹 Cleaning up old processes..."
pkill -f "python.*app.py" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# 1. Start backend service
echo "[1/2] Starting backend service..."
echo "============================================================"
cd backend
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate lifecontext
nohup python app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend service started (PID: $BACKEND_PID)${NC}"
cd ..
sleep 3

# 2. Start frontend service
echo "[2/2] Starting frontend service..."
echo "============================================================"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 First run, installing dependencies..."
    npm install
    # macOS permission handling
    if [[ "$OSTYPE" == "darwin"* ]]; then
        chmod +x node_modules/.bin/vite
    fi
fi
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend service started (PID: $FRONTEND_PID)${NC}"
cd ..
sleep 5

echo ""
echo "============================================================"
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo "============================================================"
echo ""
echo "📝 Service List:"
echo "   • Backend Service:   http://localhost:8000  (PID: $BACKEND_PID)"
echo "   • Frontend UI:       http://localhost:3000  (PID: $FRONTEND_PID)"
echo ""
echo "📊 Log Files:"
echo "   • Backend Log:   logs/backend.log"
echo "   • Frontend Log:  logs/frontend.log"
echo ""
echo "💡 Tips:"
echo "   1. Need to configure API Key in backend/config.py"
echo ""
echo "   2. Browser extension installation steps:"
echo "      - Open browser extension management page"
echo "      - Enable Developer Mode"
echo "      - Load Extension/extension folder"
echo ""
echo "   3. View real-time logs:"
echo "      tail -f logs/backend.log"
echo "      tail -f logs/frontend.log"
echo ""
echo "   4. Stop all services:"
echo "      ./stop.sh"
echo "      Or manually: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "============================================================"

# Save PID to file for easy stop
echo "$BACKEND_PID" > logs/backend.pid
echo "$FRONTEND_PID" > logs/frontend.pid

# Wait for user input
echo ""
echo "Press Ctrl+C to exit this script (services will continue running in background)"
echo "Or wait 10 seconds to exit automatically..."
sleep 10 || true

echo ""
echo -e "${GREEN}Script execution completed, services are running in background${NC}"

