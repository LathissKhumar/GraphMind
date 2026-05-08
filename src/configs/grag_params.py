from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class GraphRAGParams:
    top_k: int = 5
    num_hops: int = 2
    num_seen_min: int = 1
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.7
    fallback_to_full: bool = True
    
    presets: Dict[str, Any] = field(default_factory=lambda: {
        "fast": {"top_k": 3, "num_hops": 1, "fallback_to_full": False},
        "balanced": {"top_k": 5, "num_hops": 2, "fallback_to_full": True},
        "thorough": {"top_k": 10, "num_hops": 3, "fallback_to_full": True},
        "relationship": {"top_k": 8, "num_hops": 3, "fallback_to_full": True},
    })
    
    def apply_preset(self, preset_name: str) -> "GraphRAGParams":
        if preset_name not in self.presets:
            return self
        preset = self.presets[preset_name]
        return GraphRAGParams(
            top_k=preset.get("top_k", self.top_k),
            num_hops=preset.get("num_hops", self.num_hops),
            num_seen_min=self.num_seen_min,
            embedding_model=self.embedding_model,
            similarity_threshold=self.similarity_threshold,
            fallback_to_full=preset.get("fallback_to_full", self.fallback_to_full),
        )

    @staticmethod
    def get_preset_for_query(query: str) -> str:
        query_lower = query.lower()
        relationship_keywords = {"relationship", "between", "depends"}
        explain_keywords = {"explain", "why", "how"}
        
        if any(kw in query_lower for kw in relationship_keywords):
            return "GRAPH_RAG"
        if any(kw in query_lower for kw in explain_keywords):
            return "LLM_FULL"
        return "auto"
