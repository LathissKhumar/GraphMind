# GraphMind Interview FAQ

Quick reference for interviews, demos, and presentations. Each answer is 2-3 sentences, designed to be clear and memorable.

---

## Why 3-tier routing?

The 3-tier architecture matches query complexity to the appropriate level of LLM involvement, avoiding the one-size-fits-all trap. Most code questions are structural or need only local context, so GRAPH_ONLY and GRAPH_RAG handle 85% of queries at a fraction of the cost. LLM_FULL exists for genuinely complex tasks, ensuring we never sacrifice quality when it truly matters.

---

## How do you evaluate quality?

We use an LLM-as-a-Judge framework where GPT-4 scores answers on correctness, completeness, and clarity across 100 diverse code reasoning questions. GRAPH_RAG achieves a 92% pass rate compared to 95% for LLM_FULL, proving that graph-guided context preserves answer quality. The judge provides consistent, scalable evaluation without the need for expensive human-labeled ground truth datasets.

---

## What about latency?

GRAPH_ONLY queries return in 50-100ms since they are pure graph traversals with no LLM involvement. GRAPH_RAG adds 2-4 seconds for the focused LLM call, while LLM_FULL takes 8-15 seconds due to larger context windows. The latency tradeoff is intentional: faster responses for simpler queries, deeper reasoning time for complex ones.

---

## Why TigerGraph?

TigerGraph provides native parallel graph processing and excels at deep traversals, which are essential when tracing call paths across thousands of functions. Its REST API integrates cleanly with Python, and the performance scales well as the knowledge graph grows to tens of thousands of nodes. We evaluated Neo4j and others, but TigerGraph's speed on multi-hop traversals made it the clear choice for real-time code queries.

---

## Additional Questions

### How does GraphMind handle code changes?

The system supports incremental updates through a watch mode that re-parses changed files and updates graph nodes without full re-ingestion. This keeps the knowledge graph fresh with minimal overhead, making it practical for active development environments.

### What languages are supported?

Currently Python is fully supported through tree-sitter parsing, with JavaScript, Go, and Java on the roadmap. The graph schema is language-agnostic, so adding new languages primarily involves configuring the appropriate tree-sitter grammar and mapping AST nodes to graph entities.

### How do you prevent graph context from being too narrow?

The GRAPH_RAG tier uses configurable traversal depth and includes caller/callee relationships, ensuring sufficient context for meaningful answers. We also rank gathered nodes by relevance to the query, so the most important code always makes it into the LLM context window.
