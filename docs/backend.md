# Backend Architecture & API Guide ⚙️

The Expense Organizer backend is built with **FastAPI** (Python 3.11/3.13), providing high-performance asynchronous REST endpoints, strict Pydantic v2 data validation, CORS middleware, PostgreSQL persistence, and in-memory fallback.

---

## Directory Structure

```
backend/
├── main.py              # Application factory, lifespan, CORS, endpoint catalog
├── models.py            # Pydantic data models (ExpenseCreate, Expense, ExpenseSummary)
├── storage.py           # PostgreSQL storage engine (with in-memory fallback)
├── routers/
│   └── expenses.py      # REST CRUD & aggregation handlers
├── tests/               # 35 pytest unit & integration tests
│   ├── conftest.py      # Shared test fixtures & HTTP client
│   ├── test_api.py      # API endpoint tests (CRUD, filtering, date logic, health)
│   ├── test_main.py     # Root endpoint catalog test
│   ├── test_models.py   # Schema validation tests
│   └── test_storage.py  # Storage engine tests
├── Dockerfile           # Python Docker image (internal port 8000)
└── requirements.txt     # Production dependencies
```

---

## Data Models (`backend/models.py`)

### `ExpenseCreate`
Request payload for creating or updating an expense:
- `description` (`str`): Short description of the expense.
- `amount` (`float > 0`): Non-negative expense amount normalized to the base currency (USD).
- `category` (`str`): Category label (e.g. `Food`, `Transport`, `Loan`).
- `date` (`datetime.date`): Date of the expense in `YYYY-MM-DD` format.

### `Expense`
Extends `ExpenseCreate` with:
- `id` (`int`): Auto-incrementing unique identifier.

### `ExpenseSummary`
Aggregation response model:
- `total` (`float`): Rounded sum of all expense amounts in the aggregation (`round(..., 2)`).
- `count` (`int`): Total count of matching records.
- `expenses` (`list[Expense]`): List of matching expense records (optionally sorted by date).

---

## Endpoints

### 1. Root & Discovery
- `GET /`: Returns a JSON catalog of all available API endpoints and server status.
- `GET /health`: Health probe reporting service and database connection status (`"postgresql"` or `"in_memory"`).

### 2. Database Architecture (`backend/storage.py`)
- **PostgreSQL Container**: Running on internal container `expense-db` (port `5432` - zero host exposure).
- **Persistent Volume**: Database files are stored outside the container on the host at `./postgres_data`.
- **Relational Tables**:
  - `currency`: `(code PK, name, symbol, exchange_rate, is_default, updated_at)` supporting `USD`, `INR` (₹), `EUR` (€), `JPY` (¥), `GBP` (£), `CNY` (¥).
  - `category`: `(id PK, name, icon, color, is_active)` with case-insensitive unique index `idx_category_unique_lower_name` and soft-delete `is_active`.
  - `expenses`: `(id PK, description, amount, currency_code FK, category_id FK, date, created_at)` with expression indexes on `(year, month)` and `(iso_year, iso_week)`.
- **SQL Aggregated Views**:
  - `view_expenses_detailed`: Base view joining expenses with category names, icons, colors, currency symbols, and USD conversions.
  - `view_expense_summary_all`: Global all-time summary.
  - `view_expense_summary_daily`, `view_expense_summary_weekly`, `view_expense_summary_monthly`, `view_expense_summary_yearly`.
  - `view_expense_summary_category`: Grouped breakdown by category.
  - `view_expense_summary_monthly_category`: Monthly breakdown by category (e.g. February Online Expenses).
- **Parameterized SQL Function**:
  - `fn_expense_summary(p_year, p_month, p_iso_week, p_start_date, p_end_date, p_categories, p_currency)`: Fast in-engine multi-filter query supporting multi-category combinations and target currency denomination.
- **Dual-Engine Resilience**: If `DATABASE_URL` is omitted (e.g. running unit tests standalone), `storage.py` gracefully falls back to an in-memory dictionary/list store.

### 3. Currencies & Live Exchange Rates
- `GET /currencies`: Retrieve list of all supported currencies, symbols, and current exchange rates.
- `POST /currencies/refresh`: On-demand user trigger pulling live exchange rates from market feed (`open.er-api.com`) and updating PostgreSQL.
- **24-Hour Auto-Sync**: Background worker in `lifespan` automatically synchronizes live rates on startup and every 24 hours.

### 4. Categories CRUD
- `GET /categories`: Retrieve categories (`?active_only=true` default).
- `POST /categories`: Create new category with custom icon and color.
- `DELETE /categories/{id}`: Soft-delete category (`is_active = FALSE`).
- `PATCH /categories/{id}/activate`: Reactivate category (`is_active = TRUE`).

### 5. Expense CRUD & Summaries
- `POST /expenses`: Create a new expense (auto-resolves category name or ID, supports `currency` code).
- `GET /expenses`: Retrieve all recorded expenses summarized.
- `GET /expenses/summary`: Combined multi-filter endpoint utilizing `fn_expense_summary`:
  - `?year=2026&month=2&categories=Online`: Summary of February Online expenses.
  - `?categories=Online&categories=Shopping`: Multiple categories combined.
  - `?currency=INR`: Converts totals and returns symbol `₹`.
- `PUT /expenses/{id}`: Update an existing expense by ID. Returns 404 if not found.
- `DELETE /expenses/{id}`: Delete an expense by ID. Returns 404 if not found.

### 6. Date & Time Aggregations
- `GET /expenses/day/{date}`: Retrieve expenses for an exact date (`YYYY-MM-DD`).
- `GET /expenses/week/{year}/{week}`: Retrieve expenses for an ISO 8601 calendar week (`week`: 1–53, Monday to Sunday).
- `GET /expenses/week/date/{date}`: Retrieve expenses for the 7-day week containing `{date}` (`start_sunday: bool = False`).
- `GET /expenses/month/{year}/{month}`: Retrieve expenses for a specific month (`month`: 1–12), sorted by date.
- `GET /expenses/year/{year}`: Retrieve expenses for a specific calendar year, sorted by date.
- `GET /expenses/category/{category}`: Case-insensitive filter by category name.

---

## Utility Scripts

### Recurring Expense Seeder (`scripts/add_recurring_expenses.py`)
Generates recurring monthly entries (e.g., Home Loan EMI, Electric Bill, Internet Bill) with automated deduplication:
```bash
python3 scripts/add_recurring_expenses.py [API_URL]
# Defaults to http://localhost:13000/api (or http://localhost:8000 when running standalone backend)
```
- Deduplicates using `(description, date)` tuples.
- Normalizes currency amounts from INR to base USD (using conversion rate 84).

---

## Running Backend

### Inside Docker (Zero Host Exposure)
When running via `docker-compose up`, the `backend` service runs on internal port `8000` with **no exposed host port**.
- All external traffic routes through the frontend proxy at `http://localhost:13000/api`
- Interactive OpenAPI docs: `http://localhost:13000/api/docs`

### Standalone Local Development
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

uvicorn main:app --reload --port 8000
```

When running standalone without Docker:
- Direct API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Running Tests

The test suite contains 35 pytest unit & integration tests covering model validation, date math, week calculation, floating-point precision, and storage mutation:

```bash
pytest backend/tests -v
```
