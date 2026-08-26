import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any

class TigerGraphClient:
    def __init__(self):
        self.host = os.environ.get('TIGERGRAPH_HOST', '')
        self.user = os.environ.get('TIGERGRAPH_USER', 'tg_user')
        self.password = os.environ.get('TIGERGRAPH_PASSWORD', '')
        self.graphname = "CodeGraphX"
        self.base_url = f"https://{self.host}:9000" if self.host else ""

    def test_connection(self) -> bool:
        """Check connectivity (10s timeout)"""
        if not self.host or self.host == "your-instance.i.tgcloud.io":
            return False
            
        try:
            req = urllib.request.Request(f"{self.base_url}/echo")
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception:
            return False

    def add_vertex(self, vertex_type: str, vertex_id: str, attributes: Dict[str, Any]) -> bool:
        payload = {
            "vertices": {
                vertex_type: {
                    vertex_id: attributes
                }
            }
        }
        return self._post_data(payload)

    def add_edge(self, edge_type: str, source_type: str, source_id: str, target_type: str, target_id: str, attributes: Dict[str, Any] = None) -> bool:
        if attributes is None:
            attributes = {}
        payload = {
            "edges": {
                source_type: {
                    source_id: {
                        edge_type: {
                            target_type: {
                                target_id: attributes
                            }
                        }
                    }
                }
            }
        }
        return self._post_data(payload)

    def _post_data(self, payload: Dict[str, Any]) -> bool:
        if not self.base_url:
            return False
        try:
            req = urllib.request.Request(
                f"{self.base_url}/graph/{self.graphname}",
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception:
            return False
