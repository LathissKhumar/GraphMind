#!/bin/bash
set -e

echo "=== GraphMind Demo ==="
echo "Cloning fastapi/fastapi..."

# Clone repo if needed
if [ ! -d "/tmp/fastapi-repo" ]; then
    git clone --depth 1 https://github.com/fastapi/fastapi.git /tmp/fastapi-repo 2>/dev/null || true
fi

# Start server in background
echo "Starting API server..."
cd /home/lathiss/Projects/GraphMind
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

sleep 3

# Ingest the repo
echo "Ingesting codebase..."
curl -s -X POST http://localhost:8000/api/ingest \
    -H "Content-Type: application/json" \
    -d '{"codebase_path": "/tmp/fastapi-repo", "repo_name": "fastapi"}' | head -100

echo ""
echo "Testing queries..."

# Test 1: GRAPH_ONLY
echo "1. List functions..."
curl -s -X POST http://localhost:8000/api/query \
    -H "Content-Type: application/json" \
    -d '{"query": "List all functions"}' | head -50

# Test 2: Callers
echo "2. Who calls..."
curl -s -X POST http://localhost:8000/api/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What functions call app?"}' | head -50

# Test 3: Metrics
echo "3. Metrics..."
curl -s http://localhost:8000/api/metrics

echo ""
echo "=== Demo Complete ==="

# Cleanup
kill $SERVER_PID 2>/dev/null || true