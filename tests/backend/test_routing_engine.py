import pytest
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
from dataclasses import FrozenInstanceError

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.router.routing_engine import RoutingEngine, RoutingResult


class TestRoutingResult:
    def test_routing_result_creation(self):
        result = RoutingResult(
            answer="test answer",
            tier="GRAPH_ONLY",
            tokens_used=100,
            response_time_ms=50.5,
            savings="100%",
            reasoning="test reasoning",
            dollar_cost=0.002,
        )
        assert result.answer == "test answer"
        assert result.tier == "GRAPH_ONLY"
        assert result.tokens_used == 100
        assert result.response_time_ms == 50.5
        assert result.savings == "100%"
        assert result.reasoning == "test reasoning"
        assert result.dollar_cost == 0.002

    def test_routing_result_with_warning(self):
        result = RoutingResult(
            answer="fallback answer",
            tier="GRAPH_ONLY",
            tokens_used=0,
            response_time_ms=30.0,
            savings="100%",
            reasoning="LLM unavailable",
            dollar_cost=0.0,
            warning="LLM unavailable. Falling back to GRAPH_ONLY.",
        )
        assert result.warning is not None
        assert "LLM unavailable" in result.warning

    def test_routing_result_frozen(self):
        result = RoutingResult(
            answer="test",
            tier="GRAPH_RAG",
            tokens_used=50,
            response_time_ms=25.0,
            savings="75%",
            reasoning="test",
            dollar_cost=0.001,
        )
        with pytest.raises(FrozenInstanceError):
            result.answer = "new answer"

    def test_routing_result_to_dict(self):
        result = RoutingResult(
            answer="test",
            tier="LLM_FULL",
            tokens_used=200,
            response_time_ms=100.0,
            savings="0%",
            reasoning="complex query",
            dollar_cost=0.004,
        )
        result_dict = result.__dict__
        assert isinstance(result_dict, dict)
        assert result_dict["tier"] == "LLM_FULL"
        assert result_dict["answer"] == "test"


class TestRoutingEngineInit:
    def test_init_default(self):
        with patch('src.router.routing_engine.QueryClassifier'), \
             patch('src.router.routing_engine.QueryEngine'), \
             patch('src.router.routing_engine.LLMClient'), \
             patch('src.router.routing_engine.TokenCounter'), \
             patch('src.router.routing_engine.QueryLogger'):
            engine = RoutingEngine()
            assert engine is not None

    def test_init_custom_components(self):
        mock_classifier = MagicMock()
        mock_query_engine = MagicMock()
        mock_llm_client = MagicMock()
        mock_token_counter = MagicMock()
        mock_query_logger = MagicMock()

        engine = RoutingEngine(
            classifier=mock_classifier,
            query_engine=mock_query_engine,
            llm_client=mock_llm_client,
            token_counter=mock_token_counter,
            query_logger=mock_query_logger,
        )

        assert engine.classifier == mock_classifier
        assert engine.query_engine == mock_query_engine
        assert engine.llm_client == mock_llm_client
        assert engine.token_counter == mock_token_counter
        assert engine.query_logger == mock_query_logger


class TestRoutingEngineRoute:
    def test_route_graph_only_tier(self):
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = {
            "tier": "GRAPH_ONLY",
            "confidence": 0.9,
            "reasoning": "Simple factoid query",
        }
        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = True
        mock_query_engine.get_function.return_value = {
            "result": [{"name": "test_func"}],
            "node_count": 1,
            "edge_count": 0,
            "backend_used": "sqlite",
        }

        engine = RoutingEngine(
            classifier=mock_classifier,
            query_engine=mock_query_engine,
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        result = engine.route("function test_func")
        assert result["tier"] == "GRAPH_ONLY"
        assert result["answer"] != "Graph-only answer unavailable or graph not ready."

    def test_route_graph_rag_tier_success(self):
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = {
            "tier": "GRAPH_RAG",
            "confidence": 0.8,
            "reasoning": "Relationship query",
        }
        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = True
        mock_query_engine.get_function.return_value = {"result": [{"name": "func1"}]}
        mock_query_engine.get_class.return_value = {"result": []}

        mock_llm_client = MagicMock()
        mock_llm_client.generate.return_value = "LLM response based on context"

        mock_token_counter = MagicMock()
        mock_token_counter.count_tokens.return_value = 50

        mock_query_logger = MagicMock()

        engine = RoutingEngine(
            classifier=mock_classifier,
            query_engine=mock_query_engine,
            llm_client=mock_llm_client,
            token_counter=mock_token_counter,
            query_logger=mock_query_logger,
        )

        result = engine.route("How are func1 and func2 related?")
        assert result["tier"] == "GRAPH_RAG"
        assert result["answer"] == "LLM response based on context"
        assert result["tokens_used"] == 50
        assert result["dollar_cost"] > 0

    def test_route_graph_rag_llm_fallback(self):
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = {
            "tier": "GRAPH_RAG",
            "confidence": 0.8,
            "reasoning": "Relationship query",
        }
        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = True
        mock_query_engine.get_function.return_value = {"result": []}

        mock_llm_client = MagicMock()
        mock_llm_client.generate.return_value = "OpenRouter request failed: Connection error"

        mock_query_logger = MagicMock()

        engine = RoutingEngine(
            classifier=mock_classifier,
            query_engine=mock_query_engine,
            llm_client=mock_llm_client,
            token_counter=MagicMock(),
            query_logger=mock_query_logger,
        )

        result = engine.route("How are func1 and func2 related?")
        assert result["tier"] == "GRAPH_ONLY"
        assert result["warning"] is not None
        assert "LLM unavailable" in result["warning"]

    def test_route_llm_full_tier(self):
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = {
            "tier": "LLM_FULL",
            "confidence": 0.7,
            "reasoning": "Complex open-ended query",
        }

        mock_llm_client = MagicMock()
        mock_llm_client.generate.return_value = "Comprehensive LLM response"

        mock_token_counter = MagicMock()
        mock_token_counter.count_tokens.return_value = 150

        engine = RoutingEngine(
            classifier=mock_classifier,
            query_engine=MagicMock(),
            llm_client=mock_llm_client,
            token_counter=mock_token_counter,
            query_logger=MagicMock(),
        )

        result = engine.route("Explain the authentication architecture in detail")
        assert result["tier"] == "LLM_FULL"
        assert result["answer"] == "Comprehensive LLM response"
        assert result["tokens_used"] == 150

    def test_route_llm_full_fallback_to_graph(self):
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = {
            "tier": "LLM_FULL",
            "confidence": 0.7,
            "reasoning": "Complex query",
        }

        mock_llm_client = MagicMock()
        mock_llm_client.generate.return_value = "OpenRouter request failed: Timeout"

        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = True
        mock_query_engine.get_function.return_value = {"result": []}

        engine = RoutingEngine(
            classifier=mock_classifier,
            query_engine=mock_query_engine,
            llm_client=mock_llm_client,
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        result = engine.route("Explain the architecture")
        assert result["tier"] == "GRAPH_ONLY"
        assert result["warning"] is not None

    def test_route_response_time_recorded(self):
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = {
            "tier": "GRAPH_ONLY",
            "confidence": 0.9,
            "reasoning": "Simple query",
        }
        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = False

        engine = RoutingEngine(
            classifier=mock_classifier,
            query_engine=mock_query_engine,
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        result = engine.route("simple query")
        assert result["response_time_ms"] >= 0


class TestRoutingEngineGraphOnlyAnswer:
    def test_graph_only_calls_query(self):
        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = True
        mock_query_engine.get_callers.return_value = {
            "result": [{"id": "func:caller", "name": "caller"}],
            "node_count": 1,
            "edge_count": 1,
            "backend_used": "sqlite",
        }

        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=mock_query_engine,
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        answer = engine._graph_only_answer("What functions calls parse_file?")
        assert "caller" in answer or "callers" in answer.lower()

    def test_graph_only_callee_query(self):
        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = True
        mock_query_engine.get_callees.return_value = {
            "result": [{"id": "func:callee", "name": "callee"}],
            "node_count": 1,
            "edge_count": 1,
            "backend_used": "sqlite",
        }

        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=mock_query_engine,
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        answer = engine._graph_only_answer("what does parse_file call?")
        assert "callee" in answer or "callees" in answer.lower()

    def test_graph_only_class_query(self):
        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = True
        mock_query_engine.get_class.return_value = {
            "result": [{"id": "class:MyClass", "name": "MyClass"}],
            "node_count": 1,
            "edge_count": 0,
            "backend_used": "sqlite",
        }

        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=mock_query_engine,
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        answer = engine._graph_only_answer("What does class MyClass do?")
        assert "MyClass" in answer

    def test_graph_only_function_query(self):
        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = True
        mock_query_engine.get_function.return_value = {
            "result": [{"id": "func:my_func", "name": "my_func"}],
            "node_count": 1,
            "edge_count": 0,
            "backend_used": "sqlite",
        }

        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=mock_query_engine,
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        answer = engine._graph_only_answer("What does function my_func do?")
        assert "my_func" in answer

    def test_graph_only_not_ready(self):
        mock_query_engine = MagicMock()
        mock_query_engine.is_graph_ready.return_value = False

        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=mock_query_engine,
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        answer = engine._graph_only_answer("What does func do?")
        assert "unavailable" in answer.lower() or "not ready" in answer.lower()


class TestRoutingEngineHelperMethods:
    def test_graph_context(self):
        mock_query_engine = MagicMock()
        mock_query_engine.get_function.return_value = {
            "result": [{"name": "func1"}],
            "node_count": 1,
            "edge_count": 0,
            "backend_used": "sqlite",
        }
        mock_query_engine.get_class.return_value = {
            "result": [],
            "node_count": 0,
            "edge_count": 0,
            "backend_used": "sqlite",
        }

        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=mock_query_engine,
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        context = engine._graph_context("tell me about func1")
        assert "func1" in context

    def test_graph_context_no_entity(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        context = engine._graph_context("")
        assert context == ""

    def test_build_rag_prompt_with_context(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        prompt = engine._build_rag_prompt("What is X?", "Some context here")
        assert "Question:" in prompt
        assert "What is X?" in prompt
        assert "Context:" in prompt

    def test_build_rag_prompt_no_context(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        prompt = engine._build_rag_prompt("What is X?", "")
        assert prompt == "What is X?"

    def test_estimate_cost(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        cost = engine._estimate_cost(1000)
        expected = round(1000 * 0.00002, 4)
        assert cost == expected

    def test_format_savings_graph_only(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        savings = engine._format_savings("GRAPH_ONLY", 0)
        assert savings == "100% (zero tokens)"

    def test_format_savings_graph_rag(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        savings = engine._format_savings("GRAPH_RAG", 50)
        assert savings == "67% (50 vs ~150 tokens)"

    def test_format_savings_llm_full(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        savings = engine._format_savings("LLM_FULL", 200)
        assert savings == "0% (no savings)"

    def test_format_savings_llm_full_no_tokens(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        savings = engine._format_savings("LLM_FULL", 0)
        assert savings == "0% (no savings)"

    def test_extract_entity_with_quotes(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        entity = engine._extract_entity("'my_function'")
        assert entity == "my_function"

    def test_extract_entity_without_quotes(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        entity = engine._extract_entity("my_function")
        assert entity == "my_function"

    def test_extract_entity_colon_format(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        entity = engine._extract_entity("class:MyClass")
        assert entity == "class:MyClass"

    def test_extract_entity_no_match(self):
        engine = RoutingEngine(
            classifier=MagicMock(),
            query_engine=MagicMock(),
            llm_client=MagicMock(),
            token_counter=MagicMock(),
            query_logger=MagicMock(),
        )

        entity = engine._extract_entity("What is this?")
        assert entity == "What"
