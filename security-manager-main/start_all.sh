#!/bin/bash
set -e

echo "========================================"
echo "Starting Security Management Stack"
echo "========================================"

# Get the absolute path of the script directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Start Backend
echo ""
echo ">>> [1/2] Starting Backend Services..."
cd "$PROJECT_ROOT/backend"
if [ -f "start_manual_stack.sh" ]; then
    bash start_manual_stack.sh
else
    echo "Error: start_manual_stack.sh not found in backend directory."
    exit 1
fi

# 2. Start Frontend
echo ""
echo ">>> [2/2] Starting Frontend Service..."
cd "$PROJECT_ROOT/frontend"
echo "Stopping any existing frontend containers..."
docker-compose down || true
echo "Building and starting frontend..."
docker-compose up -d --build

# 3. Summary
echo ""
echo "========================================"
echo "Stack Startup Complete!"
echo "========================================"
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:5173"
echo "========================================"
