"""SQLite + NetworkX fallback graph backend.

Provides a minimal TigerGraph-like interface: add_node, add_edge, query, get_subgraph.

Persistence stored in .codegraphx/graph.db with PRAGMA journal_mode=WAL enabled.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:
    import networkx as nx  # type: ignore
except Exception:
    nx = None  # type: ignore


class _SimpleDiGraph:
    """Minimal DiGraph fallback when networkx is not available.

    Supports the small subset used by this module: add_node, add_edge,
    successors, predecessors, nodes, edges, subgraph, copy.
    """
    def __init__(self) -> None:
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._out: Dict[str, set[str]] = {}
        self._in: Dict[str, set[str]] = {}

    def add_node(self, n: str, **attrs: Any) -> None:
        self._nodes.setdefault(n, {})
        self._nodes[n].update(attrs)

    def add_edge(self, u: str, v: str, **attrs: Any) -> None:
        self._out.setdefault(u, set()).add(v)
        self._in.setdefault(v, set()).add(u)
        self._nodes.setdefault(u, {})
        self._nodes.setdefault(v, {})
        # store attributes on edge via separate structure if needed; omitted for minimal API

    def successors(self, n: str):
        return iter(self._out.get(n, []))

    def predecessors(self, n: str):
        return iter(self._in.get(n, []))

    def nodes(self):
        # mimic networkx.nodes() returning an iterable of node keys
        return list(self._nodes.keys())

    def __contains__(self, n: str) -> bool:
        return n in self._nodes

    def node_data(self, n: str) -> Dict[str, Any]:
        return dict(self._nodes.get(n, {}))

    def edges(self, data: bool = False):
        out = []
        for u, vs in self._out.items():
            for v in vs:
                out.append((u, v, {} if data else None))
        return out

    def subgraph(self, nodes: Iterable[str]):
        g = _SimpleDiGraph()
        for n in nodes:
            if n in self._nodes:
                g.add_node(n, **self._nodes[n])
        for u in nodes:
            for v in self._out.get(u, []):
                if v in nodes:
                    g.add_edge(u, v)
        return g

    def copy(self):
        g = _SimpleDiGraph()
        g._nodes = {k: dict(v) for k, v in self._nodes.items()}
        g._out = {k: set(v) for k, v in self._out.items()}
        g._in = {k: set(v) for k, v in self._in.items()}
        return g


DB_DIR = Path(".codegraphx")
DB_PATH = DB_DIR / "graph.db"


class SQLiteNetworkXFallback:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else DB_PATH
        DB_DIR.mkdir(parents=True, exist_ok=True)
        # ensure DB exists and WAL enabled
        self.conn = sqlite3.connect(str(self.db_path))
        cur = self.conn.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL;")
            # commit the pragma change
            self.conn.commit()
        finally:
            cur.close()

        # load or init networkx DiGraph (or fallback)
        if nx is not None:
            self.graph = nx.DiGraph()
        else:
            self.graph = _SimpleDiGraph()
        self._ensure_tables()
        self._load_from_db()

    # --- persistence schema ---
    def _ensure_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT,
                attrs TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                target TEXT,
                type TEXT,
                attrs TEXT
            )
            """
        )
        self.conn.commit()
        cur.close()

    def _load_from_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT id, type, attrs FROM nodes")
        for nid, ntype, attrs in cur.fetchall():
            data = json.loads(attrs) if attrs else {}
            self.graph.add_node(nid, type=ntype, **data)

        cur.execute("SELECT source, target, type, attrs FROM edges")
        for src, tgt, etype, attrs in cur.fetchall():
            data = json.loads(attrs) if attrs else {}
            self.graph.add_edge(src, tgt, type=etype, **data)

        cur.close()

    # --- API ---
    def add_node(self, node_id: str, node_type: str = "node", attrs: Optional[Dict[str, Any]] = None) -> None:
        """Add or update a node. Persist to SQLite."""
        attrs = attrs or {}
        self.graph.add_node(node_id, type=node_type, **attrs)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO nodes (id, type, attrs) VALUES (?, ?, ?)",
            (node_id, node_type, json.dumps(attrs)),
        )
        self.conn.commit()
        cur.close()

    def add_nodes_batch(self, nodes: list[tuple[str, str, Optional[Dict[str, Any]]]]) -> None:
        """Add multiple nodes in a single transaction for bulk ingestion."""
        cur = self.conn.cursor()
        try:
            for node_id, node_type, attrs in nodes:
                attrs = attrs or {}
                self.graph.add_node(node_id, type=node_type, **attrs)
                cur.execute(
                    "INSERT OR REPLACE INTO nodes (id, type, attrs) VALUES (?, ?, ?)",
                    (node_id, node_type, json.dumps(attrs)),
                )
            self.conn.commit()
        finally:
            cur.close()

    def add_edge(self, source: str, target: str, edge_type: str = "edge", attrs: Optional[Dict[str, Any]] = None) -> None:
        """Add an edge between nodes. Persist to SQLite."""
        attrs = attrs or {}
        has_node = lambda n: n in self.graph
        if not has_node(source):
            self.add_node(source)
        if not has_node(target):
            self.add_node(target)
        self.graph.add_edge(source, target, type=edge_type, **attrs)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO edges (source, target, type, attrs) VALUES (?, ?, ?, ?)",
            (source, target, edge_type, json.dumps(attrs)),
        )
        self.conn.commit()
        cur.close()

    def add_edges_batch(self, edges: list[tuple[str, str, str, Optional[Dict[str, Any]]]]) -> None:
        """Add multiple edges in a single transaction for bulk ingestion."""
        has_node = lambda n: n in self.graph
        cur = self.conn.cursor()
        try:
            for source, target, edge_type, attrs in edges:
                attrs = attrs or {}
                if not has_node(source):
                    self.graph.add_node(source)
                if not has_node(target):
                    self.graph.add_node(target)
                self.graph.add_edge(source, target, type=edge_type, **attrs)
                cur.execute(
                    "INSERT INTO edges (source, target, type, attrs) VALUES (?, ?, ?, ?)",
                    (source, target, edge_type, json.dumps(attrs)),
                )
            self.conn.commit()
        finally:
            cur.close()

    def query(self, node_id: str) -> Dict[str, Any]:
        """Return node data and immediate neighbors (outgoing and incoming)."""
        # membership via __contains__ works for networkx and fallback
        has_node = lambda n: n in self.graph
        if not has_node(node_id):
            return {}
        # fetch node attrs
        if not isinstance(self.graph, _SimpleDiGraph):
            # networkx.node data is a mapping
            data = dict(self.graph.nodes[node_id])
            out = list(self.graph.successors(node_id))
            inp = list(self.graph.predecessors(node_id))
        else:
            # fallback exposes node_data() helper
            data = dict(self.graph.node_data(node_id))
            out = list(self.graph.successors(node_id))
            inp = list(self.graph.predecessors(node_id))
        return {"id": node_id, "data": data, "out": out, "in": inp}

    def get_subgraph(self, node_ids: Iterable[str], depth: int = 1) -> object:
        """Return a NetworkX DiGraph containing nodes within `depth` hops from any of node_ids."""
        seeds = list(node_ids)
        nodes = set(seeds)
        frontier = set(seeds)
        for _ in range(depth):
            next_frontier = set()
            for n in frontier:
                next_frontier.update(self.graph.successors(n))
                next_frontier.update(self.graph.predecessors(n))
            next_frontier -= nodes
            if not next_frontier:
                break
            nodes.update(next_frontier)
            frontier = next_frontier

        sg = self.graph.subgraph(nodes)
        # networkx DiGraph has copy(); our fallback returns _SimpleDiGraph which also has copy()
        return sg.copy()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def pragma_journal_mode(self) -> str:
        cur = self.conn.cursor()
        cur.execute("PRAGMA journal_mode;")
        mode = cur.fetchone()[0]
        cur.close()
        return mode


__all__ = ["SQLiteNetworkXFallback"]
