# Expense Organizer 💰📊

A modern, full-stack expense tracking platform designed for desktop, web, and mobile environments. It features Excel-style spreadsheet pivot tables, spend heatmap grids, real-time multi-currency conversion, and an offline-first persistent queue engine powered by Rust.

---

## Documentation Index 📖

All in-depth component and setup documentation is organized in the [`docs/`](docs/) directory:

- 🚀 **[Setup & Deployment Guide](docs/setup.md)**: Docker Compose, local manual startup, environment variables, and troubleshooting.
- 📦 **[GitHub CI and Release Status](docs/release.md)**: Main-branch, current-branch, workflow, version, and release status.
- ⚙️ **[Backend Guide](docs/backend.md)**: FastAPI architecture, async routers, Pydantic v2 schemas, in-memory store, and 34 pytest tests.
- 💻 **[Web Frontend Guide](docs/frontend.md)**: Bun + React 19 + TypeScript, Excel pivot table views, spend heatmaps, and `/api` proxy.
- 📱 **[Mobile App & Rust Engine Guide](docs/mobile.md)**: Flutter client, Material 3 gradient UI, C-FFI Rust sync engine, offline queue, and build guides.
- 📚 **[REST API Reference](docs/api.md)**: Complete endpoint catalog, query parameters, JSON schemas, and curl examples.
- 🧠 **[AI Backend Orchestrator Guide](docs/aibackend.md)**: Agentic function calling / tool dispatcher, session state machine, and DB ingestion (port 18001).
- 🤖 **[AI Model Server Guide](docs/aimodel.md)**: Dedicated GPU-accelerated GGUF LLM inference microservice (internal port 8002).
- 💬 **[Expense Helper Mobile Guide](docs/expense-helper-mobile.md)**: Multiplatform Flutter chat client (Android & iOS) with interactive draft cards.
- 🖥️ **[Desktop Helper Roadmap (On Hold)](docs/expense-helper-desktop.md)**: Architecture and specification for planned Rust `iced` desktop client (Linux & Windows).

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
- 🌐 **Web Frontend**: [http://localhost:13000](http://localhost:13000)
- 🔧 **API Proxy (via Frontend)**: [http://localhost:13000/api](http://localhost:13000/api)
- 📚 **Swagger API Docs**: [http://localhost:13000/api/docs](http://localhost:13000/api/docs)
- 🧠 **AI Backend Orchestrator**: [http://localhost:18001](http://localhost:18001)
- 🩺 **AI Health Status**: [http://localhost:18001/health](http://localhost:18001/health)

> [!NOTE]
> **Zero Unnecessary Port Exposure**: Both `backend` (internal port `8000`) and `aimodel` (internal port `8002`) run strictly on the internal Docker network with **no host port bindings**. All client API requests route through the Bun reverse proxy at `http://localhost:13000/api` or communicate with the AI assistant on port `18001`.

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

# 2. AI Backend orchestrator pytest suite (8 tests)
pytest aibackend/tests

# 3. AI Model server pytest suite (4 tests)
pytest aimodel/tests

# 4. Rust native sync engine tests (3 tests)
cd mobile/rust && cargo test

# 5. Flutter mobile tests & analysis (7 tests)
cd mobile
flutter analyze
flutter test

# 6. Expense Helper chat app tests & analysis (3 tests)
cd expense-helper/mobile
flutter analyze
flutter test

# 7. Web frontend TypeScript type check
cd frontend
bun x tsc --noEmit
```

## GitHub Workflow and Release Status

The complete status dashboard is maintained separately in [docs/release.md](docs/release.md).
It contains the `main` branch status, current branch status, all CI sub-workflows, release
status, version tags, artifact details, status meanings, and commands for inspecting another
branch or commit.

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
# Defaults to http://localhost:13000/api
```

---

## Project Structure

```
expense-organizer/
├── docs/                         # Global documentation folder
│   ├── aibackend.md              # AI backend orchestrator & tool-caller docs
│   ├── aimodel.md                # GPU-accelerated AI model service docs
│   ├── api.md                    # Detailed REST API reference & examples
│   ├── backend.md                # FastAPI architecture & storage docs
│   ├── frontend.md               # Bun + React 19 web application docs
│   ├── mobile.md                 # Flutter mobile & Rust engine docs
│   ├── expense-helper-mobile.md  # Flutter chat assistant docs
│   ├── expense-helper-desktop.md # Desktop roadmap (on hold)
│   ├── release.md                # Branch, workflow, version, and release status
│   └── setup.md                  # Deployment & setup walkthrough
├── .github/
│   ├── workflows/ci-python.yml     # Python tests, format, and lint
│   ├── workflows/ci-frontend.yml   # Bun, Biome, and TypeScript checks
│   ├── workflows/ci-flutter.yml    # Flutter application checks
│   ├── workflows/ci-rust.yml       # Rust format, lint, and tests
│   ├── workflows/ci-services.yml   # Docker and health checks
│   ├── workflows/ci-success.yml    # Aggregate branch-protection status
│   ├── workflows/release.yml       # Tagged mobile and container releases
│   └── dependabot.yml              # Weekly dependency updates
├── backend/                      # Pure REST core backend (internal port 8000)
│   ├── main.py                   # Pure REST app factory, CORS, endpoint catalog
│   ├── models.py                 # Pydantic schemas (Expense, ExpenseSummary)
│   ├── storage.py                # In-memory data store
│   ├── routers/expenses.py       # REST route handlers & aggregations
│   ├── tests/                    # 34 pytest unit & integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── aibackend/                    # AI Orchestration container (port 18001)
│   ├── app/                      # Tools schema, dispatcher, session state machine
│   ├── tests/                    # 8 pytest tests for tools & session flows
│   ├── Dockerfile
│   └── requirements.txt
├── aimodel/                      # Dedicated AI model inference server (internal port 8002)
│   ├── app/                      # GGUF GPU model runner, completions & health endpoints
│   ├── models/                   # GGUF model weights (e.g. Qwen2.5-0.5B)
│   ├── tests/                    # 4 pytest tests for inference & health
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.ts                  # Bun HTTP server & /api reverse proxy
│   ├── bun.lock                   # Committed frontend dependency lockfile
│   ├── src/                      # React 19 TypeScript application
│   ├── package.json
│   └── Dockerfile
├── mobile/                       # Primary Expense Organizer mobile client
│   ├── lib/                      # Flutter client matching Web UI
│   ├── rust/                     # Native C-FFI offline queue engine
│   ├── test/                     # Flutter test suite
│   └── android/ ios/ linux/      # Native platform runners
├── expense-helper/               # Dedicated conversational AI companion
│   └── mobile/                   # Flutter chat client (Android & iOS)
├── scripts/
│   └── add_recurring_expenses.py # Seeding script for recurring expenses
├── docker-compose.yml
├── start.sh
└── README.md                     # Global project README
```

---

## License

MIT
