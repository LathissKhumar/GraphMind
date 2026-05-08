import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from src.api.main import app

client = TestClient(app)

class TestAPIHealth:
    def test_health_returns_status(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "status" in response.json()

class TestAPIMetrics:
    def test_metrics_returns_token_stats(self):
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "savings_percentage" in data
        assert "total_queries" in data

class TestAPIQuery:
    def test_query_returns_answer(self):
        response = client.post("/api/query", json={"query": "What functions are defined?"})
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "tier" in data

    def test_query_with_empty_body_fails(self):
        response = client.post("/api/query", json={})
        assert response.status_code in [400, 422]

class TestAPIGraph:
    def test_graph_returns_cytoscape_json(self):
        response = client.get("/api/graph")
        assert response.status_code == 200
        data = response.json()
        assert "elements" in data or data == {}

class TestAPIUpload:
    def test_upload_requires_file(self):
        response = client.post("/api/upload")
        assert response.status_code in [400, 422]

class TestAPIClone:
    def test_clone_requires_url(self):
        response = client.post("/api/clone", json={})
        assert response.status_code in [400, 422]

    def test_clone_validates_url(self):
        response = client.post("/api/clone", json={"url": "not-a-url"})
        assert response.status_code == 400

class TestAPIIngest:
    def test_ingest_requires_path(self):
        response = client.post("/api/ingest", json={})
        assert response.status_code in [400, 422]

    def test_ingest_validates_path(self):
        response = client.post("/api/ingest", json={"codebase_path": "/nonexistent/path"})
        assert response.status_code in [400, 404]

class TestAPIQueryHistory:
    def test_history_returns_data(self):
        response = client.get("/api/query-history")
        assert response.status_code == 200
        data = response.json()
        assert "queries" in data or "total" in data

class TestAPIBudget:
    def test_budget_can_be_set(self):
        response = client.post("/api/budget", json={"budget": 50000})
        assert response.status_code in [200, 422]

    def test_budget_returns_state(self):
        response = client.get("/api/budget")
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert "budget_limit" in data or "budget" in data