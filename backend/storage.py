from models import Expense, ExpenseCreate

_expenses: list[Expense] = []
_next_id = 1


async def get_all() -> list[Expense]:
    return list(_expenses)


async def add(expense: ExpenseCreate) -> Expense:
    global _next_id
    new_expense = Expense(id=_next_id, **expense.model_dump())
    _expenses.append(new_expense)
    _next_id += 1
    return new_expense


async def delete(expense_id: int) -> Expense | None:
    for i, exp in enumerate(_expenses):
        if exp.id == expense_id:
            return _expenses.pop(i)
    return None


async def update(expense_id: int, expense: ExpenseCreate) -> Expense | None:
    for i, exp in enumerate(_expenses):
        if exp.id == expense_id:
            updated = Expense(id=expense_id, **expense.model_dump())
            _expenses[i] = updated
            return updated
    return None
