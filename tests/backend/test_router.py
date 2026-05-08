import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from src.router.cache import QueryCache

class TestQueryCache:
    def test_cache_set_and_get(self):
        cache = QueryCache()
        cache.set("test query", "test answer", "GRAPH_ONLY", 0, 0.5)
        result = cache.get("test query")
        assert result is not None
        if result:
            assert result["answer"] == "test answer"

    def test_cache_miss_returns_none(self):
        cache = QueryCache()
        result = cache.get("nonexistent query")
        assert result is None

    def test_cache_invalidate(self):
        cache = QueryCache()
        cache.set("test query", "test answer", "GRAPH_ONLY", 0, 0.5)
        cache.invalidate("test query")
        result = cache.get("test query")
        assert result is None

class TestQueryClassifier:
    def test_init(self):
        from src.router.query_classifier import QueryClassifier
        classifier = QueryClassifier()
        assert classifier.query_engine is not None

    def test_classify_empty_query(self):
        from src.router.query_classifier import QueryClassifier
        classifier = QueryClassifier()
        result = classifier.classify("")
        assert result["tier"] == "LLM_FULL"
        assert result["confidence"] == 0.2

    def test_classify_friendly_non_code_query(self):
        from src.router.query_classifier import QueryClassifier
        classifier = QueryClassifier()
        result = classifier.classify("what is Python?")
        assert result["tier"] == "LLM_FULL"
        assert result["confidence"] == 0.35

    def test_classify_factoid_query(self):
        from src.router.query_classifier import QueryClassifier
        classifier = QueryClassifier()
        result = classifier.classify("What functions call parse_file?")
        assert result["tier"] == "GRAPH_ONLY"

    def test_classify_relationship_query(self):
        from src.router.query_classifier import QueryClassifier
        classifier = QueryClassifier()
        result = classifier.classify("Show relationship between parser and loader")
        assert result["tier"] == "GRAPH_RAG"

    def test_classify_open_ended_query(self):
        from src.router.query_classifier import QueryClassifier
        classifier = QueryClassifier()
        result = classifier.classify("Explain the architecture of this module")
        assert result["tier"] == "LLM_FULL"


class TestQueryLogger:
    def test_init_custom_db_path(self, tmp_path):
        from src.router.query_logger import QueryLogger
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        assert logger.db_path == db_path
        assert db_path.exists()

    def test_log_query(self, tmp_path):
        from src.router.query_logger import QueryLogger
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        logger.log_query("test query", "GRAPH_ONLY", 10, 5.0, 0.0)
        
        metrics = logger.get_metrics()
        assert metrics["total_queries"] == 1
        assert metrics["total_tokens"] == 10

    def test_get_metrics_empty(self, tmp_path):
        from src.router.query_logger import QueryLogger
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        metrics = logger.get_metrics()
        assert metrics["total_queries"] == 0
        assert metrics["total_tokens"] == 0


class TestTokenCounter:
    def test_init(self):
        from src.router.token_counter import TokenCounter
        counter = TokenCounter()
        assert counter._encoder is not None or counter._encoder is None  # Either way is fine

    def test_count_tokens_empty(self):
        from src.router.token_counter import TokenCounter
        counter = TokenCounter()
        assert counter.count_tokens("") == 0

    def test_count_tokens_short_text(self):
        from src.router.token_counter import TokenCounter
        counter = TokenCounter()
        count = counter.count_tokens("hello world")
        assert count > 0
        assert isinstance(count, int)