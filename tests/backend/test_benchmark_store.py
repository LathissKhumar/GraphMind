import pytest
import json
from pathlib import Path
from datetime import datetime

sys_path = Path(__file__).parent.parent / "src"
import sys
sys.path.insert(0, str(sys_path))

from src.benchmark.store import BenchmarkStore
from src.benchmark.runner import BenchmarkResult


class TestBenchmarkStore:
    def test_init_default(self):
        store = BenchmarkStore()
        assert store.results_dir == Path("results")
        assert store.results_dir.exists()

    def test_init_custom_dir(self, tmp_path):
        store = BenchmarkStore(results_dir=str(tmp_path / "custom"))
        assert store.results_dir == tmp_path / "custom"
        assert store.results_dir.exists()

    def test_save_result(self, tmp_path):
        store = BenchmarkStore(results_dir=str(tmp_path / "results"))
        
        result = BenchmarkResult(
            query_id="q1",
            query_text="What is X?",
            expected_tier="GRAPH_ONLY",
            run_tier="GRAPH_ONLY",
            answer="answer",
            tokens_used=10,
            response_time_ms=100.0,
            success=True,
            timestamp="2025-01-01T00:00:00",
            ground_truth="answer",
            category="factoid",
            difficulty="easy",
            tags=["test"]
        )
        
        filepath = store.save_result(result)
        assert Path(filepath).exists()
        
        # Verify the file content
        with open(filepath) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["query_id"] == "q1"

    def test_load_results(self, tmp_path):
        store = BenchmarkStore(results_dir=str(tmp_path / "results"))
        
        # Create a test result file
        test_data = [{"query_id": "q1", "run_tier": "GRAPH_ONLY"}]
        (tmp_path / "results" / "benchmark_20250101.json").write_text(json.dumps(test_data))
        
        results = store.load_results()
        assert len(results) == 1
        assert results[0]["query_id"] == "q1"

    def test_load_results_with_date_range(self, tmp_path):
        store = BenchmarkStore(results_dir=str(tmp_path / "results"))
        
        # Create test files
        (tmp_path / "results" / "benchmark_20250101.json").write_text(json.dumps([{"query_id": "q1"}]))
        (tmp_path / "results" / "benchmark_20250102.json").write_text(json.dumps([{"query_id": "q2"}]))
        (tmp_path / "results" / "benchmark_20250103.json").write_text(json.dumps([{"query_id": "q3"}]))
        
        results = store.load_results(date_range={"start": "20250101", "end": "20250102"})
        assert len(results) == 2

    def test_get_best_pipeline(self, tmp_path):
        store = BenchmarkStore(results_dir=str(tmp_path / "results"))
        
        # Create test results with different success rates
        test_data = [
            {"run_tier": "GRAPH_ONLY", "success": True},
            {"run_tier": "GRAPH_ONLY", "success": True},
            {"run_tier": "GRAPH_RAG", "success": False},
            {"run_tier": "LLM_FULL", "success": False},
        ]
        (tmp_path / "results" / "benchmark_20250101.json").write_text(json.dumps(test_data))
        
        result = store.get_best_pipeline()
        assert "best_tier" in result
        assert result["best_tier"] == "GRAPH_ONLY"  # 2/2 = 100% success
        assert "stats" in result
        assert len(result["stats"]) == 3  # GRAPH_ONLY, GRAPH_RAG, LLM_FULL
