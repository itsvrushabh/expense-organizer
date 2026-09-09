"""
Smoke tests for the AI Chat Assistant Backend.
Verifies critical paths, API routes, and agent session initialization.
"""

from fastapi.testclient import TestClient
import pytest

from app.main import create_app
from app.model_client import ModelClient
from app.session import SessionManager
import app.main as main_module


@pytest.fixture
def client():
    app = create_app()
    m_client = ModelClient(aimodel_url="http://nonexistent:8002")
    manager = SessionManager(model_client=m_client)
    main_module._session_manager = manager
    with TestClient(app) as test_client:
        yield test_client


def test_smoke_ai_backend_health(client):
    """Smoke test: GET /health returns 200 and valid health status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "aimodel_url" in data
    assert "backend_url" in data


def test_smoke_ai_backend_root(client):
    """Smoke test: GET / returns 200 and service metadata."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "name" in data
    assert "endpoints" in data


def test_smoke_session_creation(client):
    """Smoke test: POST /api/chat/message initializes session and responds."""
    res = client.post(
        "/api/chat/message",
        json={"message": "Spent 20 on Uber", "session_id": "smoke-session-1"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == "smoke-session-1"
    assert data["status"] in ["awaiting_confirmation", "idle"]
