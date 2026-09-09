import asyncio
import logging
from typing import Dict, List, Optional
import httpx

import storage
from models import Currency

logger = logging.getLogger("expense_backend.currency_service")

EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/USD"
REQUEST_TIMEOUT_SECONDS = 4.0
DAILY_SYNC_INTERVAL_SECONDS = 86400  # 24 hours


async def fetch_live_rates() -> Dict[str, float]:
    """
    Fetches real-time currency exchange rates relative to USD from the open exchange API.
    Returns a dictionary of uppercase currency codes to rates, or an empty dict on error.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.get(
                EXCHANGE_API_URL,
                headers={"User-Agent": "ExpenseOrganizer/1.0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("result") == "success" and "rates" in data:
                    rates = {k.upper(): float(v) for k, v in data["rates"].items()}
                    logger.info("Successfully fetched %d live currency exchange rates", len(rates))
                    return rates
                else:
                    logger.warning("Exchange rate API returned unexpected payload: %s", data.get("result"))
            else:
                logger.warning("Exchange rate API HTTP error %s: %s", resp.status_code, resp.text[:100])
    except Exception as e:
        logger.warning("Failed to fetch live exchange rates (offline or timeout): %s", e)

    return {}


async def sync_currency_rates(force: bool = False) -> List[Currency]:
    """
    Syncs live currency rates into the database.
    If offline or API fails, returns existing rates without raising an exception.
    """
    rates = await fetch_live_rates()
    if rates:
        updated = await storage.update_currency_rates(rates)
        logger.info("Updated %d currency rates in storage", len(updated))
        return updated
    logger.info("Retaining existing currency rates (no live update available)")
    return await storage.get_currencies()


async def start_currency_sync_worker():
    """
    Background worker that performs an initial sync on startup,
    then automatically runs every 24 hours.
    """
    logger.info("Starting background currency auto-sync worker (24h schedule)...")
    try:
        # Give DB connection pool a moment to finish initialization
        await asyncio.sleep(2.0)
        await sync_currency_rates()

        while True:
            await asyncio.sleep(DAILY_SYNC_INTERVAL_SECONDS)
            logger.info("Executing scheduled 24h currency rate update...")
            await sync_currency_rates()
    except asyncio.CancelledError:
        logger.info("Currency auto-sync background worker cancelled.")
        raise
    except Exception as e:
        logger.error("Unexpected error in currency sync worker: %s", e)
