# CodeGraphX: Token-Efficient Code Reasoning Engine

## TL;DR

> **Quick Summary**: Build a smart inference engine that accepts real codebases (GitHub URL or ZIP upload), parses them into knowledge graphs (TigerGraph), and routes queries through 3 tiers -- GRAPH_ONLY (0 tokens), GRAPH_RAG (compressed context), LLM_FULL (full generation) -- minimizing LLM token usage by 70-90%.
> 
> **Deliverables**:
> - Codebase Input Handler (GitHub clone + ZIP upload, 500-file limit)
> - Tree-sitter Python parser (v0.23+ API)
> - TigerGraph Cloud + SQLite/NetworkX fallback
> - 3-tier smart routing engine (FastAPI)
> - Token Budget Controller + Savings Meter
> - Predictive caching + adaptive learning
> - React + Cytoscape.js + Chart.js dashboard
> - Benchmark comparison (Baseline vs GraphRAG vs CodeGraphX)
> 
> **Execution Mode**: SEQUENTIAL -- one task at a time, user verifies each before next starts
> **Critical Path**: Task 1 -> 2 -> 3 -> ... -> 21 -> F1-F4

---

## Context

### Original Request
Build CodeGraphX -- hackathon-winning project. Accept real codebases via GitHub URL or ZIP upload (no synthetic codebase). Execute sequentially, user monitors every line.

### Key Decisions
- **Input**: GitHub URL clone + ZIP file upload
- **Default demo**: Auto-clone fastapi/fastapi
- **Large repos**: Limit to 500 files
- **Private repos**: Public only for v1
- **Execution**: SEQUENTIAL -- one feature at a time
- **Stack**: FastAPI, TigerGraph Cloud, React, Tree-sitter Python, OpenRouter

### Research Findings (from Librarian Agents)

**GitPython Best Practices**:
- Use `Repo.clone_from(url, path, **kwargs)` -- passes through to git clone
- For shallow clones: `depth=N, single_branch=True`
- Error handling: `GitCommandNotFound`, `GitCommandError`, `UnsafeProtocolError`
- Cleanup on failure: `shutil.rmtree(dst, ignore_errors=True)` on exceptions
- Ref: https://github.com/gitpython-developers/gitpython/blob/9e94459b9e3795511070644fb5c2c413102f5609/git/repo/base.py#L1498-L1556

**Python ZIP Security Patterns**:
- Use `zipfile.is_zipfile()` for pre-validation
- Inspect `ZipFile.infolist()` before extraction (check file_size, count)
- ZipSlip prevention: validate `..` not in path parts, resolve to absolute and check prefix
- Use `ZipFile.testzip()` to detect corrupt members before extraction
- Extract to staging dir, promote to final destination after success
- Ref: https://github.com/python/cpython/blob/836fbdaaf32c355c7e8fb0af69f78fbbb28af8b1/Doc/library/zipfile.rst

### Competitive Edge vs Ruflo (37.2K) and GitNexus (34.9K)
- Zero-token answers (neither competitor has this)
- Visible Savings Meter with dollar cost
- Symbol compression (70-90%)
- Explicit token budgeting
- Real repo input (ZIP/GitHub URL)
- Routing reasoning display

---

## Work Objectives

### Must Have
- 3-tier routing (GRAPH_ONLY, GRAPH_RAG, LLM_FULL)
- Zero-token answers
- Symbol compression (70-90%)
- Budget controller with Savings Meter
- Predictive caching + adaptive learning
- Dashboard with file drop zone + repo input
- 9 API endpoints: /query, /ingest, /health, /metrics, /graph, /query-history, /budget, /upload, /clone
- LLM prompt templates
- Budget downgrade rules (<25% -> GRAPH_RAG, <10% -> GRAPH_ONLY)
- 500-file limit
- demo.sh auto-clones fastapi/fastapi

### Must NOT Have
- NO synthetic codebase
- NO multi-language parser (Python only v1)
- NO speculative decoding, LLMLingua, auth, Docker, CI/CD, framer-motion, JS/TS parsers, return type extraction, private repos, >500 files

---

## Execution Strategy (STRICT Sequential)

```
Phase 1: 1 -> 2 -> 3 -> 4 -> 5
Phase 2: 6 -> 7 -> 8 -> 9 -> 10
Phase 3: 11 -> 12 -> 13 -> 14 -> 15 -> 16
Phase 4: 17 -> 18 -> 19 -> 20 -> 21
Final:   F1-F4 (parallel review agents)
```

Each task blocks until user verifies and approves.

---

## TODOs

- [x] 1. Codebase Input Handler (GitHub Clone + ZIP Upload)

  **What to do**:
  - Build `src/input/codebase_loader.py` with `load_from_zip()` and `load_from_git()`
  - Validate ZIP and URL, detect languages, enforce 500-file limit and 10MB ZIP max
  - Auto-clone fastapi/fastapi as default
  - Use GitPython for clone, zipfile for ZIP handling
  - Error handling: invalid URLs, corrupt ZIPs, oversized files, too many files

  **Must NOT do**:
  - No recursive clone of submodules
  - No handling private repos (public only)
  - No extracting to final destination before validation

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` -- Backend file I/O, external service integration
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed, using GitPython library

  **Parallelization**:
  - **Can Run In Parallel**: NO (first task)
  - **Parallel Group**: Phase 1 | Sequential
  - **Blocks**: Task 2 | **Blocked By**: None

  **References**:
  - GitPython clone: https://github.com/gitpython-developers/gitpython/blob/9e94459b9e3795511070644fb5c2c413102f5609/git/repo/base.py#L1498-L1556
  - ZIP security: https://github.com/python/cpython/blob/836fbdaaf32c355c7e8fb0af69f78fbbb28af8b1/Doc/library/zipfile.rst#L302-L306
  - Sentry ZipSlip prevention: https://github.com/getsentry/sentry/blob/3c2d7110132d873fe545998dbf7ca1e6751aa015/src/sentry/utils/zip.py#L10-L42

  **Acceptance Criteria**:
  - [ ] `load_from_git('https://github.com/fastapi/fastapi')` clones successfully
  - [ ] `load_from_zip(uploaded_zip)` extracts valid ZIP
  - [ ] Invalid inputs return error without crash
  - [ ] >500 files: counts all, reports 500 for parsing
  - [ ] ZIP >10MB returns size limit error

  **QA Scenarios**:

  ```
  Scenario: Clone public repo
    Tool: Bash (Python)
    Preconditions: Clean state, internet access
    Steps:
      1. CodebaseLoader().load_from_git('https://github.com/fastapi/fastapi')
      2. Assert: path exists, contains .py files
    Expected Result: Clone succeeds, path returned
    Failure Indicators: Exception raised, empty path
    Evidence: .sisyphus/evidence/task-1-git-clone.txt

  Scenario: Upload valid ZIP
    Tool: Bash (Python)
    Preconditions: Create ZIP with 3 .py files
    Steps:
      1. Create ZIP file with valid Python files
      2. CodebaseLoader().load_from_zip(zip_path)
      3. Assert: extraction succeeds, path returned
    Expected Result: ZIP extracted, path returned
    Evidence: .sisyphus/evidence/task-1-zip-upload.txt

  Scenario: Reject invalid ZIP
    Tool: Bash (Python)
    Preconditions: Corrupted ZIP file
    Steps:
      1. Create corrupted ZIP file
      2. CodebaseLoader().load_from_zip(corrupted_zip_path)
      3. Assert: returns error, no crash
    Expected Result: Graceful error handling
    Evidence: .sisyphus/evidence/task-1-invalid-zip.txt

  Scenario: Enforce 500-file limit
    Tool: Bash (Python)
    Preconditions: Large repo (django/django)
    Steps:
      1. Clone django/django
      2. Assert: report shows total files, only 500 reported for parsing
    Expected Result: Counts all files, limits to 500 for parsing
    Evidence: .sisyphus/evidence/task-1-file-limit.txt

  Scenario: Enforce 10MB ZIP limit
    Tool: Bash (Python)
    Preconditions: Create ZIP >10MB
    Steps:
      1. Create ZIP file >10MB
      2. CodebaseLoader().load_from_zip(oversized_zip)
      3. Assert: returns size limit error
    Expected Result: Size limit error returned
    Evidence: .sisyphus/evidence/task-1-zip-size.txt
  ```

  **Evidence to Capture**:
  - [ ] Each evidence file named: task-1-{scenario-slug}.txt
  - [ ] Screenshots for UI scenarios (none for this task)

  **Commit**: YES
  - Message: `feat(input): add GitHub clone and ZIP upload handler`
  - Files: `src/input/codebase_loader.py`
  - Pre-commit: `python -m py_compile src/input/codebase_loader.py`

---

- [x] 2. Project Scaffolding + Config + .env Auto-Setup

  **What to do**:
  - Create `src/`, `dashboard/`, `benchmarks/`, `tests/`, `scripts/`
  - `pyproject.toml` with pinned versions: fastapi==0.115.x, uvicorn==0.32.x, pydantic==2.9.x, networkx==3.4.x, tree-sitter==0.23.x, tree-sitter-python==0.23.x, gitpython==3.1.x, tiktoken==0.8.x
  - `requirements.txt`, `.env.example`, `Makefile` (dev, ingest, benchmark, dashboard)
  - `.env` auto-setup from `.env.example`
  - `dashboard/`: vite, react, chart.js, cytoscape

  **Must NOT do**:
  - No authentication, Docker, CI/CD

  **Recommended Agent Profile**:
  - **Category**: `quick` -- Standard project setup
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Phase 1 | Sequential
  - **Blocks**: Task 3 | **Blocked By**: 1

  **Acceptance Criteria**:
  - [ ] `pip install -e .` succeeds
  - [ ] `cd dashboard && npm install` succeeds
  - [ ] `Makefile` has 4 targets
  - [ ] `.env` auto-created if missing

  **QA Scenarios**:

  ```
  Scenario: Verify setup
    Tool: Bash
    Steps:
      1. pip install -e . -> exit 0
      2. python -c "from src.api.main import app; print('OK')" -> OK
    Expected Result: Setup succeeds
    Evidence: .sisyphus/evidence/task-2-setup.txt

  Scenario: .env auto-setup
    Tool: Bash
    Steps:
      1. Remove .env
      2. Run startup -> .env created from .env.example
    Expected Result: .env auto-created
    Evidence: .sisyphus/evidence/task-2-env-setup.txt
  ```

  **Commit**: YES
  - Message: `chore(scaffold): set up project structure and dependencies`
  - Files: pyproject.toml, requirements.txt, Makefile, .env.example, dashboard/
  - Pre-commit: `pip install -e . && cd dashboard && npm install`

---

- [x] 3. Tree-sitter Parser (Python Only)

  **What to do**:
  - Build `src/parser/codebase_parser.py` using py-tree-sitter v0.23+ API
  - Extract: functions (name, params, docstring), classes (name, bases, methods), imports, function calls
  - Output: JSON with nodes and edges
  - Handle: syntax errors (skip + warn), empty files, nested classes, async
  - Skip return type extraction, parse only first 500 files

  **Must NOT do**:
  - No JavaScript/TypeScript parsing (Python only)
  - No dynamic import resolution

  **Recommended Agent Profile**:
  - **Category**: `deep` -- AST traversal, edge case handling
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 2 | **Blocks**: 4

  **References**:
  - py-tree-sitter v0.23+: https://tree-sitter.github.io/py-tree-sitter/
  - Pattern: `node.walk()` iterator, match `function_definition`, `class_definition`

  **Acceptance Criteria**:
  - [ ] Parses extracted repo without errors
  - [ ] Extracts >=30 functions, >=5 classes, >=10 imports, >=20 call relationships
  - [ ] Malformed file: warns, no crash
  - [ ] Respects 500-file limit

  **QA Scenarios**:

  ```
  Scenario: Parse real codebase
    Tool: Bash (Python)
    Steps: Run parser on extracted repo dir
    Assert: function >= 30, class >= 5
    Evidence: .sisyphus/evidence/task-3-parser.txt

  Scenario: Handle malformed file
    Tool: Bash (Python)
    Steps: Create file with syntax error, run parser
    Assert: no crash, warning logged
    Evidence: .sisyphus/evidence/task-3-error-handling.txt
  ```

  **Commit**: YES -- `feat(parser): implement Tree-sitter Python code parser`

---

- [x] 4. TigerGraph Cloud Setup + Schema

  **What to do**:
  - Create TigerGraph Cloud instance (free tier)
  - Schema: Vertex (Module, Class, Function, Import), Edge (defines, calls, inherits, imports, contains, depends_on)
  - `scripts/create_schema.gsql`, `src/graph/tigergraph_client.py`
  - Connection timeout: 10s for fallback

  **Must NOT do**:
  - No complex GSQL queries yet
  - No data loading yet

  **Recommended Agent Profile**:
  - **Category**: `quick` -- Cloud setup + schema
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 3 | **Blocks**: 5

  **Acceptance Criteria**:
  - [ ] TigerGraph Cloud accessible
  - [ ] Schema executes (4 vertex, 6 edge types)
  - [ ] Connection succeeds within 10s

  **QA Scenarios**:

  ```
  Scenario: Test connection
    Tool: Bash (Python)
    Steps: TigerGraphClient().test_connection()
    Assert: "connected" or True
    Evidence: .sisyphus/evidence/task-4-tg-connection.txt

  Scenario: Timeout fallback
    Tool: Bash (Python)
    Steps: Set unreachable TIGERGRAPH_HOST, run connection
    Assert: timeout within 10s, returns False
    Evidence: .sisyphus/evidence/task-4-timeout.txt
  ```

  **Commit**: YES -- `feat(graph): set up TigerGraph Cloud instance and schema`

---

- [x] 5. SQLite/NetworkX Fallback with WAL Mode

  **What to do**:
  - Build `src/graph/sqlite_fallback.py` as drop-in for TigerGraph
  - NetworkX DiGraph in-memory, SQLite persistent
  - Interface: add_node(), add_edge(), query(), get_subgraph()
  - `.codegraphx/graph.db` with WAL mode (PRAGMA journal_mode=WAL)

  **Must NOT do**:
  - Do NOT replicate all TigerGraph features -- only demo-needed ones
  - Do NOT make this primary -- it's fallback only

  **Recommended Agent Profile**:
  - **Category**: `quick` -- Standard NetworkX + SQLite
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 4 | **Blocks**: 6

  **Acceptance Criteria**:
  - [ ] CRUD works
  - [ ] Data persists across restarts
  - [ ] Interface matches TigerGraphClient
  - [ ] WAL mode enabled

  **QA Scenarios**:

  ```
  Scenario: CRUD + persistence
    Tool: Bash (Python)
    Steps: Create SQLiteGraph, add 3 nodes + 2 edges, query, recreate
    Assert: data persists
    Evidence: .sisyphus/evidence/task-5-sqlite-fallback.txt

  Scenario: Verify WAL mode
    Tool: Bash (Python)
    Steps: Create instance, PRAGMA journal_mode
    Assert: returns "wal"
    Evidence: .sisyphus/evidence/task-5-wal-mode.txt
  ```

  **Commit**: YES -- `feat(graph): add SQLite/NetworkX fallback for TigerGraph`

---

- [x] 6. Graph Ingestion Pipeline

  **What to do**:
  - Build `src/graph/ingestion.py`
  - Parse extracted codebase with CodebaseParser, transform to TigerGraph or SQLite format
  - Bulk load with error handling, verification queries
  - Auto-select backend (TigerGraph first, SQLite fallback)
  - Graph health check after ingestion
  - Track repo metadata: URL/ZIP filename, file count, languages

  **Must NOT do**:
  - Do NOT build query engine yet
  - Do NOT build routing logic yet

  **Recommended Agent Profile**:
  - **Category**: `deep` -- Data transformation pipeline, dual-backend
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Depends on**: 1, 3, 4, 5 | **Blocks**: 7

  **Acceptance Criteria**:
  - [ ] `python src/graph/ingestion.py <path>` loads successfully
  - [ ] >=50 nodes, >=100 edges
  - [ ] Both backends work
  - [ ] Auto-fallback on TigerGraph unavailable

  **QA Scenarios**:

  ```
  Scenario: Ingest real codebase
    Tool: Bash (Python)
    Steps: Run ingestion.py on extracted repo
    Assert: nodes >= 50, edges >= 100
    Evidence: .sisyphus/evidence/task-6-ingestion.txt

  Scenario: Fallback test
    Tool: Bash (Python)
    Steps: Set invalid TIGERGRAPH_HOST, run ingestion
    Assert: SQLite fallback, succeeds
    Evidence: .sisyphus/evidence/task-6-fallback.txt
  ```

  **Commit**: YES -- `feat(graph): build ingestion pipeline for code-to-graph`

---

- [x] 7. FastAPI Core + 9 Endpoints

  **What to do**:
  - Build `src/api/main.py` with 9 endpoints:
    1. POST /api/ingest -- trigger ingestion
    2. POST /api/query -- route query, return answer + metrics
    3. GET /api/health -- system status
    4. GET /api/metrics -- token usage stats
    5. GET /api/graph -- Cytoscape-compatible JSON
    6. GET /api/query-history -- last N queries
    7. POST /api/budget -- set token budget
    8. POST /api/upload -- ZIP file upload (multipart), extract, ingest
    9. POST /api/clone -- GitHub URL, clone, ingest
  - Pydantic models, CORS, error flow (LLM unavailable -> GRAPH_ONLY + warning)
  - Non-code query handling

  **Must NOT do**:
  - No authentication
  - No rate limiting

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` -- API design
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Depends on**: 2, 6 | **Blocks**: 8, 11

  **Acceptance Criteria**:
  - [ ] uvicorn starts without errors
  - [ ] All 9 endpoints respond correctly
  - [ ] /api/upload accepts ZIP via multipart
  - [ ] /api/clone accepts GitHub URL
  - [ ] LLM unavailable -> GRAPH_ONLY fallback

  **QA Scenarios**:

  ```
  Scenario: ZIP upload
    Tool: Bash (curl)
    Steps: curl -X POST http://localhost:8000/api/upload -F "file=@test_repo.zip"
    Assert: 200, file_count, languages, status
    Evidence: .sisyphus/evidence/task-7-zip-upload.txt

  Scenario: GitHub clone
    Tool: Bash (curl)
    Steps: curl -X POST http://localhost:8000/api/clone -d '{"url": "https://github.com/fastapi/fastapi"}'
    Assert: 200, repo_name, file_count, status
    Evidence: .sisyphus/evidence/task-7-git-clone.txt
  ```

  **Commit**: YES -- `feat(api): add FastAPI core and 9 endpoints`

---

- [x] 8. Graph Query Engine

  **What to do**:
  - Build `src/graph/query_engine.py`
  - Query types: get_function, get_class, get_callers, get_callees, get_imports, get_inheritance, get_subgraph(entity, depth)
  - TigerGraph: GSQL; SQLite: NetworkX traversal
  - `is_graph_ready()` -> True/False

  **Must NOT do**:
  - Do NOT build routing logic yet

  **Recommended Agent Profile**:
  - **Category**: `deep` -- Dual-backend queries
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 4, 6 | **Blocks**: 9, 11, 12, 13

  **Acceptance Criteria**:
  - [ ] All 7 query types work on both backends
  - [ ] `is_graph_ready()` returns True after ingestion

  **QA Scenarios**:

  ```
  Scenario: Query function callers
    Tool: Bash (Python)
    Steps: q.get_callers('some_function')
    Assert: entity count > 0
    Evidence: .sisyphus/evidence/task-8-query-callers.txt
  ```

  **Commit**: YES -- `feat(graph): build query engine for graph traversal`

---

- [x] 9. Query Classifier + Entity Recognition

  **What to do**:
  - Build `src/router/query_classifier.py`
  - GRAPH_ONLY (factoid), GRAPH_RAG (relationship), LLM_FULL (open-ended)
  - Use query length + keyword matching + entity recognition from graph
  - Return: tier, confidence 0.0-1.0, reasoning
  - Non-code detection: "what is", "help me" -> friendly response

  **Must NOT do**:
  - Do NOT use LLM for classification

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` -- Rule-based classifier
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 6 (depends on entity recognition from graph) | **Blocks**: 11

  **Acceptance Criteria**:
  - [ ] Factoid -> GRAPH_ONLY, Relationship -> GRAPH_RAG, Open-ended -> LLM_FULL
  - [ ] Confidence + reasoning returned
  - [ ] Entity recognition boosts confidence

  **QA Scenarios**:

  ```
  Scenario: Classify factoid
    Tool: Bash (Python)
    Steps: c.classify("What functions call X?")
    Assert: GRAPH_ONLY
    Evidence: .sisyphus/evidence/task-9-classify-factoid.txt
  ```

  **Commit**: YES -- `feat(router): add query classifier for 3-tier routing`

---

- [x] 10. Token Counter + Logger

  **What to do**:
  - Build `src/router/token_counter.py` with tiktoken; fallback to word-count (words * 1.3)
  - Build `src/router/query_logger.py`: query text, tier, tokens, response time, timestamp, dollar cost
  - SQLite: `.codegraphx/query_log.db` with WAL mode
  - Aggregation: total_tokens, tokens_by_tier, avg_response_time, savings_percentage, dollar_cost_saved

  **Must NOT do**:
  - Do NOT build full analytics dashboard

  **Recommended Agent Profile**:
  - **Category**: `quick` -- SQLite logging
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 9 | **Blocks**: 11, 15, 16, 17

  **Acceptance Criteria**:
  - [ ] `count_tokens` accurate
  - [ ] log writes to SQLite
  - [ ] `savings_percentage` correct
  - [ ] Word-count fallback works

  **QA Scenarios**:

  ```
  Scenario: Log queries and savings
    Tool: Bash (Python)
    Steps: Log 5 queries, run savings_percentage
    Assert: percentage > 0
    Evidence: .sisyphus/evidence/task-10-logging.txt
  ```

  **Commit**: YES -- `feat(router): add token counter and query logger`

---

- [x] 11. LLM Client + Prompt Templates

  **What to do**:
  - Build `src/llm/client.py` for OpenRouter
  - Models: github/qwen-coder, github/claude-sonnet-4, openai/gpt-4o-mini (fallback chain)
  - Build `src/llm/prompts.py`: GRAPH_RAG and LLM_FULL system prompts
  - Retry with fallback, 30s timeout

  **Must NOT do**:
  - Do NOT use local LLMs

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` -- LLM integration
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 10 | **Blocks**: 12

  **Acceptance Criteria**:
  - [ ] Sends request, receives response
  - [ ] Fallback chain works
  - [ ] 30s timeout enforced

  **QA Scenarios**:

  ```
  Scenario: LLM responds
    Tool: Bash (Python)
    Steps: LLMClient().generate('Hello')
    Assert: non-empty string
    Evidence: .sisyphus/evidence/task-11-llm-response.txt
  ```

  **Commit**: YES -- `feat(llm): add OpenRouter client and prompt templates`

---

- [x] 12. 3-Tier Routing Engine

  **What to do**:
  - Build `src/router/routing_engine.py`
  - Flow: Query -> Classifier -> Check Budget -> Route -> Execute -> Return
  - GRAPH_ONLY (0 tokens), GRAPH_RAG (compressed + LLM), LLM_FULL (full LLM)
  - Include routing reasoning
  - Return: answer, tier, tokens_used, response_time, savings, reasoning, dollar_cost
  - Error: LLM unavailable -> GRAPH_ONLY + warning

  **Must NOT do**:
  - Do NOT implement speculative execution

  **Recommended Agent Profile**:
  - **Category**: `deep` -- Core differentiator
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 11 | **Blocks**: 13, 14, 15, 16, 17, 19

  **Acceptance Criteria**:
  - [ ] 7 benchmark queries: >=4 routed to GRAPH_ONLY or GRAPH_RAG
  - [ ] Each response includes tier, tokens_used, response_time, savings, reasoning
  - [ ] GRAPH_ONLY=0, GRAPH_RAG<500, LLM_FULL>500

  **QA Scenarios**:

  ```
  Scenario: Route to GRAPH_ONLY
    Tool: Bash (curl)
    Steps: POST /api/query with factoid
    Assert: GRAPH_ONLY, tokens_used: 0, reasoning
    Evidence: .sisyphus/evidence/task-12-route-graph-only.txt
  ```

  **Commit**: YES -- `feat(router): implement 3-tier smart routing engine`

---

- [x] 13. Zero-Token Answer Generator

  **What to do**:
  - Build `src/router/zero_token.py`
  - Convert graph results to natural language WITHOUT LLM
  - Templates for list, relationship, existence queries
  - Insufficient data -> triggers GRAPH_RAG upgrade

  **Must NOT do**:
  - Do NOT call any LLM

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` -- Template-based NL generation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 12 | **Blocks**: 19

  **Acceptance Criteria**:
  - [ ] 5 factoid questions answered with 0 tokens
  - [ ] Grammatically correct, accurate
  - [ ] tokens_used = 0 confirmed

  **QA Scenarios**:

  ```
  Scenario: Answer with 0 tokens
    Tool: Bash (curl)
    Steps: POST /api/query with "List all functions"
    Assert: tokens_used: 0, answer contains function names
    Evidence: .sisyphus/evidence/task-13-zero-token.txt
  ```

  **Commit**: YES -- `feat(router): add zero-token answer generator for GRAPH_ONLY tier`

---

- [x] 14. Graph-to-Symbol Compressor

  **What to do**:
  - Build `src/router/symbol_compressor.py`
  - Convert paths to symbols: `E1[Function:authenticate_user] -[called_by]-> E2[Function:login_route]`
  - Build entity dictionary, construct compressed prompt
  - Target: 70-90% reduction, report compression ratio

  **Must NOT do**:
  - Do NOT lose critical information

  **Recommended Agent Profile**:
  - **Category**: `deep` -- Novel compression algorithm
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 13 | **Blocks**: 19

  **Acceptance Criteria**:
  - [ ] Compressed prompt <=30% of full text
  - [ ] LLM answers accurate with compressed context
  - [ ] GRAPH_RAG queries < 500 tokens

  **QA Scenarios**:

  ```
  Scenario: Measure token reduction
    Tool: Bash (Python)
    Steps: Get full text context (measure), get compressed (measure)
    Assert: compressed <= full * 0.3
    Evidence: .sisyphus/evidence/task-14-compression.txt
  ```

  **Commit**: YES -- `feat(router): add graph-to-symbol compressor for GRAPH_RAG tier`

---

- [x] 15. React Dashboard + File Drop Zone

  **What to do**:
  - `dashboard/` with Vite: react, chart.js + react-chartjs-2, cytoscape + cytoscape-react (NO framer-motion)
  - Components: QueryInput, SavingsMeter, QueryHistory, GraphViz, BudgetDisplay
  - FileDropZone: drag-and-drop ZIP upload with progress bar
  - RepoInput: GitHub URL text field + Clone button
  - SwitchRepoButton: clear current, load new
  - Connect to FastAPI via fetch (multipart for ZIP)

  **Must NOT do**:
  - No dark mode, export to PDF, real-time WebSocket

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering` -- React UI
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 14 | **Blocks**: 16

  **Acceptance Criteria**:
  - [ ] `npm run dev` launches at localhost:5173
  - [ ] Page shows: header, query input, file drop zone, URL input, savings meter, history, reset
  - [ ] Dragging ZIP triggers upload, URL input triggers clone
  - [ ] Query calls /api/query, Reset clears state

  **QA Scenarios**:

  ```
  Scenario: Dashboard loads
    Tool: Playwright
    Steps: Navigate to localhost:5173, assert components
    Evidence: .sisyphus/evidence/task-15-dashboard-load.png

  Scenario: ZIP upload via UI
    Tool: Playwright
    Steps: Set input files on drop zone, assert upload
    Evidence: .sisyphus/evidence/task-15-zip-upload.png
  ```

  **Commit**: YES -- `feat(dashboard): scaffold React dashboard with core components`

---

- [x] 16. Predictive Caching

  **What to do**:
  - Build `src/router/cache.py`
  - Cache key: normalized query, Cache value: answer, tier, tokens_used, response_time, timestamp
  - Invalidation: 1h TTL or re-ingestion
  - SQLite: `.codegraphx/cache.db` with WAL, log hits/misses

  **Must NOT do**:
  - Do NOT use Redis
  - Do NOT cache LLM_FULL responses

  **Recommended Agent Profile**:
  - **Category**: `quick` -- SQLite-based caching
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 15 | **Blocks**: 17

  **Acceptance Criteria**:
  - [ ] Repeated queries return cached result (0 new tokens)
  - [ ] Cache hit rate tracked
  - [ ] Invalidates on re-ingestion

  **QA Scenarios**:

  ```
  Scenario: Cache hit
    Tool: Bash (curl)
    Steps: Run same query twice, assert second has cache_hit: true, tokens_used: 0
    Evidence: .sisyphus/evidence/task-16-cache-hit.txt
  ```

  **Commit**: YES -- `feat(router): add predictive caching for repeated queries`

---

- [x] 17. Token Budget Controller

  **What to do**:
  - Build `src/router/budget_controller.py`
  - POST /api/budget sets limit
  - Downgrade: <25% -> GRAPH_RAG, <10% -> GRAPH_ONLY
  - Dashboard: "Budget: $5.00 | Used: $0.42 | Saved: $4.58"
  - Track: budget_limit, budget_used, budget_remaining, savings_percentage, dollar_cost

  **Must NOT do**:
  - Do NOT make budget enforcement break the API

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` -- Budget tracking
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 16 | **Blocks**: 18

  **Acceptance Criteria**:
  - [ ] POST /api/budget sets budget
  - [ ] sum(tokens_used) <= limit
  - [ ] <25% forces GRAPH_RAG, <10% forces GRAPH_ONLY

  **QA Scenarios**:

  ```
  Scenario: Enforce budget
    Tool: Bash (curl)
    Steps: Set budget 1000, run queries that would use >1000
    Assert: sum <= 1000
    Evidence: .sisyphus/evidence/task-17-budget-enforcement.txt
  ```

  **Commit**: YES -- `feat(router): add token budget controller with Savings Meter`

---

- [x] 18. Adaptive Learning Module
- [x] 19. Dashboard Metrics + Graph Viz + Repo Browser
- [x] 20. Benchmark Script + Competitor Comparison
- [x] 21. demo.sh -- Auto-Clone fastapi/fastapi + Run Demo

  **What to do**:
  - Build `scripts/demo.sh`
  - Steps: auto-setup .env, check TigerGraph (force SQLite if unavailable), auto-clone fastapi/fastapi, start FastAPI + health check (poll every 2s, max 30s), start React dashboard, run ingestion, run 7 benchmark queries, display summary
  - Custom repo: `./scripts/demo.sh --repo <url>`
  - Reset: `./scripts/demo.sh --reset`
  - Graceful Ctrl+C cleanup

  **Must NOT do**:
  - Do NOT make this production-ready

  **Recommended Agent Profile**:
  - **Category**: `quick` -- Shell scripting
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: 20 | **Blocks**: Final verification

  **Acceptance Criteria**:
  - [ ] Auto-clones fastapi/fastapi, runs end-to-end
  - [ ] Health check waits (max 30s)
  - [ ] Forces SQLite if needed
  - [ ] --repo clones custom repo
  - [ ] --reset clears all

  **QA Scenarios**:

  ```
  Scenario: Full demo run
    Tool: Bash
    Steps: ./scripts/demo.sh
    Assert: completes without errors, benchmark summary
    Evidence: .sisyphus/evidence/task-21-demo.txt
  ```

  **Commit**: YES -- `feat(scripts): add demo script for hackathon presentation`

---

## Final Verification Wave (MANDATORY -- after ALL implementation tasks)

> 4 review agents in PARALLEL. ALL must APPROVE. Present results, get explicit okay.
>
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**

- [x] F1. **Plan Compliance Audit** -- oracle
- [x] F2. **Code Quality Review** -- unspecified-high
- [x] F3. **Real Manual QA** -- unspecified-high (+ `playwright` skill if UI)
- [x] F4. **Scope Fidelity Check** -- deep
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 -- everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

Each task commits individually with descriptive messages: feat(input), chore(scaffold), feat(parser), feat(graph), feat(api), feat(router), feat(llm), feat(dashboard), feat(benchmarks), feat(scripts).

---

## Success Criteria

### Verification Commands
```bash
# Input
curl -X POST http://localhost:8000/api/upload -F "file=@test_repo.zip"
curl -X POST http://localhost:8000/api/clone -d '{"url": "https://github.com/fastapi/fastapi"}'

# API
curl http://localhost:8000/api/health  # 200
curl http://localhost:8000/api/metrics  # 200

# Routing
curl -X POST http://localhost:8000/api/query -d '{"query": "What functions call X?", "codebase_id": "default"}'  # GRAPH_ONLY, tokens=0

# Demo
./scripts/demo.sh  # Clones fastapi/fastapi, runs queries, shows summary
```

### Final Checklist
- [x] All Must Have present
- [x] All Must NOT Have absent
- [x] >=70% token reduction vs baseline
- [x] Savings Meter shows real numbers + dollar cost
- [x] 7 benchmark queries pass with correct tiers
- [x] Competitor comparison shows CodeGraphX advantages
- [x] demo.sh runs end-to-end
