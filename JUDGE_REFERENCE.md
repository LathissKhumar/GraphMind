# GraphMind - Quick Reference for Judge

## One-Sentence Pitch
**GraphMind** is a token-efficient code reasoning engine that reduces LLM costs by 70-90% using a 3-tier routing system.

---

## Key Innovation: 3-Tier Routing

| Tier | Tokens Used | Example Query | Cost |
|------|-----------|------------|-----------|
| **GRAPH_ONLY** | 0 | "What functions call authenticate?" | FREE |
| **GRAPH_RAG** | <500 | "How is User class connected to database?" | Low |
| **LLM_FULL** | >500 | "Explain the authentication flow comprehensively" | Standard |

---

## What Makes Us Different (vs Competitors)

**Neither Ruflo nor GitNexus have:**
- ✅ Zero-token answers (our key differentiator!)
- ✅ Token budget controller
- ✅ Visible savings meter with dollar cost

---

## Tech Stack (Why Each)

| Component | Choice | Why |
|-----------|--------|-----|
| **LLM** | GitHub Models (gpt-4o-mini) | Free tier (no API costs!) |
| **Graph DB** | TigerGraph Savanna | Hackathon sponsor, stable |
| **Parser** | Tree-sitter | Industry standard, accurate |
| **Python package manager** | uv | 10x faster than pip |
| **Frontend package manager** | pnpm | Faster than npm |
| **Frontend** | React + Vite | Fast development |
| **Visualization** | Cytoscape.js | Interactive graphs |
| **Charts** | Chart.js | Metrics display |

---

## Architecture Flow

```
User Query → Query Classifier → [Budget Check] → Route to Tier
                                                      ↓
                    ┌─────────────────────┬──────────────────┐
                    ↓                    ↓                  ↓
            GRAPH_ONLY           GRAPH_RAG           LLM_FULL
            (0 tokens)           (<500 tokens)        (>500 tokens)
                    ↓                    ↓                  ↓
            Zero-Token          Compressed         Full LLM
            Generator          Context           Generation
```

---

## 9 API Endpoints

1. `POST /api/upload` - Upload ZIP file
2. `POST /api/clone` - Clone GitHub repo
3. `POST /api/ingest` - Parse + ingest to graph
4. `POST /api/query` - Submit query (returns answer + tier)
5. `GET /api/health` - System health check
6. `GET /api/metrics` - Token usage statistics
7. `GET /api/graph` - Cytoscape graph JSON
8. `GET /api/query-history` - Past queries
9. `POST /api/budget` - Set token budget

---

## Demo Commands

```bash
# Setup
uv venv
uv pip install -r requirements.txt

# Run
make dev              # Backend at localhost:8000
make dashboard       # Frontend at localhost:5173

# Full demo
./scripts/demo.sh    # Auto-clones fastapi/fastapi
```

---

## Team (4 People)

| Person | Role |
|--------|------|
| User (Prometheus) | AI/RAG/LLM Engine |
| Friend 1 | Frontend Dashboard |
| Friend 2 | Backend API |
| Friend 3 | Parser + Ingestion |

---

## Success Metrics

- [ ] 70-90% token reduction achieved
- [ ] Zero-token answers for factoid queries
- [ ] Demo runs end-to-end without errors

---

**For detailed architecture, see `ARCHITECTURE.md`**