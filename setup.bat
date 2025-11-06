@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  🚀 LifeContext Initialization Script (Windows)
echo ============================================================
echo.

REM Check dependencies
echo 🔍 Checking dependencies...
echo.

set MISSING_DEPS=0

REM Check conda
where conda >nul 2>&1
if errorlevel 1 (
    echo ❌ conda not found
    echo    Please install Miniconda or Anaconda first
    echo    Download: https://docs.conda.io/en/latest/miniconda.html
    set MISSING_DEPS=1
) else (
    echo ✅ conda found
)

REM Check node
where node >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found
    echo    Please install Node.js first
    echo    Download: https://nodejs.org/
    set MISSING_DEPS=1
) else (
    echo ✅ Node.js found
)

REM Check npm
where npm >nul 2>&1
if errorlevel 1 (
    echo ❌ npm not found
    echo    Please install npm (comes with Node.js)
    set MISSING_DEPS=1
) else (
    echo ✅ npm found
)

echo.

if %MISSING_DEPS%==1 (
    echo Please install the missing dependencies first.
    pause
    exit /b 1
)

echo ✅ All dependencies found
echo.

REM Check conda environment
echo 🔍 Checking conda environment...
echo.

conda env list | findstr /C:"lifecontext" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  lifecontext environment not found
    echo Creating conda environment from environment.yml...
    echo.
    
    if not exist "backend\environment.yml" (
        echo ❌ backend\environment.yml not found
        pause
        exit /b 1
    )
    
    cd backend
    call conda env create -f environment.yml
    if errorlevel 1 (
        echo ❌ Failed to create conda environment
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo ✅ Environment created successfully
) else (
    echo ✅ Found lifecontext environment
)

echo.

REM Configure API Keys
echo 🔧 Configuring API Keys...
echo ============================================================
echo.

set ENV_FILE=backend\.env

REM Check if .env already exists
if exist "%ENV_FILE%" (
    echo ⚠️  .env file already exists
    set /p OVERWRITE="Do you want to overwrite it? (y/N): "
    if /i not "!OVERWRITE!"=="y" (
        echo ℹ️  Skipping API Key configuration
        echo.
        goto :install_deps
    )
)

echo Please enter your API configuration:
echo Press Enter to use default values or skip optional fields
echo.

REM LLM API Configuration
echo 📝 LLM API Configuration:
set /p LLM_API_KEY="LLM_API_KEY: "
set /p LLM_BASE_URL="LLM_BASE_URL [default: https://api.openai.com/v1]: "
set /p LLM_MODEL="LLM_MODEL [default: gpt-4o-mini]: "

REM Set defaults
if "!LLM_BASE_URL!"=="" set LLM_BASE_URL=https://api.openai.com/v1
if "!LLM_MODEL!"=="" set LLM_MODEL=gpt-4o-mini

REM Embedding API Configuration
echo.
echo 📝 Embedding API Configuration:
set /p EMBEDDING_API_KEY="EMBEDDING_API_KEY: "
set /p EMBEDDING_BASE_URL="EMBEDDING_BASE_URL [default: https://api.openai.com/v1]: "
set /p EMBEDDING_MODEL="EMBEDDING_MODEL [default: text-embedding-3-small]: "

REM Set defaults
if "!EMBEDDING_BASE_URL!"=="" set EMBEDDING_BASE_URL=https://api.openai.com/v1
if "!EMBEDDING_MODEL!"=="" set EMBEDDING_MODEL=text-embedding-3-small

REM Validate required fields
if "!LLM_API_KEY!"=="" (
    echo ⚠️  LLM_API_KEY is empty, but continuing...
)
if "!EMBEDDING_API_KEY!"=="" (
    echo ⚠️  EMBEDDING_API_KEY is empty, but continuing...
)

REM Generate .env file
(
    echo # LLM API Configuration
    echo LLM_API_KEY=!LLM_API_KEY!
    echo LLM_BASE_URL=!LLM_BASE_URL!
    echo LLM_MODEL=!LLM_MODEL!
    echo.
    echo # Embedding API Configuration
    echo EMBEDDING_API_KEY=!EMBEDDING_API_KEY!
    echo EMBEDDING_BASE_URL=!EMBEDDING_BASE_URL!
    echo EMBEDDING_MODEL=!EMBEDDING_MODEL!
) > "%ENV_FILE%"

echo.
echo ✅ Configuration saved to %ENV_FILE%
echo.

:install_deps
REM Install dependencies (required)
echo.
echo 📦 Installing dependencies...
echo ============================================================
echo.

REM Frontend dependencies
if not exist "frontend\node_modules" (
    echo [1/2] Installing frontend dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo ❌ Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo ✅ Frontend dependencies installed
) else (
    echo ℹ️  Frontend dependencies already installed
)

REM Extension dependencies
if not exist "Extension\node_modules" (
    echo [2/2] Installing extension dependencies...
    cd Extension
    call npm install
    if errorlevel 1 (
        echo ❌ Failed to install extension dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo ✅ Extension dependencies installed
) else (
    echo ℹ️  Extension dependencies already installed
)

echo.

:end
echo ============================================================
echo ✅ Initialization completed!
echo ============================================================
echo.
echo Next steps:
echo   1. Start services: deploy.bat
echo   2. Install browser extension:
echo      - Open browser extension management page
echo      - Enable Developer Mode
echo      - Load Extension\extension folder
echo.

pause

