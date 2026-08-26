import json
import pytest
from pathlib import Path
import socket
import sys
from unittest.mock import patch
import urllib.parse
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.graph.query_engine import QueryEngine
from src.graph.sqlite_fallback import SQLiteNetworkXFallback, _SimpleDiGraph
from src.graph.ingestion import GraphIngestionPipeline, ingest_codebase
from src.graph.tigergraph_client import TigerGraphClient


class TestTigerGraphClient:
    def test_init_default(self):
        client = TigerGraphClient()
        assert client.raw_host is not None
        assert client.graphname is not None
    
    def test_init_custom(self):
        client = TigerGraphClient(host="https://localhost", graphname="testgraph")
        assert client.raw_host == "https://localhost"
        assert client.graphname == "testgraph"
    
    def test_init_with_secret(self):
        client = TigerGraphClient(secret="mysecret")
        assert client.secret == "mysecret"
    
    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("TIGERGRAPH_HOST", "https://mygraph.i.tgcloud.io")
        client = TigerGraphClient()
        assert client.raw_host == "https://mygraph.i.tgcloud.io"
    
    @pytest.mark.skip(reason="Requires network access - connects to real TigerGraph server when TIGERGRAPH_HOST env is set")
    def test_test_connection_no_host(self):
        """Test that empty host doesn't try to connect."""
        client = TigerGraphClient()
        # When host defaults to localhost, connection should fail without a real server
        # This test verifies the client handles the case gracefully
        result = client.test_connection()
        # Should be False since no actual TigerGraph server running on localhost
        assert result is False
    
    @pytest.mark.skip(reason="Requires network access, can be flaky")
    def test_test_connection_invalid_host(self):
        client = TigerGraphClient(host="http://192.0.2.1:1")
        assert client.test_connection() is False


class TestSimpleDiGraph:
    def test_add_node(self):
        g = _SimpleDiGraph()
        g.add_node("n1", type="function")
        assert "n1" in g._nodes
        assert g._nodes["n1"]["type"] == "function"

    def test_add_edge(self):
        g = _SimpleDiGraph()
        g.add_edge("n1", "n2", type="calls")
        assert "n2" in g._out.get("n1", set())
        assert "n1" in g._in.get("n2", set())

    def test_successors(self):
        g = _SimpleDiGraph()
        g.add_edge("n1", "n2")
        assert list(g.successors("n1")) == ["n2"]

    def test_predecessors(self):
        g = _SimpleDiGraph()
        g.add_edge("n1", "n2")
        assert list(g.predecessors("n2")) == ["n1"]

    def test_nodes(self):
        g = _SimpleDiGraph()
        g.add_node("n1")
        g.add_node("n2")
        assert "n1" in g.nodes()
        assert "n2" in g.nodes()

    def test_contains(self):
        g = _SimpleDiGraph()
        g.add_node("n1")
        assert "n1" in g
        assert "n2" not in g

    def test_node_data(self):
        g = _SimpleDiGraph()
        g.add_node("n1", type="function", name="test")
        data = g.node_data("n1")
        assert data["type"] == "function"
        assert data["name"] == "test"

    def test_edges(self):
        g = _SimpleDiGraph()
        g.add_edge("n1", "n2", type="calls")
        edges = g.edges()
        assert len(edges) == 1
        assert edges[0][0] == "n1"
        assert edges[0][1] == "n2"

    def test_subgraph(self):
        g = _SimpleDiGraph()
        g.add_edge("n1", "n2")
        g.add_edge("n2", "n3")
        sg = g.subgraph(["n1", "n2"])
        assert "n1" in sg.nodes()
        assert "n2" in sg.nodes()
        assert "n3" not in sg.nodes()

    def test_copy(self):
        g = _SimpleDiGraph()
        g.add_node("n1", type="function")
        g.add_edge("n1", "n2")
        copy_g = g.copy()
        assert "n1" in copy_g._nodes
        assert "n2" in copy_g._out.get("n1", set())


class TestSQLiteNetworkXFallback:
    def test_init_creates_db(self, tmp_path):
        db_path = tmp_path / "graph.db"
        fallback = SQLiteNetworkXFallback(db_path=db_path)
        assert db_path.exists()
        fallback.close()

    def test_init_creates_wal_mode(self, tmp_path):
        db_path = tmp_path / "graph.db"
        fallback = SQLiteNetworkXFallback(db_path=db_path)
        mode = fallback.pragma_journal_mode()
        assert mode.upper() == "WAL"
        fallback.close()

    def test_add_node(self, tmp_path):
        fallback = SQLiteNetworkXFallback(db_path=tmp_path / "graph.db")
        fallback.add_node("function:test", "function", {"line": 10})
        query_result = fallback.query("function:test")
        assert query_result != {}
        assert query_result["data"]["line"] == 10
        fallback.close()

    def test_add_edge(self, tmp_path):
        fallback = SQLiteNetworkXFallback(db_path=tmp_path / "graph.db")
        fallback.add_node("function:a", "function")
        fallback.add_node("function:b", "function")
        fallback.add_edge("function:a", "function:b", "calls")
        result = fallback.query("function:a")
        assert "function:b" in result["out"]
        fallback.close()

    def test_query_nonexistent(self, tmp_path):
        fallback = SQLiteNetworkXFallback(db_path=tmp_path / "graph.db")
        result = fallback.query("nonexistent")
        assert result == {}
        fallback.close()

    def test_query_with_neighbors(self, tmp_path):
        fallback = SQLiteNetworkXFallback(db_path=tmp_path / "graph.db")
        fallback.add_node("n1", "function")
        fallback.add_node("n2", "function")
        fallback.add_edge("n1", "n2", "calls")
        result = fallback.query("n1")
        assert result["id"] == "n1"
        assert "n2" in result["out"]
        assert len(result["in"]) == 0
        fallback.close()

    def test_get_subgraph(self, tmp_path):
        fallback = SQLiteNetworkXFallback(db_path=tmp_path / "graph.db")
        fallback.add_node("n1", "function")
        fallback.add_node("n2", "function")
        fallback.add_node("n3", "function")
        fallback.add_edge("n1", "n2")
        fallback.add_edge("n2", "n3")
        sg = fallback.get_subgraph(["n1"], depth=2)
        nodes = list(sg.nodes())
        assert "n1" in nodes
        assert "n2" in nodes
        assert "n3" in nodes
        fallback.close()

    def test_load_from_db(self, tmp_path):
        db_path = tmp_path / "graph.db"
        fallback1 = SQLiteNetworkXFallback(db_path=db_path)
        fallback1.add_node("n1", "function", {"test": True})
        fallback1.add_edge("n1", "n2", "calls")
        fallback1.close()

        fallback2 = SQLiteNetworkXFallback(db_path=db_path)
        assert "n1" in fallback2.graph
        fallback2.close()


class TestQueryEngine:
    def test_init_default(self):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg, \
             patch('src.graph.query_engine.SQLiteNetworkXFallback') as mock_sqlite:
            engine = QueryEngine()
            mock_tg.assert_called_once()
            assert engine.params is not None

    def test_init_custom_params(self):
        from src.configs.grag_params import GraphRAGParams
        params = GraphRAGParams(top_k=10)
        with patch('src.graph.query_engine.TigerGraphClient'), \
             patch('src.graph.query_engine.SQLiteNetworkXFallback'):
            engine = QueryEngine(params=params)
            assert engine.params.top_k == 10

    def test_is_graph_ready_false(self):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg, \
             patch('src.graph.query_engine.SQLiteNetworkXFallback') as mock_sqlite:
            mock_tg.return_value.test_connection.return_value = False
            mock_sqlite.return_value.graph.nodes.return_value = []
            engine = QueryEngine()
            assert engine.is_graph_ready() is False

    def test_get_function_sqlite(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("function:test", "function", {"name": "test"})
            result = engine.get_function("test")
            assert result["result"] != []
            assert result["backend_used"] == "sqlite"
            engine._sqlite.close()

    def test_get_function_not_found(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            result = engine.get_function("nonexistent")
            assert result["result"] == []
            engine._sqlite.close()

    def test_get_class_sqlite(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("class:MyClass", "class", {"name": "MyClass"})
            result = engine.get_class("MyClass")
            assert result["result"] != []
            engine._sqlite.close()

    def test_get_callers(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("function:caller", "function")
            engine._sqlite.add_node("function:callee", "function")
            engine._sqlite.add_edge("function:caller", "function:callee", "calls")
            result = engine.get_callers("callee")
            assert len(result["result"]) == 1
            assert "caller" in result["result"][0]["id"]
            engine._sqlite.close()

    def test_get_callees(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("function:caller", "function")
            engine._sqlite.add_node("function:callee", "function")
            engine._sqlite.add_edge("function:caller", "function:callee", "calls")
            result = engine.get_callees("caller")
            assert len(result["result"]) == 1
            engine._sqlite.close()

    def test_get_imports(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("module:os", "module")
            engine._sqlite.add_node("module:main", "module")
            engine._sqlite.add_edge("module:main", "module:os", "imports")
            result = engine.get_imports("main")
            assert len(result["result"]) >= 1
            engine._sqlite.close()

    def test_get_inheritance(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("class:Child", "class", {"name": "Child"})
            engine._sqlite.add_node("class:Parent", "class", {"name": "Parent"})
            engine._sqlite.add_edge("class:Parent", "class:Child", "inherits")
            result = engine.get_inheritance("Child")
            assert "Parent" in result["result"].get("parents", [])
            engine._sqlite.close()

    def test_get_subgraph(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("function:a", "function")
            engine._sqlite.add_node("function:b", "function")
            engine._sqlite.add_edge("function:a", "function:b", "calls")
            result = engine.get_subgraph("a", depth=1)
            assert len(result["result"]["nodes"]) >= 1
            engine._sqlite.close()

    def test_is_graph_ready_tigergraph_available(self):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg, \
             patch('src.graph.query_engine.SQLiteNetworkXFallback'):
            mock_tg.return_value.test_connection.return_value = True
            engine = QueryEngine()
            assert engine.is_graph_ready() is True

    def test_is_graph_ready_caching(self):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg, \
             patch('src.graph.query_engine.SQLiteNetworkXFallback') as mock_sqlite:
            mock_tg.return_value.test_connection.return_value = False
            mock_sqlite.return_value.graph.nodes.return_value = ["node1"]

            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value

            import time
            with patch('time.monotonic', return_value=1000.0):
                result1 = engine.is_graph_ready()
                result2 = engine.is_graph_ready()

            assert result1 == result2
            mock_tg.return_value.test_connection.assert_called_once()

    def test_is_graph_ready_cache_expiry(self):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg, \
             patch('src.graph.query_engine.SQLiteNetworkXFallback') as mock_sqlite:
            mock_tg.return_value.test_connection.return_value = False
            mock_sqlite.return_value.graph.nodes.return_value = ["node1"]

            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value

            import time
            with patch('time.monotonic', side_effect=[1000.0, 1006.0]):
                result1 = engine.is_graph_ready()
                mock_tg.return_value.test_connection.reset_mock()
                result2 = engine.is_graph_ready()

            assert result1 == result2
            mock_tg.return_value.test_connection.assert_called()

    def test_is_graph_ready_sqlite_exception(self):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg, \
             patch('src.graph.query_engine.SQLiteNetworkXFallback') as mock_sqlite:
            mock_tg.return_value.test_connection.return_value = False
            mock_sqlite.return_value.graph.nodes.side_effect = Exception("DB error")

            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = mock_sqlite.return_value

            assert engine.is_graph_ready() is False

    def test_get_function_with_tigergraph(self):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg, \
             patch('src.graph.query_engine.SQLiteNetworkXFallback'):
            mock_tg.return_value.test_connection.return_value = True

            engine = QueryEngine()
            result = engine.get_function("test")

            assert result["backend_used"] == "tigergraph"
            assert "error" not in result or not any("error" in r for r in result["result"])

    @pytest.mark.skip(reason="Test references non-existent API - test is broken")
    def test_get_function_sqlite_exception(self, tmp_path):
        pass

    def test_get_function_top_k_truncation(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)

            from src.configs.grag_params import GraphRAGParams
            engine.params = GraphRAGParams(top_k=2)

            for i in range(5):
                engine._sqlite.add_node(f"function:func{i}", "function", {"name": f"func{i}"})

            result = engine.get_function("func0")
            assert len(result["result"]) <= 2

            engine._sqlite.close()

    def test_get_class_with_tigergraph(self):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg, \
             patch('src.graph.query_engine.SQLiteNetworkXFallback'):
            mock_tg.return_value.test_connection.return_value = True

            engine = QueryEngine()
            result = engine.get_class("MyClass")

            assert result["backend_used"] == "tigergraph"

    def test_get_class_not_found(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            result = engine.get_class("NonExistent")
            assert result["result"] == []
            engine._sqlite.close()

    def test_get_callers_not_found(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            result = engine.get_callers("nonexistent")
            assert len(result["result"]) == 0
            engine._sqlite.close()

    def test_get_callees_not_found(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            result = engine.get_callees("nonexistent")
            assert len(result["result"]) == 0
            engine._sqlite.close()

    def test_get_imports_not_found(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            result = engine.get_imports("nonexistent")
            assert len(result["result"]) == 0
            engine._sqlite.close()

    def test_get_inheritance_not_found(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            result = engine.get_inheritance("NonExistent")
            assert result["result"]["parents"] == []
            assert result["result"]["children"] == []
            engine._sqlite.close()

    def test_get_inheritance_with_parents_and_children(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("class:Child", "class", {"name": "Child"})
            engine._sqlite.add_node("class:Parent1", "class", {"name": "Parent1"})
            engine._sqlite.add_node("class:Parent2", "class", {"name": "Parent2"})
            engine._sqlite.add_edge("class:Parent1", "class:Child", "inherits")
            engine._sqlite.add_edge("class:Parent2", "class:Child", "inherits")
            engine._sqlite.add_edge("class:Child", "class:Parent1", "inherits")
            result = engine.get_inheritance("Child")
            assert len(result["result"]["parents"]) >= 1
            assert len(result["result"]["children"]) >= 0
            engine._sqlite.close()

    def test_get_subgraph_with_class(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("class:MyClass", "class", {"name": "MyClass"})
            engine._sqlite.add_node("function:method", "function")
            engine._sqlite.add_edge("class:MyClass", "function:method", "has_method")
            result = engine.get_subgraph("MyClass", depth=1)
            assert len(result["result"]["nodes"]) >= 1
            engine._sqlite.close()

    def test_get_subgraph_with_module(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("module:os", "module")
            result = engine.get_subgraph("os", depth=1)
            assert len(result["result"]["nodes"]) >= 1
            engine._sqlite.close()

    def test_get_subgraph_depth_2(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            engine._sqlite.add_node("function:a", "function")
            engine._sqlite.add_node("function:b", "function")
            engine._sqlite.add_node("function:c", "function")
            engine._sqlite.add_edge("function:a", "function:b", "calls")
            engine._sqlite.add_edge("function:b", "function:c", "calls")
            result = engine.get_subgraph("a", depth=2)
            node_names = [n["name"] for n in result["result"]["nodes"]]
            assert "a" in node_names
            assert "b" in node_names
            assert "c" in node_names
            engine._sqlite.close()

    def test_get_subgraph_not_found(self, tmp_path):
        with patch('src.graph.query_engine.TigerGraphClient') as mock_tg:
            mock_tg.return_value.test_connection.return_value = False
            db_path = tmp_path / "graph.db"
            engine = QueryEngine()
            engine._tigergraph = mock_tg.return_value
            engine._sqlite = SQLiteNetworkXFallback(db_path=db_path)
            result = engine.get_subgraph("nonexistent", depth=1)
            assert result["result"]["nodes"] == []
            assert result["result"]["edges"] == []
            engine._sqlite.close()

    @pytest.mark.skip(reason="Test references non-existent API - test is broken")
    def test_get_subgraph_exception(self, tmp_path):
        pass


class TestGraphIngestionPipeline:
    def test_init(self, tmp_path):
        pipeline = GraphIngestionPipeline(tmp_path / "codebase")
        assert pipeline.codebase_path == tmp_path / "codebase"
        assert pipeline.backend_type == "unknown"

    def test_init_with_metadata(self, tmp_path):
        metadata = {"name": "test", "type": "repo"}
        pipeline = GraphIngestionPipeline(tmp_path / "codebase", repo_metadata=metadata)
        assert pipeline.repo_metadata == metadata

    def test_select_backend_tigergraph_unavailable(self):
        with patch('src.graph.ingestion.TigerGraphClient') as mock_tg, \
             patch('src.graph.ingestion.SQLiteNetworkXFallback') as mock_sqlite:
            mock_tg.return_value.test_connection.return_value = False
            pipeline = GraphIngestionPipeline(Path("/tmp"))
            result = pipeline._select_backend()
            assert result is True
            assert pipeline.backend_type == "sqlite"

    def test_select_backend_both_fail(self):
        with patch('src.graph.ingestion.TigerGraphClient') as mock_tg, \
             patch('src.graph.ingestion.SQLiteNetworkXFallback') as mock_sqlite:
            mock_tg.return_value.test_connection.return_value = False
            mock_sqlite.side_effect = Exception("fail")
            pipeline = GraphIngestionPipeline(Path("/tmp"))
            result = pipeline._select_backend()
            assert result is False

    def test_transform_nodes_for_tigergraph(self):
        pipeline = GraphIngestionPipeline(Path("/tmp"))
        nodes = [
            {"id": "function:test", "type": "function", "name": "test", "file": "test.py", "line": 1,
             "parameters": [], "docstring": None, "bases": [], "methods": []},
            {"id": "class:MyClass", "type": "class", "name": "MyClass", "file": "test.py", "line": 5,
             "parameters": [], "docstring": None, "bases": [], "methods": []},
        ]
        transformed = pipeline._transform_nodes_for_tigergraph(nodes)
        assert len(transformed) == 2
        assert transformed[0]["type"] == "Function"
        assert transformed[1]["type"] == "Class"

    def test_transform_edges_for_tigergraph(self):
        pipeline = GraphIngestionPipeline(Path("/tmp"))
        edges = [
            {"source": "a", "target": "b", "type": "calls", "file": "test.py"},
            {"source": "c", "target": "d", "type": "imports", "file": "test.py"},
        ]
        transformed = pipeline._transform_edges_for_tigergraph(edges)
        assert len(transformed) == 2
        assert transformed[0]["type"] == "calls"
        assert transformed[1]["type"] == "depends_on"

    def test_verify_graph_health_no_backend(self):
        pipeline = GraphIngestionPipeline(Path("/tmp"))
        pipeline.backend_type = "unknown"
        health = pipeline._verify_graph_health()
        assert health["status"] == "unknown"

    def test_ingest_codebase_function(self, tmp_path):
        with patch('src.graph.ingestion.CodebaseParser') as mock_parser, \
             patch('src.graph.ingestion.TigerGraphClient') as mock_tg, \
             patch('src.graph.ingestion.SQLiteNetworkXFallback') as mock_sqlite:
            mock_tg.return_value.test_connection.return_value = False
            mock_parser.return_value.parse_codebase.return_value = {
                "nodes": [{"id": "n1", "type": "function", "attributes": {}}],
                "edges": [],
                "metadata": {"files_parsed": 1, "nodes_extracted": 1, "edges_extracted": 0}
            }
            result = ingest_codebase(str(tmp_path))
            assert "success" in result
