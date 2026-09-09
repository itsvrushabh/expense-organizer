from datetime import date, timedelta

import storage
from fastapi import APIRouter, HTTPException, Path
from models import Expense, ExpenseCreate, ExpenseSummary

router = APIRouter(prefix="/expenses", tags=["expenses"])


def summarize(expenses: list[Expense], *, sort: bool = False) -> ExpenseSummary:
    if sort:
        expenses = sorted(expenses, key=lambda x: x.date)
    return ExpenseSummary(
        total=round(sum(exp.amount for exp in expenses), 2),
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


@router.get("/week/date/{target_date}", response_model=ExpenseSummary)
async def get_week_by_date_expenses(target_date: date, start_sunday: bool = False):
    """Get expenses for the 7-day week containing target_date.
    Defaults to Monday to Sunday (ISO). If start_sunday=True, computes Sunday to Saturday.
    """
    if start_sunday:
        start_of_week = target_date - timedelta(days=(target_date.weekday() + 1) % 7)
    else:
        start_of_week = target_date - timedelta(days=target_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    expenses = await storage.get_all()
    return summarize(
        [exp for exp in expenses if start_of_week <= exp.date <= end_of_week],
        sort=True,
    )


@router.get("/week/{year}/{week}", response_model=ExpenseSummary)
async def get_week_expenses(
    year: int,
    week: int = Path(..., ge=1, le=53, description="ISO week must be between 1 and 53"),
):
    """Get expenses for a specific ISO week"""
    expenses = await storage.get_all()
    return summarize(
        [
            exp
            for exp in expenses
            if exp.date.isocalendar().year == year and exp.date.isocalendar().week == week
        ],
        sort=True,
    )


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
    return summarize([exp for exp in expenses if exp.category.lower() == category.lower()])


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
