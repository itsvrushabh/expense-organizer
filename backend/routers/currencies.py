import logging
from typing import List
from fastapi import APIRouter

import storage
from models import Currency
from services import currency_service

logger = logging.getLogger("expense_backend.routers.currencies")

router = APIRouter(prefix="/currencies", tags=["currencies"])


@router.get("", response_model=List[Currency])
async def list_currencies():
    """List all available currencies with symbols and current exchange rates."""
    return await storage.get_currencies()


@router.post("/refresh", response_model=List[Currency])
async def refresh_currency_rates():
    """
    On-demand user trigger to fetch latest live exchange rates
    from the open market feed and update the database.
    """
    logger.info("User triggered live currency exchange rate refresh")
    return await currency_service.sync_currency_rates(force=True)
