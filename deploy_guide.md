# 🚀 LifeContext One-Click Deployment Guide

This document explains how to quickly start all LifeContext services using the one-click deployment script.

## 📋 Prerequisites

### Required Environment

1. **Python Environment**
   - Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/)
   - Ensure the `conda` command is available

2. **Node.js Environment**
   - Install [Node.js](https://nodejs.org/) (recommended v18 or higher)
   - Ensure `node` and `npm` commands are available

3. **Configure API Keys**
   - Edit the `backend/config.py` file
   - Configure your LLM API Key and Embedding API Key

### First-Time Setup

**Only needed for first run** - Create conda environment:

```bash
cd backend
conda env create -f environment.yml
cd ..
```

## 🎯 Quick Start

### Windows

#### Start All Services

In conda environment:

```cmd
deploy.bat
```

#### Stop All Services

In conda environment:

```cmd
stop.bat
```

### Linux / macOS

#### First Time: Add Execution Permissions

```bash
chmod +x deploy.sh stop.sh
```

#### Start All Services

```bash
./deploy.sh
```

#### Stop All Services

```bash
./stop.sh
```

## 📊 Service Overview

The script automatically starts the following three services:

| Service | Port | Description |
|---------|------|-------------|
| Backend Service | 8000 | Flask API service |
| Frontend Interface | 3000 | Vue.js frontend interface |
| Extension Service | - | Browser extension backend support |

## 🔍 Service Verification

### Check if Services Started Successfully

Visit the following addresses to verify:

- **Backend API**: http://localhost:8000
- **Frontend Interface**: http://localhost:3000

### View Logs (Linux/macOS)

```bash
# View backend logs
tail -f logs/backend.log

# View extension logs
tail -f logs/extension.log

# View frontend logs
tail -f logs/frontend.log
```

## 🧩 Browser Extension Installation

After starting the services, you also need to manually install the browser extension:

1. Open your browser (recommended: Chrome or Edge)
2. Go to the extension management page
   - Chrome: `chrome://extensions/`
   - Edge: `edge://extensions/`
3. Enable **Developer Mode** in the top-right corner
4. Click **Load unpacked extension**
5. Select the `Extension/extension` folder in the project directory
6. Once the extension is loaded, you can start using it

## ⚙️ Configuration

### Backend Configuration

Edit the `backend/config.py` file:

```python
# LLM API Configuration
LLM_API_KEY = "your-api-key-here"
LLM_BASE_URL = "https://api.openai.com/v1"
LLM_MODEL = "gpt-4o-mini"

# Embedding API Configuration
EMBEDDING_API_KEY = "your-embedding-key-here"
EMBEDDING_BASE_URL = "https://api.openai.com/v1"
EMBEDDING_MODEL = "text-embedding-3-small"

# Scheduled Task Configuration
ENABLE_SCHEDULER_ACTIVITY = True   # Generate activity records every 15 minutes
ENABLE_SCHEDULER_TODO = False      # Generate todo tasks every 30 minutes
ENABLE_SCHEDULER_TIP = True        # Generate tips on the hour
ENABLE_SCHEDULER_REPORT = True     # Generate daily report at 8 AM
```

### Event Push Configuration

Control various event pushes in `backend/config.py`:

```python
ENABLE_EVENT_TIP = True           # Tips generation event push
ENABLE_EVENT_TODO = False         # Todo generation event push
ENABLE_EVENT_ACTIVITY = False     # Activity generation event push
ENABLE_EVENT_REPORT = True        # Report generation event push
```

## 🐛 Common Issues

### 1. Conda Environment Not Found

**Error**: `Environment 'lifecontext' does not exist`

**Solution**: Manually create the environment

```bash
cd backend
conda env create -f environment.yml
conda activate lifecontext
```

### 2. Port Already in Use

**Error**: `Address already in use`

**Solution**: 
- Run the stop script to close previous services
- Or manually kill the process occupying the port

```bash
# Linux/macOS
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### 3. npm Dependency Installation Failed

**Solution**: Clear cache and reinstall

```bash
cd frontend  # or Extension
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### 4. Python Package Installation Failed

**Solution**: Install manually using pip

```bash
conda activate lifecontext
cd backend
pip install -r requirements.txt
```

### 5. macOS Vite Permission Issue

**Error**: `Permission denied: vite`

**Solution**: Add execution permission

```bash
cd frontend
chmod +x node_modules/.bin/vite
```

## 📝 Manual Startup

If the one-click deployment script encounters issues, you can manually start each service:

### Start Backend

```bash
cd backend
conda activate lifecontext
python app.py
```

### Start Extension Service

```bash
cd Extension
npm install  # First time only
node server.js
```

### Start Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

## 🔄 Restart After Code Update

When code is updated, use the following steps to restart services:

```bash
# 1. Stop all services
./stop.sh        # Linux/macOS
stop.bat         # Windows

# 2. Update code
git pull

# 3. Restart
./deploy.sh      # Linux/macOS
deploy.bat       # Windows
```

## 💡 Development Tips

- **Modify Backend Code**: Backend uses Flask, code changes will auto-reload (if DEBUG mode is enabled)
- **Modify Frontend Code**: Frontend uses Vite, code changes will hot-reload automatically
- **Modify Extension Code**: Extension needs to be reloaded to see updates

## 📚 More Information

For detailed usage instructions, please refer to:
- [中文文档](deploy_guide_zh.md)
- [English Documentation](readme.md)

