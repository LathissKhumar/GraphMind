import pytest
from src.benchmark.queries import (
    BenchmarkQuery,
    GRAPH_ONLY_QUERIES,
    GRAPH_RAG_QUERIES,
    LLM_FULL_QUERIES,
)


class TestBenchmarkQueries:
    def test_graph_only_queries_exist(self):
        assert len(GRAPH_ONLY_QUERIES) >= 15

    def test_graph_rag_queries_exist(self):
        assert len(GRAPH_RAG_QUERIES) >= 15

    def test_llm_full_queries_exist(self):
        assert len(LLM_FULL_QUERIES) >= 15

    def test_total_queries_above_50(self):
        total = len(GRAPH_ONLY_QUERIES) + len(GRAPH_RAG_QUERIES) + len(LLM_FULL_QUERIES)
        assert total >= 50

    def test_graph_only_query_has_ground_truth(self):
        for q in GRAPH_ONLY_QUERIES:
            assert q.ground_truth

    def test_graph_rag_query_has_ground_truth(self):
        for q in GRAPH_RAG_QUERIES:
            assert q.ground_truth

    def test_llm_full_query_has_ground_truth(self):
        for q in LLM_FULL_QUERIES:
            assert q.ground_truth

    def test_all_queries_have_unique_ids(self):
        all_ids = [q.id for q in GRAPH_ONLY_QUERIES + GRAPH_RAG_QUERIES + LLM_FULL_QUERIES]
        assert len(all_ids) == len(set(all_ids))

    def test_queries_have_valid_tiers(self):
        valid_tiers = {"GRAPH_ONLY", "GRAPH_RAG", "LLM_FULL"}
        for q in GRAPH_ONLY_QUERIES + GRAPH_RAG_QUERIES + LLM_FULL_QUERIES:
            assert q.tier in valid_tiers

    def test_queries_have_valid_difficulty(self):
        valid_diff = {"easy", "medium", "hard"}
        for q in GRAPH_ONLY_QUERIES + GRAPH_RAG_QUERIES + LLM_FULL_QUERIES:
            assert q.difficulty in valid_diff


class TestBenchmarkQueryDataclass:
    def test_create_query(self):
        q = BenchmarkQuery(
            id="test-001",
            query_text="Test query?",
            tier="GRAPH_ONLY",
            category="factoid",
            difficulty="easy",
            ground_truth="test answer",
            tags=["test"],
        )
        assert q.id == "test-001"
        assert q.query_text == "Test query?"
        assert q.tier == "GRAPH_ONLY"

    def test_query_is_immutable(self):
        q = GRAPH_ONLY_QUERIES[0]
        with pytest.raises(AttributeError):
            q.ground_truth = "changed"