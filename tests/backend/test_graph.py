import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys_path = Path(__file__).parent.parent / "src"
import sys
sys.path.insert(0, str(sys_path))

from src.graph.query_engine import QueryEngine
from src.graph.sqlite_fallback import SQLiteNetworkXFallback, _SimpleDiGraph
from src.graph.ingestion import GraphIngestionPipeline, ingest_codebase


class TestSimpleDiGraph:
    def test_add_node(self):
        g = _SimpleDiGraph()
        g.add_node("n1", type="function")
        assert "n1" in g
        assert g.node_data("n1")["type"] == "function"

    def test_add_edge(self):
        g = _SimpleDiGraph()
        g.add_node("n1")
        g.add_node("n2")
        g.add_edge("n1", "n2", type="calls")
        assert "n2" in list(g.successors("n1"))
        assert "n1" in list(g.predecessors("n2"))

    def test_subgraph(self):
        g = _SimpleDiGraph()
        g.add_node("n1")
        g.add_node("n2")
        g.add_node("n3")
        g.add_edge("n1", "n2")
        g.add_edge("n2", "n3")
        
        sg = g.subgraph(["n1", "n2"])
        assert "n1" in sg.nodes()
        assert "n3" not in sg.nodes()

    def test_copy(self):
        g = _SimpleDiGraph()
        g.add_node("n1", type="test")
        g.add_edge("n1", "n2")
        
        copy_g = g.copy()
        assert "n1" in copy_g
        assert copy_g.node_data("n1")["type"] == "test"


class TestSQLiteNetworkXFallback:
    def test_init(self, tmp_path):
        db_path = tmp_path / "test.db"
        fallback = SQLiteNetworkXFallback(db_path=db_path)
        assert fallback.db_path == db_path
        assert db_path.exists()

    def test_add_and_query_node(self, tmp_path):
        db_path = tmp_path / "test.db"
        fallback = SQLiteNetworkXFallback(db_path=db_path)
        fallback.add_node("function:test", "function", {"name": "test"})
        
        result = fallback.query("function:test")
        assert result["id"] == "function:test"
        assert result["data"]["type"] == "function"

    def test_add_edge(self, tmp_path):
        db_path = tmp_path / "test.db"
        fallback = SQLiteNetworkXFallback(db_path=db_path)
        fallback.add_node("n1")
        fallback.add_node("n2")
        fallback.add_edge("n1", "n2", "calls")
        
        result = fallback.query("n1")
        assert "n2" in result["out"]

    def test_get_subgraph(self, tmp_path):
        db_path = tmp_path / "test.db"
        fallback = SQLiteNetworkXFallback(db_path=db_path)
        fallback.add_node("n1")
        fallback.add_node("n2")
        fallback.add_node("n3")
        fallback.add_edge("n1", "n2")
        fallback.add_edge("n2", "n3")
        
        sg = fallback.get_subgraph(["n1"], depth=2)
        assert "n1" in sg.nodes()
        assert "n2" in sg.nodes()
        assert "n3" in sg.nodes()

    def test_pragma_journal_mode(self, tmp_path):
        db_path = tmp_path / "test.db"
        fallback = SQLiteNetworkXFallback(db_path=db_path)
        mode = fallback.pragma_journal_mode()
        assert mode.upper() == "WAL"


class TestQueryEngine:
    def test_init(self):
        engine = QueryEngine()
        assert engine.params is not None
        assert engine._tigergraph is not None
        assert engine._sqlite is None

    def test_is_graph_ready_no_backend(self, monkeypatch):
        engine = QueryEngine()
        # Mock TigerGraph to fail and SQLite to have no nodes
        monkeypatch.setattr(engine._tigergraph, "test_connection", lambda: False)
        mock_sqlite = MagicMock()
        mock_sqlite.graph.nodes.return_value = []
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)
        assert engine.is_graph_ready() is False

    def test_get_function_sqlite_fallback(self, monkeypatch):
        engine = QueryEngine()
        # Mock SQLite with a function node
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.return_value = True
        mock_sqlite.graph.node_data.return_value = {"name": "test"}
        mock_sqlite.graph.successors.return_value = []
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)
        monkeypatch.setattr(engine._tigergraph, "test_connection", lambda: False)
        
        result = engine.get_function("test")
        assert "result" in result
        assert result["backend_used"] == "sqlite"

    def test_get_class(self, monkeypatch):
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.return_value = True
        mock_sqlite.graph.node_data.return_value = {"name": "Test"}
        mock_sqlite.graph.successors.return_value = []
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)
        monkeypatch.setattr(engine._tigergraph, "test_connection", lambda: False)

        result = engine.get_class("Test")
        assert "result" in result

    def test_get_callers(self, monkeypatch):
        """Test get_callers method"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.return_value = True
        mock_sqlite.graph.predecessors.return_value = ["function:caller1", "function:caller2"]
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_callers("test_func")
        assert "result" in result
        assert result["backend_used"] == "sqlite"
        assert len(result["result"]) == 2
        assert result["result"][0]["name"] == "caller1"

    def test_get_callees(self, monkeypatch):
        """Test get_callees method"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.return_value = True
        mock_sqlite.graph.successors.return_value = ["function:callee1", "function:callee2"]
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_callees("test_func")
        assert "result" in result
        assert result["backend_used"] == "sqlite"
        assert len(result["result"]) == 2
        assert result["result"][0]["name"] == "callee1"

    def test_get_imports(self, monkeypatch):
        """Test get_imports method"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.return_value = True
        mock_sqlite.graph.successors.return_value = ["module:import1", "module:import2"]
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_imports("test_module")
        assert "result" in result
        assert result["backend_used"] == "sqlite"
        assert len(result["result"]) == 2

    def test_get_inheritance(self, monkeypatch):
        """Test get_inheritance method"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.return_value = True
        mock_sqlite.graph.predecessors.return_value = ["class:ParentClass"]
        mock_sqlite.graph.successors.return_value = ["class:ChildClass"]
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_inheritance("TestClass")
        assert "result" in result
        assert "parents" in result["result"]
        assert "children" in result["result"]
        assert "ParentClass" in result["result"]["parents"]
        assert "ChildClass" in result["result"]["children"]

    def test_get_subgraph(self, monkeypatch):
        """Test get_subgraph method"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.return_value = True
        
        # Create a mock graph structure
        mock_graph = MagicMock()
        mock_graph.nodes.return_value = ["function:test", "function:related1", "function:related2"]
        mock_graph.edges.return_value = [("function:test", "function:related1"), ("function:related1", "function:related2")]
        mock_sqlite.graph.subgraph.return_value = mock_graph
        mock_sqlite.graph.successors.return_value = ["function:related1"]
        mock_sqlite.graph.predecessors.return_value = []
        
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_subgraph("test", depth=2)
        assert "result" in result
        assert "nodes" in result["result"]
        assert "edges" in result["result"]
        assert len(result["result"]["nodes"]) > 0

    def test_get_subgraph_with_class_entity(self, monkeypatch):
        """Test get_subgraph with class entity"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        
        # First call for function:test returns False, second call for class:test returns True
        mock_sqlite.graph.__contains__ = MagicMock(side_effect=[False, True, True, True])
        
        mock_graph = MagicMock()
        mock_graph.nodes.return_value = ["class:test", "function:method1"]
        mock_graph.edges.return_value = [("class:test", "function:method1")]
        mock_sqlite.graph.subgraph.return_value = mock_graph
        mock_sqlite.graph.successors.return_value = ["function:method1"]
        mock_sqlite.graph.predecessors.return_value = []
        
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_subgraph("test", depth=1)
        assert "result" in result
        assert len(result["result"]["nodes"]) > 0

    def test_get_subgraph_with_module_entity(self, monkeypatch):
        """Test get_subgraph with module entity"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        
        # First two calls return False, third call for module:test returns True
        mock_sqlite.graph.__contains__ = MagicMock(side_effect=[False, False, True, True, True])
        
        mock_graph = MagicMock()
        mock_graph.nodes.return_value = ["module:test", "function:func1", "class:Class1"]
        mock_graph.edges.return_value = [("module:test", "function:func1"), ("module:test", "class:Class1")]
        mock_sqlite.graph.subgraph.return_value = mock_graph
        mock_sqlite.graph.successors.return_value = ["function:func1", "class:Class1"]
        mock_sqlite.graph.predecessors.return_value = []
        
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_subgraph("test", depth=1)
        assert "result" in result
        assert len(result["result"]["nodes"]) > 0

    def test_get_subgraph_entity_not_found(self, monkeypatch):
        """Test get_subgraph when entity is not found"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        
        # All entity types return False
        mock_sqlite.graph.__contains__ = MagicMock(return_value=False)
        
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_subgraph("nonexistent", depth=1)
        assert "result" in result
        assert result["result"]["nodes"] == []
        assert result["result"]["edges"] == []

    def test_is_graph_ready_with_tigergraph(self, monkeypatch):
        """Test is_graph_ready when TigerGraph is available"""
        engine = QueryEngine()
        monkeypatch.setattr(engine._tigergraph, "test_connection", lambda: True)
        
        result = engine.is_graph_ready()
        assert result is True

    def test_is_graph_ready_cache(self, monkeypatch):
        import time
        engine = QueryEngine()
        engine._graph_ready_cache = True
        engine._graph_ready_cache_time = time.monotonic() - 2  # within 5s TTL
        
        result = engine.is_graph_ready()
        assert result is True

    def test_get_function_error_handling(self, monkeypatch):
        """Test get_function error handling"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.side_effect = Exception("DB error")
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)
        monkeypatch.setattr(engine._tigergraph, "test_connection", lambda: False)

        result = engine.get_function("test")
        assert "result" in result
        assert "error" in result["result"][0]

    def test_get_class_error_handling(self, monkeypatch):
        """Test get_class error handling"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.side_effect = Exception("DB error")
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)
        monkeypatch.setattr(engine._tigergraph, "test_connection", lambda: False)

        result = engine.get_class("test")
        assert "result" in result
        assert "error" in result["result"][0]

    def test_get_inheritance_error_handling(self, monkeypatch):
        """Test get_inheritance error handling"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.side_effect = Exception("DB error")
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_inheritance("test")
        assert "result" in result
        assert "error" in result["result"]

    def test_get_subgraph_error_handling(self, monkeypatch):
        """Test get_subgraph error handling"""
        engine = QueryEngine()
        mock_sqlite = MagicMock()
        mock_sqlite.graph.__contains__.side_effect = Exception("DB error")
        monkeypatch.setattr(engine, "_get_sqlite", lambda: mock_sqlite)

        result = engine.get_subgraph("test")
        assert "result" in result
        assert "error" in result["result"]


class TestGraphIngestionPipeline:
    def test_init(self, tmp_path):
        pipeline = GraphIngestionPipeline(tmp_path)
        assert pipeline.codebase_path == tmp_path
        assert pipeline.backend_type == "unknown"

    def test_select_backend_sqlite(self, monkeypatch, tmp_path):
        pipeline = GraphIngestionPipeline(tmp_path)
        mock_tg = MagicMock()
        mock_tg.test_connection.return_value = False
        pipeline.tigergraph_client = mock_tg
        
        result = pipeline._select_backend()
        assert result is True
        assert pipeline.backend_type in ["sqlite", "tigergraph"]

    def test_run_with_sqlite(self, monkeypatch, tmp_path):
        pipeline = GraphIngestionPipeline(tmp_path)
        # Mock all dependencies
        mock_parser = MagicMock()
        mock_parser.parse_codebase.return_value = {
            "nodes": [{"id": "n1", "type": "function", "attributes": {}}],
            "edges": [],
            "metadata": {"files_parsed": 1, "nodes_extracted": 1, "edges_extracted": 0}
        }
        pipeline.parser = mock_parser
        
        # Mock backend selection to use SQLite
        pipeline._select_backend = MagicMock(return_value=True)
        pipeline.backend_type = "sqlite"
        pipeline.sqlite_backend = MagicMock()
        pipeline.sqlite_backend.add_node = MagicMock()
        pipeline.sqlite_backend.add_edge = MagicMock()
        pipeline._verify_graph_health = MagicMock(return_value={"status": "healthy"})
        pipeline._run_vector_ingestion = MagicMock(return_value={"success": True})
        
        result = pipeline.run()
        assert result["success"] is True
        assert result["backend_type"] == "sqlite"
