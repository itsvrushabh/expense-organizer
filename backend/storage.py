import os
import re
from datetime import date
from typing import List, Optional

from models import Expense, ExpenseCreate

_expenses: List[Expense] = []
_next_id = 1

_SEED_INSERT_RE = re.compile(
    r"VALUES\s*\(\s*(\d+)\s*,\s*'([^']*)'\s*,\s*([0-9.]+)\s*,\s*'([^']*)'\s*,\s*'(\d{4}-\d{2}-\d{2})'\s*\)"
)


def load_seed_data() -> int:
    """Load expenses from a SQL dump file (SEED_FILE env var) if storage is empty."""
    global _next_id
    if _expenses:
        return 0
    seed_file = os.environ.get("SEED_FILE")
    if not seed_file or not os.path.exists(seed_file):
        return 0
    loaded = 0
    with open(seed_file, "r", encoding="utf-8") as fh:
        for line in fh:
            match = _SEED_INSERT_RE.search(line)
            if not match:
                continue
            expense_id, description, amount, category, expense_date = match.groups()
            _expenses.append(
                Expense(
                    id=int(expense_id),
                    description=description,
                    amount=float(amount),
                    category=category,
                    date=date.fromisoformat(expense_date),
                )
            )
            loaded += 1
    _next_id = max((exp.id for exp in _expenses), default=0) + 1
    return loaded


async def get_all() -> List[Expense]:
    return list(_expenses)


async def add(expense: ExpenseCreate) -> Expense:
    global _next_id
    new_expense = Expense(id=_next_id, **expense.model_dump())
    _expenses.append(new_expense)
    _next_id += 1
    return new_expense


async def delete(expense_id: int) -> Optional[Expense]:
    for i, exp in enumerate(_expenses):
        if exp.id == expense_id:
            return _expenses.pop(i)
    return None
