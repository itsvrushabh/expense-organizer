import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import create_app
from app.llm import LLMEngine
from app.session import SessionManager
import app.main as main_module


@pytest.fixture
def client():
    application = create_app()
    # Initialize engine and session manager manually for tests
    engine = LLMEngine(model_path="/nonexistent/model.gguf")
    manager = SessionManager(llm_engine=engine)
    main_module.llm_engine = engine
    main_module.session_manager = manager

    with TestClient(application) as test_client:
        yield test_client


def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "endpoints" in data


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "model_file_exists" in data
    assert "model_loaded" in data


def test_chat_message_extraction(client):
    session_id = "test-session-1"
    res = client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "Spent 45 on groceries today"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "awaiting_confirmation"
    assert data["action_required"] == "confirm"
    assert data["draft"] is not None
    assert data["draft"]["amount"] == 45.0
    assert data["draft"]["category"] == "Groceries"
    assert data["draft"]["date"] == datetime.now().strftime("%Y-%m-%d")


def test_chat_update_field(client):
    session_id = "test-session-2"
    # Step 1: Create initial draft
    res1 = client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "Paid 30 for pizza"},
    )
    assert res1.status_code == 200
    assert res1.json()["draft"]["amount"] == 30.0

    # Step 2: Change amount
    res2 = client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "change amount to 35"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["draft"]["amount"] == 35.0

    # Step 3: Change category
    res3 = client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "change category to Entertainment"},
    )
    assert res3.status_code == 200
    assert res3.json()["draft"]["category"] == "Entertainment"

    # Step 4: Change date to yesterday
    res4 = client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "change date to yesterday"},
    )
    assert res4.status_code == 200
    expected_yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert res4.json()["draft"]["date"] == expected_yesterday


@patch("app.session.insert_expense_to_db", new_callable=AsyncMock)
def test_chat_confirm_via_message(mock_insert, client):
    mock_insert.return_value = 42
    session_id = "test-session-3"

    # 1. Draft
    client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "Spent 25 on uber ride today"},
    )

    # 2. Confirm via message "yes"
    res = client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "yes"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "saved"
    assert data["saved_expense_id"] == 42
    assert "successfully saved" in data["message"]
    mock_insert.assert_awaited_once()


@patch("app.session.insert_expense_to_db", new_callable=AsyncMock)
def test_chat_confirm_via_endpoint(mock_insert, client):
    mock_insert.return_value = 99
    session_id = "test-session-4"

    client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "Dinner with friends 60"},
    )

    res = client.post("/api/chat/confirm", json={"session_id": session_id})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "saved"
    assert data["saved_expense_id"] == 99
    mock_insert.assert_awaited_once()


def test_chat_cancel_draft(client):
    session_id = "test-session-5"
    client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "Flight ticket 200"},
    )

    res = client.post("/api/chat/cancel", json={"session_id": session_id})
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"

    # Confirming after cancel should return empty/idle prompt
    res2 = client.post("/api/chat/confirm", json={"session_id": session_id})
    assert res2.status_code == 200
    assert res2.json()["status"] == "idle"
