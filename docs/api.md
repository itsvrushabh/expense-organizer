# REST API Reference 📚

All amounts are stored as non-negative floats in base USD and rounded to 2 decimal places. Dates use the ISO `YYYY-MM-DD` standard.

---

## Endpoint Summary

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | API discovery catalog & service health |
| `POST` | `/expenses` | Create a new expense |
| `GET` | `/expenses` | Retrieve all expenses |
| `PUT` | `/expenses/{id}` | Update an existing expense by ID |
| `DELETE` | `/expenses/{id}` | Delete an expense by ID |
| `GET` | `/expenses/day/{date}` | Daily expenses (`YYYY-MM-DD`) |
| `GET` | `/expenses/week/{year}/{week}` | ISO 8601 week expenses (`week`: 1–53) |
| `GET` | `/expenses/week/date/{date}` | 7-day week for date (`?start_sunday=true` for Sun–Sat) |
| `GET` | `/expenses/month/{year}/{month}` | Monthly expenses (`month`: 1–12) |
| `GET` | `/expenses/year/{year}` | Annual expenses |
| `GET` | `/expenses/category/{category}` | Filter by category name |

---

## Schemas

### `ExpenseCreate`
```json
{
  "description": "Grocery shopping",
  "amount": 125.50,
  "category": "Food",
  "date": "2026-09-07"
}
```

### `Expense`
```json
{
  "id": 1,
  "description": "Grocery shopping",
  "amount": 125.50,
  "category": "Food",
  "date": "2026-09-07"
}
```

### `ExpenseSummary`
```json
{
  "total": 125.50,
  "count": 1,
  "expenses": [
    {
      "id": 1,
      "description": "Grocery shopping",
      "amount": 125.50,
      "category": "Food",
      "date": "2026-09-07"
    }
  ]
}
```

---

## Curl Examples

> [!TIP]
> In Docker, the API is proxied through the frontend reverse proxy at `http://localhost:13000/api`. If you are running the backend standalone locally without Docker, use `http://localhost:8000`.

### Create an Expense
```bash
curl -X POST "http://localhost:13000/api/expenses" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Internet Bill",
    "amount": 50.00,
    "category": "Utilities",
    "date": "2026-09-07"
  }'
```

### Query Week by Date (Sunday–Saturday view)
```bash
curl "http://localhost:13000/api/expenses/week/date/2026-09-07?start_sunday=true"
```

### Query Month
```bash
curl "http://localhost:13000/api/expenses/month/2026/9"
```

### Delete an Expense
```bash
curl -X DELETE "http://localhost:13000/api/expenses/1"
```
