import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from src.router.routing_engine import RoutingEngine, RoutingResult
from src.router.query_classifier import QueryClassifier

class TestRoutingEngine:
    def test_route_returns_tier(self):
        engine = RoutingEngine()
        result = engine.route("test query")
        assert "tier" in result
        assert result["tier"] in ["GRAPH_ONLY", "GRAPH_RAG", "LLM_FULL"]

    def test_route_includes_reasoning(self):
        engine = RoutingEngine()
        result = engine.route("test query")
        assert "reasoning" in result

    def test_simple_query_gets_graph_only(self):
        engine = RoutingEngine()
        result = engine.route("What functions call X?")
        assert result["tier"] == "GRAPH_ONLY"

    def test_graph_rag_tier_with_llm_success(self):
        """Test GRAPH_RAG tier when LLM call succeeds"""
        engine = RoutingEngine()
        # Mock classifier to return GRAPH_RAG
        engine.classifier.classify = MagicMock(return_value={"tier": "GRAPH_RAG", "reasoning": "test"})
        # Mock LLM to succeed
        engine.llm_client.generate = MagicMock(return_value="LLM answer")
        # Mock graph context
        engine._graph_context = MagicMock(return_value="context")
        
        result = engine.route("test query")
        
        assert result["tier"] == "GRAPH_RAG"
        assert result["answer"] == "LLM answer"
        assert result["tokens_used"] > 0

    def test_graph_rag_tier_with_llm_failure_fallback(self):
        """Test GRAPH_RAG tier falls back to GRAPH_ONLY when LLM fails"""
        engine = RoutingEngine()
        # Mock classifier to return GRAPH_RAG
        engine.classifier.classify = MagicMock(return_value={"tier": "GRAPH_RAG", "reasoning": "test"})
        # Mock LLM to fail
        engine.llm_client.generate = MagicMock(return_value="OpenRouter request failed")
        # Mock graph methods
        engine._graph_context = MagicMock(return_value="context")
        engine._graph_only_answer = MagicMock(return_value="Graph answer")
        
        result = engine.route("test query")
        
        assert result["tier"] == "GRAPH_ONLY"
        assert result["warning"] is not None
        assert "LLM unavailable" in result["warning"]

    def test_llm_full_tier_with_llm_success(self):
        """Test LLM_FULL tier when LLM call succeeds"""
        engine = RoutingEngine()
        # Mock classifier to return LLM_FULL
        engine.classifier.classify = MagicMock(return_value={"tier": "LLM_FULL", "reasoning": "test"})
        # Mock LLM to succeed
        engine.llm_client.generate = MagicMock(return_value="Full LLM answer")
        
        result = engine.route("test query")
        
        assert result["tier"] == "LLM_FULL"
        assert result["answer"] == "Full LLM answer"
        assert result["tokens_used"] > 0

    def test_llm_full_tier_with_llm_failure_fallback(self):
        """Test LLM_FULL tier falls back to GRAPH_ONLY when LLM fails"""
        engine = RoutingEngine()
        # Mock classifier to return LLM_FULL
        engine.classifier.classify = MagicMock(return_value={"tier": "LLM_FULL", "reasoning": "test"})
        # Mock LLM to fail
        engine.llm_client.generate = MagicMock(return_value="OpenRouter request failed")
        # Mock graph method
        engine._graph_only_answer = MagicMock(return_value="Graph answer")
        
        result = engine.route("test query")
        
        assert result["tier"] == "GRAPH_ONLY"
        assert result["warning"] is not None
        assert "LLM unavailable" in result["warning"]

    def test_graph_only_answer_with_callers_query(self):
        """Test _graph_only_answer with callers query"""
        engine = RoutingEngine()
        engine.query_engine.is_graph_ready = MagicMock(return_value=True)
        engine.query_engine.get_callers = MagicMock(return_value={"result": [{"name": "func1"}]})
        engine._extract_entity = MagicMock(return_value="test_func")
        
        result = engine._graph_only_answer("What functions calls test_func?")
        
        assert "Found callers" in result
        engine.query_engine.get_callers.assert_called_once()

    def test_graph_only_answer_with_callees_query(self):
        """Test _graph_only_answer with callees query"""
        engine = RoutingEngine()
        engine.query_engine.is_graph_ready = MagicMock(return_value=True)
        engine.query_engine.get_callees = MagicMock(return_value={"result": [{"name": "func1"}]})
        engine._extract_entity = MagicMock(return_value="test_func")
        
        result = engine._graph_only_answer("What does test_func call?")
        
        assert "Found callees" in result
        engine.query_engine.get_callees.assert_called_once()

    def test_graph_only_answer_with_class_query(self):
        """Test _graph_only_answer with class query"""
        engine = RoutingEngine()
        engine.query_engine.is_graph_ready = MagicMock(return_value=True)
        engine.query_engine.get_class = MagicMock(return_value={"result": ["class1"]})
        engine._extract_entity = MagicMock(return_value="TestClass")
        
        result = engine._graph_only_answer("What is class TestClass?")
        
        assert "['class1']" in result
        engine.query_engine.get_class.assert_called_once()

    def test_graph_only_answer_with_function_query(self):
        """Test _graph_only_answer with function query"""
        engine = RoutingEngine()
        engine.query_engine.is_graph_ready = MagicMock(return_value=True)
        engine.query_engine.get_function = MagicMock(return_value={"result": ["func1"]})
        engine._extract_entity = MagicMock(return_value="test_func")
        
        result = engine._graph_only_answer("What is function test_func?")
        
        assert "['func1']" in result
        engine.query_engine.get_function.assert_called_once()

    def test_graph_only_answer_graph_not_ready(self):
        """Test _graph_only_answer when graph is not ready"""
        engine = RoutingEngine()
        engine.query_engine.is_graph_ready = MagicMock(return_value=False)
        
        result = engine._graph_only_answer("What functions call test_func?")
        
        assert "Graph-only answer unavailable" in result

    def test_graph_context_with_entity(self):
        """Test _graph_context with valid entity"""
        engine = RoutingEngine()
        engine.query_engine.get_function = MagicMock(return_value={"result": ["func_data"]})
        engine.query_engine.get_class = MagicMock(return_value={"result": ["class_data"]})
        engine._extract_entity = MagicMock(return_value="test_entity")
        
        result = engine._graph_context("What is test_entity?")
        
        assert "function=" in result
        assert "class=" in result

    def test_graph_context_without_entity(self):
        """Test _graph_context without valid entity"""
        engine = RoutingEngine()
        engine._extract_entity = MagicMock(return_value="")
        
        result = engine._graph_context("What is?")
        
        assert result == ""

    def test_build_rag_prompt_with_context(self):
        """Test _build_rag_prompt with context"""
        engine = RoutingEngine()
        
        result = engine._build_rag_prompt("What is X?", "Context: data")
        
        assert "Question: What is X?" in result
        assert "Context: data" in result

    def test_build_rag_prompt_without_context(self):
        """Test _build_rag_prompt without context"""
        engine = RoutingEngine()
        
        result = engine._build_rag_prompt("What is X?", "")
        
        assert result == "What is X?"

    def test_estimate_cost(self):
        """Test _estimate_cost calculation"""
        engine = RoutingEngine()
        
        cost = engine._estimate_cost(1000)
        
        assert cost == 0.02  # 1000 * 0.00002


class TestRoutingEngineFormatting:
    def test_format_savings_graph_only(self):
        """Test _format_savings for GRAPH_ONLY tier"""
        engine = RoutingEngine()

        savings = engine._format_savings("GRAPH_ONLY", 100)

        assert savings == "100% (zero tokens)"
    
    def test_format_savings_graph_rag(self):
        """Test _format_savings for GRAPH_RAG tier"""
        engine = RoutingEngine()
        
        savings = engine._format_savings("GRAPH_RAG", 100)
        
        assert savings == "67% (100 vs ~300 tokens)"
    
    def test_format_savings_llm_full_with_tokens(self):
        """Test _format_savings for LLM_FULL tier with tokens"""
        engine = RoutingEngine()
        
        savings = engine._format_savings("LLM_FULL", 100)
        
        assert savings == "0% (no savings)"
    
    def test_format_savings_llm_full_no_tokens(self):
        """Test _format_savings for LLM_FULL tier with no tokens"""
        engine = RoutingEngine()
        
        savings = engine._format_savings("LLM_FULL", 0)
        
        assert savings == "0% (no savings)"

    def test_extract_entity_with_quotes(self):
        """Test _extract_entity with quoted entity"""
        engine = RoutingEngine()
        
        entity = engine._extract_entity('What is "TestClass"?')
        
        assert entity == "TestClass"

    def test_extract_entity_without_quotes(self):
        """Test _extract_entity without quotes"""
        engine = RoutingEngine()
        
        entity = engine._extract_entity("What is TestClass?")
        
        assert entity == "TestClass"

    def test_extract_entity_first_word(self):
        """Test _extract_entity returns first word when no match"""
        engine = RoutingEngine()
        
        entity = engine._extract_entity("test")
        
        assert entity == "test"

    def test_routing_result_structure(self):
        """Test RoutingResult dataclass structure"""
        result = RoutingResult(
            answer="test answer",
            tier="GRAPH_ONLY",
            tokens_used=10,
            response_time_ms=5.0,
            savings="100%",
            reasoning="test reasoning",
            dollar_cost=0.0002,
            warning=None
        )
        
        result_dict = result.__dict__
        
        assert result_dict["answer"] == "test answer"
        assert result_dict["tier"] == "GRAPH_ONLY"
        assert result_dict["tokens_used"] == 10
        assert result_dict["response_time_ms"] == 5.0
        assert result_dict["savings"] == "100%"
        assert result_dict["reasoning"] == "test reasoning"
        assert result_dict["dollar_cost"] == 0.0002
        assert result_dict["warning"] is None

class TestQueryClassifier:
    def test_classifier_identity(self):
        classifier = QueryClassifier()
        assert classifier is not None

    def test_classify_returns_tier(self):
        classifier = QueryClassifier()
        result = classifier.classify("simple question")
        assert "tier" in result
        assert result["tier"] in ["GRAPH_ONLY", "GRAPH_RAG", "LLM_FULL"]