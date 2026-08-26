"""Graph Ingestion Pipeline for GraphMind.

Coordinates parsing, backend selection (TigerGraph preferred, SQLite fallback),
transformation, bulk loading, and verification.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Bootstrap for direct script execution: ensure src package is discoverable
if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from src.graph.tigergraph_client import TigerGraphClient
from src.graph.sqlite_fallback import SQLiteNetworkXFallback
from src.parser.codebase_parser import CodebaseParser
from src.chunking.semantic_chunker import SemanticChunker
from src.embeddings.embedder import Embedder
from src.vectorstore.faiss_store import FAISSStore

logger = logging.getLogger(__name__)


class GraphIngestionPipeline:
    """Ingest codebase into graph database with auto backend selection."""

    def __init__(self, codebase_path: Path, repo_metadata: Optional[Dict[str, Any]] = None):
        self.codebase_path = Path(codebase_path)
        self.repo_metadata = repo_metadata or {}
        self.parser = CodebaseParser(file_limit=500)
        self.tigergraph_client: Optional[TigerGraphClient] = None
        self.sqlite_backend: Optional[SQLiteNetworkXFallback] = None
        self.backend_type: str = "unknown"

    def _select_backend(self) -> bool:
        """Auto-select backend: TigerGraph first, SQLite fallback.

        Returns True if a backend is available.
        """
        self.tigergraph_client = TigerGraphClient()
        if self.tigergraph_client.test_connection():
            self.backend_type = "tigergraph"
            logger.info("TigerGraph backend selected")
            return True

        try:
            self.sqlite_backend = SQLiteNetworkXFallback()
            self.backend_type = "sqlite"
            logger.info("SQLite fallback backend selected")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SQLite backend: {e}")
            return False

    def _parse_codebase(self) -> Dict[str, Any]:
        """Parse codebase using existing parser."""
        logger.info(f"Parsing codebase: {self.codebase_path}")
        result = self.parser.parse_codebase(self.codebase_path)
        logger.info(
            f"Parsed {result['metadata']['files_parsed']} files, "
            f"extracted {result['metadata']['nodes_extracted']} nodes, "
            f"{result['metadata']['edges_extracted']} edges"
        )
        return result

    def _transform_nodes_for_tigergraph(self, nodes: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Transform parser nodes to TigerGraph vertex format."""
        transformed = []
        for node in nodes:
            node_type = node["type"]
            if node_type == "function":
                vtype = "Function"
            elif node_type == "class":
                vtype = "Class"
            elif node_type == "import":
                vtype = "Import"
            else:
                vtype = "Module"

            transformed.append({
                "id": node["id"],
                "type": vtype,
                "attributes": {
                    "name": node.get("name", ""),
                    "file": node.get("file", ""),
                    "line": node.get("line", 0),
                    "parameters": node.get("parameters", []),
                    "docstring": node.get("docstring", None),
                    "bases": node.get("bases", []),
                    "methods": node.get("methods", []),
                }
            })
        return transformed

    def _transform_edges_for_tigergraph(self, edges: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Transform parser edges to TigerGraph edge format."""
        transformed = []
        for edge in edges:
            edge_type = edge["type"]
            if edge_type == "calls":
                etype = "calls"
            else:
                etype = "depends_on"

            transformed.append({
                "from": edge["source"],
                "to": edge["target"],
                "type": etype,
                "attributes": {
                    "file": edge.get("file", "")
                }
            })
        return transformed

    def _load_to_tigergraph(self, nodes: list[Dict[str, Any]], edges: list[Dict[str, Any]]) -> bool:
        """Load data to TigerGraph with actual upsert operations."""
        logger.info(f"Loading {len(nodes)} nodes and {len(edges)} edges to TigerGraph")
        
        if not self.tigergraph_client:
            logger.error("TigerGraph client not initialized")
            return False
        
        # Create schema first
        if not self.tigergraph_client.create_schema():
            logger.error("Failed to create TigerGraph schema")
            return False
        
        # Build node type lookup for edge resolution
        node_type_map = {n["id"]: n.get("type", "Module") for n in nodes}
        
        # Transform nodes for TigerGraph format
        transformed_nodes = self._transform_nodes_for_tigergraph(nodes)
        
        # Group vertices by type
        vertices_by_type: Dict[str, list] = {}
        for node in transformed_nodes:
            vtype = node.get("type", "Module")
            if vtype not in vertices_by_type:
                vertices_by_type[vtype] = []
            vertices_by_type[vtype].append(node)
        
        # Upsert all vertices (must be done before edges)
        total_vert_upserted = 0
        for vtype, vertices in vertices_by_type.items():
            if vertices:
                count = self.tigergraph_client.upsert_vertices(vtype, vertices)
                total_vert_upserted += count
                logger.info(f"Upserted {count} vertices of type {vtype}")
        
        # Transform edges
        transformed_edges = self._transform_edges_for_tigergraph(edges)
        
        # Group edges by source_type + edge_type + target_type
        edges_by_type: Dict[tuple, list] = {}
        for edge in transformed_edges:
            from_id = edge.get("from")
            to_id = edge.get("to")
            if not from_id or not to_id:
                continue
            
            # Resolve source and target types from node lookup
            src_type = node_type_map.get(from_id, "Module")
            tgt_type = node_type_map.get(to_id, "Module")
            edge_type = edge.get("type", "depends_on")
            
            key = (src_type, edge_type, tgt_type)
            if key not in edges_by_type:
                edges_by_type[key] = []
            edges_by_type[key].append(edge)
        
        # Upsert all edges
        total_edge_upserted = 0
        for (src_type, edge_type, tgt_type), edge_list in edges_by_type.items():
            if edge_list:
                count = self.tigergraph_client.upsert_edges(src_type, edge_type, tgt_type, edge_list)
                total_edge_upserted += count
                logger.info(f"Upserted {count} edges of type {edge_type}")
        
        logger.info(f"Total: {total_vert_upserted} vertices, {total_edge_upserted} edges loaded to TigerGraph")
        return True

    def _load_to_sqlite(self, nodes: list[Dict[str, Any]], edges: list[Dict[str, Any]]) -> bool:
        """Load data to SQLite/NetworkX backend."""
        if not self.sqlite_backend:
            logger.error("SQLite backend not initialized")
            return False

        logger.info(f"Loading {len(nodes)} nodes and {len(edges)} edges to SQLite (batch)")
        try:
            node_batch = [(n["id"], n["type"], n.get("attributes")) for n in nodes]
            self.sqlite_backend.add_nodes_batch(node_batch)

            edge_batch = [(e["from"], e["to"], e["type"], e.get("attributes")) for e in edges]
            self.sqlite_backend.add_edges_batch(edge_batch)

            logger.info("Successfully loaded data to SQLite backend")
            return True
        except Exception as e:
            logger.error(f"Failed to load data to SQLite: {e}")
            return False

    def _verify_graph_health(self) -> Dict[str, Any]:
        """Run basic health checks on the loaded graph."""
        health = {
            "backend_type": self.backend_type,
            "status": "unknown",
            "node_count": 0,
            "edge_count": 0,
            "sample_query": {}
        }

        if self.backend_type == "sqlite" and self.sqlite_backend:
            try:
                nodes = list(self.sqlite_backend.graph.nodes())
                health["node_count"] = len(nodes)

                if hasattr(self.sqlite_backend.graph, 'edges'):
                    edges = list(self.sqlite_backend.graph.edges())
                    health["edge_count"] = len(edges)

                if nodes:
                    sample_node = nodes[0]
                    health["sample_query"] = self.sqlite_backend.query(sample_node)

                health["status"] = "healthy"
                logger.info(f"Graph health check: {health['node_count']} nodes, {health['edge_count']} edges")
            except Exception as e:
                health["status"] = f"error: {e}"
                logger.error(f"Graph health check failed: {e}")

        elif self.backend_type == "tigergraph" and self.tigergraph_client:
            try:
                conn = self.tigergraph_client._get_connection()
                if conn:
                    # Get vertex counts
                    vertex_types = ["Function", "Class", "Import", "Module"]
                    total_nodes = 0
                    for vtype in vertex_types:
                        try:
                            vertices = conn.getVerticesByType(vtype)
                            if vertices:
                                total_nodes += len(vertices)
                        except Exception as e:
                            # Log and continue - failure to fetch one vertex type shouldn't abort health check
                            logger.debug(f"Failed to get vertices for type {vtype}: {e}")
                    
                    health["node_count"] = total_nodes
                    
                    # Get edge count using getEdges
                    total_edges = 0
                    try:
                        # Try to get edges from a vertex type
                        functions = conn.getVerticesByType("Function")
                        for func in functions[:10]:  # Sample a few
                            edges = conn.getEdges(func.get("id", func.get("v_id")), "Function")
                            if edges:
                                total_edges += len(edges)
                    except Exception as e:
                        # Log and continue - non-critical for aggregate edge counts
                        logger.debug(f"Failed to get sample edges from Function vertices: {e}")
                    
                    health["edge_count"] = total_edges
                    health["status"] = "healthy"
                    logger.info(f"TigerGraph health check: {health['node_count']} nodes, {health['edge_count']} edges")
            except Exception as e:
                health["status"] = f"error: {e}"
                logger.error(f"TigerGraph health check failed: {e}")

        return health

    def _run_vector_ingestion(self) -> Dict[str, Any]:
        try:
            import os
            import time
            from concurrent.futures import ThreadPoolExecutor, as_completed

            start = time.monotonic()
            codebase_path = Path(self.codebase_path)

            if not codebase_path.is_dir():
                return {"success": False, "error": f"Path is not a directory: {codebase_path}"}

            SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.jsx', '.tsx', '.c', '.cpp', '.h', '.rb', '.php', '.swift', '.kt'}

            all_texts: list[str] = []
            all_metadata: list[dict[str, Any]] = []
            total_files_processed = 0
            total_chars = 0
            files_with_errors: list[str] = []

            file_paths = []
            for file_path in codebase_path.rglob('*'):
                if file_path.is_file() and file_path.suffix in SUPPORTED_EXTENSIONS:
                    file_paths.append(file_path)

            batch_size = 100
            chunker = SemanticChunker()

            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i + batch_size]
                for file_path in batch:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                        if not text:
                            continue

                        total_files_processed += 1
                        total_chars += len(text)

                        chunks = chunker.auto_chunk(text)
                        if chunks:
                            metadata = [
                                {"source": str(file_path), "chunk_idx": j, "total_chunks": len(chunks)}
                                for j in range(len(chunks))
                            ]
                            all_texts.extend(chunks)
                            all_metadata.extend(metadata)
                    except Exception as e:
                        files_with_errors.append(str(file_path))
                        logger.warning(f"Failed to process {file_path}: {e}")

            if not all_texts:
                logger.warning("No chunks extracted from codebase")
                return {
                    "success": True,
                    "chunks_ingested": 0,
                    "vector_store_size": 0,
                    "files_processed": total_files_processed,
                    "index_path": ""
                }

            embed_batch_size = 128
            store = FAISSStore()

            for j in range(0, len(all_texts), embed_batch_size):
                text_batch = all_texts[j:j + embed_batch_size]
                meta_batch = all_metadata[j:j + embed_batch_size]
                store.add(text_batch, meta_batch)

            index_path = ".codegraphx/faiss_index.bin"
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            store.save(index_path)

            elapsed = time.monotonic() - start

            return {
                "success": True,
                "chunks_ingested": len(all_texts),
                "vector_store_size": store.size(),
                "files_processed": total_files_processed,
                "total_chars": total_chars,
                "estimated_tokens": total_chars // 4,
                "index_path": index_path,
                "ingestion_time_seconds": round(elapsed, 2),
                "files_with_errors": len(files_with_errors),
            }
        except Exception as e:
            logger.error(f"Vector ingestion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def run(self) -> Dict[str, Any]:
        """Run the complete ingestion pipeline."""
        logger.info("Starting graph ingestion pipeline")

        if not self._select_backend():
            return {"success": False, "error": "No backend available"}

        parse_result = self._parse_codebase()
        nodes = parse_result["nodes"]
        edges = parse_result["edges"]
        metadata = parse_result["metadata"]

        if self.backend_type == "tigergraph":
            nodes_to_load = self._transform_nodes_for_tigergraph(nodes)
            edges_to_load = self._transform_edges_for_tigergraph(edges)
            load_success = self._load_to_tigergraph(nodes_to_load, edges_to_load)
        elif self.backend_type == "sqlite":
            load_success = self._load_to_sqlite(nodes, edges)
        else:
            load_success = False

        if not load_success:
            return {"success": False, "error": "Failed to load data to backend"}

        health = self._verify_graph_health()
        vector_stats = self._run_vector_ingestion()

        result = {
            "success": True,
            "backend_type": self.backend_type,
            "repo_metadata": self.repo_metadata,
            "parse_metadata": metadata,
            "load_stats": {
                "nodes_loaded": len(nodes),
                "edges_loaded": len(edges)
            },
            "graph_health": health,
            "vector_stats": vector_stats
        }

        logger.info("Graph ingestion pipeline completed successfully")
        return result


def ingest_codebase(codebase_path: str, repo_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Main entry point for codebase ingestion."""
    pipeline = GraphIngestionPipeline(Path(codebase_path), repo_metadata)
    return pipeline.run()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingestion.py <codebase_path>")
        sys.exit(1)

    codebase_path = sys.argv[1]

    repo_metadata = {
        "path": str(Path(codebase_path).resolve()),
        "name": Path(codebase_path).name,
        "type": "directory"
    }

    result = ingest_codebase(codebase_path, repo_metadata)
    print(json.dumps(result, indent=2))
