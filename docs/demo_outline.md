# GraphMind Demo Video Production Outline

## Pre-Production Checklist

### Demo Dataset
Use the `sample_repo/` directory (or create a small Python web app with auth, database, and API layers):
- **Repository:** Flask-based REST API with authentication module
- **Size:** ~15-20 Python files, ~2000 lines of code total
- **Key components to highlight:**
  - `auth.py` - Authentication logic (login, token verification)
  - `api.py` - REST endpoints
  - `models.py` - Database models
  - `utils.py` - Helper functions
  - `config.py` - Configuration management

This size is large enough to show graph benefits but small enough to display clearly on screen.

---

## Screen Recordings Needed

### Recording 1: Codebase Ingestion (Scene 1)
- **Tool:** SimpleScreenRecorder or OBS Studio
- **Resolution:** 1920x1080
- **Frame rate:** 60 fps
- **Audio:** None (voiceover added in post)
- **Actions to capture:**
  1. Terminal window, navigate to GraphMind directory
  2. Run `python -m graphmind ingest --repo ./sample_repo`
  3. Show progress output (parse files, create nodes, build edges)
  4. Switch to TigerGraph GraphStudio or graph visualization
  5. Show node count, edge relationships forming

### Recording 2: Query Interface - All Three Modes (Scenes 2-4)
- **Tool:** OBS Studio with browser source for UI
- **Resolution:** 1920x1080
- **Actions to capture:**
  1. Open GraphMind query interface (dashboard)
  2. Scene 2: Type "What functions call the authenticate method?" → Select GRAPH_ONLY → Submit
  3. Show instant response, highlight "0 tokens" badge
  4. Scene 3: Type "How does error handling work in auth flow?" → Select GRAPH_RAG → Submit
  5. Show token count (450 tokens) vs baseline (1800 tokens)
  6. Scene 4: Type "Refactor auth to use JWT" → Select LLM_FULL → Submit
  7. Show full response with higher token usage

### Recording 3: Evaluation Dashboard (Scene 5)
- **Tool:** OBS Studio
- **Actions to capture:**
  1. Navigate to evaluation results page
  2. Show pass rate table: GRAPH_ONLY (78%), GRAPH_RAG (92%), LLM_FULL (95%)
  3. Show token savings chart (bar chart, 75% reduction for GRAPH_RAG)
  4. Show LLM-as-a-Judge confidence scores

### Recording 4: Pipeline Comparison Dashboard (Scene 6)
- **Tool:** OBS Studio
- **Actions to capture:**
  1. Full dashboard view with all three pipelines visible
  2. Pan across metrics: latency, token usage, accuracy
  3. Highlight cost comparison ($0.02 vs $0.15 per query)
  4. End with GitHub repo link and logo

---

## Voiceover Script (Full Transcript)

### Scene 1 (0:00 - 0:30)
"Large language models are great at reasoning about code, but they're expensive and slow when you dump an entire codebase into the context window. GraphMind takes a different approach. Let's start by ingesting a codebase. We parse the repository, extract functions, classes, and their relationships, then build a knowledge graph in TigerGraph. This graph captures the structure of your code, not just the text. In seconds, we have a queryable graph. No vectors, no embeddings, just pure code structure."

### Scene 2 (0:30 - 1:00)
"Now let's ask a question that the graph can answer directly. What functions call the authenticate method? GraphMind routes this to the GRAPH_ONLY tier. The query hits TigerGraph, traverses the call graph, and returns the answer instantly. Zero LLM tokens used. The response is fast, precise, and free."

### Scene 3 (1:00 - 1:45)
"Now a harder question. How does the error handling work in the auth flow? This needs context, but we don't need the full LLM treatment. GraphMind uses GRAPH_RAG. It queries the graph to find relevant code nodes, pulls in just that context, and sends a focused prompt to the LLM. We're using 75% fewer tokens than dumping the whole repo, and the answer is just as good. The graph acts as a smart filter, giving the LLM exactly what it needs and nothing more."

### Scene 4 (1:45 - 2:15)
"Sometimes you need the full power of the LLM. Refactor the entire authentication system to use JWT tokens. This is a LLM_FULL query. GraphMind routes to the full LLM pipeline. We still use graph context when available, but the LLM gets the full picture. This is the most expensive tier, but it's only used when the graph can't handle it alone."

### Scene 5 (2:15 - 2:40)
"But does it work? We built an evaluation framework using LLM-as-a-Judge methodology. Here are the results across 100 code reasoning tasks. GRAPH_RAG achieves 92% pass rate while using a fraction of the tokens. The judge model confirms that answer quality is preserved even with reduced context."

### Scene 6 (2:40 - 3:00)
"The dashboard gives you real-time visibility into all three pipelines. Compare token usage, latency, and accuracy side by side. GraphMind puts you in control of cost and quality. GraphMind. Smarter code reasoning through graph intelligence. Check it out on GitHub."

---

## Production Notes

### Equipment
- **Microphone:** Blue Yeti or equivalent (record voiceover in quiet room)
- **Screen capture:** OBS Studio with display capture
- **Editing software:** DaVinci Resolve (free) or Adobe Premiere Pro

### Visual Style
- **Color palette:** Dark mode UI, GraphMind brand colors (blue/purple gradient)
- **Font:** Inter or Roboto for overlays, monospace for code/terminal
- **Animations:** Subtle fade transitions, no flashy effects
- **Highlight style:** Yellow box shadows for important numbers (token counts, savings)

### Audio
- **Background music:** "Tech Corporate" or "Upbeat Electronic" (copyright-free from YouTube Audio Library)
- **Volume levels:** Voiceover at -3dB, music at -18dB
- **Silence removal:** Cut dead air between sentences

### Post-Production Timeline
1. **Day 1:** Record all screen captures (2 hours)
2. **Day 2:** Record voiceover, sync with visuals (3 hours)
3. **Day 3:** Edit, add music, export (4 hours)
4. **Day 4:** Review, iterate based on feedback (2 hours)

---

## Final Call-to-Action

### End Screen Elements
- **Logo:** GraphMind logo centered
- **Tagline:** "Smarter code reasoning through graph intelligence"
- **GitHub URL:** `github.com/yourusername/GraphMind`
- **QR Code:** Links to GitHub repo (generate at qr-code-generator.com)
- **Duration:** 5 seconds static, then fade to black

### Social Media Snippets
Extract these 30-second clips for social media:
1. **"Zero tokens" clip** - Scene 2 GRAPH_ONLY response (great for Twitter/X)
2. **"75% savings" clip** - Scene 3 token comparison (great for LinkedIn)
3. **"92% pass rate" clip** - Scene 5 evaluation results (great for tech blogs)

### Distribution
- **Primary:** YouTube (full 3-minute video)
- **Secondary:** LinkedIn (75% savings clip)
- **Secondary:** Twitter/X (zero tokens clip)
- **Embed:** GraphMind GitHub README
