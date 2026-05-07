#!/bin/bash

cleanup() {
    echo -e "\n[!] Shutting down CodeGraphX demo..."
    if [ ! -z "$API_PID" ]; then kill $API_PID 2>/dev/null; fi
    if [ ! -z "$DASH_PID" ]; then kill $DASH_PID 2>/dev/null; fi
    exit 0
}
trap cleanup SIGINT SIGTERM

REPO="https://github.com/fastapi/fastapi"
for i in "$@"; do
    case $i in
        --reset)
        echo "Resetting data..."
        rm -rf .codegraphx dashboard/node_modules
        exit 0
        ;;
        --repo=*)
        REPO="${i#*=}"
        shift
        ;;
    esac
done

if [[ "$1" == "--repo" ]]; then
    REPO="$2"
fi

echo "--- CodeGraphX Demo ---"

if [ ! -f .env ]; then
    cp .env.example .env
    echo "[x] Created .env from .env.example"
fi

echo "[x] Ensuring dependencies..."
pip install requests tabulate > /dev/null 2>&1

echo "[x] Checking TigerGraph..."
python -c "from src.graph.tigergraph_client import TigerGraphClient; exit(0 if TigerGraphClient().test_connection() else 1)"
if [ $? -eq 0 ]; then
    echo "    -> TigerGraph Cloud connected."
else
    echo "    -> TigerGraph unavailable. Forcing SQLite fallback with WAL mode."
    export TIGERGRAPH_HOST=""
fi

echo "[x] Starting FastAPI server..."
uvicorn src.api.main:app --port 8000 > .uvicorn.log 2>&1 &
API_PID=$!

echo "[x] Waiting for API to become healthy..."
HEALTHY=0
for i in {1..15}; do
    curl -s http://localhost:8000/api/health | grep '"status":"healthy"' > /dev/null
    if [ $? -eq 0 ]; then
        HEALTHY=1
        break
    fi
    sleep 2
done

if [ $HEALTHY -eq 0 ]; then
    echo "API failed to start. See .uvicorn.log"
    cat .uvicorn.log
    cleanup
fi
echo "    -> API is healthy."

echo "[x] Starting Dashboard..."
cd dashboard
npm install > /dev/null 2>&1
npm run dev > ../.vite.log 2>&1 &
DASH_PID=$!
cd ..

echo "[x] Cloning & Ingesting $REPO..."
curl -s -X POST http://localhost:8000/api/clone \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"$REPO\"}" > /dev/null

curl -s -X POST http://localhost:8000/api/ingest \
     -H "Content-Type: application/json" \
     -d '{"codebase_id": "demo"}' > /dev/null

echo "[x] Running Benchmark..."
python benchmarks/run_benchmark.py

echo ""
echo "Demo is running! Access the dashboard at http://localhost:5173"
echo "Press Ctrl+C to stop the demo."
wait
