# GraphMind Architecture Decision Record (ADR)

## Project: GraphMind - Token-Efficient Code Reasoning Engine

**Date**: May 4, 2026  
**Status**: In Development

---

## 1. Core Architecture

### Why We Build This
Traditional LLM code analysis uses thousands of tokens per query, making it expensive and slow. GraphMind uses a **3-tier routing system** to minimize token usage by 70-90% while maintaining accuracy.

### The 3-Tier Routing System

| Tier | Token Usage | Use Case | Cost |
|------|-----------|---------|-------|
| **GRAPH_ONLY** | 0 tokens | Simple facts (function names, line numbers) | Free |
| **GRAPH_RAG** | <500 tokens | Relationships (call graphs, imports) | Low |
| **LLM_FULL** | >500 tokens | Complex analysis | Standard |

---

## 2. Technology Choices

### 2.1 LLM Provider: GitHub Models (NOT OpenRouter)

**Decision**: Use GitHub Models free inference tier

**Reason**:
- OpenRouter costs money per token
- GitHub Models offers free chat completions (150 req/day, 15 req/min)
- Uses existing `gh` authentication — no separate API key needed
- No API billing required for hackathon demo
- Model available: `openai/gpt-4o-mini` (fast, reliable JSON output)

**Why not HuggingFace?**
- v1 used HuggingFace Inference API, but the new provider routing system (huggingface_hub >=1.12) requires manual provider configuration at hf.co/settings/inference-providers
- GitHub Models works out of the box with `gh auth token`
- HuggingFace client removed entirely in v2 — GitHub Models alone sufficed for 100% of evaluation runs

### 2.2 Graph Database: TigerGraph Savanna (NOT Classic)

**Decision**: Use TigerGraph Cloud Savanna tier

**Reason**:
- **Savanna**: Free trial with credits valid 1 year, usage-based pricing
- **Classic**: Auto-stops after 1 hour of inactivity = demo dies mid-presentation!
- More stable for live demos

**Alternative Considered**: SQLite/NetworkX only
- Rejected - TigerGraph is the hackathon sponsor
- NetworkX kept as fallback for offline/demo reliability

### 2.3 Package Manager: uv (NOT pip)

**Decision**: Use uv for Python

**Reason**:
- 10-100x faster than pip
- Better dependency resolution
- Cleaner output

**Installation**:
```bash
uv venv
uv pip install -r requirements.txt
```

### 2.4 Frontend Package Manager: pnpm (NOT npm)

**Decision**: Use pnpm for React dashboard

**Reason**:
- Faster than npm
- Better disk space usage
- More reliable installs

**Installation**:
```bash
cd dashboard && pnpm install
```

---

## 3. Code Parsing

### 3.1 Parser: Tree-sitter (NOT AST)

**Decision**: Use Tree-sitter for Python parsing

**Reason**:
- Language-agnostic (supports 40+ languages)
- Faster than python-ast
- More accurate for incomplete code
- Industry standard (used by GitHub, Stripe)

**Scope**: Python only for v1
- JavaScript/TypeScript parsing deferred

---

## 4. Query Classification

### 4.1 ML-Based Classifier (NOT Rule-Based)

**Decision**: Use sentence-transformers for query classification

**Reason**:
- Rule-based too simple for open-source quality
- Neural embeddings capture query complexity
- Two-stage: fast heuristic (sub-1ms) + neural (10ms)
- Pluggable architecture

**Stage 1: Heuristic Filter**
- Query length
- Keywords ("how is", "connected" → GRAPH_ONLY)
- Code density (backticks, function def → LLM_FULL)

**Stage 2: Neural Classification**
- Embedding: all-MiniLM-L6-v2
- Complexity scoring
- Route: <0.3 → GRAPH_ONLY, <0.7 → GRAPG_RAG, >=0.7 → LLM_FULL

---

## 5. Zero-Token Generation

### 5.1 3-Layer Architecture (KEY DIFFERENTIATOR)

**Decision**: Build zero-LLM answer generator

**Reason**:
- Judges love zero-API-cost approaches
- Competitors (Ruflo, GitNexus) don't have this
- Extensible for open-source community

**Layer 1: Jinja2 Templates**
```python
TEMPLATES = {
    "function_definition": "Function `{name}` is defined at line {line} in {file}",
    "class_hierarchy": "Class `{name}` inherits from `{parent}`",
}
```

**Layer 2: pySimpleNLG**
- Grammar (plurals, tenses)
- "1 person" vs "2 people"

**Layer 3: LLM-as-Compiler (optional)**
- Use LLM once to write rules
- Rules run forever without API calls

---

## 6. Input Handling

### 6.1 GitHub Clone + ZIP Upload

**Decision**: Support both GitHub URL and ZIP file

**Reason**:
- Flexibility for different demo scenarios
- ZIP for offline/large repos
- GitHub for real-time cloning

**Limits**:
- 500 files max
- 10MB ZIP size limit
- Public repos only (v1)

### 6.2 Language Detection: Pygments

**Decision**: Use Pygments lexer for language detection

**Reason**:
- Industry-standard (used by GitHub, Read the Docs, PyPI)
- Detects 300+ languages automatically
- More accurate than file extension matching
- Handles unknown file types gracefully

**Implementation**:
```python
from pygments.lexers import get_lexer_by_filename, guess_lexer_for_filename

# Try by filename first (fast)
lexer = get_lexer_by_filename(f)
# Fallback: guess from content (for ambiguous files)
lexer = guess_lexer_for_filename(f, content)
```

**Supported Languages** (partial list):
- Python, JavaScript, TypeScript, Go, Rust, Java, C++, Ruby, PHP, Swift, Kotlin, Scala

---

## 7. Error Handling

### 7.1 Multi-Tier Fallback Chain

**Decision**: Implement fallback chain for production-grade reliability

**Chain**:
1. **Primary**: GitHub Models `openai/gpt-4o-mini`
2. **Fallback**: GRAPH_ONLY (zero-token)
3. **Final**: Graceful error message

**Error Types**:
- RATE_LIMIT (429) → retry with backoff
- OVERLOAD (503/502) → skip immediately
- TIMEOUT → skip to next provider
- CONTEXT (400) → skip to larger model

### 7.2 Circuit Breaker

**Decision**: Trip after 5 failures in 60 seconds

**Reason**:
- Prevent cascade failures
- Auto-recovery probe every 30 seconds

---

## 8. Budget Controller

### 8.1 Token Budget with Downgrade Rules

**Decision**: Implement budget enforcement with automatic downgrades

**Rules**:
- Budget <25% remaining → Force GRAPH_RAG
- Budget <10% remaining → Force GRAPH_ONLY

**Dashboard Display**:
```
Budget: $5.00 | Used: $0.42 | Saved: $4.58
```

---

## 9. Caching & Learning

### 9.1 Predictive Caching

**Decision**: Cache repeated queries

**Storage**: SQLite with WAL mode
- Cache hit = 0 new tokens
- 1 hour TTL or re-ingestion invalidation

### 9.2 Adaptive Learning

**Decision**: Self-improving router

**Mechanism**:
- Log predicted vs actual tier
- After 10+ same-pattern queries: auto-adjust thresholds
- No ML model - rule-based only

---

## 10. File Structure

```
GraphMind/
├── src/
│   ├── api/              # FastAPI endpoints (9 total)
│   ├── input/            # GitHub/ZIP loading
│   ├── graph/            # TigerGraph + SQLite
│   ├── router/          # Query routing (3-tier)
│   ├── parser/           # Tree-sitter
│   └── llm/             # GitHub Models + OpenRouter clients
├── dashboard/           # React + Cytoscape + Chart.js
├── benchmarks/          # Benchmark scripts
├── scripts/              # Demo scripts
├── tests/               # Test files
├── pyproject.toml        # Python config
├── Makefile             # Build commands
├── .env.example        # Environment template
└── requirements.txt    # Dependencies
```

---

## 11. API Endpoints (9 Total)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/upload | POST | ZIP file upload |
| /api/clone | POST | GitHub clone |
| /api/ingest | POST | Trigger ingestion |
| /api/query | POST | Submit query |
| /api/health | GET | System health |
| /api/metrics | GET | Token usage |
| /api/graph | GET | Cytoscape JSON |
| /api/query-history | GET | Query history |
| /api/budget | POST | Set budget |

---

## 12. Competition Analysis

### vs Ruflo (37.2K GitHub stars)
| Feature | Ruflo | GraphMind |
|--------|------|----------|
| Zero-token answers | ❌ | ✅ |
| Token budget | ❌ | ✅ |
| Savings meter | ❌ | ✅ |
| Free tier | Limited | Free |

### vs GitNexus (34.9K GitHub stars)
| Feature | GitNexus | GraphMind |
|---------|---------|----------|
| Zero-token answers | ❌ | ✅ |
| 3-tier routing | ❌ | ✅ |
| Graph visualization | ❌ | ✅ |

**Our Key Differentiator**: Zero-token answers (neither competitor has this!)

---

## 13. Dependencies Summary

### Core (Required)
```
fastapi>=0.115.0        # Web framework
uvicorn>=0.32.0         # ASGI server
pydantic>=2.9.0        # Data validation
tree-sitter>=0.23.0      # Code parsing
gitpython>=3.1.0         # Git integration
tiktoken>=0.8.0         # Token counting
jinja2>=3.1.0           # Template engine
httpx>=0.27.0           # HTTP client
# huggingface-hub removed — HF client deleted in v2
requests>=2.31.0        # HTTP client (GitHub Models)
pygments>=2.17.0         # Language detection (300+ languages)
```

### ML (Optional - for advanced classifier)
```
sentence-transformers>=3.0.0
```

### Frontend (dashboard/)
```
react>=18.0.0
vite>=5.0.0
chart.js>=4.0.0
react-chartjs-2>=5.0.0
cytoscape>=3.30.0
```

---

## 14. Build Commands

```bash
# Python setup
uv venv
uv pip install -r requirements.txt
uv pip install -e .

# Development
make dev              # Start FastAPI server
make dashboard        # Start React frontend
make ingest          # Run ingestion
make benchmark      # Run benchmarks
make test            # Run tests

# Demo
./scripts/demo.sh    # Auto-clone fastapi/fastapi + demo
```

---

## 15. Open-Source Readiness

### Why This Will Be Successful as Open-Source

1. **Pluggable architecture** - Easy to swap components
2. **Good documentation** - Clear ADRs and comments
3. **Testable** - pytest with async support
4. **No vendor lock-in** - GitHub Models + OpenRouter
5. **Extensible** - Template registry, custom classifiers

### License
- MIT License (permissive, open-source friendly)

---

## 16. Team Division

| Person | Role | Tasks |
|--------|------|-------|
| Prometheus (User) | AI/RAG/LLM Engine | Tasks 8-14 |
| Friend 1 | Frontend | Tasks 15, 19 |
| Friend 2 | Backend | Tasks 1,2,4,5,7 |
| Friend 3 | Parser | Tasks 3,6 |

---

## 17. Execution Plan

### Sequential (STRICT)
```
Phase 1: Task 1 → 2 → 3 → 4 → 5
Phase 2: Task 6 → 7 → 8 → 9 → 10
Phase 3: Task 11 → 12 → 13 → 14 → 15
Phase 4: Task 16 → 17 → 18 → 19 → 20 → 21
```

Each task blocks until user verifies.

---

## 18. Success Criteria

- [ ] 70-90% token reduction vs baseline
- [ ] Zero-token answers for factoid queries
- [ ] Token budget with downgrade rules
- [ ] Demo runs end-to-end
- [ ] 7 benchmark queries pass

---

**Document Version**: 1.0  
**Last Updated**: May 4, 2026