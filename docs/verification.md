# Verification Guide

## Overview
This document describes the end-to-end verification process for GraphMind, including token analysis and system validation.

## Prerequisites
- Python 3.8+
- Dependencies installed: `pip install -r requirements.txt` (fastapi, uvicorn, requests, tiktoken)
- GraphMind project cloned and set up

## Token Verification (Wave 3.3)
### Tools
1. **Token Analyzer** (`src/benchmark/token_analyzer.py`)
   - `count_tokens(file_path)`: Count tokens in a single file
   - `count_dataset_tokens(directory)`: Count all tokens in a directory
   - `verify_2m_threshold(directory)`: Check if dataset exceeds 2 million tokens
   - `get_token_report(directory)`: Get detailed token breakdown

2. **Token Report** (`src/benchmark/token_report.py`)
   - `TokenReport` class for generating and saving reports
   - Reports saved to `.codegraphx/reports/` by default
   - Supports JSON and Markdown formats

### Usage
```bash
# Count tokens in a single file
python -c "import sys; sys.path.insert(0, 'src'); from benchmark import count_tokens; print(count_tokens('src/router/token_counter.py'))"

# Generate full token report
python -c "import sys; sys.path.insert(0, 'src'); from benchmark import TokenReport; r = TokenReport('src'); r.generate(); print(r.save_report(fmt='markdown'))"
```

## End-to-End Verification (Wave 5.2)
### Script
`scripts/verify_e2e.py` validates the entire system:
1. Tests all API endpoints (health, query, metrics, graph, etc.)
2. Verifies all 3 routing tiers work: `GRAPH_ONLY`, `GRAPH_RAG`, `LLM_FULL`
3. Confirms evaluation endpoint returns valid results
4. Checks benchmark token counting produces valid output
5. Validates token count logic

### How to Run
```bash
# Make executable (if not already)
chmod +x scripts/verify_e2e.py

# Run verification (starts API automatically if not running)
python scripts/verify_e2e.py
```

### Expected Output
- All API endpoints return 200 status codes
- Queries are routed to all 3 tiers correctly
- Evaluation endpoint returns summary data
- Token reports are generated and saved
- Script exits with code 0 if all checks pass

## Troubleshooting
- **API fails to start**: Check `requirements.txt` has `fastapi` and `uvicorn` installed
- **Routing tiers missing**: Ensure `src/router/routing_engine.py` is properly configured
- **Token count errors**: Verify `tiktoken` is installed, or the fallback word-count method will be used
- **Evaluation fails**: Check `src/evaluation/` modules are present

## Reports
Token reports are saved to `.codegraphx/reports/`:
- `token_report.json`: Machine-readable token data
- `token_report.md`: Human-readable Markdown report
