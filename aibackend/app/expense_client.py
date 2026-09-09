import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import httpx

from app.config import EXPENSE_API_URL
from app.schemas import ExpenseDraft

logger = logging.getLogger("aibackend.expense_client")


def normalize_iso_date(date_str: str, ref_date: Optional[datetime] = None) -> str:
    """
    Normalizes any date string (including 'today', 'yesterday', 'tomorrow', '2026-09-09')
    into a valid ISO 8601 YYYY-MM-DD string that the core backend expects.
    """
    now = ref_date or datetime.now()
    cleaned = (date_str or "").strip().lower()

    if not cleaned or cleaned in ["today", "now"]:
        return now.strftime("%Y-%m-%d")
    if cleaned == "yesterday":
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    if cleaned == "tomorrow":
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")

    iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", cleaned)
    if iso_match:
        return iso_match.group(1)

    try:
        dt = datetime.fromisoformat(cleaned)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return now.strftime("%Y-%m-%d")


async def insert_expense_to_db(draft: ExpenseDraft) -> Optional[int]:
    """
    Sends HTTP POST request to the core FastAPI backend to persist the expense.
    """
    url = f"{EXPENSE_API_URL}/expenses"
    normalized_date = normalize_iso_date(draft.date)
    payload = {
        "description": draft.description,
        "amount": draft.amount,
        "category": draft.category,
        "date": normalized_date,
    }
    logger.info("Persisting expense to core backend at %s: %s", url, payload)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code in [200, 201]:
                data = resp.json()
                expense_id = data.get("id")
                logger.info("Successfully created expense ID #%s in core backend", expense_id)
                return expense_id
            else:
                logger.error("Failed to persist expense: status %s, response %s", resp.status_code, resp.text)
                return None
    except Exception as e:
        logger.error("Exception occurred while calling core backend: %s", e)
        return None


async def check_backend_health() -> Dict[str, Any]:
    """
    Checks if the core FastAPI backend is reachable.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{EXPENSE_API_URL}/")
            if resp.status_code == 200:
                return {"status": "reachable", "details": resp.json()}
            return {"status": "unreachable", "status_code": resp.status_code}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}


async def refresh_exchange_rates_in_backend() -> Optional[list[dict]]:
    """
    Calls backend POST /currencies/refresh to fetch live exchange rates.
    """
    url = f"{EXPENSE_API_URL}/currencies/refresh"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url)
            if resp.status_code in [200, 201]:
                return resp.json()
            logger.error("Failed to refresh currencies in backend: status %s, body %s", resp.status_code, resp.text)
            return None
    except Exception as e:
        logger.error("Error refreshing currency rates via backend: %s", e)
        return None


async def get_currencies_from_backend() -> Optional[list[dict]]:
    """
    Calls backend GET /currencies.
    """
    url = f"{EXPENSE_API_URL}/currencies"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
            return None
    except Exception as e:
        logger.error("Error fetching currencies from backend: %s", e)
        return None
