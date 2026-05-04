# GraphMind Backend Development Plan

**Project**: GraphMind (CodeGraphX)  
**Assigned To**: Friend 2 - Backend Developer  
**Date**: May 3, 2026  
**Status**: Ready for Implementation

---

## Executive Summary

You are tasked with building the **backend infrastructure** for GraphMind - a token-efficient code reasoning engine. You'll set up the project scaffolding, handle codebase input (GitHub/ZIP), configure TigerGraph + SQLite fallback, and build the FastAPI server with 9 endpoints.

**Your Tasks**: 1, 2, 4, 5, 7, 16, 17, 18, 20, 21

**Collaborators**:
- **User (Prometheus)**: AI/RAG/LLM parts (Tasks 8-14)
- **Friend 1**: Frontend dashboard (Tasks 15, 19) - see `graphmind-frontend-plan.md`
- **Friend 3**: Parser + Graph ingestion (Tasks 3, 6)

---

## 1. Your Task List (10 Tasks)

### Phase 1: Foundation
- **Task 1**: Codebase Input Handler (GitHub Clone + ZIP Upload)
- **Task 2**: Project Scaffolding + Config + .env Auto-Setup

### Phase 2: Graph Database
- **Task 4**: TigerGraph Cloud Setup + Schema
- **Task 5**: SQLite/NetworkX Fallback with WAL Mode

### Phase 3: API Layer
- **Task 7**: FastAPI Core + 9 Endpoints

### Phase 4: Advanced Features
- **Task 16**: Predictive Caching
- **Task 17**: Token Budget Controller
- **Task 18**: Adaptive Learning Module

### Phase 5: Benchmarks + Demo
- **Task 20**: Benchmark Script + Competitor Comparison
- **Task 21**: demo.sh -- Auto-Clone fastapi/fastapi + Run Demo

---

## 2. Tech Stack

### Core Framework
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Programming language |
| **FastAPI** | 0.115.x | Web framework |
| **Uvicorn** | 0.32.x | ASGI server |
| **Pydantic** | 2.9.x | Data validation |

### Graph Database
| Technology | Purpose |
|------------|---------|
| **TigerGraph Cloud** | Primary graph database (Savanna tier - more stable for demos) |
| **SQLite** | Persistent fallback storage |
| **NetworkX** | In-memory graph operations |

### Dependencies
```txt
# From pyproject.toml
fastapi==0.115.x
uvicorn==0.32.x
pydantic==2.9.x
networkx==3.4.x
tree-sitter==0.23.x
tree-sitter-python==0.23.x
gitpython==3.1.x
tiktoken==0.8.x
```

---

## 3. Task Details

### Task 1: Codebase Input Handler (GitHub Clone + ZIP Upload)

**File**: `src/input/codebase_loader.py`

**What to do**:
- Build `CodebaseLoader` class with methods:
  - `load_from_zip(zip_path)` - Extract ZIP, validate, return path
  - `load_from_git(url)` - Clone GitHub repo, return path
- Validate ZIP and URL
- Detect languages (Python, JavaScript, etc.)
- Enforce 500-file limit
- Enforce 10MB ZIP max size
- Auto-clone `fastapi/fastapi` as default demo

**Must NOT do**:
- No recursive clone of submodules
- No handling private repos (public only)
- No extracting to final destination before validation

**Acceptance Criteria**:
- [ ] `CodebaseLoader().load_from_git('https://github.com/fastapi/fastapi')` clones successfully
- [ ] `CodebaseLoader().load_from_zip(uploaded_zip)` extracts valid ZIP
- [ ] Invalid inputs return error without crash
- [ ] >500 files: counts all, reports 500 for parsing
- [ ] ZIP >10MB returns size limit error

**References**:
- GitPython clone: https://github.com/gitpython-developers/gitpython/blob/main/git/repo/base.py#L1498-L1556
- ZIP security: https://docs.python.org/3/library/zipfile.html
- ZipSlip prevention: https://github.com/getsentry/sentry/blob/master/src/sentry/utils/zip.py#L10-L42

**Commit**: `feat(input): add GitHub clone and ZIP upload handler`

---

### Task 2: Project Scaffolding + Config + .env Auto-Setup

**Files**: 
- `pyproject.toml`
- `requirements.txt`
- `Makefile`
- `.env.example`
- `dashboard/` (Vite, React, Chart.js, Cytoscape)

**What to do**:
- Create directory structure: `src/`, `dashboard/`, `benchmarks/`, `tests/`, `scripts/`
- Create `pyproject.toml` with pinned versions
- Create `requirements.txt`
- Create `Makefile` with 4 targets: dev, ingest, benchmark, dashboard
- Create `.env.example` with required variables
- Auto-setup `.env` from `.env.example` if missing
- Set up `dashboard/` with: vite, react, chart.js, cytoscape

**Must NOT do**:
- No authentication, Docker, CI/CD

**Acceptance Criteria**:
- [ ] `pip install -e .` succeeds
- [ ] `cd dashboard && npm install` succeeds
- [ ] `Makefile` has 4 targets
- [ ] `.env` auto-created if missing

**Commit**: `chore(scaffold): set up project structure and dependencies`

---

### Task 4: TigerGraph Cloud Setup + Schema (Savanna Tier)

**Files**:
- `scripts/create_schema.gsql`
- `src/graph/tigergraph_client.py`

**What to do**:
- Create TigerGraph Cloud instance using **Savanna tier** (NOT Classic)
- **Why Savanna**: Free trial with credits valid 1 year, more stable for demos
- **Why NOT Classic**: Auto-stops after 1hr inactivity = demo death mid-presentation
- Define schema with:
  - **Vertices**: Module, Class, Function, Import
  - **Edges**: defines, calls, inherits, imports, contains, depends_on
- Build `TigerGraphClient` class:
  - `test_connection()` - Check connectivity (10s timeout)
  - CRUD operations for vertices/edges
- Connection timeout: 10s for fallback to SQLite

**Must NOT do**:
- No complex GSQL queries yet
- No data loading yet

**Acceptance Criteria**:
- [ ] TigerGraph Cloud accessible
- [ ] Schema executes (4 vertex, 6 edge types)
- [ ] Connection succeeds within 10s

**Commit**: `feat(graph): set up TigerGraph Cloud instance and schema`

---

### Task 5: SQLite/NetworkX Fallback with WAL Mode

**File**: `src/graph/sqlite_fallback.py`

**What to do**:
- Build `SQLiteGraph` class as drop-in replacement for TigerGraph
- Use NetworkX DiGraph for in-memory operations
- Use SQLite for persistent storage: `.codegraphx/graph.db`
- Enable WAL mode: `PRAGMA journal_mode=WAL`
- Interface methods:
  - `add_node(node_data)`
  - `add_edge(edge_data)`
  - `query(query_spec)`
  - `get_subgraph(entity, depth)`

**Must NOT do**:
- Do NOT replicate all TigerGraph features - only demo-needed ones
- Do NOT make this primary - it's fallback only

**Acceptance Criteria**:
- [ ] CRUD works
- [ ] Data persists across restarts
- [ ] Interface matches TigerGraphClient
- [ ] WAL mode enabled

**Commit**: `feat(graph): add SQLite/NetworkX fallback for TigerGraph`

---

### Task 7: FastAPI Core + 9 Endpoints

**File**: `src/api/main.py`

**What to do**:
- Build FastAPI application with 9 endpoints:

#### 1. POST /api/ingest
Trigger ingestion of a codebase.
```python
# Request
{ "codebase_id": "abc123" }

# Response
{
  "status": "success",
  "nodes_created": 1200,
  "edges_created": 3400
}
```

#### 2. POST /api/query
Submit query about codebase (routed through 3-tier engine).
```python
# Request
{
  "query": "What does authenticate function do?",
  "codebase_id": "abc123"
}

# Response
{
  "answer": "The authenticate function...",
  "tier": "GRAPH_RAG",
  "tokens_used": 850,
  "response_time": 1.2,
  "savings": 0.75,
  "reasoning": "Found relevant nodes in graph..."
}
```

#### 3. GET /api/health
System health check.
```python
# Response
{ "status": "healthy" }
```

#### 4. GET /api/metrics
Token usage statistics.
```python
# Response
{
  "total_tokens": 15000,
  "total_cost": 0.45,
  "savings_percentage": 78.5,
  "queries_count": 42
}
```

#### 5. GET /api/graph
Cytoscape-compatible graph JSON.
```python
# Response
{
  "nodes": [
    { "data": { "id": "func1", "label": "authenticate", "type": "function" } }
  ],
  "edges": [
    { "data": { "source": "func1", "target": "func2", "type": "calls" } }
  ]
}
```

#### 6. GET /api/query-history
Recent query history.
```python
# Response
[
  {
    "query": "What does authenticate do?",
    "answer": "The authenticate function...",
    "tier": "GRAPH_RAG",
    "timestamp": "2026-05-03T12:00:00Z",
    "tokens_used": 850,
    "reasoning": "..."
  }
]
```

#### 7. POST /api/budget
Set token budget.
```python
# Request
{ "budget": 10000 }

# Response
{
  "budget_limit": 10000,
  "budget_used": 2500,
  "budget_remaining": 7500
}
```

#### 8. POST /api/upload
ZIP file upload (multipart).
```python
# Request
Content-Type: multipart/form-data
Body: file=@codebase.zip

# Response
{
  "status": "success",
  "file_count": 150,
  "languages": ["Python", "JavaScript"],
  "codebase_id": "abc123"
}
```

#### 9. POST /api/clone
Clone GitHub repository.
```python
# Request
{ "url": "https://github.com/fastapi/fastapi" }

# Response
{
  "status": "success",
  "repo_name": "fastapi/fastapi",
  "file_count": 500,
  "codebase_id": "def456"
}
```

**Must NOT do**:
- No authentication
- No rate limiting

**Acceptance Criteria**:
- [ ] uvicorn starts without errors
- [ ] All 9 endpoints respond correctly
- [ ] /api/upload accepts ZIP via multipart
- [ ] /api/clone accepts GitHub URL
- [ ] LLM unavailable -> GRAPH_ONLY fallback

**Commit**: `feat(api): add FastAPI core and 9 endpoints`

---

### Task 16: Predictive Caching

**File**: `src/router/cache.py`

**What to do**:
- Build `PredictiveCache` class
- Cache key: normalized query text
- Cache value: answer, tier, tokens_used, response_time, timestamp
- Storage: SQLite database (`.codegraphx/cache.db`) with WAL mode
- Invalidation: 1 hour TTL or on re-ingestion
- Log hits/misses

**Must NOT do**:
- Do NOT use Redis
- Do NOT cache LLM_FULL responses

**Acceptance Criteria**:
- [ ] Repeated queries return cached result (0 new tokens)
- [ ] Cache hit rate tracked
- [ ] Invalidates on re-ingestion

**Commit**: `feat(router): add predictive caching for repeated queries`

---

### Task 17: Token Budget Controller

**File**: `src/router/budget_controller.py`

**What to do**:
- Build `BudgetController` class
- `POST /api/budget` sets limit
- Track: budget_limit, budget_used, budget_remaining, savings_percentage, dollar_cost
- Downgrade rules:
  - Budget <25% remaining -> Force GRAPH_RAG
  - Budget <10% remaining -> Force GRAPH_ONLY
- Dashboard display: "Budget: $5.00 | Used: $0.42 | Saved: $4.58"

**Must NOT do**:
- Do NOT make budget enforcement break the API

**Acceptance Criteria**:
- [ ] `POST /api/budget` sets budget
- [ ] sum(tokens_used) <= limit
- [ ] <25% forces GRAPH_RAG, <10% forces GRAPH_ONLY

**Commit**: `feat(router): add token budget controller with Savings Meter`

---

### Task 18: Adaptive Learning Module

**File**: `src/router/adaptive_learning.py`

**What to do**:
- Build `AdaptiveLearning` class
- Log query text, predicted tier, actual effectiveness
- After N same-pattern queries: auto-adjust thresholds
- Storage: SQLite database (`.codegraphx/learning.db`) with WAL mode
- `GET /api/learning/stats` returns accuracy, common patterns

**Must NOT do**:
- Do NOT train an ML model

**Acceptance Criteria**:
- [ ] After 10+ same-pattern queries, confidence increases
- [ ] `GET /api/learning/stats` returns metrics
- [ ] Routing accuracy improves over time

**Commit**: `feat(router): add adaptive learning for routing optimization`

---

### Task 20: Benchmark Script + Competitor Comparison

**File**: `benchmarks/run_benchmark.py`

**What to do**:
- Build benchmark script
- Run 7 queries:
  - Factoid x4 (expected: GRAPH_ONLY)
  - Relationship x2 (expected: GRAPH_RAG)
  - Open-ended x1 (expected: LLM_FULL)
- Generate comparison table: Baseline vs GraphRAG vs CodeGraphX
- Competitor comparison: CodeGraphX vs Ruflo vs GitNexus

**Must NOT do**:
- Do NOT fabricate benchmark numbers

**Acceptance Criteria**:
- [ ] 7 queries run successfully
- [ ] Comparison table with real numbers
- [ ] CodeGraphX >=70% token reduction vs baseline

**Commit**: `feat(benchmarks): add benchmark script and demo script`

---

### Task 21: demo.sh -- Auto-Clone fastapi/fastapi + Run Demo

**File**: `scripts/demo.sh`

**What to do**:
- Build demo script that:
  1. Auto-setup .env from .env.example
  2. Check TigerGraph (force SQLite if unavailable)
  3. Auto-clone fastapi/fastapi
  4. Start FastAPI + health check (poll every 2s, max 30s)
  5. Start React dashboard
  6. Run ingestion
  7. Run 7 benchmark queries
  8. Display summary
- Custom repo support: `./scripts/demo.sh --repo <url>`
- Reset support: `./scripts/demo.sh --reset`
- Graceful Ctrl+C cleanup

**Must NOT do**:
- Do NOT make this production-ready

**Acceptance Criteria**:
- [ ] Auto-clones fastapi/fastapi, runs end-to-end
- [ ] Health check waits (max 30s)
- [ ] Forces SQLite if needed
- [ ] --repo clones custom repo
- [ ] --reset clears all

**Commit**: `feat(scripts): add demo script for hackathon presentation`

---

## 4. File Structure

```
src/
├── api/
│   └── main.py                    # FastAPI app with 9 endpoints
├── input/
│   └── codebase_loader.py         # GitHub clone + ZIP upload
├── graph/
│   ├── tigergraph_client.py      # TigerGraph client
│   └── sqlite_fallback.py        # SQLite/NetworkX fallback
├── router/
│   ├── cache.py                  # Predictive caching
│   ├── budget_controller.py      # Token budget controller
│   └── adaptive_learning.py     # Adaptive learning module
├── parser/
│   └── codebase_parser.py        # (Built by Friend 3)
└── llm/
    ├── client.py                 # (Built by User)
    └── prompts.py                # (Built by User)
```

---

## 5. Execution Strategy

### Sequential Execution (STRICT)
Tasks must be completed IN ORDER:
```
Task 1 → Task 2 → Task 4 → Task 5 → Task 7 → Task 16 → Task 17 → Task 18 → Task 20 → Task 21
```

Each task blocks until completed and verified.

### Dependencies on Other Developers
- **Task 3, 6** (Friend 3): Must complete before Task 7
- **Tasks 8-14** (User): Must complete before Task 16, 17, 18

---

## 6. Constraints (MUST NOT DO)

❌ **No authentication** - Public access only  
❌ **No Docker** - Keep it simple  
❌ **No CI/CD** - Not for v1  
❌ **No private repos** - Public GitHub only  
❌ **No Redis** - Use SQLite for caching  
❌ **No ML models** - Rule-based adaptive learning only  

---

## 7. Environment Variables (.env)

```bash
# .env.example
TIGERGRAPH_HOST=your-instance.i.tgcloud.io
TIGERGRAPH_USER=tg_user
TIGERGRAPH_PASSWORD=your_password
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=github/qwen-coder
FALLBACK_MODEL=github/claude-sonnet-4
CODEBASE_LIMIT=500
ZIP_SIZE_LIMIT=10485760
```

---

## 8. Acceptance Criteria (All Tasks)

### Setup
- [ ] `pip install -e .` succeeds
- [ ] `.env` auto-created from `.env.example`
- [ ] `uvicorn src.api.main:app --reload` starts at `http://localhost:8000`

### API Endpoints
- [ ] All 9 endpoints respond correctly
- [ ] `/api/upload` accepts ZIP (multipart)
- [ ] `/api/clone` accepts GitHub URL
- [ ] `/api/graph` returns Cytoscape-compatible JSON
- [ ] CORS enabled for frontend (`http://localhost:5173`)

### Graph Database
- [ ] TigerGraph Cloud accessible (or SQLite fallback)
- [ ] Schema created (4 vertex, 6 edge types)
- [ ] Auto-fallback to SQLite on TigerGraph timeout

### Advanced Features
- [ ] Caching works (repeated queries = 0 tokens)
- [ ] Budget controller enforces limits
- [ ] Adaptive learning improves accuracy

### Demo
- [ ] `./scripts/demo.sh` runs end-to-end
- [ ] Auto-clones fastapi/fastapi
- [ ] Benchmark shows >=70% token reduction

---

## 9. Testing Your Code

### Manual Testing
```bash
# Test API health
curl http://localhost:8000/api/health

# Test ZIP upload
curl -X POST http://localhost:8000/api/upload -F "file=@test.zip"

# Test GitHub clone
curl -X POST http://localhost:8000/api/clone -H "Content-Type: application/json" -d '{"url": "https://github.com/fastapi/fastapi"}'

# Test query
curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" -d '{"query": "What does authenticate do?", "codebase_id": "abc123"}'
```

### Python Testing
```bash
# Run tests
pytest tests/

# Test specific module
python -m pytest tests/test_codebase_loader.py -v
```

---

## 10. Collaboration Notes

### Before Starting Task 7 (API):
- ✅ Task 3 (Parser) must be done by Friend 3
- ✅ Task 6 (Ingestion) must be done by Friend 3

### Before Starting Tasks 16-18 (Router):
- ✅ Tasks 8-14 (AI/RAG/LLM) must be done by User

### For Friend 1 (Frontend):
- Your API endpoints must match the contract in `graphmind-frontend-plan.md`
- CORS must allow `http://localhost:5173`
- Responses must match the format specified in frontend plan

---

## 11. Timeline Estimate

| Task | Description | Estimated Time |
|------|-------------|----------------|
| 1 | Codebase Input Handler | 1 day |
| 2 | Project Scaffolding | 0.5 day |
| 4 | TigerGraph Setup | 1 day |
| 5 | SQLite Fallback | 1 day |
| 7 | FastAPI + 9 Endpoints | 2 days |
| 16 | Predictive Caching | 1 day |
| 17 | Budget Controller | 1 day |
| 18 | Adaptive Learning | 1 day |
| 20 | Benchmark Script | 1 day |
| 21 | Demo Script | 0.5 day |
| **Total** | | **10-12 days** |

---

## 12. Getting Help

If you get stuck:
1. **Check the main plan**: `.sisyphus/plans/codegraphx.md`
2. **Ask the project owner** (Prometheus)
3. **Check API documentation**: FastAPI docs at `http://localhost:8000/docs` when running
4. **TigerGraph docs**: https://docs.tigergraph.com/
5. **FastAPI docs**: https://fastapi.tiangolo.com/

---

## 13. Final Checklist Before Starting

- [ ] Read this entire document
- [ ] Read the main plan: `.sisyphus/plans/codegraphx.md`
- [ ] Have Python 3.10+ installed
- [ ] Have Git installed (for cloning repos)
- [ ] Understand the 9 API endpoints
- [ ] Know your dependencies (see `pyproject.toml`)
- [ ] TigerGraph Cloud account ready (Savanna tier)

---

**Good luck! Build a solid backend! 🚀**

---

*Document saved to: `.sisyphus/plans/graphmind-backend-plan.md`*  
*Assigned to: Friend 2 (Backend Developer)*  
*Date: May 3, 2026*
