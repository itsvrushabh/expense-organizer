"""Add recurring expense entries to the Expense Organizer API.

Usage:
    python3 scripts/add_recurring_expenses.py [API_URL]

Defaults to http://localhost:13000/api. Amounts are entered in INR and
normalized to the app's base currency (INR rate 84). Idempotent by
description + date; skips duplicates.
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:13000/api"
INR_RATE = 84
TODAY = date.today()


def months(start: date):
    year, month = start.year, start.month
    while True:
        # Determine max day for this month
        if month == 12:
            next_first = date(year + 1, 1, 1)
        else:
            next_first = date(year, month + 1, 1)
        max_day = (next_first - timedelta(days=1)).day
        day = min(start.day, max_day)
        yield date(year, month, day)
        month += 1
        if month > 12:
            month = 1
            year += 1


def get_existing() -> set:
    """Fetch current expenses and return (description, date) pairs."""
    try:
        with urllib.request.urlopen(f"{API_URL}/expenses") as res:
            if res.status != 200:
                return set()
            data = json.load(res)
            expenses = data.get("expenses") or []
            return {(e.get("description"), e.get("date")) for e in expenses}
    except Exception:
        return set()


def post(description: str, amount_inr: float, category: str, day_date: date) -> bool:
    payload = {
        "description": description,
        "amount": round(amount_inr / INR_RATE, 2),
        "category": category,
        "date": day_date.isoformat(),
    }
    req = urllib.request.Request(
        f"{API_URL}/expenses",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            if res.status == 200:
                return True
            else:
                print(f"Unexpected status {res.status} posting {description} on {day_date}")
                return False
    except urllib.error.HTTPError as e:
        # If already exists (e.g., backend dedup), ignore; else warn
        print(f"HTTP error {e.code} posting {description} on {day_date}")
        return False
    except Exception as e:
        print(f"Error posting {description} on {day_date}: {e}")
        return False


def main() -> None:
    existing = get_existing()
    counts = {"Home Loan EMI": 0, "Electric Bill": 0, "Internet Bill": 0}

    # Home Loan EMI: 360 payments (2025-01-07 through 2054-12-07), inclusive start, exclusive end
    # Use 30-year span = 360 months
    for d in months(date(2025, 1, 7)):
        if d > date(2054, 12, 7):
            break
        if ("Home Loan EMI", d.isoformat()) not in existing:
            if post("Home Loan EMI", 25000, "Loan", d):
                counts["Home Loan EMI"] += 1
        else:
            counts["Home Loan EMI"] += 1  # already exists

    for d in months(date(2025, 1, 15)):
        if d > TODAY:
            break
        if ("Electric Bill", d.isoformat()) not in existing:
            if post("Electric Bill", 2000, "Electricity", d):
                counts["Electric Bill"] += 1
        else:
            counts["Electric Bill"] += 1

    for d in months(date(2025, 1, 24)):
        if d > TODAY:
            break
        if ("Internet Bill", d.isoformat()) not in existing:
            if post("Internet Bill", 2000, "Internet", d):
                counts["Internet Bill"] += 1
        else:
            counts["Internet Bill"] += 1

    for name, count in counts.items():
        print(f"{name}: {count} entries (total after run: includes existing)")


if __name__ == "__main__":
    main()
