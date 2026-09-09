import logging
from typing import List

import storage
from fastapi import APIRouter, HTTPException, Query
from models import Category, CategoryCreate

logger = logging.getLogger("expense_backend.routers.categories")

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=List[Category])
async def list_categories(
    active_only: bool = Query(True, description="Filter only active categories"),
):
    """List categories (defaults to active only)."""
    return await storage.get_categories(active_only=active_only)


@router.post("", response_model=Category)
async def create_category(category: CategoryCreate):
    """Create a new custom category."""
    try:
        return await storage.create_category(category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}")
async def delete_category(category_id: int):
    """Soft-delete a category (sets is_active to FALSE)."""
    success = await storage.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deactivated", "category_id": category_id}


@router.patch("/{category_id}/activate")
async def activate_category(category_id: int):
    """Reactivate a soft-deleted category (sets is_active to TRUE)."""
    success = await storage.activate_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category activated", "category_id": category_id}
