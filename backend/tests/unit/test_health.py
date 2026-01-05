"""
Health endpoint tests.
"""

from fastapi.testclient import TestClient

from src.container import Container


def test_health_check(client: TestClient):
    """Test health check returns 200 and has expected structure."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "environment" in data
    assert "dependencies" in data


def test_health_live(client: TestClient):
    """Test liveness check (no dependency checks)."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_readiness_check(client: TestClient):
    """Test readiness check returns 200 and has expected structure."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "checks" in data


def test_trace_id_header(client: TestClient):
    """Test that trace-id and request-id headers are returned."""
    response = client.get("/api/v1/health/live")
    assert "x-trace-id" in response.headers
    assert "x-request-id" in response.headers


def test_custom_trace_id_propagation(client: TestClient):
    """Test that custom trace-id is propagated."""
    custom_trace_id = "test-trace-123"
    response = client.get("/api/v1/health/live", headers={"X-Trace-ID": custom_trace_id})
    assert response.headers["x-trace-id"] == custom_trace_id
