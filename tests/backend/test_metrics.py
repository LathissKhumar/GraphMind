import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from src.router.token_counter import TokenCounter
from src.router.query_logger import QueryLogger

class TestTokenCounter:
    def test_count_tokens(self):
        counter = TokenCounter()
        count = counter.count_tokens("hello world test")
        assert count >= 0
        assert isinstance(count, int)

class TestQueryLogger:
    def test_log_query(self):
        logger = QueryLogger()
        logger.log_query("test query", "GRAPH_ONLY", 0, 1.0, 0.0)
        metrics = logger.get_metrics()
        assert metrics is not None

    def test_get_metrics(self):
        logger = QueryLogger()
        logger.log_query("test", "GRAPH_ONLY", 10, 1.0, 0.5)
        metrics = logger.get_metrics()
        assert "total_queries" in metrics
        assert "total_tokens" in metrics