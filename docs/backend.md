# Backend Architecture & API Guide ⚙️

The Expense Organizer backend is built with **FastAPI** (Python 3.11/3.13), providing high-performance asynchronous REST endpoints, strict Pydantic v2 data validation, CORS middleware, and in-memory transactional storage.

---

## Directory Structure

```
backend/
├── main.py              # Application factory, CORS, endpoint catalog
├── models.py            # Pydantic data models (ExpenseCreate, Expense, ExpenseSummary)
├── storage.py           # In-memory storage engine
├── routers/
│   └── expenses.py      # REST CRUD & aggregation handlers
├── tests/               # 34 pytest unit & integration tests
│   ├── conftest.py      # Shared test fixtures & HTTP client
│   ├── test_api.py      # API endpoint tests (CRUD, filtering, date logic)
│   ├── test_main.py     # Root endpoint catalog test
│   ├── test_models.py   # Schema validation tests
│   └── test_storage.py  # Storage engine tests
├── Dockerfile           # Python Docker image
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

### 2. Expense CRUD
- `POST /expenses`: Create a new expense.
- `GET /expenses`: Retrieve all recorded expenses.
- `PUT /expenses/{id}`: Update an existing expense by ID. Returns 404 if not found.
- `DELETE /expenses/{id}`: Delete an expense by ID. Returns 404 if not found.

### 3. Date & Time Aggregations
- `GET /expenses/day/{date}`: Retrieve expenses for an exact date (`YYYY-MM-DD`).
- `GET /expenses/week/{year}/{week}`: Retrieve expenses for an ISO 8601 calendar week (`week`: 1–53, Monday to Sunday).
- `GET /expenses/week/date/{date}`: Retrieve expenses for the 7-day week containing `{date}`.
  - **Query Parameter**: `start_sunday: bool = False`
  - When `start_sunday=false` (default): 7-day Monday–Sunday window.
  - When `start_sunday=true`: 7-day Sunday–Saturday window matching calendar and spreadsheet views.
- `GET /expenses/month/{year}/{month}`: Retrieve expenses for a specific month (`month`: 1–12), sorted by date.
- `GET /expenses/year/{year}`: Retrieve expenses for a specific calendar year, sorted by date.
- `GET /expenses/category/{category}`: Case-insensitive filter by category name.

---

## Utility Scripts

### Recurring Expense Seeder (`scripts/add_recurring_expenses.py`)
Generates recurring monthly entries (e.g., Home Loan EMI, Electric Bill, Internet Bill) with automated deduplication:
```bash
python3 scripts/add_recurring_expenses.py [API_URL]
# Defaults to http://localhost:8000
```
- Deduplicates using `(description, date)` tuples.
- Normalizes currency amounts from INR to base USD (using conversion rate 84).

---

---

## AI Function Calling & Tool Use Engine (`backend/ai/`)

The backend embeds an agentic LLM tool-calling engine powered by `llama-cpp-python` with **GPU CUDA Offloading** (`n_gpu_layers = -1`) targeting NVIDIA GPUs (e.g. GeForce GTX 1650 Ti).

### Registered Tools
- `draft_expense(description, amount, category, date)`: Parses message into an expense draft.
- `update_draft_field(field, value)`: Updates `amount`, `category`, `date`, or `description` in the pending draft.
- `commit_expense(description, amount, category, date)`: Directly inserts the confirmed expense into `storage.add()`.
- `ask_clarification(missing_field, question)`: Prompts user when information (e.g. amount) is missing.
- `cancel_draft()`: Discards the active draft.

### Endpoints
- `POST /api/ai/chat` (alias `/api/chat/message`): Send message and trigger LLM tool selection and execution.
- `POST /api/ai/confirm` (alias `/api/chat/confirm`): Confirm and persist active draft directly to storage.
- `POST /api/ai/cancel` (alias `/api/chat/cancel`): Discard active draft.
- `GET /api/ai/health`: Model status, GPU offload device info, and registered tools catalog.

---

## Running Backend Locally

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

uvicorn main:app --reload --port 8000
```

Interactive OpenAPI documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Running Tests

The test suite contains 43 pytest unit & integration tests covering model validation, date math, week calculation, floating-point precision, and AI tool calling:

```bash
pytest backend/tests -v
```
