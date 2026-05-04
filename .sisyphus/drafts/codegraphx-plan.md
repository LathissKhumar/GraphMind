# Draft: CodeGraphX - Token-Efficient Code Reasoning Engine

## Core Concept
**Product Name**: CodeGraphX: Token-Efficient Code Reasoning
**Repo**: /home/lathiss/Projects/Practice/GraphMind
**URL**: https://github.com/LathissKhumar/GraphMind.git

## Key Insight (Winning Angle)
> "Other systems make LLMs better. We make LLMs unnecessary when possible."

### Three-Layer Routing Engine:
1. **GRAPH_ONLY** → 0 tokens, deterministic answers from code graph
2. **GRAPH_RAG** → compressed structured context + LLM reasoning
3. **LLM_FULL** → full LLM only when truly needed

### Target Metrics:
| Metric | Baseline LLM | GraphRAG | CodeGraphX |
|--------|-------------|----------|------------|
| Tokens | 5000 | 1200 | **300** |
| Time | 3.2s | 1.5s | **0.6s** |
| Cost | ₹X | ₹X/3 | **₹X/10** |
| Accuracy | 78% | 88% | **89%** |

## Use Case: AI Codebase Understanding Engine
- Query: "What does function X do?" → GRAPH_ONLY (0 tokens)
- Query: "How does module A connect to module B?" → GRAPH_RAG
- Query: "How should I refactor this architecture?" → LLM_FULL

## Tech Stack Decisions (CONFIRMED)
- **Backend**: FastAPI
- **Graph**: TigerGraph Cloud (as originally suggested)
- **LLM**: OpenAI/Claude/Mistral (TBD based on cost)(Actually planning to use local Llamma 3 from ollama)
- **Frontend**: React + Chart.js (for polished dashboard)(Glassmorphic)
- **DB**: PostgreSQL (Local)(for query logs)
- **Graph parsing**: Python AST or tree-sitter (pending research results)

## Timeline: 5-day intensive build

## Research Findings

### Existing Code Knowledge Graph Projects (Landscape Analysis)

**1. code-review-graph (tirth8205)** — 5k+ stars
- **Parser**: Tree-sitter AST → graph nodes (functions, classes, imports) + edges (calls, inheritance)
- **Graph DB**: SQLite (local, zero-ops)
- **Query**: 28 MCP tools for graph traversal, blast-radius analysis, semantic search
- **Key insight**: Incremental diff-driven updates — re-parses only changed files
- **Relevance for us**: Token-efficient context via "minimal context" tool — exactly our routing concept

**2. code-graph-rag (vitali87)** — 2.3k stars
- **Parser**: Tree-sitter (12 languages, unified graph)
- **Graph DB**: Memgraph (native graph engine)
- **Query**: NL → Cypher translation via MCP, RAG pipeline with embeddings
- **Key insight**: Single graph model across all languages, enterprise-grade
- **Relevance for us**: Proves Tree-sitter + graph DB + MCP is a production pattern

**3. stakgraph (stakwork)** — 100+ stars
- **Parser**: Rust core + Tree-sitter (16 languages, framework-aware)
- **Graph DB**: Neo4j-backed with vector search
- **Query**: 19 Neo4j tools, autonomous Explore/Describe agents
- **Key insight**: Multi-repo daemon, cross-file analysis, embeddings built-in
- **Relevance for us**: Neo4j integration pattern matches our TigerGraph approach

### Parser Decision: Tree-sitter (via py-tree-sitter)
- **Why**: Fast incremental parsing, 23+ languages, designed for editor-speed
- **Alternative considered**: LibCST (preserves formatting but heavier), Python ast (stdlib but loses comments/formatting)
- **API**: `parser.parse(bytes(source, "utf8"))` + Query patterns for function/class/call extraction
- **Performance**: Handles 100+ files easily — designed for keystroke-speed parsing

### Graph Schema Design (from landscape patterns)
**Nodes**: Module, Class, Function, Import, Variable
**Edges**: defines, calls, imports, inherits, contains, depends_on
**Node ID format**: Fully-qualified (e.g., `myapp.auth.models.User`)

### Query Classification Strategy
Based on research + our smart routing concept:
1. **Factoid** (what/where/who): "What does function X do?" → GRAPH_ONLY (0 tokens)
2. **Relationship** (how/trace): "How does auth connect to the database?" → GRAPH_RAG (compressed context)
3. **Open-ended** (why/should): "How should I refactor this?" → LLM_FULL

### Demo Codebase Decision
**Build a synthetic FastAPI demo project** with deliberate complexity:
- Multiple modules (auth, api, models, services, utils)
- Cross-file function calls
- Class inheritance
- Clear domain (e.g., task management API)
This gives full control over graph demonstrations and query variety.

## Advanced Features (CONFIRMED)
**All 8 techniques from the original idea — implementing the best 5:**

### Layer 1: Token Elimination
1. **Zero-Token Answers (Graph Execution Engine)** — Deterministic graph queries return answers directly
2. **NL-to-Graph-Query** — Tiny classifier/regex converts natural language → graph query, only call LLM if it fails

### Layer 2: Compression
3. **Graph-to-Symbol Compression** — Send `[E1:Person] -[CEO]-> [E2:Company]` instead of prose text (70-90% token reduction)
4. **ID-Based Encoding** — `N12 → R5 → N87` with prompt-local dictionary mapping

### Layer 3: Smart Routing
5. **Token Budget Controller** — Every query gets a max budget, system optimizes within it (Savings Meter: "Budget: 300, Used: 42, Saved: 258")
6. **Predictive Caching** — Query pattern memory learns best strategy per type, caches answers (repeated queries = 0 cost)

### Layer 4: Advanced
7. **Speculative Execution** — Graph pre-computes likely answers while LLM generates, cancel LLM early if match found
8. **Adaptive Learning** — System logs query + best pipeline, improves routing decisions over time

### Research-Backed Techniques (from librarian findings)
- **RouteLLM pattern** (arXiv 2406.18665): 2x cost reduction via learned router
- **LLMLingua compression** (Microsoft, EMNLP'23): 20x compression with minimal loss
- **Dual-Pool Token-Budget Routing** (arXiv 2604.08075): 31-42% GPU-hours reduction
- **Speculative Decoding** (SSD/Saguaro, arXiv 2603.03251): 2x faster than baselines, 5x faster than autoregressive

## Architecture Summary
```
User Query → Query Classifier → Route Decision
    ├── GRAPH_ONLY (0 tokens) → Graph Query → Deterministic Answer
    ├── GRAPH_RAG (compressed) → Symbol Encoding → LLM with 70-90% less tokens
    └── LLM_FULL (full) → Budget-controlled generation
                        ↓
              Token Budget Controller (Savings Meter)
                        ↓
              Query Logger → Adaptive Learning (improves routing)
```

## 5-Day Build Plan Outline
- **Day 1**: Project scaffolding + synthetic demo codebase + TigerGraph Cloud setup
- **Day 2**: Multi-language code parser (Tree-sitter) → Graph builder + ingestion pipeline
- **Day 3**: Smart routing layer + query classifier + 3-tier routing engine
- **Day 4**: Advanced features (symbol compression, token budget controller, caching, speculative execution)
- **Day 5**: React dashboard + benchmark comparison + demo script + polish
