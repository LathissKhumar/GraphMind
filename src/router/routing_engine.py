from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.graph.query_engine import QueryEngine
from src.llm.client import LLMClient
from src.router.query_classifier import QueryClassifier
from src.router.query_logger import QueryLogger
from src.router.token_counter import TokenCounter


@dataclass(frozen=True)
class RoutingResult:
    answer: str
    tier: str
    tokens_used: int
    response_time_ms: float
    savings: str
    reasoning: str
    dollar_cost: float
    warning: Optional[str] = None


class RoutingEngine:
    def __init__(
        self,
        classifier: Optional[QueryClassifier] = None,
        query_engine: Optional[QueryEngine] = None,
        llm_client: Optional[LLMClient] = None,
        token_counter: Optional[TokenCounter] = None,
        query_logger: Optional[QueryLogger] = None,
    ) -> None:
        self.classifier = classifier or QueryClassifier(query_engine=query_engine)
        self.query_engine = query_engine or QueryEngine()
        self.llm_client = llm_client or LLMClient()
        self.token_counter = token_counter or TokenCounter()
        self.query_logger = query_logger or QueryLogger()

    def route(self, query: str) -> Dict[str, Any]:
        start = time.monotonic()
        classification = self.classifier.classify(query)
        tier = classification["tier"]
        reasoning = classification["reasoning"]

        warning: Optional[str] = None
        answer = ""
        tokens_used = 0
        dollar_cost = 0.0

        if tier == "GRAPH_ONLY":
            answer = self._graph_only_answer(query)
        elif tier == "GRAPH_RAG":
            context = self._graph_context(query)
            rag_prompt = self._build_rag_prompt(query, context)
            llm_result = self.llm_client.generate(rag_prompt, context)
            if llm_result.startswith("OpenRouter request failed"):
                tier = "GRAPH_ONLY"
                warning = "LLM unavailable. Falling back to GRAPH_ONLY."
                answer = self._graph_only_answer(query)
            else:
                answer = llm_result
                tokens_used = self.token_counter.count_tokens(rag_prompt + "\n" + context)
                dollar_cost = self._estimate_cost(tokens_used)
        else:
            full_prompt = query
            llm_result = self.llm_client.generate(full_prompt)
            if llm_result.startswith("OpenRouter request failed"):
                tier = "GRAPH_ONLY"
                warning = "LLM unavailable. Falling back to GRAPH_ONLY."
                answer = self._graph_only_answer(query)
            else:
                answer = llm_result
                tokens_used = self.token_counter.count_tokens(full_prompt)
                dollar_cost = self._estimate_cost(tokens_used)

        response_time_ms = (time.monotonic() - start) * 1000
        savings = self._format_savings(tier, tokens_used)

        self.query_logger.log_query(query, tier, tokens_used, response_time_ms, dollar_cost)

        result = RoutingResult(
            answer=answer,
            tier=tier,
            tokens_used=tokens_used,
            response_time_ms=round(response_time_ms, 2),
            savings=savings,
            reasoning=reasoning,
            dollar_cost=round(dollar_cost, 4),
            warning=warning,
        )
        return result.__dict__

    def _graph_only_answer(self, query: str) -> str:
        query_lower = query.lower()
        if not self.query_engine.is_graph_ready():
            return "Graph-only answer unavailable or graph not ready."

        entity = self._extract_entity(query)
        if "calls" in query_lower or "caller" in query_lower:
            callers = self.query_engine.get_callers(entity).get("result", [])
            return f"Found callers for {entity}: {callers}" if callers else f"No callers found for {entity}."
        if "callee" in query_lower or "what does" in query_lower:
            callees = self.query_engine.get_callees(entity).get("result", [])
            return f"Found callees for {entity}: {callees}" if callees else f"No callees found for {entity}."
        if "class" in query_lower:
            result = self.query_engine.get_class(entity).get("result", [])
            return str(result) if result else f"No class data found for {entity}."
        if "function" in query_lower:
            result = self.query_engine.get_function(entity).get("result", [])
            return str(result) if result else f"No function data found for {entity}."
        return f"Graph data for {entity}: {self._graph_context(query)}"

    def _graph_context(self, query: str) -> str:
        entity = self._extract_entity(query)
        if not entity:
            return ""
        function_data = self.query_engine.get_function(entity)
        class_data = self.query_engine.get_class(entity)
        return f"function={function_data.get('result', [])}; class={class_data.get('result', [])}"

    def _build_rag_prompt(self, query: str, context: str) -> str:
        return f"Question: {query}\n\nContext: {context}" if context else query

    def _estimate_cost(self, tokens_used: int) -> float:
        return round(tokens_used * 0.00002, 4)

    def _format_savings(self, tier: str, tokens_used: int) -> str:
        if tier == "GRAPH_ONLY":
            return "100% (zero tokens)"
        if tier == "GRAPH_RAG":
            estimated_full = max(tokens_used * 3, 100)
            pct = round((1 - tokens_used / estimated_full) * 100)
            return f"{pct}% ({tokens_used} vs ~{estimated_full} tokens)"
        if tier == "LLM_FULL":
            return "0% (no savings)"
        return "0%"

    def _extract_entity(self, query: str) -> str:
        import re
        quoted_match = re.search(r"['\"]([a-zA-Z_][\w:]*?)['\"]", query)
        if quoted_match:
            return quoted_match.group(1)
        
        words = [w.strip('.,!?;:') for w in query.split()]
        common_words = {'what', 'is', 'are', 'does', 'do', 'how', 'who', 'where', 'when', 'which', 'why', 'the', 'a', 'an', 'class', 'function', 'method', 'this', 'that'}
        
        for word in words:
            if word.lower() not in common_words:
                return word
        
        return words[0] if words else ""


if __name__ == "__main__":
    engine = RoutingEngine()
    print(engine.route("What functions call parse_file?"))
