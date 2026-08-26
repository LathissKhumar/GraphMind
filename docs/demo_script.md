# GraphMind Demo Video Script

**Total Runtime:** ~2.5-3 minutes  
**Tone:** Professional, energetic, developer-focused  
**Pacing:** Moderate, allow time for UI elements to be visible

---

## Scene 1: Ingest Codebase (0:00 - 0:30)

**[Visual: Terminal window, GraphMind CLI running]**

**Voiceover:**
"Large language models are great at reasoning about code, but they're expensive and slow when you dump an entire codebase into the context window. GraphMind takes a different approach. Let's start by ingesting a codebase."

**[Action: Type `python -m graphmind ingest --repo ./sample_repo`]**

**Voiceover:**
"We parse the repository, extract functions, classes, and their relationships, then build a knowledge graph in TigerGraph. This graph captures the structure of your code, not just the text."

**[Visual: Progress bar, nodes being created in graph visualization]**

**Voiceover:**
"In seconds, we have a queryable graph. No vectors, no embeddings, just pure code structure."

---

## Scene 2: GRAPH_ONLY Query (0:30 - 1:00)

**[Visual: Switch to GraphMind query interface]**

**Voiceover:**
"Now let's ask a question that the graph can answer directly. 'What functions call the authenticate method?'"

**[Action: Type query, select GRAPH_ONLY mode]**

**Voiceover:**
"GraphMind routes this to the GRAPH_ONLY tier. The query hits TigerGraph, traverses the call graph, and returns the answer instantly. Zero LLM tokens used. The response is fast, precise, and free."

**[Visual: Highlight "0 tokens" in response metadata, show instant response time]**

---

## Scene 3: GRAPH_RAG Query (1:00 - 1:45)

**[Visual: New query in interface]**

**Voiceover:**
"Now a harder question. 'How does the error handling work in the auth flow?' This needs context, but we don't need the full LLM treatment."

**[Action: Type query, select GRAPH_RAG mode]**

**Voiceover:**
"GraphMind uses GRAPH_RAG. It queries the graph to find relevant code nodes, pulls in just that context, and sends a focused prompt to the LLM. We're using 75% fewer tokens than dumping the whole repo, and the answer is just as good."

**[Visual: Show token count comparison - 450 tokens vs 1800 tokens for full context]**

**Voiceover:**
"The graph acts as a smart filter, giving the LLM exactly what it needs and nothing more."

---

## Scene 4: LLM_FULL Query (1:45 - 2:15)

**[Visual: Complex query input]**

**Voiceover:**
"Sometimes you need the full power of the LLM. 'Refactor the entire authentication system to use JWT tokens.' This is a LLM_FULL query."

**[Action: Select LLM_FULL mode, submit query]**

**Voiceover:**
"GraphMind routes to the full LLM pipeline. We still use graph context when available, but the LLM gets the full picture. This is the most expensive tier, but it's only used when the graph can't handle it alone."

**[Visual: Show higher token usage, complete refactoring response]**

---

## Scene 5: Evaluation Results (2:15 - 2:40)

**[Visual: Switch to evaluation dashboard]**

**Voiceover:**
"But does it work? We built an evaluation framework using LLM-as-a-Judge methodology. Here are the results across 100 code reasoning tasks."

**[Visual: Show pass rates - GRAPH_ONLY: 78%, GRAPH_RAG: 92%, LLM_FULL: 95%]**

**Voiceover:**
"GRAPH_RAG achieves 92% pass rate while using a fraction of the tokens. The judge model confirms that answer quality is preserved even with reduced context."

**[Visual: Bar chart showing token savings vs quality retention]**

---

## Scene 6: Dashboard Comparison (2:40 - 3:00)

**[Visual: Full dashboard view with 3-pipeline comparison]**

**Voiceover:**
"The dashboard gives you real-time visibility into all three pipelines. Compare token usage, latency, and accuracy side by side. GraphMind puts you in control of cost and quality."

**[Visual: Pan across dashboard, highlight key metrics]**

**Voiceover:**
"GraphMind. Smarter code reasoning through graph intelligence. Check it out on GitHub."

**[Visual: GitHub repo URL, logo animation, end screen]**

---

## Production Notes

- **Screen resolution:** 1920x1080 minimum
- **Terminal font:** Monospace, 14pt minimum for readability
- **Highlight colors:** Use yellow highlights for token counts, green for savings
- **Transitions:** Smooth fade between scenes, 0.5s duration
- **Background music:** Upbeat, tech-focused, low volume
- **Logo reveal:** Final 3 seconds, centered, with tagline
