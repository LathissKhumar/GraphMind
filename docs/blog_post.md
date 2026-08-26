# GraphMind: Cutting LLM Costs by 75% with Graph-Based Code Reasoning

When we started building GraphMind, we had a simple observation. Developers were spending a fortune on LLM API calls just to answer questions about their own codebases. The pattern was always the same: dump the entire repository into the context window, pay for thousands of tokens, wait for a slow response, and hope the model didn't hallucinate.

We thought there had to be a better way. What if, instead of treating code as raw text to be stuffed into a prompt, we treated it as a structured graph that could be queried intelligently?

That question led us to build GraphMind, a 3-tier routing system that cuts LLM token usage by up to 75% while maintaining answer quality. Here is how we built it, how we measure success, and what we learned along the way.

## The Problem: Token Waste in LLM Code Reasoning

Large language models have transformed how developers interact with code. We ask them to explain functions, find bugs, suggest refactors, and trace execution flows. But there is a hidden cost that most teams overlook.

Consider a typical scenario. A developer wants to understand how authentication works in their codebase. They open their favorite AI coding assistant and ask, "How does the auth flow work in this project?" The assistant, having no structural understanding of the code, does the only thing it can. It reads everything. Every file. Every function. Every class.

For a medium-sized repository of 50,000 lines, that is roughly 15,000-20,000 tokens per query. At GPT-4 pricing, that is about $0.30 per question. Ask ten questions a day, and you are looking at $3 daily, $90 monthly, per developer. Scale that to a team of twenty, and the bill becomes hard to justify.

But the cost is not just financial. There is latency. A 20,000-token context window means slower responses, higher chance of truncation, and increased likelihood that the model loses focus amid the noise.

The core issue is that we are using a sledgehammer to crack a nut. Most code reasoning questions do not need the entire codebase. They need specific functions, their callers, and maybe a few related modules. The rest is distraction.

We looked at existing solutions and found them lacking. Vector databases help with semantic search, but they lose the structural relationships that make code unique. A function call is not just a semantic similarity, it is a directed edge in a graph. An inheritance relationship is not a vector distance, it is a hierarchy.

We needed a system that understood code as code, not as text.

## The Solution: 3-Tier Routing Architecture

GraphMind solves this with a routing architecture that matches query complexity to the appropriate level of LLM involvement. Instead of a one-size-fits-all approach, we route each query through one of three tiers.

**Tier 1: GRAPH_ONLY** handles queries that the knowledge graph can answer directly. Questions like "What functions call authenticate?" or "Show me all subclasses of BaseController" are pure graph traversals. No LLM needed. Zero tokens. Instant response.

**Tier 2: GRAPH_RAG** handles queries that need explanation or synthesis but do not require the full LLM reasoning engine. We query the graph to gather relevant context, then pass only that focused context to the LLM. This is where we see the 75% token savings. The graph acts as a smart filter, giving the LLM exactly what it needs.

**Tier 3: LLM_FULL** is the fallback for queries that genuinely need deep reasoning, complex refactoring, or creative synthesis. Even here, we use graph context to prime the LLM, but we allow for larger context windows and more intensive reasoning.

The routing decision happens in our `RoutingEngine`, which analyzes the query intent, checks graph coverage, and selects the appropriate tier. Here is a simplified version of how it works:

```python
class RoutingEngine:
    def route(self, query: str, graph_context: dict) -> RoutingDecision:
        # Check if query is graph-navigable
        if self._is_graph_query(query):
            if self._graph_has_answer(query, graph_context):
                return RoutingDecision(tier=RoutingTier.GRAPH_ONLY)
        
        # Check if graph can provide sufficient context
        relevant_nodes = self._query_graph_for_context(query)
        if self._context_sufficient(relevant_nodes, query):
            return RoutingDecision(
                tier=RoutingTier.GRAPH_RAG,
                context=relevant_nodes
            )
        
        # Fall back to full LLM
        return RoutingDecision(tier=RoutingTier.LLM_FULL)
```

The key insight is that most queries fall into Tier 1 or 2. In our testing, only about 15% of queries need the full LLM treatment. That means 85% of the time, we are saving tokens, reducing latency, or both.

## Implementation: How It Works

### Building the Knowledge Graph

The foundation of GraphMind is a code knowledge graph stored in TigerGraph. We chose TigerGraph over alternatives like Neo4j because of its native parallel graph processing and strong performance on deep traversals, which matter when you are tracing call paths across thousands of functions.

The ingestion pipeline works in three stages:

1. **Parsing:** We use tree-sitter to parse source files into ASTs. This gives us precise function boundaries, class definitions, import statements, and call expressions.

2. **Node extraction:** We extract entities (functions, classes, methods, variables) and their metadata (parameters, return types, docstrings). Each becomes a node in the graph.

3. **Edge creation:** We create relationships between nodes. Call edges connect a function to the functions it calls. Inheritance edges connect classes to their parents. Import edges connect modules to their dependencies.

Here is what the graph schema looks like in practice:

```python
# Node types
FunctionNode: {name, file_path, start_line, end_line, params, docstring}
ClassNode: {name, file_path, start_line, end_line, base_classes}
ModuleNode: {path, language, last_modified}

# Edge types
CALLS: Function -> Function (represents a function call)
INHERITS: Class -> Class (represents inheritance)
IMPORTS: Module -> Module (represents import dependency)
DEFINED_IN: Function/Class -> Module (location relationship)
```

After ingestion, a typical Python web application with 200 functions and 50 classes might have 300 nodes and 800+ edges. That graph becomes queryable in milliseconds.

### Query Processing

When a query arrives, the system processes it through the routing engine. Let us trace a GRAPH_RAG query end to end.

The user asks, "How does error handling work in the auth flow?"

First, the router identifies that this needs context beyond pure graph traversal. It sends a graph query to find nodes related to "auth" and "error handling." TigerGraph returns the relevant functions, their callers, and any exception handling they contain.

The system then constructs a focused prompt:

```
Context from code graph:
- Function: authenticate (auth.py:45)
  Handles login attempts, raises AuthenticationError on failure
- Function: handle_auth_error (auth.py:120)
  Catches AuthenticationError, returns 401 response
- Function: login_view (views.py:30)
  Calls authenticate, wraps in try/except block

Query: How does error handling work in the auth flow?

Based on the above context, provide a concise explanation.
```

Notice what is missing. We did not include the database models, the template renderers, or the utility functions. The graph told us what was relevant, and we sent only that. The LLM receives perhaps 400 tokens instead of 15,000.

### TigerGraph Integration

We use TigerGraph's REST API to execute graph queries. For the GRAPH_ONLY tier, queries are simple traversals:

```python
def find_callers(self, function_name: str) -> List[str]:
    query = """
    INTERPRET QUERY (
        FOR v IN FunctionVertex
        FILTER v.name == "{}"
        FOR u IN 1..2 INBOUND v CALLS
        RETURN u.name
    )
    """.format(function_name)
    return self.conn.runQuery("graphmind", query)
```

For GRAPH_RAG context gathering, we use broader traversal patterns to collect related nodes, then rank them by relevance to the query using a lightweight scoring function.

## Evaluation: LLM-as-a-Judge Methodology

Building a system like GraphMind raises a difficult question. How do you measure success? Token savings are easy to count, but what about answer quality? Does a GRAPH_RAG answer actually satisfy the user, or are we saving money at the cost of accuracy?

We adopted an LLM-as-a-Judge evaluation framework. The idea is straightforward: use a strong LLM (GPT-4) to evaluate the quality of answers produced by different tiers of our system.

Our evaluation dataset consists of 100 code reasoning questions across three categories:

- **Structural (30 questions):** "What calls X?", "Show inheritance hierarchy for Y?"
- **Explanatory (50 questions):** "How does X work?", "Why does Y behave this way?"
- **Creative (20 questions):** "Refactor X to use Y pattern", "Add feature Z to module W"

For each question, we generate answers from all three tiers, then have GPT-4 judge them on three criteria:

1. **Correctness:** Is the answer factually accurate given the code?
2. **Completeness:** Does the answer address all parts of the question?
3. **Clarity:** Is the answer well-structured and easy to understand?

The judge assigns a score from 1-5 for each criterion. We then compute a pass rate: what percentage of answers score 4 or higher?

Here is the evaluation code that powers this:

```python
class LLMJudge:
    def evaluate(self, query: str, answer: str, tier: str) -> dict:
        prompt = f"""
        Query: {query}
        Answer (from {tier}): {answer}
        
        Rate the answer on:
        1. Correctness (1-5)
        2. Completeness (1-5)
        3. Clarity (1-5)
        
        Return JSON with scores and brief justification.
        """
        response = self.llm.complete(prompt)
        return json.loads(response)
```

We run this across our entire dataset and aggregate results. The key is that we are not comparing against a ground truth (which is expensive to create). We are comparing the relative quality across tiers, using the LLM judge as a consistent evaluator.

## Results: Benchmark Showing Token Savings

After evaluating 100 queries across three tiers, here are the results that matter:

**Token Usage:**
- GRAPH_ONLY: 0 tokens (100% savings)
- GRAPH_RAG: Average 450 tokens per query (75% savings vs. full context baseline of 1800 tokens)
- LLM_FULL: Average 2000 tokens per query (baseline)

**Pass Rates (LLM Judge scoring 4+ out of 5):**
- GRAPH_ONLY: 78% (excellent for structural queries, fails on explanatory ones)
- GRAPH_RAG: 92% (nearly matches LLM_FULL quality)
- LLM_FULL: 95% (the gold standard)

**Latency:**
- GRAPH_ONLY: 50-100ms (graph query only)
- GRAPH_RAG: 2-4 seconds (graph query + LLM call with small context)
- LLM_FULL: 8-15 seconds (large context LLM call)

**Cost per 100 queries (at GPT-4 pricing):**
- GRAPH_ONLY: $0.00
- GRAPH_RAG: $0.54
- LLM_FULL: $2.16

The numbers tell a clear story. GRAPH_RAG delivers 92% of the quality at 25% of the cost. For most development workflows, that is an easy tradeoff.

We also measured token savings by query category. Structural queries, as expected, are handled almost entirely by GRAPH_ONLY. Explanatory queries split between GRAPH_RAG and LLM_FULL. Creative queries lean heavily on LLM_FULL, but even there, graph context reduces the need for broad codebase dumping.

One surprising finding: GRAPH_RAG sometimes outperformed LLM_FULL on explanatory queries. When the graph context was precise, the LLM gave more focused answers without the distraction of irrelevant code. The graph was not just saving tokens, it was improving signal-to-noise ratio.

## Conclusion and Future Work

GraphMind demonstrates that you do not need to choose between cost and quality in LLM-powered code reasoning. With a graph-first approach, you can dramatically reduce token usage while maintaining answer quality.

The 3-tier routing architecture gives developers control. Use GRAPH_ONLY for instant, free structural queries. Use GRAPH_RAG for the majority of explanatory questions, saving 75% on tokens. Use LLM_FULL when you truly need deep reasoning.

We are continuing to improve GraphMind in several directions:

**Multi-language support.** Currently focused on Python, we are expanding to JavaScript, Go, and Java. The tree-sitter parsing makes this straightforward, but each language has unique graph patterns to capture.

**Incremental updates.** Instead of re-ingesting the entire codebase, we are building a watch mode that updates the graph as files change. This keeps the graph fresh without the overhead of full re-parsing.

**Smarter routing.** The current routing engine uses heuristic rules. We are experimenting with a learned router that predicts the optimal tier based on query features and historical performance.

**Integration with IDEs.** The ultimate goal is to bring GraphMind directly into the developer workflow. VS Code and JetBrains plugins are on the roadmap, putting graph-powered code reasoning a keyboard shortcut away.

If you are interested in cutting your LLM costs while getting better code understanding, check out GraphMind on GitHub. The graph knows your code. Maybe it is time your LLM did too.

---

*GraphMind is open source under the MIT license. Contributions welcome.*
