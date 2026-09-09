import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import create_app
from app.model_client import ModelClient
from app.session import SessionManager
from app.tools import (
    TOOLS_SCHEMA,
    tool_draft_expense,
    tool_update_draft_field,
    tool_commit_expense,
    tool_ask_clarification,
    tool_cancel_draft,
    execute_tool,
    ExpenseDraft,
    ToolCall,
)
import app.main as main_module


@pytest.fixture
def client():
    application = create_app()
    m_client = ModelClient(aimodel_url="http://nonexistent:8002")
    manager = SessionManager(model_client=m_client)
    main_module.model_client = m_client
    main_module.session_manager = manager

    with TestClient(application) as test_client:
        yield test_client


def test_tools_schema():
    tool_names = [t["function"]["name"] for t in TOOLS_SCHEMA]
    assert "draft_expense" in tool_names
    assert "update_draft_field" in tool_names
    assert "commit_expense" in tool_names
    assert "ask_clarification" in tool_names
    assert "cancel_draft" in tool_names


def test_tool_draft_expense():
    res = tool_draft_expense("Team Lunch", 45.0, "Food", "2026-09-09")
    assert res.status == "awaiting_confirmation"
    assert res.draft.amount == 45.0
    assert res.draft.category == "Food"


def test_tool_update_draft_field():
    draft = ExpenseDraft(
        description="Groceries",
        amount=50.0,
        category="Groceries",
        date="2026-09-09",
    )
    res = tool_update_draft_field("amount", "60", draft)
    assert res.draft.amount == 60.0

    res2 = tool_update_draft_field("date", "yesterday", res.draft)
    expected_yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert res2.draft.date == expected_yesterday


@pytest.mark.anyio
@patch("app.tools.insert_expense_to_db", new_callable=AsyncMock)
async def test_tool_commit_expense(mock_insert):
    mock_insert.return_value = 88
    res = await tool_commit_expense("Flight", 300.0, "Travel", "2026-09-09")
    assert res.status == "saved"
    assert res.saved_expense_id == 88


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "aimodel_url" in data
    assert "backend_url" in data


def test_chat_message_flow(client):
    session_id = "test-session-flow"
    res1 = client.post(
        "/api/chat/message",
        json={"message": "Spent 45 on pizza lunch today", "session_id": session_id},
    )
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["status"] == "awaiting_confirmation"
    assert d1["draft"]["amount"] == 45.0
    assert d1["draft"]["category"] == "Food"

    # Update field
    res2 = client.post(
        "/api/chat/message",
        json={"message": "change amount to 50", "session_id": session_id},
    )
    assert res2.status_code == 200
    assert res2.json()["draft"]["amount"] == 50.0


@patch("app.tools.insert_expense_to_db", new_callable=AsyncMock)
def test_chat_confirm(mock_insert, client):
    mock_insert.return_value = 55
    session_id = "test-session-confirm"

    client.post(
        "/api/chat/message",
        json={"message": "Spent 25 on uber ride today", "session_id": session_id},
    )

    res = client.post("/api/chat/confirm", json={"session_id": session_id})
    assert res.status_code == 200
    assert res.json()["status"] == "saved"
    assert res.json()["saved_expense_id"] == 55


def test_chat_cancel(client):
    session_id = "test-session-cancel"
    client.post(
        "/api/chat/message",
        json={"message": "Bought shoes 120", "session_id": session_id},
    )

    res = client.post("/api/chat/cancel", json={"session_id": session_id})
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"


@pytest.mark.anyio
@patch("app.tools.refresh_exchange_rates_in_backend", new_callable=AsyncMock)
async def test_refresh_exchange_rates_tool(mock_refresh):
    mock_refresh.return_value = [
        {"code": "USD", "symbol": "$", "exchange_rate": 1.0},
        {"code": "INR", "symbol": "₹", "exchange_rate": 94.84},
        {"code": "EUR", "symbol": "€", "exchange_rate": 0.86},
    ]

    res = await execute_tool(ToolCall(tool="refresh_exchange_rates", arguments={}))
    assert res.status == "idle"
    assert "Successfully refreshed live currency exchange rates" in res.message
    assert "INR" in res.message
    assert "94.8400" in res.message
