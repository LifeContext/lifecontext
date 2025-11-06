#!/bin/bash

echo "============================================================"
echo " 🚀 LifeContext Initialization Script (Linux/macOS)"
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
    
    local missing_deps=()
    
    # Check conda
    if ! command -v conda &> /dev/null; then
        missing_deps+=("conda (Miniconda/Anaconda)")
    fi
    
    # Check node
    if ! command -v node &> /dev/null; then
        missing_deps+=("Node.js")
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        missing_deps+=("npm")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing dependencies:${NC}"
        for dep in "${missing_deps[@]}"; do
            echo -e "   • $dep"
        done
        echo ""
        echo "Please install the missing dependencies first."
        echo "• Miniconda: https://docs.conda.io/en/latest/miniconda.html"
        echo "• Node.js: https://nodejs.org/"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All dependencies found${NC}"
    echo ""
}

# Check and create conda environment
setup_conda_env() {
    echo "🔍 Checking conda environment..."
    
    if conda env list | grep -q "lifecontext"; then
        echo -e "${GREEN}✅ Found lifecontext environment${NC}"
    else
        echo -e "${YELLOW}⚠️  lifecontext environment not found${NC}"
        echo "Creating conda environment from environment.yml..."
        
        if [ ! -f "backend/environment.yml" ]; then
            echo -e "${RED}❌ backend/environment.yml not found${NC}"
            exit 1
        fi
        
        cd backend
        conda env create -f environment.yml
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Environment created successfully${NC}"
        else
            echo -e "${RED}❌ Failed to create conda environment${NC}"
            exit 1
        fi
        cd ..
    fi
    echo ""
}

# Interactive API Key configuration
configure_api_keys() {
    echo "🔧 Configuring API Keys..."
    echo "============================================================"
    echo ""
    
    local env_file="backend/.env"
    
    # Check if .env already exists
    if [ -f "$env_file" ]; then
        echo -e "${YELLOW}⚠️  .env file already exists${NC}"
        read -p "Do you want to overwrite it? (y/N): " overwrite
        if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}ℹ️  Skipping API Key configuration${NC}"
            echo ""
            return
        fi
    fi
    
    echo "Please enter your API configuration:"
    echo "(Press Enter to use default values or skip optional fields)"
    echo ""
    
    # LLM API Configuration
    echo -e "${BLUE}📝 LLM API Configuration:${NC}"
    read -p "LLM_API_KEY: " llm_api_key
    read -p "LLM_BASE_URL [default: https://api.openai.com/v1]: " llm_base_url
    read -p "LLM_MODEL [default: gpt-4o-mini]: " llm_model
    
    # Embedding API Configuration
    echo ""
    echo -e "${BLUE}📝 Embedding API Configuration:${NC}"
    read -p "EMBEDDING_API_KEY: " embedding_api_key
    read -p "EMBEDDING_BASE_URL [default: https://api.openai.com/v1]: " embedding_base_url
    read -p "EMBEDDING_MODEL [default: text-embedding-3-small]: " embedding_model
    
    # Set defaults
    llm_base_url=${llm_base_url:-https://api.openai.com/v1}
    llm_model=${llm_model:-gpt-4o-mini}
    embedding_base_url=${embedding_base_url:-https://api.openai.com/v1}
    embedding_model=${embedding_model:-text-embedding-3-small}
    
    # Validate required fields
    if [ -z "$llm_api_key" ]; then
        echo -e "${YELLOW}⚠️  LLM_API_KEY is empty, but continuing...${NC}"
    fi
    
    if [ -z "$embedding_api_key" ]; then
        echo -e "${YELLOW}⚠️  EMBEDDING_API_KEY is empty, but continuing...${NC}"
    fi
    
    # Generate .env file
    cat > "$env_file" << EOF
# LLM API Configuration
LLM_API_KEY=${llm_api_key}
LLM_BASE_URL=${llm_base_url}
LLM_MODEL=${llm_model}

# Embedding API Configuration
EMBEDDING_API_KEY=${embedding_api_key}
EMBEDDING_BASE_URL=${embedding_base_url}
EMBEDDING_MODEL=${embedding_model}
EOF
    
    echo ""
    echo -e "${GREEN}✅ Configuration saved to $env_file${NC}"
    echo ""
}

# Install dependencies (required)
install_dependencies() {
    echo "📦 Installing dependencies..."
    echo "============================================================"
    echo ""
    
    # Frontend dependencies
    if [ ! -d "frontend/node_modules" ]; then
        echo "[1/2] Installing frontend dependencies..."
        cd frontend
        npm install
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
            exit 1
        fi
        if [[ "$OSTYPE" == "darwin"* ]]; then
            chmod +x node_modules/.bin/vite 2>/dev/null || true
        fi
        cd ..
        echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
    else
        echo -e "${BLUE}ℹ️  Frontend dependencies already installed${NC}"
    fi
    
    # Extension dependencies
    if [ ! -d "Extension/node_modules" ]; then
        echo "[2/2] Installing extension dependencies..."
        cd Extension
        npm install
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to install extension dependencies${NC}"
            exit 1
        fi
        cd ..
        echo -e "${GREEN}✅ Extension dependencies installed${NC}"
    else
        echo -e "${BLUE}ℹ️  Extension dependencies already installed${NC}"
    fi
    
    echo ""
}

# Main execution
main() {
    # Check dependencies
    check_dependencies
    
    # Setup conda environment
    setup_conda_env
    
    # Configure API keys
    configure_api_keys
    
    # Install dependencies (required)
    install_dependencies
    
    echo "============================================================"
    echo -e "${GREEN}✅ Initialization completed!${NC}"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Start services: ./deploy.sh"
    echo "  2. Install browser extension:"
    echo "     - Open browser extension management page"
    echo "     - Enable Developer Mode"
    echo "     - Load Extension/extension folder"
    echo ""
}

# Run main function
main

