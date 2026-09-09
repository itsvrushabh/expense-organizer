from datetime import date
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from main import create_app
import storage


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
# Currencies Tests
# ---------------------------------------------------------------------------

def test_list_currencies_returns_defaults(client):
    response = client.get("/currencies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 6

    codes = {c["code"]: c for c in data}
    assert "USD" in codes
    assert "INR" in codes
    assert "EUR" in codes
    assert "JPY" in codes
    assert "GBP" in codes
    assert "CNY" in codes

    assert codes["USD"]["symbol"] == "$"
    assert codes["INR"]["symbol"] == "₹"
    assert codes["EUR"]["symbol"] == "€"
    assert codes["JPY"]["symbol"] == "¥"
    assert codes["USD"]["is_default"] is True


def test_currencies_refresh_updates_rates(client):
    mock_rates = {"USD": 1.0, "INR": 95.0, "EUR": 0.88, "JPY": 155.0, "GBP": 0.75, "CNY": 6.8}
    with patch("services.currency_service.fetch_live_rates", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_rates

        response = client.post("/currencies/refresh")
        assert response.status_code == 200
        data = response.json()
        codes = {c["code"]: c for c in data}

        assert codes["INR"]["exchange_rate"] == 95.0
        assert codes["EUR"]["exchange_rate"] == 0.88


def test_currencies_refresh_resilient_on_offline(client):
    with patch("services.currency_service.fetch_live_rates", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {}  # simulates offline or timeout

        response = client.post("/currencies/refresh")
        assert response.status_code == 200
        data = response.json()
        codes = {c["code"]: c for c in data}
        assert codes["INR"]["exchange_rate"] == 84.0  # remains default


# ---------------------------------------------------------------------------
# Categories Tests
# ---------------------------------------------------------------------------

def test_list_categories_includes_online_and_defaults(client):
    response = client.get("/categories")
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Online" in names
    assert "Food" in names
    assert "Groceries" in names


def test_create_category_success(client):
    payload = {"name": "Cryptocurrency", "icon": "bitcoin", "color": "#FFD700"}
    response = client.post("/categories", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cryptocurrency"
    assert data["icon"] == "bitcoin"
    assert data["color"] == "#FFD700"
    assert data["is_active"] is True


def test_create_category_case_insensitive_duplicate_rejected(client):
    client.post("/categories", json={"name": "Gaming"})
    # duplicate in different casing
    response = client.post("/categories", json={"name": "gaming"})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_soft_delete_and_reactivate_category(client):
    # Create category
    res = client.post("/categories", json={"name": "Subscriptions"})
    cat_id = res.json()["id"]

    # Soft-delete
    del_res = client.delete(f"/categories/{cat_id}")
    assert del_res.status_code == 200

    # Active-only list should not include Subscriptions
    active_res = client.get("/categories?active_only=true")
    active_names = [c["name"] for c in active_res.json()]
    assert "Subscriptions" not in active_names

    # All list should include Subscriptions with is_active=False
    all_res = client.get("/categories?active_only=false")
    sub_cat = next(c for c in all_res.json() if c["id"] == cat_id)
    assert sub_cat["is_active"] is False

    # Reactivate
    react_res = client.patch(f"/categories/{cat_id}/activate")
    assert react_res.status_code == 200
    assert react_res.json()["message"] == "Category activated"

    # Now appears in active
    active_res2 = client.get("/categories?active_only=true")
    assert "Subscriptions" in [c["name"] for c in active_res2.json()]


# ---------------------------------------------------------------------------
# Combined Summary Endpoint (/expenses/summary) Tests
# ---------------------------------------------------------------------------

def test_combined_summary_multiple_categories(client):
    client.post("/expenses", json={"description": "Netflix", "amount": 15.0, "category": "Online", "date": "2026-02-10"})
    client.post("/expenses", json={"description": "Keyboard", "amount": 45.0, "category": "Shopping", "date": "2026-02-14"})
    client.post("/expenses", json={"description": "Dinner", "amount": 30.0, "category": "Food", "date": "2026-02-15"})

    # Query Online + Shopping only
    res = client.get("/expenses/summary?categories=Online&categories=Shopping")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 2
    assert data["total"] == 60.0
    descs = {e["description"] for e in data["expenses"]}
    assert descs == {"Netflix", "Keyboard"}


def test_combined_summary_february_online_expenses(client):
    # Feb Online
    client.post("/expenses", json={"description": "Server hosting", "amount": 50.0, "category": "Online", "date": "2026-02-05"})
    client.post("/expenses", json={"description": "Domain renewal", "amount": 20.0, "category": "Online", "date": "2026-02-20"})
    # March Online
    client.post("/expenses", json={"description": "SaaS tool", "amount": 35.0, "category": "Online", "date": "2026-03-01"})

    # Summary of February Month for Online Expense
    res = client.get("/expenses/summary?year=2026&month=2&categories=Online")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 2
    assert data["total"] == 70.0


def test_combined_summary_currency_conversion(client):
    client.post("/expenses", json={"description": "Book", "amount": 10.0, "currency": "USD", "category": "Education", "date": "2026-09-01"})

    # Convert to INR (84.0 rate)
    res_inr = client.get("/expenses/summary?currency=INR")
    assert res_inr.status_code == 200
    data_inr = res_inr.json()
    assert data_inr["currency"] == "INR"
    assert data_inr["currency_symbol"] == "₹"
    assert data_inr["total"] == 840.0

    # Convert to EUR (0.92 rate)
    res_eur = client.get("/expenses/summary?currency=EUR")
    assert res_eur.status_code == 200
    data_eur = res_eur.json()
    assert data_eur["currency"] == "EUR"
    assert data_eur["currency_symbol"] == "€"
    assert data_eur["total"] == 9.2
