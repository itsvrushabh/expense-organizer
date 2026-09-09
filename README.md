# Expense Organizer 💰📊

A modern, full-stack expense tracking platform designed for desktop, web, and mobile environments. It features Excel-style spreadsheet pivot tables, spend heatmap grids, real-time multi-currency conversion, and an offline-first persistent queue engine powered by Rust.

---

## Documentation Index 📖

All in-depth component and setup documentation is organized in the [`docs/`](docs/) directory:

- 🚀 **[Setup & Deployment Guide](docs/setup.md)**: Docker Compose, local manual startup, environment variables, and troubleshooting.
- ⚙️ **[Backend Guide](docs/backend.md)**: FastAPI architecture, async routers, Pydantic v2 schemas, in-memory store, and 34 pytest tests.
- 💻 **[Web Frontend Guide](docs/frontend.md)**: Bun + React 19 + TypeScript, Excel pivot table views, spend heatmaps, and `/api` proxy.
- 📱 **[Mobile App & Rust Engine Guide](docs/mobile.md)**: Flutter client, Material 3 gradient UI, C-FFI Rust sync engine, offline queue, and build guides.
- 📚 **[REST API Reference](docs/api.md)**: Complete endpoint catalog, query parameters, JSON schemas, and curl examples.

---

## System Overview

```
                      ┌─────────────────────────────────────────┐
                      │        Expense Organizer System         │
                      └────────────────────┬────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│  FastAPI Backend │             │  React 19 / Bun  │             │  Flutter Mobile  │
│  (backend/)      │             │  (frontend/)     │             │  (mobile/)       │
│                  │             │                  │             │                  │
│ • Async REST API │◄────────────┤ • Excel Pivot    │◄────────────┤ • Web UI Parity  │
│ • Day/Week/Month │  /api Proxy │ • 6x6 Heatmap    │   REST HTTP │ • Rust FFI Queue │
│ • Multi-Currency │             │ • Multi-Currency │             │ • Offline First  │
└──────────────────┘             └──────────────────┘             └──────────────────┘
```

---

## Quick Start with Docker 🐳

The easiest way to run the entire stack (FastAPI backend + Bun React frontend) with a single command:

```bash
# Using the startup script
./start.sh

# Or directly with Docker Compose
docker-compose up --build
```

To run in the background (detached):
```bash
docker-compose up -d --build
```

### Access Points
- 🌐 **Web Frontend**: [http://localhost:3000](http://localhost:3000)
- 🔧 **Backend API**: [http://localhost:8000](http://localhost:8000)
- 📚 **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Local Development (Quick Reference)

### 1. Backend (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

### 2. Web Frontend (Bun + React)
```bash
cd frontend
bun install
bun run dev
```

### 3. Mobile App (Flutter + Rust)
```bash
cd mobile
flutter run
```

---

## Automated Test Suites 🧪

Run automated verification across all layers:

```bash
# 1. Backend pytest suite (34 tests)
pytest backend/tests

# 2. Rust native sync engine tests (3 tests)
cd mobile/rust && cargo test

# 3. Flutter mobile tests & analysis (7 tests)
cd mobile
flutter analyze
flutter test

# 4. Web frontend TypeScript type check
cd frontend
bun x tsc --noEmit
```

---

## API Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API catalog & server status |
| `POST` | `/expenses` | Create a new expense |
| `GET` | `/expenses` | Retrieve all expenses |
| `PUT` | `/expenses/{id}` | Update an existing expense by ID |
| `DELETE` | `/expenses/{id}` | Delete an expense by ID |
| `GET` | `/expenses/day/{date}` | Daily expenses (`YYYY-MM-DD`) |
| `GET` | `/expenses/week/{year}/{week}` | ISO 8601 week expenses (`week: 1-53`) |
| `GET` | `/expenses/week/date/{date}` | 7-day week for date (`?start_sunday=true` for Sun–Sat) |
| `GET` | `/expenses/month/{year}/{month}` | Monthly expenses (`month: 1-12`) |
| `GET` | `/expenses/year/{year}` | Annual expenses |
| `GET` | `/expenses/category/{category}` | Filter by category name |

*For complete payload and response schemas, see [REST API Reference](docs/api.md).*

---

## Utility Scripts

### Recurring Expense Seeder
Seed recurring expenses (e.g. Home Loan EMI, Electric Bill, Internet Bill) with automated deduplication:
```bash
python3 scripts/add_recurring_expenses.py [API_URL]
# Defaults to http://localhost:8000
```

---

## Project Structure

```
expense-organizer/
├── docs/                         # Global documentation folder
│   ├── api.md                    # Detailed REST API reference & examples
│   ├── backend.md                # FastAPI architecture & storage docs
│   ├── frontend.md               # Bun + React 19 web application docs
│   ├── mobile.md                 # Flutter mobile & Rust engine docs
│   └── setup.md                  # Deployment & setup walkthrough
├── .github/
│   └── workflows/build-mobile.yml # CI/CD for Android & iOS builds
├── backend/
│   ├── main.py                   # App factory, CORS, endpoint catalog
│   ├── models.py                 # Pydantic schemas (Expense, ExpenseSummary)
│   ├── storage.py                # In-memory data store
│   ├── routers/expenses.py       # REST route handlers & aggregations
│   ├── tests/                    # 34 pytest unit & integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.ts                  # Bun HTTP server & /api reverse proxy
│   ├── src/                      # React 19 TypeScript application
│   ├── package.json
│   └── Dockerfile
├── mobile/
│   ├── lib/                      # Flutter client matching Web UI
│   ├── rust/                     # Native C-FFI offline queue engine
│   ├── test/                     # Flutter test suite
│   └── android/ ios/ linux/      # Native platform runners
├── scripts/
│   └── add_recurring_expenses.py # Seeding script for recurring expenses
├── docker-compose.yml
├── start.sh
└── README.md                     # Global project README
```

---

## License

MIT
