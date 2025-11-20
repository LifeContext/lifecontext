#!/bin/bash

# Pre-commit hook for LifeContext
# Place this file in .git/hooks/pre-commit with execute permissions
# chmod +x .git/hooks/pre-commit

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}      LifeContext Pre-Commit Checks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check which files are staged
STAGED_FILES=$(git diff --cached --name-only)
STAGED_BACKEND=$(echo "$STAGED_FILES" | grep '^backend/' | wc -l)
STAGED_FRONTEND=$(echo "$STAGED_FILES" | grep '^frontend/' | wc -l)
STAGED_EXTENSION=$(echo "$STAGED_FILES" | grep '^Extension/' | wc -l)

# Backend checks
if [ $STAGED_BACKEND -gt 0 ]; then
    echo -e "${YELLOW}[1/3] Checking Backend files...${NC}"
    
    # Check Python syntax
    cd "$PROJECT_ROOT/backend"
    
    # Get staged Python files
    git diff --cached --name-only --diff-filter=d | grep '\.py$' | while read file; do
        if [ -f "$file" ]; then
            echo -n "  Checking $file... "
            if python -m py_compile "$file" 2>/dev/null; then
                echo -e "${GREEN}✓${NC}"
            else
                echo -e "${RED}✗ Syntax Error${NC}"
                exit 1
            fi
        fi
    done
    
    cd "$PROJECT_ROOT"
    echo ""
fi

# Frontend checks
if [ $STAGED_FRONTEND -gt 0 ]; then
    echo -e "${YELLOW}[2/3] Checking Frontend files...${NC}"
    
    cd "$PROJECT_ROOT/frontend"
    
    # Check TypeScript syntax if modified
    if git diff --cached --name-only | grep -E '\.(ts|tsx|vue)$' >/dev/null; then
        echo -n "  Running TypeScript check... "
        if npx tsc --noEmit 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠ TypeScript issues (continuing)${NC}"
        fi
    fi
    
    cd "$PROJECT_ROOT"
    echo ""
fi

# Extension checks
if [ $STAGED_EXTENSION -gt 0 ]; then
    echo -e "${YELLOW}[3/3] Checking Extension files...${NC}"
    
    cd "$PROJECT_ROOT/Extension"
    
    # Validate manifest.json if modified
    if git diff --cached --name-only | grep 'manifest.json' >/dev/null; then
        echo -n "  Validating manifest.json... "
        if node -e "JSON.parse(require('fs').readFileSync('extension/manifest.json', 'utf8'))" 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗ Invalid JSON${NC}"
            exit 1
        fi
    fi
    
    cd "$PROJECT_ROOT"
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Pre-commit checks passed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

