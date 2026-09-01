#!/usr/bin/env bash
# =============================================================================
# FedBank MLOps — Local Platform Shutdown Script
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping FedBank MLOps Platform..."

if [ -f ".backend.pid" ]; then
    PID=$(cat .backend.pid)
    echo "Stopping Backend (PID: $PID)..."
    kill $PID 2>/dev/null || true
    rm -f .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    PID=$(cat .frontend.pid)
    echo "Stopping Frontend (PID: $PID)..."
    kill $PID 2>/dev/null || true
    rm -f .frontend.pid
fi

# Kill any leftover uvicorn or vite on ports 8000/5173
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

echo "✅ All FedBank MLOps processes have been stopped."
