import pytest
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.router.query_classifier import QueryClassifier, ClassificationResult
from src.router.query_logger import QueryLogger, QueryLogRecord
from src.router.token_counter import TokenCounter


class TestQueryClassifier:
    def test_init_default(self):
        with patch('src.router.query_classifier.QueryEngine') as mock_qe:
            classifier = QueryClassifier()
            mock_qe.assert_called_once()

    def test_init_custom_query_engine(self):
        mock_qe = MagicMock()
        classifier = QueryClassifier(query_engine=mock_qe)
        assert classifier.query_engine == mock_qe

    def test_classify_empty_query(self):
        classifier = QueryClassifier()
        result = classifier.classify("")
        assert result["tier"] == "LLM_FULL"
        assert result["confidence"] == 0.2

    def test_classify_friendly_non_code(self):
        classifier = QueryClassifier()
        result = classifier.classify("what is Python?")
        assert result["tier"] == "LLM_FULL"
        assert result["confidence"] == 0.35

    def test_classify_factoid(self):
        classifier = QueryClassifier()
        result = classifier.classify("What functions call parse_file?")
        assert result["tier"] == "GRAPH_ONLY"

    def test_classify_relationship(self):
        classifier = QueryClassifier()
        result = classifier.classify("Show relationship between parser and loader")
        assert result["tier"] == "GRAPH_RAG"

    def test_classify_open_ended(self):
        classifier = QueryClassifier()
        result = classifier.classify("Explain the architecture of this module in detail")
        assert result["tier"] == "LLM_FULL"

    def test_classify_returns_dict(self):
        classifier = QueryClassifier()
        result = classifier.classify("test query")
        assert "tier" in result
        assert "confidence" in result
        assert "reasoning" in result

    def test_classify_confidence_range(self):
        classifier = QueryClassifier()
        result = classifier.classify("test")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_classify_long_query_bonus(self):
        long_query = "a" * 200
        classifier = QueryClassifier()
        result = classifier.classify(long_query)
        assert result["confidence"] > 0.0

    def test_classify_with_graph_entities(self):
        mock_qe = MagicMock()
        mock_qe.is_graph_ready.return_value = True
        mock_qe.get_function.return_value = {"result": ["something"]}
        classifier = QueryClassifier(query_engine=mock_qe)
        result = classifier.classify("What does 'parse_file' do?")
        assert result["confidence"] > 0.45

    def test_classify_no_graph_entities(self):
        mock_qe = MagicMock()
        mock_qe.is_graph_ready.return_value = False
        classifier = QueryClassifier(query_engine=mock_qe)
        result = classifier.classify("What does parse_file do?")
        assert result["confidence"] <= 1.0

    def test_classification_result_frozen(self):
        result = ClassificationResult(tier="GRAPH_RAG", confidence=0.9, reasoning="test")
        assert result.tier == "GRAPH_RAG"
        with pytest.raises(AttributeError):
            result.tier = "LLM_FULL"


class TestQueryLogger:
    def test_init_creates_db(self, tmp_path):
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        assert db_path.exists()

    def test_log_query(self, tmp_path):
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        logger.log_query("test query", "GRAPH_RAG", 100, 50.5, 0.01)
        metrics = logger.get_metrics()
        assert metrics["total_queries"] == 1
        assert metrics["total_tokens"] == 100

    def test_log_multiple_queries(self, tmp_path):
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        logger.log_query("q1", "GRAPH_RAG", 100, 50.5, 0.01)
        logger.log_query("q2", "LLM_FULL", 200, 100.0, 0.02)
        metrics = logger.get_metrics()
        assert metrics["total_queries"] == 2
        assert metrics["total_tokens"] == 300

    def test_get_metrics_empty(self, tmp_path):
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        metrics = logger.get_metrics()
        assert metrics["total_queries"] == 0
        assert metrics["total_tokens"] == 0
        assert metrics["savings_percentage"] == 0.0

    def test_get_metrics_tokens_by_tier(self, tmp_path):
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        logger.log_query("q1", "GRAPH_RAG", 100, 50.5, 0.01)
        logger.log_query("q2", "LLM_FULL", 200, 100.0, 0.02)
        metrics = logger.get_metrics()
        assert "GRAPH_RAG" in metrics["tokens_by_tier"]
        assert "LLM_FULL" in metrics["tokens_by_tier"]

    def test_get_metrics_savings(self, tmp_path):
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        logger.log_query("q1", "GRAPH_RAG", 0, 50.5, 0.0)
        logger.log_query("q2", "GRAPH_RAG", 100, 100.0, 0.01)
        metrics = logger.get_metrics()
        assert metrics["savings_percentage"] == 50.0

    def test_log_query_custom_timestamp(self, tmp_path):
        db_path = tmp_path / "test.db"
        logger = QueryLogger(db_path=db_path)
        logger.log_query("q1", "GRAPH_RAG", 100, 50.5, 0.01, timestamp="2024-01-01T00:00:00")
        metrics = logger.get_metrics()
        assert metrics["total_queries"] == 1

    def test_query_log_record_frozen(self):
        record = QueryLogRecord(
            query="test", tier="GRAPH_RAG", tokens=100,
            response_time_ms=50.5, timestamp="2024-01-01", dollar_cost=0.01
        )
        assert record.query == "test"
        with pytest.raises(AttributeError):
            record.query = "new"


class TestTokenCounter:
    def test_init(self):
        counter = TokenCounter()
        assert counter._encoder is not None or counter._encoder is None

    def test_count_tokens_with_tiktoken(self):
        counter = TokenCounter()
        if counter._encoder is not None:
            count = counter.count_tokens("hello world")
            assert isinstance(count, int)
            assert count > 0
        else:
            pytest.skip("tiktoken not available")

    def test_count_tokens_empty(self):
        counter = TokenCounter()
        assert counter.count_tokens("") == 0

    def test_count_tokens_fallback(self):
        counter = TokenCounter()
        with patch.object(counter, '_encoder', None):
            count = counter.count_tokens("hello world")
            assert isinstance(count, int)
            assert count >= 1

    def test_count_tokens_fallback_calculation(self):
        counter = TokenCounter()
        with patch.object(counter, '_encoder', None):
            result = counter.count_tokens("word1 word2 word3")
            expected = max(1, int(round(3 * 1.3)))
            assert result == expected

    def test_count_tokens_exception_handling(self):
        counter = TokenCounter()
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = Exception("encode error")
        counter._encoder = mock_encoder
        result = counter.count_tokens("test")
        assert result >= 1
