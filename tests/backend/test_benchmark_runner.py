import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

sys_path = Path(__file__).parent.parent / "src"
import sys
sys.path.insert(0, str(sys_path))

# Mock BenchmarkQuery since we might not have the full definition
@dataclass
class MockBenchmarkQuery:
    id: str
    query_text: str
    tier: str
    ground_truth: str
    category: str
    difficulty: str
    tags: List[str]

from src.benchmark.runner import BenchmarkRunner, BenchmarkResult


class TestBenchmarkRunner:
    def test_init(self, tmp_path):
        runner = BenchmarkRunner(results_dir=str(tmp_path / "results"))
        assert runner.results_dir == tmp_path / "results"
        assert runner.results_dir.exists()

    @patch("src.benchmark.runner.RoutingEngine")
    def test_run_single_query_graph_only(self, mock_routing_engine):
        runner = BenchmarkRunner()
        mock_routing_engine.return_value = MagicMock()
        mock_routing_engine.return_value._graph_only_answer.return_value = "graph answer"
        mock_routing_engine.return_value.token_counter.count_tokens.return_value = 10
        
        query = MockBenchmarkQuery(
            id="q1", query_text="What is X?", tier="GRAPH_ONLY",
            ground_truth="answer", category="factoid", difficulty="easy", tags=[]
        )
        
        result = runner._run_single_query(query, "GRAPH_ONLY")
        assert result.query_id == "q1"
        assert result.run_tier == "GRAPH_ONLY"
        assert result.success is True

    @patch("src.benchmark.runner.RoutingEngine")
    def test_run_all_pipelines(self, mock_routing_engine):
        runner = BenchmarkRunner()
        mock_routing_engine.return_value = MagicMock()
        mock_routing_engine.return_value._graph_only_answer.return_value = "answer"
        mock_routing_engine.return_value.token_counter.count_tokens.return_value = 10
        
        queries = [
            MockBenchmarkQuery(
                id="q1", query_text="What is X?", tier="GRAPH_ONLY",
                ground_truth="answer", category="factoid", difficulty="easy", tags=[]
            )
        ]
        
        results = runner.run_all_pipelines(queries)
        assert len(results) == 3  # GRAPH_ONLY, GRAPH_RAG, LLM_FULL

    @patch("src.benchmark.runner.RoutingEngine")
    def test_run_tier(self, mock_routing_engine):
        runner = BenchmarkRunner()
        mock_routing_engine.return_value = MagicMock()
        mock_routing_engine.return_value._graph_only_answer.return_value = "answer"
        mock_routing_engine.return_value.token_counter.count_tokens.return_value = 10
        
        queries = [
            MockBenchmarkQuery(
                id="q1", query_text="What is X?", tier="GRAPH_ONLY",
                ground_truth="answer", category="factoid", difficulty="easy", tags=[]
            )
        ]
        
        results = runner.run_tier("GRAPH_ONLY", queries)
        assert len(results) == 1
        assert results[0].run_tier == "GRAPH_ONLY"

    def test_save_results(self, tmp_path):
        runner = BenchmarkRunner(results_dir=str(tmp_path / "results"))
        
        results = [
            BenchmarkResult(
                query_id="q1", query_text="What is X?", expected_tier="GRAPH_ONLY",
                run_tier="GRAPH_ONLY", answer="answer", tokens_used=10,
                response_time_ms=100.0, success=True, timestamp="2025-01-01",
                ground_truth="answer", category="factoid", difficulty="easy", tags=[]
            )
        ]
        
        filepath = runner.save_results(results)
        assert Path(filepath).exists()
