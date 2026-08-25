from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException, Path

import storage
from models import Expense, ExpenseCreate, ExpenseSummary

router = APIRouter(prefix="/expenses", tags=["expenses"])


def summarize(expenses: List[Expense], *, sort: bool = False) -> ExpenseSummary:
    if sort:
        expenses = sorted(expenses, key=lambda x: x.date)
    return ExpenseSummary(
        total=sum(exp.amount for exp in expenses),
        count=len(expenses),
        expenses=expenses,
    )


@router.post("", response_model=Expense)
async def create_expense(expense: ExpenseCreate):
    """Create a new expense"""
    return await storage.add(expense)


@router.get("", response_model=ExpenseSummary)
async def get_expenses():
    """Get all expenses"""
    return summarize(await storage.get_all())


@router.get("/day/{target_date}", response_model=ExpenseSummary)
async def get_day_expenses(target_date: date):
    """Get expenses for a specific day"""
    expenses = await storage.get_all()
    return summarize([exp for exp in expenses if exp.date == target_date])


@router.get("/month/{year}/{month}", response_model=ExpenseSummary)
async def get_month_expenses(
    year: int,
    month: int = Path(..., ge=1, le=12, description="Month must be between 1 and 12"),
):
    """Get expenses for a specific month"""
    expenses = await storage.get_all()
    return summarize(
        [exp for exp in expenses if exp.date.year == year and exp.date.month == month],
        sort=True,
    )


@router.get("/year/{year}", response_model=ExpenseSummary)
async def get_year_expenses(year: int):
    """Get expenses for a specific year"""
    expenses = await storage.get_all()
    return summarize(
        [exp for exp in expenses if exp.date.year == year],
        sort=True,
    )


@router.get("/category/{category}", response_model=ExpenseSummary)
async def get_expenses_by_category(category: str):
    """Get all expenses for a specific category"""
    expenses = await storage.get_all()
    return summarize(
        [exp for exp in expenses if exp.category.lower() == category.lower()]
    )


@router.put("/{expense_id}", response_model=Expense)
async def update_expense(expense_id: int, expense: ExpenseCreate):
    """Update an existing expense by ID"""
    updated = await storage.update(expense_id, expense)
    if updated is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return updated


@router.delete("/{expense_id}")
async def delete_expense(expense_id: int):
    """Delete an expense by ID"""
    deleted = await storage.delete(expense_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": f"Expense {expense_id} deleted", "expense": deleted}
