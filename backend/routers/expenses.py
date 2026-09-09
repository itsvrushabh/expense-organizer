from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query

import storage
from models import Expense, ExpenseCreate, ExpenseSummary

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=Expense)
async def create_expense(expense: ExpenseCreate):
    """Create a new expense with category auto-resolution and currency support."""
    return await storage.add(expense)


@router.get("", response_model=ExpenseSummary)
async def get_expenses():
    """Get all expenses summarized."""
    return await storage.get_summary()


@router.get("/summary", response_model=ExpenseSummary)
async def get_combined_summary(
    year: Optional[int] = Query(None, description="Filter by calendar year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (1-12)"),
    week: Optional[int] = Query(None, ge=1, le=53, description="Filter by ISO week (1-53)"),
    start_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date (inclusive)"),
    categories: Optional[List[str]] = Query(None, description="List of categories to filter (e.g. Online, Shopping)"),
    currency: Optional[str] = Query("USD", description="Target currency code (e.g. USD, INR, EUR, JPY)"),
):
    """
    Combined high-performance ExpenseSummary using SQL views and fn_expense_summary.
    Allows filtering by single or multiple categories and custom dates/months with currency conversion.
    """
    return await storage.get_summary(
        year=year,
        month=month,
        week=week,
        start_date=start_date,
        end_date=end_date,
        categories=categories,
        currency=currency or "USD",
    )


@router.get("/day/{target_date}", response_model=ExpenseSummary)
async def get_day_expenses(target_date: date):
    """Get expenses for a specific day."""
    return await storage.get_summary(start_date=target_date, end_date=target_date)


@router.get("/week/date/{target_date}", response_model=ExpenseSummary)
async def get_week_by_date_expenses(target_date: date, start_sunday: bool = False):
    """
    Get expenses for the 7-day week containing target_date.
    Defaults to Monday to Sunday (ISO). If start_sunday=True, computes Sunday to Saturday.
    """
    if start_sunday:
        start_of_week = target_date - timedelta(days=(target_date.weekday() + 1) % 7)
    else:
        start_of_week = target_date - timedelta(days=target_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return await storage.get_summary(start_date=start_of_week, end_date=end_of_week)


@router.get("/week/{year}/{week}", response_model=ExpenseSummary)
async def get_week_expenses(
    year: int,
    week: int = Path(..., ge=1, le=53, description="ISO week must be between 1 and 53"),
):
    """Get expenses for a specific ISO week."""
    return await storage.get_summary(year=year, week=week)


@router.get("/month/{year}/{month}", response_model=ExpenseSummary)
async def get_month_expenses(
    year: int,
    month: int = Path(..., ge=1, le=12, description="Month must be between 1 and 12"),
):
    """Get expenses for a specific month."""
    return await storage.get_summary(year=year, month=month)


@router.get("/year/{year}", response_model=ExpenseSummary)
async def get_year_expenses(year: int):
    """Get expenses for a specific year."""
    return await storage.get_summary(year=year)


@router.get("/category/{category}", response_model=ExpenseSummary)
async def get_expenses_by_category(category: str):
    """Get all expenses for a specific category."""
    return await storage.get_summary(categories=[category])


@router.put("/{expense_id}", response_model=Expense)
async def update_expense(expense_id: int, expense: ExpenseCreate):
    """Update an existing expense by ID."""
    updated = await storage.update(expense_id, expense)
    if updated is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return updated


@router.delete("/{expense_id}")
async def delete_expense(expense_id: int):
    """Delete an expense by ID."""
    deleted = await storage.delete(expense_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": f"Expense {expense_id} deleted", "expense": deleted}
