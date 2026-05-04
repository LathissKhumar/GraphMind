# GraphMind Parser + Graph Ingestion Plan

**Project**: GraphMind (CodeGraphX)  
**Assigned To**: Friend 3 - Parser & Graph Specialist  
**Date**: May 3, 2026  
**Status**: Ready for Implementation

---

## Executive Summary

You are tasked with building the **code parser and graph ingestion pipeline** for GraphMind - a token-efficient code reasoning engine. You'll create a Python parser using Tree-sitter to extract code structure, then build a pipeline to transform parsed code into graph database format (TigerGraph or SQLite/NetworkX).

**Your Tasks**: 3, 6

**Collaborators**:
- **User (Prometheus)**: AI/RAG/LLM parts (Tasks 8-14)
- **Friend 1**: Frontend dashboard (Tasks 15, 19) - see `graphmind-frontend-plan.md`
- **Friend 2**: Backend API + Infrastructure (Tasks 1, 2, 4, 5, 7, 16-18, 20, 21) - see `graphmind-backend-plan.md`

---

## 1. Your Task List (2 Tasks)

### Task 3: Tree-sitter Parser (Python Only)
- Build `src/parser/codebase_parser.py`
- Parse Python code using Tree-sitter v0.23+ API
- Extract: functions, classes, imports, function calls
- Output structured JSON with nodes and edges

### Task 6: Graph Ingestion Pipeline
- Build `src/graph/ingestion.py`
- Transform parsed code into graph database format
- Support both TigerGraph and SQLite/NetworkX backends
- Bulk load with verification

---

## 2. Tech Stack

### Core Technologies
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Programming language |
| **Tree-sitter** | 0.23.x | Code parsing |
| **tree-sitter-python** | 0.23.x | Python grammar |
| **TigerGraph** | Cloud (Savanna tier) | Primary graph DB |
| **SQLite** | 3.x | Fallback persistent storage |
| **NetworkX** | 3.4.x | In-memory graph operations |

### Dependencies
```txt
# From pyproject.toml
tree-sitter==0.23.x
tree-sitter-python==0.23.x
networkx==3.4.x
```

---

## 3. Task 3: Tree-sitter Parser (Python Only)

**File**: `src/parser/codebase_parser.py`

### What to do

Build a `CodebaseParser` class that:

1. **Initializes Tree-sitter** with Python grammar
2. **Walks the AST** using `node.walk()` iterator
3. **Extracts entities**:

#### Functions
```python
{
  "type": "function",
  "name": "authenticate",
  "params": ["username", "password"],
  "docstring": "Authenticates user credentials...",
  "start_line": 10,
  "end_line": 25,
  "file": "auth.py"
}
```

#### Classes
```python
{
  "type": "class",
  "name": "User",
  "bases": ["BaseModel"],
  "methods": ["__init__", "save", "delete"],
  "docstring": "Represents a user...",
  "start_line": 30,
  "end_line": 60,
  "file": "models.py"
}
```

#### Imports
```python
{
  "type": "import",
  "module": "fastapi",
  "items": ["FastAPI", "HTTPException"],
  "file": "main.py"
}
```

#### Function Calls
```python
{
  "type": "call",
  "caller": "authenticate",
  "callee": "verify_password",
  "file": "auth.py"
}
```

4. **Output JSON format**:
```json
{
  "nodes": [
    { "id": "func_authenticate", "type": "function", "label": "authenticate", "file": "auth.py", ... },
    { "id": "class_User", "type": "class", "label": "User", "file": "models.py", ... }
  ],
  "edges": [
    { "source": "func_authenticate", "target": "func_verify_password", "type": "calls" },
    { "source": "class_User", "target": "class_BaseModel", "type": "inherits" }
  ]
}
```

### Must NOT do

- ❌ No JavaScript/TypeScript parsing (Python only for v1)
- ❌ No dynamic import resolution
- ❌ No return type extraction
- ❌ Parse only first 500 files (enforced by Task 1)

### Handle Edge Cases

- Syntax errors: Skip file + log warning
- Empty files: Skip gracefully
- Nested classes: Extract correctly
- Async functions: Handle `async def`
- Decorators: Preserve but don't analyze

### Acceptance Criteria

- [ ] Parses extracted repo without errors
- [ ] Extracts >=30 functions, >=5 classes, >=10 imports, >=20 call relationships
- [ ] Malformed file: warns, no crash
- [ ] Respects 500-file limit (set by Task 1)

### References

- **py-tree-sitter v0.23+**: https://tree-sitter.github.io/py-tree-sitter/
- **Pattern**: `node.walk()` iterator, match `function_definition`, `class_definition`
- **Tree-sitter Python grammar**: https://github.com/tree-sitter/tree-sitter-python

### QA Scenarios

```python
# Scenario: Parse real codebase
Steps: Run parser on extracted repo dir
Assert: function >= 30, class >= 5, edges >= 20
Evidence: .sisyphus/evidence/task-3-parser.txt

# Scenario: Handle malformed file
Steps: Create file with syntax error, run parser
Assert: no crash, warning logged
Evidence: .sisyphus/evidence/task-3-error-handling.txt
```

### Commit Message
```
feat(parser): implement Tree-sitter Python code parser
```

---

## 4. Task 6: Graph Ingestion Pipeline

**File**: `src/graph/ingestion.py`

### What to do

Build an `IngestionPipeline` class that:

1. **Orchestrates the flow**:
   ```
   CodebaseParser → Parse Code → Transform to Graph Format → Load into DB
   ```

2. **Transforms parsed data** to graph database format:

#### For TigerGraph
```python
# Vertices
CREATE VERTEX Module (PRIMARY_ID name STRING, file STRING, ...)
CREATE VERTEX Class (PRIMARY_ID name STRING, bases LIST<STRING>, ...)
CREATE VERTEX Function (PRIMARY_ID name STRING, params LIST<STRING>, ...)
CREATE VERTEX Import (PRIMARY_ID name STRING, module STRING, ...)

# Edges
CREATE DIRECTED EDGE defines (FROM Module, TO Class|Function, ...)
CREATE DIRECTED EDGE calls (FROM Function, TO Function, ...)
CREATE DIRECTED EDGE inherits (FROM Class, TO Class, ...)
CREATE DIRECTED EDGE imports (FROM Module, TO Import, ...)
CREATE DIRECTED EDGE contains (FROM Module, TO Class|Function, ...)
CREATE DIRECTED EDGE depends_on (FROM *, TO *, ...)
```

#### For SQLite/NetworkX
```python
# NetworkX DiGraph
G.add_node("func_authenticate", type="function", label="authenticate", ...)
G.add_edge("func_authenticate", "func_verify_password", type="calls")

# SQLite (persistence)
INSERT INTO nodes (id, type, label, ...) VALUES (...)
INSERT INTO edges (source, target, type, ...) VALUES (...)
```

3. **Auto-selects backend**:
   - Try TigerGraph first
   - On failure/timeout (10s): Fallback to SQLite/NetworkX
   - Use `TigerGraphClient` (built by Friend 2 in Task 4, 5)

4. **Bulk loads data** with error handling:
   - Batch insert (100 nodes/edges at a time)
   - Retry on failure (max 3 attempts)
   - Log progress

5. **Verifies ingestion**:
   - Run verification queries
   - Check node/edge counts
   - Graph health check

6. **Tracks repo metadata**:
   - URL/ZIP filename
   - File count
   - Languages detected
   - Ingestion timestamp

### Must NOT do

- ❌ Do NOT build query engine (that's Task 8)
- ❌ Do NOT build routing logic (that's Task 12)

### Dependencies

- **Task 1**: Codebase Input Handler (provides parsed code path)
- **Task 3**: Tree-sitter Parser (provides parsed JSON)
- **Task 4**: TigerGraph Client (provides `TigerGraphClient`)
- **Task 5**: SQLite Fallback (provides `SQLiteGraph`)

### Acceptance Criteria

- [ ] `python src/graph/ingestion.py <path>` loads successfully
- [ ] >=50 nodes, >=100 edges created
- [ ] Both backends work (TigerGraph and SQLite)
- [ ] Auto-fallback on TigerGraph unavailable
- [ ] Graph health check passes after ingestion

### Usage

```bash
# Ingest a parsed codebase
python src/graph/ingestion.py /path/to/extracted/repo

# Called by API
# POST /api/ingest with codebase_id
# -> Triggers ingestion pipeline
```

### QA Scenarios

```python
# Scenario: Ingest real codebase
Steps: Run ingestion.py on extracted fastapi/fastapi repo
Assert: nodes >= 50, edges >= 100
Evidence: .sisyphus/evidence/task-6-ingestion.txt

# Scenario: Fallback test
Steps: Set invalid TIGERGRAPH_HOST, run ingestion
Assert: SQLite fallback, succeeds
Evidence: .sisyphus/evidence/task-6-fallback.txt
```

### Commit Message
```
feat(graph): build ingestion pipeline for code-to-graph
```

---

## 5. File Structure

```
src/
├── parser/
│   ├── __init__.py
│   └── codebase_parser.py         # Your Task 3
├── graph/
│   ├── __init__.py
│   ├── ingestion.py              # Your Task 6
│   ├── tigergraph_client.py      # (Built by Friend 2 - Task 4)
│   └── sqlite_fallback.py        # (Built by Friend 2 - Task 5)
└── input/
    └── codebase_loader.py         # (Built by Friend 2 - Task 1)
```

---

## 6. Execution Strategy

### Sequential Execution
Your tasks must be completed IN ORDER:
```
Task 3 → Task 6
```

### Dependencies on Other Developers
- **Task 1** (Friend 2): Must complete before Task 6 (provides codebase input)
- **Task 4, 5** (Friend 2): Must complete before Task 6 (provides graph backends)

### Who Depends on You
- **Task 7** (Friend 2): Needs your Task 6 to build API endpoints
- **Tasks 8-14** (User): Need your parsed data for query engine and routing

---

## 7. Constraints (MUST NOT DO)

❌ **No multi-language parser** - Python only for v1  
❌ **No return type extraction** - Skip for simplicity  
❌ **No >500 files** - Limit enforced by Task 1  
❌ **No JavaScript/TypeScript** - Python only  
❌ **No query engine** - That's for the User (Tasks 8-14)  

---

## 8. Data Flow

### Task 3: Parser
```
Input: /path/to/codebase (extracted ZIP or cloned repo)
  ↓
Tree-sitter parses each .py file
  ↓
Extract: functions, classes, imports, calls
  ↓
Output: parsed_code.json (nodes + edges)
```

### Task 6: Ingestion
```
Input: parsed_code.json
  ↓
Auto-select backend (TigerGraph first, SQLite fallback)
  ↓
Transform to graph format (vertices + edges)
  ↓
Bulk load into graph database
  ↓
Verify: node/edge counts, health check
  ↓
Output: Ingestion report (nodes_created, edges_created)
```

---

## 9. Acceptance Criteria (Both Tasks)

### Task 3: Parser
- [ ] Parses Python code without errors
- [ ] Extracts functions with params, docstrings
- [ ] Extracts classes with bases, methods
- [ ] Extracts imports with module and items
- [ ] Extracts function calls (caller → callee)
- [ ] Handles syntax errors gracefully
- [ ] Respects 500-file limit

### Task 6: Ingestion
- [ ] Transforms parsed code to graph format
- [ ] Loads data into TigerGraph (primary)
- [ ] Falls back to SQLite/NetworkX (on TigerGraph failure)
- [ ] Creates >=50 nodes, >=100 edges
- [ ] Verification queries pass
- [ ] Graph health check passes
- [ ] Tracks repo metadata

---

## 10. Testing Your Code

### Test Task 3: Parser
```python
from src.parser.codebase_parser import CodebaseParser

# Parse a directory
parser = CodebaseParser()
result = parser.parse_directory("/path/to/fastapi")

# Check output
print(f"Functions: {len([n for n in result['nodes'] if n['type'] == 'function'])}")
print(f"Classes: {len([n for n in result['nodes'] if n['type'] == 'class'])}")
print(f"Edges: {len(result['edges'])}")

# Save output
import json
with open('parsed_code.json', 'w') as f:
    json.dump(result, f, indent=2)
```

### Test Task 6: Ingestion
```python
from src.graph.ingestion import IngestionPipeline

# Ingest a parsed codebase
pipeline = IngestionPipeline()
report = pipeline.ingest("/path/to/fastapi")

# Check report
print(f"Nodes created: {report['nodes_created']}")
print(f"Edges created: {report['edges_created']}")
print(f"Backend used: {report['backend']}")
```

### Test with FastAPI
```bash
# Start API (after Friend 2 completes Task 7)
uvicorn src.api.main:app --reload

# Upload ZIP
curl -X POST http://localhost:8000/api/upload -F "file=@fastapi.zip"

# Clone GitHub repo
curl -X POST http://localhost:8000/api/clone -H "Content-Type: application/json" -d '{"url": "https://github.com/fastapi/fastapi"}'

# Trigger ingestion (auto-triggered by upload/clone)
# Check graph
curl http://localhost:8000/api/graph
```

---

## 11. Tree-sitter Patterns (Quick Reference)

### Function Definition
```python
# Tree-sitter query
(query "(function_definition name: (identifier) @func_name)" )

# Output
{
  "type": "function",
  "name": "authenticate",
  "params": ["username", "password"],
  ...
}
```

### Class Definition
```python
# Tree-sitter query
(query "(class_definition name: (identifier) @class_name)" )

# Output
{
  "type": "class",
  "name": "User",
  "bases": ["BaseModel"],
  ...
}
```

### Function Calls
```python
# Tree-sitter query
(query "(call function: (identifier) @func_name)" )

# Output
{
  "type": "call",
  "caller": "authenticate",
  "callee": "verify_password",
  ...
}
```

---

## 12. Timeline Estimate

| Task | Description | Estimated Time |
|------|-------------|----------------|
| 3 | Tree-sitter Parser | 2-3 days |
| 6 | Graph Ingestion Pipeline | 2-3 days |
| **Total** | | **4-6 days** |

---

## 13. Getting Help

If you get stuck:
1. **Check the main plan**: `.sisyphus/plans/codegraphx.md`
2. **Ask the project owner** (Prometheus)
3. **Tree-sitter docs**: https://tree-sitter.github.io/tree-sitter/
4. **py-tree-sitter**: https://github.com/tree-sitter/py-tree-sitter
5. **TigerGraph docs**: https://docs.tigergraph.com/

---

## 14. Final Checklist Before Starting

- [ ] Read this entire document
- [ ] Read the main plan: `.sisyphus/plans/codegraphx.md` (Tasks 3 and 6)
- [ ] Have Python 3.10+ installed
- [ ] Understand Tree-sitter v0.23+ API
- [ ] Know the output format (nodes + edges JSON)
- [ ] Understand both backends (TigerGraph and SQLite/NetworkX)

---

## 15. Collaboration Notes

### Before Starting Task 6:
- ✅ Task 1 (Friend 2) must be done - provides codebase input
- ✅ Task 3 (You) must be done - provides parsed JSON
- ✅ Task 4, 5 (Friend 2) must be done - provides graph backends

### Handoff to Friend 2 (Task 7):
Your `ingestion.py` output format must match what Task 7 expects:
```json
{
  "status": "success",
  "nodes_created": 1200,
  "edges_created": 3400,
  "backend": "tigergraph"
}
```

### Handoff to User (Tasks 8-14):
Your parsed data format (Task 3) will be used by:
- Task 8: Graph Query Engine
- Task 9: Query Classifier + Entity Recognition
- Task 12: 3-Tier Routing Engine

---

**Good luck! Build a robust parser and ingestion pipeline! 🌳**

---

*Document saved to: `.sisyphus/plans/graphmind-parser-ingestion-plan.md`*  
*Assigned to: Friend 3 (Parser & Graph Specialist)*  
*Date: May 3, 2026*
