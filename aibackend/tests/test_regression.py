"""
Regression test suite for the AI Backend service.
Guards against parsing regressions, session lifecycle edge cases,
and fallback logic for tool use and date normalization.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from app.expense_client import (
    check_backend_health,
    get_currencies_from_backend,
    insert_expense_to_db,
    normalize_iso_date,
    refresh_exchange_rates_in_backend,
)
from app.model_client import ModelClient
from app.schemas import ExpenseDraft, ToolCall
from app.session import SessionManager
from app.tools import (
    execute_tool,
    tool_ask_clarification,
    tool_cancel_draft,
    tool_update_draft_field,
)

# ---------------------------------------------------------------------------
# 1. Date Normalization Regressions
# ---------------------------------------------------------------------------


def test_regression_normalize_iso_date_relative_keywords():
    ref = datetime(2026, 3, 15, 12, 0, 0)
    assert normalize_iso_date("today", ref) == "2026-03-15"
    assert normalize_iso_date("now", ref) == "2026-03-15"
    assert normalize_iso_date("", ref) == "2026-03-15"
    assert normalize_iso_date("yesterday", ref) == "2026-03-14"
    assert normalize_iso_date("tomorrow", ref) == "2026-03-16"


def test_regression_normalize_iso_date_iso_and_fallback():
    ref = datetime(2026, 3, 15, 12, 0, 0)
    assert normalize_iso_date("2026-02-28", ref) == "2026-02-28"
    assert normalize_iso_date("Spent on 2026-12-25 holiday", ref) == "2026-12-25"
    # Unparseable gibberish falls back safely to reference date
    assert normalize_iso_date("someday-random", ref) == "2026-03-15"


# ---------------------------------------------------------------------------
# 2. Tool Execution & Draft Field Modification Regressions
# ---------------------------------------------------------------------------


def test_regression_tool_update_draft_field_all_fields():
    draft = ExpenseDraft(description="Old", amount=10.0, category="Food", date="2026-03-01")
    ref = datetime(2026, 3, 15)

    # 1. Update amount
    res_amt = tool_update_draft_field("amount", "25.50", draft, ref)
    assert res_amt.draft.amount == 25.50

    # 2. Update category
    res_cat = tool_update_draft_field("category", "Online", draft, ref)
    assert res_cat.draft.category == "Online"

    # 3. Update description
    res_desc = tool_update_draft_field("description", "'New Laptop Stand'", draft, ref)
    assert res_desc.draft.description == "New Laptop Stand"

    # 4. Update date
    res_date = tool_update_draft_field("date", "yesterday", draft, ref)
    assert res_date.draft.date == "2026-03-14"


def test_regression_tool_update_without_draft_returns_idle():
    """Updating a draft when none exists must not raise an exception."""
    res = tool_update_draft_field("amount", "20", None)
    assert res.status == "idle"
    assert "no active draft" in res.message.lower()


def test_regression_tool_ask_clarification():
    res = tool_ask_clarification("amount", "How much was the coffee?")
    assert res.status == "idle"
    assert res.action_required == "clarify"
    assert res.message == "How much was the coffee?"


def test_regression_tool_cancel_draft_with_and_without_reason():
    res_no_reason = tool_cancel_draft()
    assert res_no_reason.status == "cancelled"

    res_with_reason = tool_cancel_draft(reason="User changed mind")
    assert res_with_reason.status == "cancelled"
    assert "User changed mind" in res_with_reason.message


# ---------------------------------------------------------------------------
# 3. Expense Client HTTP Error Handling Regressions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_regression_insert_expense_to_db_error_handling():
    draft = ExpenseDraft(description="Test", amount=10.0, category="Food", date="2026-09-10")

    # 500 error
    mock_500 = AsyncMock()
    mock_500.status_code = 500
    mock_500.text = "DB error"
    with patch("httpx.AsyncClient.post", return_value=mock_500):
        res = await insert_expense_to_db(draft)
        assert res is None

    # Exception
    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
        res = await insert_expense_to_db(draft)
        assert res is None


@pytest.mark.anyio
async def test_regression_check_backend_health_unreachable():
    mock_503 = AsyncMock()
    mock_503.status_code = 503
    with patch("httpx.AsyncClient.get", return_value=mock_503):
        res = await check_backend_health()
        assert res["status"] == "unreachable"

    with patch("httpx.AsyncClient.get", side_effect=Exception("Timeout")):
        res = await check_backend_health()
        assert res["status"] == "unreachable"
        assert "error" in res


@pytest.mark.anyio
async def test_regression_currency_client_error_handling():
    # Refresh currencies failure
    mock_error = AsyncMock()
    mock_error.status_code = 500
    mock_error.text = "Internal error"
    with patch("httpx.AsyncClient.post", return_value=mock_error):
        res = await refresh_exchange_rates_in_backend()
        assert res is None

    # Get currencies network exception
    with patch("httpx.AsyncClient.get", side_effect=Exception("Network error")):
        res = await get_currencies_from_backend()
        assert res is None


# ---------------------------------------------------------------------------
# 4. Session Manager Lifecycle Regressions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_regression_session_manager_confirm_cancel_edge_cases():
    m_client = ModelClient("http://nonexistent:8002")
    manager = SessionManager(model_client=m_client)

    # Confirming when no draft exists
    res_confirm = await manager.confirm_draft("sess-no-draft")
    assert res_confirm.status == "idle"
    assert "no active draft to confirm" in res_confirm.message.lower()

    # Cancelling when no draft exists
    res_cancel = await manager.cancel_draft("sess-no-draft-cancel")
    assert res_cancel.status == "cancelled"
    assert "discarded" in res_cancel.message.lower()

    # Resetting session
    session = manager.get_or_create_session("sess-to-reset")
    session.pending_draft = ExpenseDraft(
        description="X", amount=5.0, category="Food", date="2026-09-10"
    )
    manager.reset_session("sess-to-reset")
    assert "sess-to-reset" not in manager.sessions


@pytest.mark.anyio
async def test_regression_fetch_expense_summary_error_handling():
    from app.expense_client import fetch_expense_summary

    mock_500 = AsyncMock()
    mock_500.status_code = 500
    mock_500.text = "Internal error"
    with patch("httpx.AsyncClient.get", return_value=mock_500):
        res = await fetch_expense_summary(year=2026, month=2)
        assert res is None

    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
        res = await fetch_expense_summary(year=2026, month=2)
        assert res is None


@pytest.mark.anyio
@patch("app.tools.fetch_expense_summary", new_callable=AsyncMock)
async def test_regression_query_expense_summary_empty_results(mock_fetch):
    mock_fetch.return_value = {
        "total": 0.0,
        "count": 0,
        "currency": "USD",
        "currency_symbol": "$",
        "expenses": [],
    }

    res = await execute_tool(
        ToolCall(
            tool="query_expense_summary",
            arguments={"relative_period": "yesterday"},
        )
    )
    assert res.status == "idle"
    assert "No expenses found" in res.message
    assert "yesterday" in res.message
