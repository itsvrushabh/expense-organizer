import logging
from typing import Optional
import httpx

from app.config import EXPENSE_API_URL
from app.schemas import ExpenseDraft

logger = logging.getLogger(__name__)


async def insert_expense_to_db(draft: ExpenseDraft) -> Optional[int]:
    """
    Sends POST /expenses to the core expense backend to persist the confirmed expense.
    Returns the new expense ID if successful, or raises an Exception.
    """
    url = f"{EXPENSE_API_URL}/expenses"
    payload = {
        "description": draft.description,
        "amount": round(draft.amount, 2),
        "category": draft.category,
        "date": draft.date,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            expense_id = data.get("id")
            logger.info("Successfully persisted expense to core DB with ID %s", expense_id)
            return expense_id
        except httpx.HTTPError as err:
            logger.error("Failed to persist expense via %s: %s", url, err)
            raise RuntimeError(f"Could not connect to core backend at {url}: {err}") from err
