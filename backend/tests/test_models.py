from datetime import date

import pytest
from models import Expense, ExpenseCreate, ExpenseSummary
from pydantic import ValidationError


def test_expense_create_parses_iso_date():
    expense = ExpenseCreate(description="Lunch", amount=12.5, category="Food", date="2026-03-15")
    assert expense.date == date(2026, 3, 15)


def test_expense_create_rejects_non_positive_amount():
    with pytest.raises(ValidationError):
        ExpenseCreate(description="Free", amount=0, category="Food", date="2026-03-15")
    with pytest.raises(ValidationError):
        ExpenseCreate(description="Refund", amount=-5, category="Food", date="2026-03-15")


def test_expense_create_rejects_bad_date():
    with pytest.raises(ValidationError):
        ExpenseCreate(description="Lunch", amount=10, category="Food", date="not-a-date")


def test_expense_create_rejects_missing_fields():
    with pytest.raises(ValidationError):
        ExpenseCreate(description="Lunch")


def test_expense_inherits_create_fields():
    expense = Expense(
        id=7, description="Lunch", amount=12.5, category="Food", date=date(2026, 3, 15)
    )
    assert expense.id == 7
    assert isinstance(expense, ExpenseCreate)


def test_expense_summary_aggregates():
    expenses = [
        Expense(id=1, description="A", amount=10.0, category="Food", date=date(2026, 1, 1)),
        Expense(id=2, description="B", amount=5.5, category="Other", date=date(2026, 1, 2)),
    ]
    summary = ExpenseSummary(total=15.5, count=2, expenses=expenses)
    assert summary.total == 15.5
    assert summary.count == 2
