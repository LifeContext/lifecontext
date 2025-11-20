#!/bin/bash

# Install git hooks for LifeContext
# This script sets up pre-commit hooks to run checks before each commit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "=========================================="
echo "     Installing Git Hooks"
echo "=========================================="
echo ""

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "   Please run this script from the project root"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Copy pre-commit hook
if [ -f "$SCRIPT_DIR/pre-commit-hook.sh" ]; then
    cp "$SCRIPT_DIR/pre-commit-hook.sh" "$GIT_HOOKS_DIR/pre-commit"
    chmod +x "$GIT_HOOKS_DIR/pre-commit"
    echo "✓ Pre-commit hook installed"
else
    echo "✗ pre-commit-hook.sh not found"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Git hooks installed successfully!"
echo "=========================================="
echo ""
echo "Installed hooks:"
echo "  • pre-commit: Runs checks before each commit"
echo ""
echo "To uninstall hooks, run:"
echo "  rm -f $GIT_HOOKS_DIR/pre-commit"
echo ""

