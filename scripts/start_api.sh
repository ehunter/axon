#!/bin/bash
# Start the Axon API server

set -e

cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run: python3 -m venv .venv && pip install -e ."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if database is running
if ! docker ps | grep -q axon-db; then
    echo "⚠️  Database not running. Starting..."
    docker start axon-db 2>/dev/null || docker run -d \
        --name axon-db \
        -e POSTGRES_USER=axon \
        -e POSTGRES_PASSWORD=axon \
        -e POSTGRES_DB=axon \
        -p 5433:5432 \
        pgvector/pgvector:pg16
    sleep 3
fi

echo "🧠 Starting Axon API..."
echo ""
echo "   API:  http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

uvicorn axon.api.main:app --host 0.0.0.0 --port 8000 --reload

