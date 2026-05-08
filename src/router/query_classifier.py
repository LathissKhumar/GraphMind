from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from src.graph.query_engine import QueryEngine

# Pre-compiled regex patterns for performance
_RE_COUNT_SHOW = re.compile(r"\b(count|show|list|find)\b")
_RE_RELATIONSHIP_BETWEEN = re.compile(r"\bbetween\b.+\band\b")
_RE_OPEN_ENDED_KEYWORDS = re.compile(r"\b(explain|design|architect|refactor|optimize|compare)\b")
_RE_WHY_HOW = re.compile(r"\bwhy\b|\bhow\b")
_RE_HAS_UPPER = re.compile(r"[A-Z]")
_RE_QUOTED_ENTITY = re.compile(r"['\"]([A-Za-z_][\w:]*)['\"]")
_RE_CANDIDATE_TOKEN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_:]{2,}\b")


@dataclass(frozen=True)
class ClassificationResult:
    tier: str
    confidence: float
    reasoning: str


class QueryClassifier:
    def __init__(self, query_engine: Optional[QueryEngine] = None) -> None:
        self.query_engine = query_engine or QueryEngine()
        self._cache: dict[str, Dict[str, Any]] = {}
        self._cache_max_size = 100
        # Entity cache: set of known entity names (functions/classes) for O(1) lookups
        self._known_entities: set[str] = set()
        # Time when the entity cache was last refreshed (monotonic seconds)
        self._entity_cache_time: float = 0.0
        # TTL for the entity cache in seconds
        self._entity_cache_ttl: float = 60.0
        # Max entities to keep in the cache to bound memory
        self._entity_cache_max: int = 500

        # Build initial entity cache
        try:
            self.refresh_entity_cache()
        except Exception:
            # Best-effort: if graph not ready or refresh fails, start with empty cache
            self._known_entities = set()
            self._entity_cache_time = 0.0
    
    def classify(self, query: str) -> Dict[str, Any]:
        cache_key = query.strip()[:50]
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        text = query.strip()
        lowered = text.lower()

        if not text:
            result = ClassificationResult(
                tier="LLM_FULL",
                confidence=0.2,
                reasoning="Empty query needs open-ended handling.",
            )
            return result.__dict__

        if self._is_friendly_non_code_query(lowered):
            result = ClassificationResult(
                tier="LLM_FULL",
                confidence=0.35,
                reasoning="Friendly non-code query detected; treat as open-ended.",
            )
            return result.__dict__

        factoid_score = self._score_factoid(lowered)
        relationship_score = self._score_relationship(lowered)
        openness_score = self._score_open_ended(lowered)

        tier = "LLM_FULL"
        score = openness_score
        reasoning_parts: List[str] = ["No strong factoid or relationship pattern found."]

        if factoid_score >= relationship_score and factoid_score >= openness_score:
            tier = "GRAPH_ONLY"
            score = factoid_score
            reasoning_parts = ["Factoid pattern matched."]
        elif relationship_score >= factoid_score and relationship_score >= openness_score:
            tier = "GRAPH_RAG"
            score = relationship_score
            reasoning_parts = ["Relationship pattern matched."]
        else:
            reasoning_parts = ["Open-ended query pattern matched."]

        entity_bonus = self._entity_bonus(text)
        if entity_bonus > 0:
            score = min(1.0, score + entity_bonus)
            reasoning_parts.append("Graph entity recognition increased confidence.")

        if len(text) > 160:
            score = min(1.0, score + 0.05)
            reasoning_parts.append("Long-form query nudged toward open-ended handling.")

        if tier == "LLM_FULL" and not self._is_friendly_non_code_query(lowered):
            score = max(score, 0.55 if openness_score >= 0.5 else 0.45)

        result = {
            "tier": tier,
            "confidence": round(max(0.0, min(1.0, score)), 2),
            "reasoning": " ".join(reasoning_parts),
        }
        
        if len(self._cache) < self._cache_max_size:
            self._cache[cache_key] = result
        
        return result

    def _is_friendly_non_code_query(self, lowered: str) -> bool:
        prefixes = (
            "what is ",
            "help me",
            "can you help",
            "i need help",
            "how do i",
        )
        return lowered.startswith(prefixes)

    FACTIOD_KEYWORDS = ("what functions", "list classes", "who calls", "how many",
                        "what imports", "what class", "which function", "caller", "callee")
    RELATIONSHIP_KEYWORDS = ("relationship", "between", "depends on", "depend on",
                             "connected to", "calls", "references", "uses", "inherit",
                             "how does", "what is the", "dependency", "related to")

    def _score_factoid(self, lowered: str) -> float:
        score = 0.0
        if any(keyword in lowered for keyword in self.FACTIOD_KEYWORDS):
            score += 0.7
        if _RE_COUNT_SHOW.search(lowered):
            score += 0.15
        if "?" in lowered:
            score += 0.05
        return min(score, 1.0)

    def _score_relationship(self, lowered: str) -> float:
        score = 0.0
        if any(keyword in lowered for keyword in self.RELATIONSHIP_KEYWORDS):
            score += 0.7
        if _RE_RELATIONSHIP_BETWEEN.search(lowered):
            score += 0.1
        if "?" in lowered:
            score += 0.05
        return min(score, 1.0)

    def _score_open_ended(self, lowered: str) -> float:
        score = 0.35
        if _RE_OPEN_ENDED_KEYWORDS.search(lowered):
            score = 0.85
        if _RE_WHY_HOW.search(lowered):
            score = max(score, 0.75)
        if len(lowered) > 120:
            score = max(score, 0.7)
        return min(score, 1.0)

    def _entity_bonus(self, text: str) -> float:
        if not self.query_engine.is_graph_ready():
            return 0.0

        candidates = self._extract_candidates(text)
        if not candidates:
            return 0.0

        bonus = 0.0
        for candidate in candidates[:5]:
            if self._candidate_exists(candidate):
                bonus = max(bonus, 0.2)
                if _RE_HAS_UPPER.search(candidate):
                    bonus = max(bonus, 0.3)
                break
        return bonus

    def refresh_entity_cache(self) -> None:
        """Rebuild the in-memory set of known entity names (functions and classes).

        Limits to the first self._entity_cache_max entities discovered to keep memory bounded.
        Updates self._entity_cache_time on success or when graph not ready.
        """
        now = time.monotonic()
        # If graph isn't ready, clear cache and update timestamp
        if not self.query_engine.is_graph_ready():
            self._known_entities = set()
            self._entity_cache_time = now
            return

        known: set[str] = set()
        try:
            # Prefer SQLite fallback introspection for node listing
            # QueryEngine exposes _get_sqlite via attribute; use public behavior by attempting to access graph
            sqlite = None
            try:
                sqlite = self.query_engine._get_sqlite()
            except Exception:
                sqlite = None

            if sqlite is not None:
                # Node ids are like 'function:name' or 'class:name'
                for node_id in sqlite.graph.nodes():
                    if len(known) >= self._entity_cache_max:
                        break
                    if not isinstance(node_id, str):
                        continue
                    if node_id.startswith("function:") or node_id.startswith("class:"):
                        name = node_id.split(":", 1)[1]
                        known.add(name)
            # Fallback: leave known empty if we couldn't access sqlite
        except Exception:
            # On any error, keep whatever we've collected so far
            pass

        self._known_entities = set(list(known)[: self._entity_cache_max])
        self._entity_cache_time = now

    def _extract_candidates(self, text: str) -> List[str]:
        quoted = _RE_QUOTED_ENTITY.findall(text)
        tokens = _RE_CANDIDATE_TOKEN.findall(text)
        candidates = list(dict.fromkeys(quoted + tokens))
        stopwords = {
            "what",
            "functions",
            "function",
            "classes",
            "class",
            "calls",
            "call",
            "between",
            "relationship",
            "dependencies",
            "depends",
            "on",
            "the",
            "and",
            "with",
            "for",
            "how",
            "many",
            "list",
            "show",
            "find",
            "who",
            "does",
            "import",
            "imports",
            "uses",
            "used",
        }
        return [c for c in candidates if c.lower() not in stopwords]

    def _candidate_exists(self, candidate: str) -> bool:
        # Refresh cache if stale
        now = time.monotonic()
        if (now - self._entity_cache_time) > self._entity_cache_ttl:
            try:
                self.refresh_entity_cache()
            except Exception:
                # Best-effort: ignore refresh failures and proceed to fallback
                self._entity_cache_time = now

        # Fast O(1) check against in-memory set
        try:
            if candidate in self._known_entities:
                return True
        except Exception:
            # If any issue with cache, continue to graph lookup
            pass

        # Fall back to graph-backed lookups (slower)
        function_result = self.query_engine.get_function(candidate)
        if function_result.get("result"):
            return True

        class_result = self.query_engine.get_class(candidate)
        if class_result.get("result"):
            return True

        return False


if __name__ == "__main__":
    classifier = QueryClassifier()
    samples = [
        "What functions call parse_file?",
        "What is the architecture of this module?",
        "Show the relationship between parser and loader",
    ]
    for sample in samples:
        print(sample, "=>", classifier.classify(sample))
