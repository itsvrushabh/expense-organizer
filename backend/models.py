from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Currency Models
class CurrencyBase(BaseModel):
    code: str  # e.g., 'USD', 'INR', 'EUR', 'JPY', 'GBP', 'CNY'
    name: str  # e.g., 'US Dollar', 'Indian Rupee'
    symbol: str  # e.g., '$', '₹', '€', '¥', '£'
    exchange_rate: float = 1.0  # Rate relative to USD (base: 1.0)
    is_default: bool = False
    updated_at: Optional[datetime] = None


class Currency(CurrencyBase):
    pass


# Category Models
class CategoryBase(BaseModel):
    name: str
    icon: str = "help-circle"
    color: str = "#607D8B"
    is_active: bool = True


class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = "help-circle"
    color: Optional[str] = "#607D8B"


class Category(CategoryBase):
    id: int


# Expense Models
class ExpenseCreate(BaseModel):
    description: str
    amount: float = Field(..., gt=0)
    currency: Optional[str] = "USD"
    category: str
    date: date


class Expense(ExpenseCreate):
    id: int
    currency_symbol: str = "$"
    amount_usd: Optional[float] = None
    category_id: Optional[int] = None
    category_icon: Optional[str] = None
    category_color: Optional[str] = None


class ExpenseSummary(BaseModel):
    total: float
    count: int
    currency: str = "USD"
    currency_symbol: str = "$"
    expenses: List[Expense]

