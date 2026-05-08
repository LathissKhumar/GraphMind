from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import List, Literal

Difficulty = Literal["easy", "medium", "hard"]
Category = Literal["factoid", "relationship", "open-ended"]
Tier = Literal["GRAPH_ONLY", "GRAPH_RAG", "LLM_FULL"]


@dataclass(frozen=True)
class BenchmarkQuery:
    id: str
    query_text: str
    tier: Tier
    category: Category
    difficulty: Difficulty
    ground_truth: str
    tags: List[str]


GRAPH_ONLY_QUERIES: List[BenchmarkQuery] = [
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What functions are defined in src/router/query_classifier.py?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="Methods: classify, _is_friendly_non_code_query, _score_factoid, _score_relationship, _score_open_ended, _entity_bonus, _extract_candidates, _candidate_exists",
        tags=["factoid", "functions", "query_classifier"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="List all classes in the src/router directory",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="ClassificationResult, QueryClassifier",
        tags=["factoid", "classes", "router"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="How many methods are in the RoutingEngine class?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="8 methods: __init__, route, _graph_only_answer, _graph_context, _build_rag_prompt, _estimate_cost, _format_savings, _extract_entity",
        tags=["factoid", "methods", "routing_engine"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What imports are used in src/api/main.py?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="medium",
        ground_truth="fastapi, tempfile, time, uuid, datetime, pathlib, typing, pydantic, starlette, src.graph.ingestion, src.graph.sqlite_fallback, src.input.codebase_loader, src.router.routing_engine, src.llm.github_models_client",
        tags=["factoid", "imports", "main"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Who calls the classify method in QueryClassifier?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="medium",
        ground_truth="Called by RoutingEngine.route() method",
        tags=["factoid", "callers", "classify"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="List all fields in the RoutingResult dataclass",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="answer, tier, tokens_used, response_time_ms, savings, reasoning, dollar_cost, warning",
        tags=["factoid", "dataclass", "routing_result"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the default tier for an empty query in QueryClassifier?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="LLM_FULL (confidence 0.2, empty query needs open-ended handling)",
        tags=["factoid", "classification", "empty_query"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="How many lines are in src/router/query_classifier.py?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="212 lines (as of current codebase version)",
        tags=["factoid", "line_count", "query_classifier"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the primary key of the query_log table in QueryLogger?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="id INTEGER PRIMARY KEY AUTOINCREMENT",
        tags=["factoid", "database", "query_logger"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="List all decorators used in src/api/main.py",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="medium",
        ground_truth="@app.get, @app.post, @app.exception_handler",
        tags=["factoid", "decorators", "main"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the type of the 'tier' field in ClassificationResult?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="str",
        tags=["factoid", "types", "classification_result"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="How many tables are in the QueryLogger database?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="1 table: query_log",
        tags=["factoid", "database", "query_logger"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What functions are in src/llm/github_models_client.py?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="medium",
        ground_truth="generate, is_available, close (GitHub Models API client with caching, rate limiting, and circuit breaker)",
        tags=["factoid", "functions", "github_models_client"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the parent class of QueryLogger?",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="easy",
        ground_truth="object (no explicit parent class, inherits from object implicitly)",
        tags=["factoid", "inheritance", "query_logger"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="List all HTTP methods used in src/api/main.py endpoints",
        tier="GRAPH_ONLY",
        category="factoid",
        difficulty="medium",
        ground_truth="GET, POST (used for all 9 endpoints)",
        tags=["factoid", "http", "endpoints"],
    ),
]

GRAPH_RAG_QUERIES: List[BenchmarkQuery] = [
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the relationship between QueryClassifier and RoutingEngine?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="easy",
        ground_truth="RoutingEngine uses QueryClassifier to classify queries and determine the processing tier",
        tags=["relationship", "routing", "classifier"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Who calls the route method of RoutingEngine?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="easy",
        ground_truth="Called by the POST /api/query endpoint in src/api/main.py",
        tags=["relationship", "callers", "route"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Does RoutingEngine depend on LLMClient?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="easy",
        ground_truth="Yes, RoutingEngine uses llm_client to generate responses for GRAPH_RAG and LLM_FULL tiers",
        tags=["relationship", "dependency", "llm"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the relationship between QueryLogger and RoutingEngine?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="RoutingEngine uses QueryLogger to log query metrics (tokens, response time, cost) after processing each query",
        tags=["relationship", "logging", "routing"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Which classes use the TokenCounter?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="RoutingEngine uses TokenCounter to count tokens in prompts and responses for cost estimation",
        tags=["relationship", "token", "counter"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Is there a dependency between query_classifier.py and query_engine.py?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="Yes, QueryClassifier uses QueryEngine to check if the graph is ready and to look up entities in the graph",
        tags=["relationship", "dependency", "graph"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What functions does the classify method call?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="_is_friendly_non_code_query, _score_factoid, _score_relationship, _score_open_ended, _entity_bonus",
        tags=["relationship", "calls", "classify"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Does the GRAPH_ONLY tier use the LLM?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="easy",
        ground_truth="No, GRAPH_ONLY uses only the graph structure to answer queries without LLM involvement",
        tags=["relationship", "tier", "graph_only"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the relationship between SQLiteNetworkXFallback and the graph backend?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="SQLiteNetworkXFallback is the persistent graph backend used to store and query the code knowledge graph",
        tags=["relationship", "graph", "backend"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Which endpoints in main.py use the RoutingEngine?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="Only POST /api/query endpoint uses RoutingEngine to process and route queries",
        tags=["relationship", "endpoints", "routing"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Does QueryLogger store dollar_cost?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="easy",
        ground_truth="Yes, QueryLogger stores dollar_cost in the query_log table for each logged query",
        tags=["relationship", "logging", "cost"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What context is passed to the LLM in GRAPH_RAG tier?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="Graph context from QueryEngine (function and class data for the entity in the query)",
        tags=["relationship", "rag", "context"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Is RoutingEngine's _graph_only_answer method dependent on QueryEngine?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="Yes, it uses QueryEngine to get callers, callees, classes, functions from the graph",
        tags=["relationship", "graph_only", "query_engine"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the relationship between TokenCounter and the benchmark framework?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="hard",
        ground_truth="TokenCounter is used to count tokens in queries and responses for metrics and cost estimation in benchmark results",
        tags=["relationship", "benchmark", "token"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Does the LLM_FULL tier use graph context?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="easy",
        ground_truth="No, LLM_FULL sends the raw query to the LLM without graph context",
        tags=["relationship", "tier", "llm_full"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Which classes are in the src/router directory?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="easy",
        ground_truth="ClassificationResult, QueryClassifier, RoutingResult, RoutingEngine, QueryLogRecord, QueryLogger",
        tags=["relationship", "classes", "router"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the dependency chain from POST /api/query to getting an answer?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="hard",
        ground_truth="query() -> get_routing_engine() -> RoutingEngine.route() -> QueryClassifier.classify() -> (tier-based processing) -> QueryLogger.log_query()",
        tags=["relationship", "flow", "query"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Does the benchmark framework depend on RoutingEngine?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="Yes, BenchmarkRunner uses RoutingEngine to run queries through different tiers",
        tags=["relationship", "benchmark", "routing"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the relationship between GitHubModelsClient and LLMClient?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="medium",
        ground_truth="GitHubModelsClient is a standalone LLM client used directly by the routing engine and judge, while LLMClient is a separate OpenRouter-based client",
        tags=["relationship", "llm", "client"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Which tiers use the llm_client.generate method?",
        tier="GRAPH_RAG",
        category="relationship",
        difficulty="easy",
        ground_truth="GRAPH_RAG and LLM_FULL tiers use llm_client.generate to get LLM responses",
        tags=["relationship", "tier", "llm"],
    ),
]

LLM_FULL_QUERIES: List[BenchmarkQuery] = [
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Explain the architecture of the GraphMind routing system",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="The routing system uses QueryClassifier to classify queries into GRAPH_ONLY, GRAPH_RAG, or LLM_FULL tiers, then RoutingEngine processes the query using the appropriate tier with QueryLogger tracking metrics",
        tags=["open-ended", "architecture", "routing"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What design pattern is used in the RoutingEngine class?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="Strategy pattern - each tier represents a different processing strategy determined by query classification",
        tags=["open-ended", "design_pattern", "routing_engine"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Why does the QueryClassifier assign empty queries to LLM_FULL tier?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="Empty queries are not code-related and need open-ended LLM handling rather than graph-based factoid answers",
        tags=["open-ended", "classification", "empty_query"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="How would you refactor the RoutingEngine to support custom tiers?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="hard",
        ground_truth="Add a tier registry, allow registering custom tier handlers, modify route() to check registry first before default classification",
        tags=["open-ended", "refactor", "routing_engine"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Explain the tradeoffs between GRAPH_ONLY and LLM_FULL tiers",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="GRAPH_ONLY is fast/cheap (no tokens) but only handles factoids. LLM_FULL is slower/more expensive but handles open-ended questions",
        tags=["open-ended", "tradeoff", "tiers"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What improvements would you make to the QueryLogger?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="hard",
        ground_truth="Add more metrics, support exporting to JSON, add query history search, include query success/failure status",
        tags=["open-ended", "improvement", "logging"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Describe the flow of a GRAPH_RAG query from start to finish",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="1. Classify as GRAPH_RAG 2. Get graph context from QueryEngine 3. Build RAG prompt 4. Call LLM with prompt+context 5. Return answer 6. Log metrics",
        tags=["open-ended", "flow", "rag"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Why is the QueryClassifier's entity bonus important?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="It increases classification confidence when queries contain entities that exist in the graph, improving routing accuracy",
        tags=["open-ended", "classification", "entity"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="How does the benchmark framework help evaluate the routing system?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="Runs predefined queries through all tiers, compares results to ground truth, measures token usage and response time",
        tags=["open-ended", "benchmark", "evaluation"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What are the limitations of the current GRAPH_ONLY implementation?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="hard",
        ground_truth="Only handles basic factoids, no complex graph traversals, falls back to generic answers when graph is unavailable",
        tags=["open-ended", "limitation", "graph_only"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Explain the purpose of the TokenCounter in the system",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="Counts tokens in prompts and responses to estimate cost and track token usage by tier for metrics",
        tags=["open-ended", "token", "counter"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="How would you extend the benchmark to support custom datasets?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="hard",
        ground_truth="Add dataset loader, allow specifying custom query files, add configuration for ground truth sources, support multiple codebases",
        tags=["open-ended", "extension", "benchmark"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="What is the role of the SQLiteNetworkXFallback class?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="Provides persistent graph storage using SQLite with NetworkX for in-memory graph operations and queries",
        tags=["open-ended", "graph", "backend"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Why does the RoutingEngine fall back to GRAPH_ONLY when LLM is unavailable?",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="medium",
        ground_truth="To provide degraded but functional answers instead of failing completely when LLM services are unavailable",
        tags=["open-ended", "fallback", "routing"],
    ),
    BenchmarkQuery(
        id=str(uuid.uuid4())[:8],
        query_text="Describe the evolution of the query processing pipeline in GraphMind",
        tier="LLM_FULL",
        category="open-ended",
        difficulty="hard",
        ground_truth="Started with basic graph-only answers, added RAG with LLM context, then full LLM for open-ended queries with classification routing",
        tags=["open-ended", "evolution", "pipeline"],
    ),
]

ALL_BENCHMARK_QUERIES: List[BenchmarkQuery] = (
    GRAPH_ONLY_QUERIES + GRAPH_RAG_QUERIES + LLM_FULL_QUERIES
)

assert len(ALL_BENCHMARK_QUERIES) >= 50, f"Expected 50+ queries, got {len(ALL_BENCHMARK_QUERIES)}"
assert len(GRAPH_ONLY_QUERIES) == 15, f"Expected 15 GRAPH_ONLY queries, got {len(GRAPH_ONLY_QUERIES)}"
assert len(GRAPH_RAG_QUERIES) == 20, f"Expected 20 GRAPH_RAG queries, got {len(GRAPH_RAG_QUERIES)}"
assert len(LLM_FULL_QUERIES) == 15, f"Expected 15 LLM_FULL queries, got {len(LLM_FULL_QUERIES)}"


def get_queries_by_tier(tier: Tier) -> List[BenchmarkQuery]:
    return [q for q in ALL_BENCHMARK_QUERIES if q.tier == tier]


def get_queries_by_category(category: Category) -> List[BenchmarkQuery]:
    return [q for q in ALL_BENCHMARK_QUERIES if q.category == category]


def get_queries_by_difficulty(difficulty: Difficulty) -> List[BenchmarkQuery]:
    return [q for q in ALL_BENCHMARK_QUERIES if q.difficulty == difficulty]
