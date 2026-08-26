from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

# Load .env if not already loaded
if not os.environ.get("TIGERGRAPH_HOST"):
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

from pyTigerGraph import TigerGraphConnection
import logging

# Module logger
logger = logging.getLogger(__name__)


class TigerGraphClient:
    def __init__(
        self,
        host: Optional[str] = None,
        graphname: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> None:
        self.raw_host = host or os.environ.get("TIGERGRAPH_HOST", "http://localhost")
        self.graphname = graphname or os.environ.get("TIGERGRAPH_GRAPH", "codegraphx")
        self.username = username or os.environ.get("TIGERGRAPH_USER", "tigergraph")
        self.password = password or os.environ.get("TIGERGRAPH_PASSWORD", "tigergraph")
        self.secret = secret or os.environ.get("TIGERGRAPH_SECRET")
        self._conn: Optional[TigerGraphConnection] = None
        self._connected = False
    
    def _get_connection(self) -> Optional[TigerGraphConnection]:
        if self._conn is not None:
            return self._conn
        if not self.raw_host or self.raw_host == "http://localhost":
            return None
        try:
            conn_params = {
                "host": self.raw_host,
                "graphname": self.graphname,
            }
            if self.secret:
                conn_params["gsqlSecret"] = self.secret
            else:
                conn_params["username"] = self.username
                conn_params["password"] = self.password
            self._conn = TigerGraphConnection(**conn_params)
            
            # For Cloud instances, we need to get a token
            if self.secret:
                self._conn.getToken(self.secret)
            
            return self._conn
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return None
    
    def test_connection(self) -> bool:
        try:
            conn = self._get_connection()
            if conn is None:
                return False
            result = conn.echo()
            self._connected = result is not None
            return self._connected
        except Exception:
            self._connected = False
            return False
    
    def get_version(self) -> Optional[str]:
        try:
            conn = self._get_connection()
            if conn is None:
                return None
            return conn.getVer()
        except Exception:
            return None
    
    def create_graph(self, schema: Optional[dict[str, Any]] = None) -> bool:
        conn = self._get_connection()
        if conn is None:
            return False
        try:
            conn.gsql(f"CREATE GRAPH {self.graphname}()")
            return True
        except Exception:
            return True
    
    def create_schema(self) -> bool:
        """Create vertex and edge types for the graph schema."""
        conn = self._get_connection()
        if conn is None:
            return False
        
        # Vertex types
        vertex_types = [
            ("Function", "id STRING, name STRING, file STRING, line INT, parameters STRING, docstring STRING"),
            ("Class", "id STRING, name STRING, file STRING, line INT, docstring STRING, bases STRING, methods STRING"),
            ("Import", "id STRING, name STRING, file STRING, line INT"),
            ("Module", "id STRING, name STRING, file STRING"),
        ]
        
        # Edge types
        edge_types = [
            ("calls", "Function", "Function"),
            ("depends_on", "Module", "Module"),
        ]
        
        try:
            # Create vertices
            for vtype, attrs in vertex_types:
                try:
                    gsql = f"CREATE VERTEX {vtype} (PRIMARY_ID id STRING, {attrs}) WITH primary_id_as_attribute='true'"
                    conn.gsql(gsql)
                    logger.info(f"Created vertex type: {vtype}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.info(f"Vertex type {vtype} already exists")
                    else:
                        logger.warning(f"Warning creating vertex {vtype}: {e}")
            
            # Create edges
            for etype, src, tgt in edge_types:
                try:
                    gsql = f"CREATE DIRECTED EDGE {etype} (FROM {src}, TO {tgt}) WITH REVERSE_EDGE='{etype}_reverse'"
                    conn.gsql(gsql)
                    logger.info(f"Created edge type: {etype}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.info(f"Edge type {etype} already exists")
                    else:
                        logger.warning(f"Warning creating edge {etype}: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            return False
    
    def upsert_vertices(
        self,
        vertex_type: str,
        vertices: list[dict[str, Any]],
    ) -> int:
        conn = self._get_connection()
        if conn is None or not vertices:
            return 0
        try:
            # Convert dict format to tuple format for pyTigerGraph
            # Expected: [(id, {attrs}), ...]
            vertex_tuples = []
            for v in vertices:
                vid = v.get("id")
                attrs = v.get("attributes", {})
                if vid:
                    vertex_tuples.append((vid, attrs))
            
            if not vertex_tuples:
                return 0
                
            result = conn.upsertVertices(vertex_type, vertex_tuples)
            logger.info(f"Upserted {result} vertices of type {vertex_type}")
            return result
        except Exception as e:
            logger.error(f"Failed to upsert vertices: {e}")
            return 0
    
    def upsert_edges(
        self,
        source_type: str,
        edge_type: str,
        target_type: str,
        edges: list[dict[str, Any]],
    ) -> int:
        conn = self._get_connection()
        if conn is None or not edges:
            return 0
        try:
            # Convert dict format to tuple format for pyTigerGraph
            # Expected: [(source_id, target_id, {attrs}), ...]
            edge_tuples = []
            for e in edges:
                from_id = e.get("from") or e.get("from_id")
                to_id = e.get("to") or e.get("to_id")
                attrs = e.get("attributes", {})
                if from_id and to_id:
                    edge_tuples.append((from_id, to_id, attrs))
            
            if not edge_tuples:
                return 0
                
            result = conn.upsertEdges(source_type, edge_type, target_type, edge_tuples)
            logger.info(f"Upserted {result} edges of type {edge_type}")
            return result
        except Exception as e:
            logger.error(f"Failed to upsert edges: {e}")
            return 0
    
    def run_gsql(self, query: str) -> Optional[list[dict[str, Any]]]:
        conn = self._get_connection()
        if conn is None:
            return None
        try:
            result = conn.gsql(query)
            return result if result else []
        except Exception:
            return None
    
    def run_installed_query(
        self,
        query_name: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Optional[list[dict[str, Any]]]:
        conn = self._get_connection()
        if conn is None:
            return None
        try:
            result = conn.runInstalledQuery(query_name, params or {})
            return result if result else []
        except Exception:
            return None
    
    def get_subgraph(
        self,
        vertex_type: str,
        vertex_ids: list[str],
        edge_types: Optional[list[str]] = None,
        depth: int = 2,
    ) -> Optional[dict[str, Any]]:
        if not vertex_ids:
            return None
        conn = self._get_connection()
        if conn is None:
            return None
        try:
            vertices = conn.getVerticesByType(vertex_type)
            requested = {v["id"]: v for v in vertices if v["id"] in vertex_ids}
            all_edges = []
            for vid in vertex_ids:
                edges = conn.getEdges(vid, vertex_type)
                all_edges.extend(edges)
            return {"vertices": requested, "edges": all_edges}
        except Exception:
            return None
    
    def get_all_vertices(
        self,
        vertex_type: Optional[str] = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        conn = self._get_connection()
        if conn is None:
            return []
        try:
            if vertex_type:
                return conn.getVerticesByType(vertex_type)[:limit]
            return conn.getVerticesByType("CodeEntity")[:limit]
        except Exception:
            return []


def test_connection() -> bool:
    return TigerGraphClient().test_connection()


if __name__ == "__main__":
    c = TigerGraphClient()
    ok = c.test_connection()
    if ok:
        logger.info("Connected to TigerGraph")
        ver = c.get_version()
        if ver:
            logger.info(f"Version: {ver}")
    else:
        logger.error("Not connected (check TIGERGRAPH_HOST)")
