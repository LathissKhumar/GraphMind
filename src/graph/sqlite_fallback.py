import sqlite3
import networkx as nx
import os
import json
from typing import Dict, Any, List

class SQLiteGraph:
    def __init__(self):
        self.db_path = os.path.join('.codegraphx', 'graph.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.graph = nx.DiGraph()
        self._init_db()
        self._load_into_memory()

    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT,
                attributes TEXT
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT,
                target TEXT,
                type TEXT,
                attributes TEXT,
                PRIMARY KEY (source, target, type)
            )
        ''')
        self.conn.commit()

    def _load_into_memory(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, type, attributes FROM nodes")
        for row in cursor.fetchall():
            self.graph.add_node(row[0], type=row[1], **json.loads(row[2]))
            
        cursor.execute("SELECT source, target, type, attributes FROM edges")
        for row in cursor.fetchall():
            self.graph.add_edge(row[0], row[1], type=row[2], **json.loads(row[3]))

    def add_node(self, node_data: Dict[str, Any]):
        node_id = node_data.get('id')
        node_type = node_data.get('type', 'Unknown')
        attributes = json.dumps(node_data.get('attributes', {}))
        
        self.conn.execute(
            "INSERT OR REPLACE INTO nodes (id, type, attributes) VALUES (?, ?, ?)",
            (node_id, node_type, attributes)
        )
        self.conn.commit()
        
        self.graph.add_node(node_id, type=node_type, **node_data.get('attributes', {}))

    def add_edge(self, edge_data: Dict[str, Any]):
        source = edge_data.get('source')
        target = edge_data.get('target')
        edge_type = edge_data.get('type')
        attributes = json.dumps(edge_data.get('attributes', {}))
        
        self.conn.execute(
            "INSERT OR REPLACE INTO edges (source, target, type, attributes) VALUES (?, ?, ?, ?)",
            (source, target, edge_type, attributes)
        )
        self.conn.commit()
        
        self.graph.add_edge(source, target, type=edge_type, **edge_data.get('attributes', {}))

    def query(self, query_spec: Dict[str, Any]) -> List[Any]:
        node_type = query_spec.get('type')
        if node_type:
            return [n for n, attr in self.graph.nodes(data=True) if attr.get('type') == node_type]
        return list(self.graph.nodes(data=True))

    def get_subgraph(self, entity: str, depth: int = 1) -> Dict[str, Any]:
        if entity not in self.graph:
            return {"nodes": [], "edges": []}
            
        subgraph_nodes = {entity}
        current_layer = {entity}
        for _ in range(depth):
            next_layer = set()
            for node in current_layer:
                next_layer.update(self.graph.successors(node))
                next_layer.update(self.graph.predecessors(node))
            subgraph_nodes.update(next_layer)
            current_layer = next_layer
            
        sub_g = self.graph.subgraph(subgraph_nodes)
        
        nodes = [{"data": {"id": n, "label": sub_g.nodes[n].get("name", n), "type": sub_g.nodes[n].get("type", "unknown")}} for n in sub_g.nodes()]
        edges = [{"data": {"source": u, "target": v, "type": sub_g.edges[u, v].get("type", "unknown")}} for u, v in sub_g.edges()]
        
        return {"nodes": nodes, "edges": edges}
