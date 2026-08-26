#!/bin/bash
# Benchmark script for GraphMind

set -e

echo "=== GraphMind Benchmark ==="
echo ""

# Test 1: Baseline (no graph)
echo "[1/3] Baseline: Plain LLM query"
start=$(date +%s%N)
curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the architecture"}' > /dev/null
end=$(date +%s%N)
echo "  Done ($(( ($end - $start) / 1000000 ))ms)"

# Test 2: Graph-RAG
echo "[2/3] Graph-RAG: With context"
start=$(date +%s%N)
curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What functions call authenticate?"}' > /dev/null
end=$(date +%s%N)
echo "  Done ($(( ($end - $start) / 1000000 ))ms)"

# Test 3: Zero-token
echo "[3/3] Zero-token: GRAPH_ONLY"
start=$(date +%s%N)
curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List all functions"}' > /dev/null
end=$(date +%s%N)
echo "  Done ($(( ($end - $start) / 1000000 ))ms)"

echo ""
echo "=== Benchmark Complete ==="