"""Graph query engine with dual-backend support.

Provides 7 query types: get_function, get_class, get_callers, get_callees, 
get_imports, get_inheritance, get_subgraph. Tries TigerGraph first,
falls back to SQLite/NetworkX.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .sqlite_fallback import SQLiteNetworkXFallback
from .tigergraph_client import TigerGraphClient
from src.configs.grag_params import GraphRAGParams


class QueryEngine:
    def __init__(self, params: Optional[GraphRAGParams] = None) -> None:
        self._tigergraph = TigerGraphClient()
        self._sqlite: Optional[SQLiteNetworkXFallback] = None
        self.params = params or GraphRAGParams()
        self._graph_ready_cache = None
        self._graph_ready_cache_time = 0.0

    def _get_sqlite(self) -> SQLiteNetworkXFallback:
        if self._sqlite is None:
            self._sqlite = SQLiteNetworkXFallback()
        return self._sqlite

    def is_graph_ready(self) -> bool:
        import time
        now = time.monotonic()
        if self._graph_ready_cache is not None and (now - self._graph_ready_cache_time) < 5.0:
            return self._graph_ready_cache
        
        if self._tigergraph.test_connection():
            self._graph_ready_cache = True
            self._graph_ready_cache_time = now
            return True
        try:
            sqlite = self._get_sqlite()
            result = len(sqlite.graph.nodes()) > 0
            self._graph_ready_cache = result
            self._graph_ready_cache_time = now
            return result
        except Exception:
            self._graph_ready_cache = False
            self._graph_ready_cache_time = now
            return False

    def get_function(self, name: str) -> Dict[str, Any]:
        """Get function node by name. Returns dict with result, counts, backend."""
        result: List[Dict[str, Any]] = []
        backend_used = "tigergraph"
        node_count = 0
        edge_count = 0

        try:
            if self._tigergraph.test_connection():
                pass # TODO: TigerGraph query when connected
            else:
                raise Exception("TigerGraph not available")
        except Exception:
            backend_used = "sqlite"
            try:
                sqlite = self._get_sqlite()
                node_id = f"function:{name}"
                if node_id in sqlite.graph:
                    data = sqlite.graph.node_data(node_id)
                    result.append({"id": node_id, "name": name, **data})
                    node_count = 1
                    edge_count = len(list(sqlite.graph.successors(node_id)))
            except Exception as e:
                result = [{"error": str(e)}]

        # Apply top_k truncation
        if result and not any("error" in r for r in result):
            result = result[:self.params.top_k]
            node_count = min(node_count, len(result))

        return {
            "result": result,
            "node_count": node_count,
            "edge_count": edge_count,
            "backend_used": backend_used,
        }

    def get_class(self, name: str) -> Dict[str, Any]:
        """Get class node by name."""
        result: List[Dict[str, Any]] = []
        backend_used = "tigergraph"
        node_count = 0
        edge_count = 0

        try:
            if self._tigergraph.test_connection():
                pass
            else:
                raise Exception("TigerGraph not available")
        except Exception:
            backend_used = "sqlite"
            try:
                sqlite = self._get_sqlite()
                node_id = f"class:{name}"
                if node_id in sqlite.graph:
                    data = sqlite.graph.node_data(node_id)
                    result.append({"id": node_id, "name": name, **data})
                    node_count = 1
                    edge_count = len(list(sqlite.graph.successors(node_id)))
            except Exception as e:
                result = [{"error": str(e)}]

        return {
            "result": result,
            "node_count": node_count,
            "edge_count": edge_count,
            "backend_used": backend_used,
        }

    def get_callers(self, function_name: str) -> Dict[str, Any]:
        """Get functions that call the given function."""
        result: List[Dict[str, str]] = []
        backend_used = "sqlite"
        node_count = 0
        edge_count = 0

        try:
            sqlite = self._get_sqlite()
            target_id = f"function:{function_name}"
            
            if target_id in sqlite.graph:
                predecessors = list(sqlite.graph.predecessors(target_id))
                node_count = len(predecessors)
                for caller in predecessors[:self.params.top_k]:
                    result.append({"id": caller, "name": caller.split(":")[-1] if ":" in caller else caller})
                edge_count = node_count
        except Exception as e:
            result = [{"error": str(e)}]

        return {
            "result": result,
            "node_count": node_count,
            "edge_count": edge_count,
            "backend_used": backend_used,
        }

    def get_callees(self, function_name: str) -> Dict[str, Any]:
        """Get functions called by the given function."""
        result: List[Dict[str, str]] = []
        backend_used = "sqlite"
        node_count = 0
        edge_count = 0

        try:
            sqlite = self._get_sqlite()
            source_id = f"function:{function_name}"
            
            if source_id in sqlite.graph:
                successors = list(sqlite.graph.successors(source_id))
                node_count = len(successors)
                for callee in successors[:self.params.top_k]:
                    result.append({"id": callee, "name": callee.split(":")[-1] if ":" in callee else callee})
                edge_count = node_count
        except Exception as e:
            result = [{"error": str(e)}]

        return {
            "result": result,
            "node_count": node_count,
            "edge_count": edge_count,
            "backend_used": backend_used,
        }

    def get_imports(self, module_name: str) -> Dict[str, Any]:
        """Get imports for a given module."""
        result: List[Dict[str, str]] = []
        backend_used = "sqlite"
        node_count = 0
        edge_count = 0

        try:
            sqlite = self._get_sqlite()
            node_id = f"module:{module_name}"
            
            if node_id in sqlite.graph:
                successors = list(sqlite.graph.successors(node_id))
                node_count = len(successors)
                for imp in successors[:self.params.top_k]:
                    result.append({"id": imp, "name": imp.split(":")[-1] if ":" in imp else imp})
                edge_count = node_count
        except Exception as e:
            result = [{"error": str(e)}]

        return {
            "result": result,
            "node_count": node_count,
            "edge_count": edge_count,
            "backend_used": backend_used,
        }

    def get_inheritance(self, class_name: str) -> Dict[str, Any]:
        """Get class inheritance hierarchy."""
        result: Dict[str, Any] = {"parents": [], "children": []}
        backend_used = "sqlite"
        node_count = 0
        edge_count = 0

        try:
            sqlite = self._get_sqlite()
            node_id = f"class:{class_name}"
            
            if node_id in sqlite.graph:
                parents = list(sqlite.graph.predecessors(node_id))
                children = list(sqlite.graph.successors(node_id))
                result["parents"] = [p.split(":")[-1] if ":" in p else p for p in parents]
                result["children"] = [c.split(":")[-1] if ":" in c else c for c in children]
                node_count = len(parents) + len(children)
                edge_count = node_count
        except Exception as e:
            result = {"error": str(e)}

        return {
            "result": result,
            "node_count": node_count,
            "edge_count": edge_count,
            "backend_used": backend_used,
        }

    def get_subgraph(self, entity_name: str, depth: int = 1) -> Dict[str, Any]:
        """Get all nodes within N hops of the entity."""
        result: Dict[str, Any] = {"nodes": [], "edges": []}
        backend_used = "sqlite"
        node_count = 0
        edge_count = 0

        try:
            sqlite = self._get_sqlite()
            entity_id = f"function:{entity_name}"
            if entity_id not in sqlite.graph:
                entity_id = f"class:{entity_name}"
            if entity_id not in sqlite.graph:
                entity_id = f"module:{entity_name}"
            
            if entity_id in sqlite.graph:
                visited = {entity_id}
                frontier = {entity_id}
                
                for _ in range(depth):
                    new_frontier = set()
                    for node in frontier:
                        for succ in sqlite.graph.successors(node):
                            if succ not in visited and len(visited) < self.params.top_k * 2:
                                visited.add(succ)
                                new_frontier.add(succ)
                        for pred in sqlite.graph.predecessors(node):
                            if pred not in visited and len(visited) < self.params.top_k * 2:
                                visited.add(pred)
                                new_frontier.add(pred)
                    frontier = new_frontier
                
                subgraph = sqlite.graph.subgraph(visited)
                result["nodes"] = [{"id": n, "name": n.split(":")[-1] if ":" in n else n} for n in visited]
                result["edges"] = [{"source": e[0], "target": e[1]} for e in subgraph.edges()]
                node_count = len(visited)
                edge_count = len(result["edges"])
        except Exception as e:
            result = {"error": str(e)}

        return {
            "result": result,
            "node_count": node_count,
            "edge_count": edge_count,
            "backend_used": backend_used,
        }


if __name__ == "__main__":
    qe = QueryEngine()
    print(f"is_graph_ready: {qe.is_graph_ready()}")