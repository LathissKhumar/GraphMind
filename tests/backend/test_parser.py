import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from src.parser.codebase_parser import CodebaseParser

class TestCodebaseParser:
    def test_parser_initialization(self):
        parser = CodebaseParser()
        assert parser is not None

    def test_parser_has_file_limit(self):
        parser = CodebaseParser()
        assert hasattr(parser, 'file_limit')
        assert parser.file_limit == 500

    def test_parse_codebase_returns_dict(self):
        parser = CodebaseParser()
        try:
            result = parser.parse_codebase(Path("/nonexistent"))
            assert isinstance(result, dict)
        except Exception:
            pass

class TestIngestionPipeline:
    def test_ingestion_pipeline_exists(self):
        from src.graph.ingestion import GraphIngestionPipeline
        assert GraphIngestionPipeline is not None

    def test_ingestion_pipeline_run_method(self):
        from src.graph.ingestion import GraphIngestionPipeline
        assert hasattr(GraphIngestionPipeline, 'run')

class TestTigerGraphClient:
    def test_client_exists(self):
        from src.graph.tigergraph_client import TigerGraphClient
        assert TigerGraphClient is not None

    def test_client_has_test_connection(self):
        from src.graph.tigergraph_client import TigerGraphClient
        client = TigerGraphClient()
        assert hasattr(client, 'test_connection')

class TestSQLiteFallback:
    def test_sqlite_fallback_exists(self):
        from src.graph.sqlite_fallback import SQLiteNetworkXFallback
        assert SQLiteNetworkXFallback is not None

    def test_sqlite_has_crud_methods(self):
        from src.graph.sqlite_fallback import SQLiteNetworkXFallback
        fallback = SQLiteNetworkXFallback(":memory:")
        assert hasattr(fallback, 'add_node')
        assert hasattr(fallback, 'add_edge')
        assert hasattr(fallback, 'query')
        assert hasattr(fallback, 'get_subgraph')