import asyncio
from datetime import date

from models import ExpenseCreate

import storage


def run(coro):
    return asyncio.run(coro)


def make_expense(**overrides):
    payload = {
        "description": "Coffee",
        "amount": 3.5,
        "category": "Food",
        "date": date(2026, 1, 1),
    }
    payload.update(overrides)
    return ExpenseCreate(**payload)


def test_add_assigns_incrementing_ids():
    first = run(storage.add(make_expense()))
    second = run(storage.add(make_expense(description="Bus", category="Transport")))

    assert first.id == 1
    assert second.id == 2
    assert storage._next_id == 3


def test_get_all_returns_copy():
    run(storage.add(make_expense()))

    result = run(storage.get_all())
    result.append("garbage")

    assert len(run(storage.get_all())) == 1


def test_delete_existing():
    expense = run(storage.add(make_expense()))

    deleted = run(storage.delete(expense.id))

    assert deleted is not None
    assert deleted.id == expense.id
    assert run(storage.get_all()) == []


def test_delete_missing_returns_none():
    assert run(storage.delete(999)) is None


def test_update_replaces_fields_keeps_id():
    created = run(storage.add(make_expense()))

    updated = run(storage.update(created.id, make_expense(
        description="Groceries", amount=45.0, category="Other", date=date(2026, 1, 9)
    )))

    assert updated is not None
    assert updated.id == created.id
    assert updated.description == "Groceries"
    assert updated.amount == 45.0
    assert updated.category == "Other"
    assert updated.date == date(2026, 1, 9)
    assert len(run(storage.get_all())) == 1


def test_update_missing_returns_none():
    assert run(storage.update(999, make_expense())) is None
