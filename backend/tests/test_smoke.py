"""
Smoke tests for the Core Backend API.
Verifies critical paths, service health, and basic CRUD loop.
"""

from fastapi.testclient import TestClient
import pytest

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


def test_smoke_health_check(client):
    """Smoke test: GET /health returns HTTP 200 with status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data


def test_smoke_root_catalog(client):
    """Smoke test: GET / returns HTTP 200 with catalog of endpoints."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Expense Organizer API"
    assert "endpoints" in data
    assert "add_expense" in data["endpoints"]
    assert "combined_summary" in data["endpoints"]


def test_smoke_currencies_endpoint(client):
    """Smoke test: GET /currencies returns list with base USD."""
    response = client.get("/currencies")
    assert response.status_code == 200
    currencies = response.json()
    assert isinstance(currencies, list)
    assert any(c["code"] == "USD" for c in currencies)


def test_smoke_categories_endpoint(client):
    """Smoke test: GET /categories returns standard categories."""
    response = client.get("/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert any(c["name"] == "Food" for c in categories)


def test_smoke_expense_lifecycle(client):
    """Smoke test: Full CRUD lifecycle round-trip."""
    # 1. Create
    create_payload = {
        "description": "Smoke Coffee",
        "amount": 4.50,
        "currency": "USD",
        "category": "Food",
        "date": "2026-09-10",
    }
    create_res = client.post("/expenses", json=create_payload)
    assert create_res.status_code == 200
    created = create_res.json()
    expense_id = created["id"]
    assert created["description"] == "Smoke Coffee"
    assert created["amount"] == 4.50

    # 2. Read
    list_res = client.get("/expenses")
    assert list_res.status_code == 200
    summary = list_res.json()
    assert summary["count"] >= 1
    assert any(e["id"] == expense_id for e in summary["expenses"])

    # 3. Update
    update_payload = {
        "description": "Smoke Coffee & Donut",
        "amount": 7.00,
        "currency": "USD",
        "category": "Food",
        "date": "2026-09-10",
    }
    update_res = client.put(f"/expenses/{expense_id}", json=update_payload)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["description"] == "Smoke Coffee & Donut"
    assert updated["amount"] == 7.00

    # 4. Delete
    delete_res = client.delete(f"/expenses/{expense_id}")
    assert delete_res.status_code == 200

    # 5. Verify deletion
    after_list = client.get("/expenses").json()
    assert not any(e["id"] == expense_id for e in after_list["expenses"])
