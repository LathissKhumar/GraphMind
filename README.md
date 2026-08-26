# GraphMind [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-0100E7.svg)](https://fastapi.tiangolo.com/)

> **Token-Efficient Code Reasoning Engine** – 70-90% token reduction via 3-tier routing (Graph-only → Graph-RAG → LLM-Full)

---

## 📖 Overview

**GraphMind** is a code analysis engine that dramatically reduces LLM token consumption while maintaining accuracy. It uses a **3-tier routing system** to serve queries with zero tokens for simple facts, <500 tokens for relationships, and standard LLM usage only for complex analysis.

**Key Differentiator**: Unlike competitors (Ruflo, GitNexus), GraphMind provides **zero-token answers** for factoid queries by using a predictive tier router and zero-token generation layers (Jinja2 templates + pySimpleNLG).

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **3-Tier Routing** | GRAPH_ONLY (0 tokens) → GRAPH_RAG (<500 tokens) → LLM_FULL (>500 tokens) |
| **Zero-Token Answers** | Jinja2 templates + pySimpleNLG for factoid queries without API calls |
| **Token Budget Controller** | Automatic downgrade rules: <25% → GRAPH_RAG, <10% → GRAPH_ONLY |
| **Multi-Tier Error Handling** | Circuit breaker, rate-limit retry, provider fallback chain |
| **Predictive Caching** | SQLite WAL-mode cache: hit = 0 new tokens |
| **Adaptive Learning** | Rule-based threshold adjustment after 10+ same-pattern queries |
| **Dual Code Parsing** | Tree-sitter for Python (v1), with language-agnostic foundation |
| **GitHub + ZIP Upload** | Clone repos or upload ZIP files (500 files max, 10MB limit) |
| **Cytoscape Visualization** | Interactive graph graphs via React dashboard |
| **HuggingFace-First** | Free inference endpoints (Qwen2.5-Coder, Gemma-2) |

---

## 🚀 Quick Start

```bash
# 1. Clone & setup
uv venv
uv pip install -r requirements.txt
uv pip install -e .

# 2. Environment
cp .env.example .env
# Edit .env with your TigerGraph + HuggingFace credentials

# 3. Run development
make dev          # FastAPI server (http://localhost:8000)
make dashboard    # React frontend (http://localhost:5173)

# 4. Demo
./scripts/demo.sh  # Auto-clone fastapi/fastapi + demo
```

---

## 🏗️ Architecture

### 3-Tier Routing System

| Tier | Token Usage | Use Case | Cost |
|------|-------------|----------|------|
| **GRAPH_ONLY** | 0 tokens | Simple facts (function names, line numbers) | Free |
| **GRAPH_RAG** | <500 tokens | Relationships (call graphs, imports) | Low |
| **LLM_FULL** | >500 tokens | Complex analysis | Standard |

### Error Handling Chain

1. **Primary**: HuggingFace Qwen2.5-Coder
2. **Fallback 1**: HuggingFace Gemma-2
3. **Fallback 2**: GRAPH_ONLY (zero-token)
4. **Final**: Graceful error message

### Circuit Breaker

- Trip after 5 failures in 60 seconds
- Auto-recovery probe every 30 seconds

### Budget Controller

- Budget <25% remaining → Force GRAPH_RAG
- Budget <10% remaining → Force GRAPH_ONLY

---

## 📦 Installation

### Python Setup

```bash
uv venv
uv pip install -r requirements.txt
uv pip install -e .
```

### Dependencies (Core)

```text
fastapi>=0.115.0        # Web framework
uvicorn>=0.32.0         # ASGI server
pydantic>=2.9.0        # Data validation
tree-sitter>=0.23.0      # Code parsing
gitpython>=3.1.0         # Git integration
tiktoken>=0.8.0         # Token counting
jinja2>=3.1.0           # Template engine
httpx>=0.27.0           # HTTP client
huggingface-hub>=0.20.0 # LLM access
```

### ML (Optional)

```text
sentence-transformers>=3.0.0  # Advanced classifier
```

### Frontend (dashboard/)

```text
react>=18.0.0
vite>=5.0.0
chart.js>=4.0.0
react-chartjs-2>=5.0.0
cytoscape>=3.30.0
```

---

## 🔌 API Endpoints (9 Total)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload` | POST | ZIP file upload |
| `/api/clone` | POST | GitHub clone |
| `/api/ingest` | POST | Trigger ingestion |
| `/api/query` | POST | Submit query |
| `/api/health` | GET | System health |
| `/api/metrics` | GET | Token usage |
| `/api/graph` | GET | Cytoscape JSON |
| `/api/query-history` | GET | Query history |
| `/api/budget` | POST | Set budget |

---

## 📁 Project Structure

```
GraphMind/
├── src/
│   ├── api/              # FastAPI endpoints (9 total)
│   ├── input/            # GitHub/ZIP loading
│   ├── graph/            # TigerGraph + SQLite
│   ├── router/           # Query routing (3-tier)
│   ├── parser/           # Tree-sitter
│   └── llm/             # HuggingFace client
├── dashboard/           # React + Cytoscape + Chart.js
├── benchmarks/          # Benchmark scripts
├── scripts/             # Demo scripts
├── tests/               # Test files
├── pyproject.toml        # Python config
├── Makefile             # Build commands
├── .env.example        # Environment template
└── requirements.txt    # Dependencies
```

---

## 🏆 Competition Analysis

| Feature | Ruflo (37.2K stars) | GraphNexus (34.9K stars) | GraphMind |
|---------|---------------------|--------------------------|-----------|
| Zero-token answers | ❌ | ❌ | ✅ |
| Token budget | ❌ | ❌ | ✅ |
| Savings meter | ❌ | ❌ | ✅ |
| Free tier | Limited | Limited | **Free** |

**Our Key Differentiator**: Zero-token answers (neither competitor has this!)

---

## 📄 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 👥 Team Division

| Person | Role | Tasks |
|--------|------|-------|
| Prometheus (User) | AI/RAG/LLM Engine | Tasks 8-14 |
| Friend 1 | Frontend | Tasks 15, 19 |
| Friend 2 | Backend | Tasks 1,2,4,5,7 |
| Friend 3 | Parser | Tasks 3,6 |

---

## 📈 Success Criteria

- [ ] 70-90% token reduction vs baseline
- [ ] Zero-token answers for factoid queries
- [ ] Token budget with downgrade rules
- [ ] Demo runs end-to-end
- [ ] 7 benchmark queries pass

---

**Document Version**: 1.0  
**Last Updated**: August 26, 2026

---