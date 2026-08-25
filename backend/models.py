from datetime import date

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    description: str
    amount: float = Field(..., gt=0)
    category: str
    date: date


class Expense(ExpenseCreate):
    id: int


class ExpenseSummary(BaseModel):
    total: float
    count: int
    expenses: list[Expense]
