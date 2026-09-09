"""
Regression test suite for Core Backend API.
Guards against known regressions, edge cases, boundary conditions,
and legacy API contracts.
"""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
import storage
from fastapi.testclient import TestClient
from main import create_app
from models import Expense, ExpenseCreate, ExpenseSummary
from services import currency_service


@pytest.fixture(autouse=True)
def clean_storage():
    storage.reset_in_memory()
    yield
    storage.reset_in_memory()


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# 1. Model Inheritance & Legacy Schema Regression
# ---------------------------------------------------------------------------


def test_regression_expense_model_isinstance():
    """Guards against regression where Expense did not subclass ExpenseCreate."""
    exp = Expense(
        id=99,
        description="Headphones",
        amount=59.99,
        currency="USD",
        currency_symbol="$",
        category="Shopping",
        date=date(2026, 9, 10),
    )
    assert isinstance(exp, ExpenseCreate)
    assert exp.id == 99
    assert exp.amount == 59.99


def test_regression_expense_summary_defaults():
    """ExpenseSummary must include currency and currency_symbol defaults."""
    summary = ExpenseSummary(total=100.0, count=1, expenses=[])
    assert summary.currency == "USD"
    assert summary.currency_symbol == "$"


# ---------------------------------------------------------------------------
# 2. Date Sorting Regression (Must Ascend by Date in Aggregations)
# ---------------------------------------------------------------------------


def test_regression_month_view_date_sorting(client):
    """Month queries must return expenses ordered chronologically (ASC)."""
    # Insert unordered dates
    client.post(
        "/expenses",
        json={
            "description": "Late March",
            "amount": 10.0,
            "category": "Food",
            "date": "2026-03-28",
        },
    )
    client.post(
        "/expenses",
        json={
            "description": "Early March",
            "amount": 20.0,
            "category": "Food",
            "date": "2026-03-02",
        },
    )
    client.post(
        "/expenses",
        json={"description": "Mid March", "amount": 15.0, "category": "Food", "date": "2026-03-15"},
    )

    res = client.get("/expenses/month/2026/3")
    assert res.status_code == 200
    expenses = res.json()["expenses"]
    dates = [e["date"] for e in expenses]
    assert dates == ["2026-03-02", "2026-03-15", "2026-03-28"]


def test_regression_week_view_date_sorting(client):
    """Week queries must return expenses ordered chronologically (ASC)."""
    # 2026-03-16 to 2026-03-22 is Week 12
    client.post(
        "/expenses",
        json={"description": "Friday", "amount": 10.0, "category": "Food", "date": "2026-03-20"},
    )
    client.post(
        "/expenses",
        json={"description": "Tuesday", "amount": 20.0, "category": "Food", "date": "2026-03-17"},
    )
    client.post(
        "/expenses",
        json={"description": "Monday", "amount": 15.0, "category": "Food", "date": "2026-03-16"},
    )

    res = client.get("/expenses/week/2026/12")
    assert res.status_code == 200
    dates = [e["date"] for e in res.json()["expenses"]]
    assert dates == ["2026-03-16", "2026-03-17", "2026-03-20"]


# ---------------------------------------------------------------------------
# 3. Category Deduplication & Auto-Resolution Regression
# ---------------------------------------------------------------------------


def test_regression_category_case_insensitivity(client):
    """Different casings of existing category must resolve without creating duplicates."""
    initial_categories = client.get("/categories").json()
    initial_count = len(initial_categories)

    # Post with lowercase and whitespace
    res1 = client.post(
        "/expenses",
        json={"description": "Burger", "amount": 8.0, "category": " food ", "date": "2026-09-01"},
    )
    assert res1.status_code == 200
    assert res1.json()["category"] == "Food"  # Normalized to canonical name

    # Post with uppercase
    res2 = client.post(
        "/expenses",
        json={"description": "Pizza", "amount": 12.0, "category": "FOOD", "date": "2026-09-02"},
    )
    assert res2.status_code == 200
    assert res2.json()["category"] == "Food"

    # Category table count should not increase
    after_categories = client.get("/categories").json()
    assert len(after_categories) == initial_count


def test_regression_unseeded_category_auto_creation(client):
    """Posting with an unknown category string must auto-create it gracefully."""
    res = client.post(
        "/expenses",
        json={
            "description": "Bitcoin Mining",
            "amount": 100.0,
            "category": "CryptoHardware",
            "date": "2026-09-01",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "CryptoHardware"
    assert data["category_id"] is not None

    # Check it now appears in active categories list
    categories = client.get("/categories").json()
    assert any(c["name"] == "CryptoHardware" for c in categories)


def test_regression_soft_delete_preserves_historical_expenses(client):
    """Soft-deleting a category must not break historical expense summaries."""
    # Create category and expense
    cat_res = client.post("/categories", json={"name": "GymMemberships"})
    cat_id = cat_res.json()["id"]

    exp_res = client.post(
        "/expenses",
        json={
            "description": "Gold's Gym",
            "amount": 50.0,
            "category": "GymMemberships",
            "date": "2026-01-10",
        },
    )
    exp_id = exp_res.json()["id"]

    # Soft delete category
    del_cat = client.delete(f"/categories/{cat_id}")
    assert del_cat.status_code == 200

    # Historical expense summary should still retrieve and display the expense intact
    summary_res = client.get("/expenses/category/GymMemberships")
    assert summary_res.status_code == 200
    assert summary_res.json()["count"] == 1
    assert summary_res.json()["expenses"][0]["id"] == exp_id


# ---------------------------------------------------------------------------
# 4. Input Validation & Error Handling Regressions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("invalid_amount", [0.0, -0.01, -100.0])
def test_regression_rejects_non_positive_amounts(client, invalid_amount):
    """Amount must strictly be > 0."""
    res = client.post(
        "/expenses",
        json={
            "description": "Bad Amount",
            "amount": invalid_amount,
            "category": "Food",
            "date": "2026-09-01",
        },
    )
    assert res.status_code == 422


@pytest.mark.parametrize("invalid_month", [0, 13, 99])
def test_regression_rejects_invalid_month_boundaries(client, invalid_month):
    """Month parameter must be between 1 and 12."""
    res = client.get(f"/expenses/month/2026/{invalid_month}")
    assert res.status_code == 422


@pytest.mark.parametrize("invalid_week", [0, 54, 99])
def test_regression_rejects_invalid_week_boundaries(client, invalid_week):
    """ISO week parameter must be between 1 and 53."""
    res = client.get(f"/expenses/week/2026/{invalid_week}")
    assert res.status_code == 422


def test_regression_non_existent_id_operations(client):
    """Updating or deleting non-existent IDs must return 404, not 500."""
    put_res = client.put(
        "/expenses/999999",
        json={"description": "Ghost", "amount": 10.0, "category": "Food", "date": "2026-09-01"},
    )
    assert put_res.status_code == 404

    del_res = client.delete("/expenses/999999")
    assert del_res.status_code == 404


# ---------------------------------------------------------------------------
# 5. Multi-Currency & Rate Conversion Regressions
# ---------------------------------------------------------------------------


def test_regression_multi_currency_summary_conversion(client):
    """Guards currency precision and correct symbol attachment."""
    # Post $100 USD expense
    client.post(
        "/expenses",
        json={
            "description": "Laptop Stand",
            "amount": 100.0,
            "currency": "USD",
            "category": "Shopping",
            "date": "2026-09-01",
        },
    )

    # Check in INR (rate 84.0)
    inr_res = client.get("/expenses/summary?currency=INR")
    assert inr_res.status_code == 200
    inr_data = inr_res.json()
    assert inr_data["total"] == 8400.0
    assert inr_data["currency"] == "INR"
    assert inr_data["currency_symbol"] == "₹"

    # Check in EUR (rate 0.92)
    eur_res = client.get("/expenses/summary?currency=EUR")
    assert eur_res.status_code == 200
    eur_data = eur_res.json()
    assert eur_data["total"] == 92.0
    assert eur_data["currency"] == "EUR"
    assert eur_data["currency_symbol"] == "€"


# ---------------------------------------------------------------------------
# 6. Combined Multi-Category Summary Regression
# ---------------------------------------------------------------------------


def test_regression_combined_summary_empty_result(client):
    """Summary with no matching records must return 0 total, 0 count, empty list."""
    res = client.get("/expenses/summary?year=1999&categories=NonExistentCategory")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0.0
    assert data["count"] == 0
    assert data["expenses"] == []


# ---------------------------------------------------------------------------
# 7. Currency Service Resilience Regression
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_regression_currency_service_network_timeout():
    """Currency service must catch network errors and return empty dict safely."""
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection timed out")):
        rates = await currency_service.fetch_live_rates()
        assert rates == {}


def test_regression_category_404_handling(client):
    """Deleting or activating non-existent category IDs returns 404."""
    del_res = client.delete("/categories/99999")
    assert del_res.status_code == 404
    assert "not found" in del_res.json()["detail"].lower()

    patch_res = client.patch("/categories/99999/activate")
    assert patch_res.status_code == 404
    assert "not found" in patch_res.json()["detail"].lower()


@pytest.mark.anyio
async def test_regression_currency_service_http_error_handling():
    """Currency service handles non-200 status code and unexpected payload format."""
    mock_resp_500 = AsyncMock()
    mock_resp_500.status_code = 500
    mock_resp_500.text = "Internal server error"

    mock_client_500 = AsyncMock()
    mock_client_500.__aenter__.return_value.get.return_value = mock_resp_500

    with patch("httpx.AsyncClient", return_value=mock_client_500):
        rates = await currency_service.fetch_live_rates()
        assert rates == {}

    mock_resp_unexpected = AsyncMock()
    mock_resp_unexpected.status_code = 200
    mock_resp_unexpected.json.return_value = {"result": "error"}

    mock_client_unexp = AsyncMock()
    mock_client_unexp.__aenter__.return_value.get.return_value = mock_resp_unexpected

    with patch("httpx.AsyncClient", return_value=mock_client_unexp):
        rates = await currency_service.fetch_live_rates()
        assert rates == {}


@pytest.mark.anyio
async def test_regression_currency_worker_clean_cancellation():
    """Currency sync worker starts and cancels cleanly without hanging or error."""
    import asyncio

    with patch("services.currency_service.sync_currency_rates", new_callable=AsyncMock):
        task = asyncio.create_task(currency_service.start_currency_sync_worker())
        await asyncio.sleep(0.01)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert task.cancelled()
