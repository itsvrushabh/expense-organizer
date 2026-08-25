"""Add recurring expense entries to the Expense Organizer API.

Usage:
    python3 scripts/add_recurring_expenses.py [API_URL]

Defaults to http://localhost:8000. Amounts are entered in INR and
normalized to the app's base currency (INR rate 84).
"""

import json
import sys
import urllib.request
from datetime import date

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
INR_RATE = 84
TODAY = date.today()


def months(start: date):
    year, month = start.year, start.month
    while True:
        yield date(year, month, start.day)
        month += 1
        if month > 12:
            month = 1
            year += 1


def post(description: str, amount_inr: float, category: str, day_date: date) -> None:
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
    with urllib.request.urlopen(req) as res:
        assert res.status == 200, f"Unexpected status {res.status}"


def main() -> None:
    counts = {"Home Loan EMI": 0, "Electric Bill": 0, "Internet Bill": 0}

    for d in months(date(2025, 1, 7)):
        if d > date(2055, 1, 7):
            break
        post("Home Loan EMI", 25000, "Loan", d)
        counts["Home Loan EMI"] += 1

    for d in months(date(2025, 1, 15)):
        if d > TODAY:
            break
        post("Electric Bill", 2000, "Electricity", d)
        counts["Electric Bill"] += 1

    for d in months(date(2025, 1, 24)):
        if d > TODAY:
            break
        post("Internet Bill", 2000, "Internet", d)
        counts["Internet Bill"] += 1

    for name, count in counts.items():
        print(f"{name}: {count} entries")


if __name__ == "__main__":
    main()
