from datetime import date

from models import ExpenseCreate

import storage


def add(client, payload):
    response = client.post("/expenses", json=payload)
    assert response.status_code == 200
    return response.json()


def test_root_lists_endpoints(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Expense Organizer API"
    assert body["endpoints"]["add_expense"] == "POST /expenses"


def test_create_expense_echoes_fields(client, sample_payload):
    body = add(client, sample_payload(amount=42.25, description="Dinner"))

    assert body["id"] == 1
    assert body["description"] == "Dinner"
    assert body["amount"] == 42.25
    assert body["date"] == "2026-03-15"


def test_create_expense_rejects_invalid_amount(client, sample_payload):
    response = client.post("/expenses", json=sample_payload(amount=-1))
    assert response.status_code == 422


def test_create_expense_rejects_invalid_date(client, sample_payload):
    response = client.post("/expenses", json=sample_payload(date="2026-13-99"))
    assert response.status_code == 422


def test_get_all_empty_summary(client):
    response = client.get("/expenses")
    assert response.status_code == 200
    assert response.json() == {"total": 0, "count": 0, "expenses": []}


def test_get_all_returns_summary(client, sample_payload):
    add(client, sample_payload(amount=10.0))
    add(client, sample_payload(amount=32.5))

    body = client.get("/expenses").json()
    assert body["count"] == 2
    assert body["total"] == 42.5


def test_get_day_expenses_filters_exact_date(client, sample_payload):
    add(client, sample_payload(date="2026-03-15", amount=5.0))
    add(client, sample_payload(date="2026-03-15", amount=7.0))
    add(client, sample_payload(date="2026-03-16", amount=100.0))

    body = client.get("/expenses/day/2026-03-15").json()
    assert body["count"] == 2
    assert body["total"] == 12.0


def test_get_month_expenses_sorted_by_date(client, sample_payload):
    add(client, sample_payload(date="2026-03-20", amount=1.0))
    add(client, sample_payload(date="2026-03-05", amount=2.0))
    add(client, sample_payload(date="2026-04-01", amount=99.0))

    body = client.get("/expenses/month/2026/3").json()
    assert body["count"] == 2
    dates = [e["date"] for e in body["expenses"]]
    assert dates == sorted(dates)
    assert all(d.startswith("2026-03") for d in dates)


def test_get_month_expenses_rejects_invalid_month(client):
    assert client.get("/expenses/month/2026/13").status_code == 422
    assert client.get("/expenses/month/2026/0").status_code == 422


def test_get_year_expenses(client, sample_payload):
    add(client, sample_payload(date="2026-02-01"))
    add(client, sample_payload(date="2025-02-01"))

    body = client.get("/expenses/year/2026").json()
    assert body["count"] == 1
    assert body["expenses"][0]["date"].startswith("2026")


def test_get_category_expenses_case_insensitive(client, sample_payload):
    add(client, sample_payload(category="Food"))
    add(client, sample_payload(category="Other"))

    body = client.get("/expenses/category/fOOD").json()
    assert body["count"] == 1
    assert body["expenses"][0]["category"] == "Food"


def test_update_expense(client, sample_payload):
    created = add(client, sample_payload())

    response = client.put(f"/expenses/{created['id']}", json=sample_payload(
        description="Dinner", amount=88.0, category="Food", date="2026-03-20"
    ))
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["description"] == "Dinner"
    assert body["amount"] == 88.0
    assert body["date"] == "2026-03-20"

    summary = client.get("/expenses").json()
    assert summary["total"] == 88.0


def test_update_expense_rejects_invalid_payload(client, sample_payload):
    created = add(client, sample_payload())
    response = client.put(f"/expenses/{created['id']}", json=sample_payload(amount=0))
    assert response.status_code == 422


def test_update_missing_expense_returns_404(client, sample_payload):
    response = client.put("/expenses/12345", json=sample_payload())
    assert response.status_code == 404


def test_delete_expense_removes_it(client, sample_payload):
    created = add(client, sample_payload())

    response = client.delete(f"/expenses/{created['id']}")
    assert response.status_code == 200
    assert response.json()["expense"]["id"] == created["id"]
    assert client.get("/expenses").json()["count"] == 0


def test_delete_missing_expense_returns_404(client):
    assert client.delete("/expenses/12345").status_code == 404
