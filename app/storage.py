from typing import List, Optional

from models import Expense, ExpenseCreate

_expenses: List[Expense] = []
_next_id = 1


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
