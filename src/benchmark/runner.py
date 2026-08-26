from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.router.routing_engine import RoutingEngine
from src.benchmark.queries import ALL_BENCHMARK_QUERIES, BenchmarkQuery


@dataclass(frozen=True)
class BenchmarkResult:
    query_id: str
    query_text: str
    expected_tier: str
    run_tier: str
    answer: str
    tokens_used: int
    response_time_ms: float
    success: bool
    timestamp: str
    ground_truth: str
    category: str
    difficulty: str
    tags: List[str]


class BenchmarkRunner:
    def __init__(self, results_dir: str = "results") -> None:
        self.routing_engine = RoutingEngine()
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._setup_routing_engine_for_tiers()

    def _setup_routing_engine_for_tiers(self) -> None:
        self._graph_only_func = self.routing_engine._graph_only_answer
        self._graph_rag_func = self._run_graph_rag
        self._llm_full_func = self._run_llm_full

    def _run_graph_rag(self, query: str) -> Dict[str, Any]:
        context = self.routing_engine._graph_context(query)
        rag_prompt = self.routing_engine._build_rag_prompt(query, context)
        llm_result = self.routing_engine.llm_client.generate(rag_prompt, context)
        tokens_used = self.routing_engine.token_counter.count_tokens(rag_prompt + "\n" + context)
        dollar_cost = self.routing_engine._estimate_cost(tokens_used)
        return {
            "answer": llm_result,
            "tokens_used": tokens_used,
            "dollar_cost": dollar_cost,
        }

    def _run_llm_full(self, query: str) -> Dict[str, Any]:
        full_prompt = query
        llm_result = self.routing_engine.llm_client.generate(full_prompt)
        tokens_used = self.routing_engine.token_counter.count_tokens(full_prompt)
        dollar_cost = self.routing_engine._estimate_cost(tokens_used)
        return {
            "answer": llm_result,
            "tokens_used": tokens_used,
            "dollar_cost": dollar_cost,
        }

    def run_all_pipelines(self, queries: List[BenchmarkQuery]) -> List[BenchmarkResult]:
        results = []
        for query in queries:
            for tier in ["GRAPH_ONLY", "GRAPH_RAG", "LLM_FULL"]:
                result = self._run_single_query(query, tier)
                results.append(result)
        return results

    def run_tier(self, tier: str, queries: List[BenchmarkQuery]) -> List[BenchmarkResult]:
        results = []
        for query in queries:
            result = self._run_single_query(query, tier)
            results.append(result)
        return results

    def _run_single_query(self, query: BenchmarkQuery, tier: str) -> BenchmarkResult:
        start = time.monotonic()
        success = True
        answer = ""
        tokens_used = 0

        try:
            if tier == "GRAPH_ONLY":
                answer = self._graph_only_func(query.query_text)
                tokens_used = 0
            elif tier == "GRAPH_RAG":
                rag_result = self._graph_rag_func(query.query_text)
                answer = rag_result["answer"]
                tokens_used = rag_result["tokens_used"]
                if answer.startswith("OpenRouter request failed"):
                    success = False
                    tier = "GRAPH_ONLY"
                    answer = self._graph_only_func(query.query_text)
            else:
                llm_result = self._llm_full_func(query.query_text)
                answer = llm_result["answer"]
                tokens_used = llm_result["tokens_used"]
                if answer.startswith("OpenRouter request failed"):
                    success = False
                    tier = "GRAPH_ONLY"
                    answer = self._graph_only_func(query.query_text)
        except Exception:
            success = False
            answer = "Error running query"
            tokens_used = 0

        response_time_ms = (time.monotonic() - start) * 1000
        timestamp = datetime.now().isoformat()

        return BenchmarkResult(
            query_id=query.id,
            query_text=query.query_text,
            expected_tier=query.tier,
            run_tier=tier,
            answer=answer,
            tokens_used=tokens_used,
            response_time_ms=round(response_time_ms, 2),
            success=success,
            timestamp=timestamp,
            ground_truth=query.ground_truth,
            category=query.category,
            difficulty=query.difficulty,
            tags=query.tags,
        )

    def save_results(self, results: List[BenchmarkResult], date_str: Optional[str] = None) -> str:
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        filename = f"benchmark_{date_str}.json"
        filepath = self.results_dir / filename
        results_dict = [asdict(r) for r in results]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        return str(filepath)
