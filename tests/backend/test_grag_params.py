import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.configs.grag_params import GraphRAGParams


class TestGraphRAGParams:
    def test_default_values(self):
        params = GraphRAGParams()
        assert params.top_k == 5
        assert params.num_hops == 2
        assert params.num_seen_min == 1
        assert params.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert params.similarity_threshold == 0.7
        assert params.fallback_to_full is True

    def test_custom_values(self):
        params = GraphRAGParams(top_k=10, num_hops=3, similarity_threshold=0.8)
        assert params.top_k == 10
        assert params.num_hops == 3
        assert params.similarity_threshold == 0.8

    def test_get_preset_for_query_graph_rag(self):
        assert GraphRAGParams.get_preset_for_query("relationship between A and B") == "GRAPH_RAG"
        assert GraphRAGParams.get_preset_for_query("What depends on X?") == "GRAPH_RAG"

    def test_get_preset_for_query_llm_full(self):
        assert GraphRAGParams.get_preset_for_query("explain the architecture") == "LLM_FULL"
        assert GraphRAGParams.get_preset_for_query("why does this happen?") == "LLM_FULL"
        assert GraphRAGParams.get_preset_for_query("how does it work?") == "LLM_FULL"

    def test_get_preset_for_query_auto(self):
        assert GraphRAGParams.get_preset_for_query("random question here") == "auto"

    def test_get_preset_case_insensitive(self):
        assert GraphRAGParams.get_preset_for_query("RELATIONSHIP between A and B") == "GRAPH_RAG"
        assert GraphRAGParams.get_preset_for_query("EXPLAIN the code") == "LLM_FULL"

    def test_get_preset_empty_string(self):
        assert GraphRAGParams.get_preset_for_query("") == "auto"

    def test_get_preset_multiple_keywords(self):
        query = "explain the relationship between X and Y"
        assert GraphRAGParams.get_preset_for_query(query) == "GRAPH_RAG"
