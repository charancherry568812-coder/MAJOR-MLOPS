#!/usr/bin/env bash
# =============================================================================
# FedBank MLOps — Local Platform Startup Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🏦 Starting FedBank MLOps Platform..."

# 1. Check Python Virtualenv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r backend/requirements.txt
else
    source .venv/bin/activate
fi

# 2. Generate Synthetic Datasets and Seed Database
echo "📊 Preparing synthetic banking datasets and database..."
PYTHONPATH=backend python3 -c "
from app.database.init_db import init_db
from scripts.generate_data import generate_all_datasets
import os

generate_all_datasets(os.path.abspath('dataset_storage'))
init_db()
"

# 3. Start Backend Server
echo "🚀 Launching FastAPI Backend on http://localhost:8000..."
export PYTHONPATH=backend:.
nohup python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid
echo "Backend running (PID: $BACKEND_PID, logs: backend.log)"

# 4. Start Frontend Server
echo "💻 Launching Frontend on http://localhost:5173..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
nohup npm run dev -- --host 0.0.0.0 --port 5173 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo $FRONTEND_PID > .frontend.pid
echo "Frontend running (PID: $FRONTEND_PID, logs: frontend.log)"

echo ""
echo "============================================================================="
echo "✅ FedBank MLOps Platform is LIVE and ready!"
echo "   • Frontend UI:       http://localhost:5173"
echo "   • REST API Docs:     http://localhost:8000/docs"
echo "   • Health Endpoint:   http://localhost:8000/health"
echo "   • Demo Super Admin:  admin@fedbank.com / Admin@123"
echo "============================================================================="
echo "To stop the platform, run: ./stop.sh"
