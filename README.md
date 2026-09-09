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

## GitHub Workflow Status and Releases

The repository uses GitHub Actions for continuous validation and releases:

### Live Workflow Status

The badges below show the latest status for the default `main` branch. Click a badge
to open the complete workflow history, including every branch, commit, job, and step.

| Workflow | Current status | Trigger | Scope |
|---|---|---|---|
| `CI / Success` | [![CI success status](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-success.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-success.yml) | After each CI sub-workflow completes | Required aggregate status for branch protection |
| `CI / Python` | [![Python CI status](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-python.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-python.yml) | Every pushed commit, pull request, and manual run | Backend, AI backend, and AI model tests plus Ruff formatting and linting |
| `CI / Frontend` | [![Frontend CI status](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-frontend.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-frontend.yml) | Every pushed commit, pull request, and manual run | Bun lockfile install, Biome formatting/linting, and TypeScript checks |
| `CI / Flutter` | [![Flutter CI status](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-flutter.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-flutter.yml) | Every pushed commit, pull request, and manual run | Both Flutter applications: Dart format, analyze, and tests |
| `CI / Rust` | [![Rust CI status](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-rust.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-rust.yml) | Every pushed commit, pull request, and manual run | rustfmt, Clippy, and native queue tests |
| `CI / Services` | [![Services CI status](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-services.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-services.yml) | Every pushed commit, pull request, and manual run | Compose validation, Docker startup, API proxy, and service health probes |
| `Release` | [![Release status](https://github.com/itsvrushabh/expense-organizer/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/release.yml) | `vMAJOR.MINOR.PATCH` tags and manual runs | Android APKs, unsigned iOS IPAs, Docker image publishing, and GitHub Release attachments |
| `Dependabot` | [View update activity](https://github.com/itsvrushabh/expense-organizer/pulls?q=is%3Apr+author%3Aapp%2Fdependabot) | Weekly schedule | Dependency update pull requests for Python, Bun/npm, Flutter/Dart, Cargo, Docker, and GitHub Actions |

### Status Meanings

GitHub reports the following workflow and job states:

| Status | Meaning |
|---|---|
| `Passed` / `Success` | All required steps completed successfully. |
| `Failed` | At least one required step failed; open the run for the failing job and log. |
| `Running` / `In progress` | The workflow is currently executing. |
| `Queued` / `Waiting` | GitHub has accepted the run but has not started it yet. |
| `Cancelled` | The run was stopped manually or superseded by a newer commit. CI cancels older runs for the same ref. |
| `Skipped` | A conditional job was intentionally not run, such as release-only work on a normal branch push. |
| `Neutral` / `No status` | No applicable result is available yet, or the workflow has not run for that branch. |

The required `CI / Success` workflow is the branch-protection gate. It runs after the
Python, frontend, Flutter, Rust, and service workflows complete for a commit, and fails
if any required sub-workflow fails, is cancelled, or is missing. Configure the repository's
branch protection rules to require the displayed `CI / Success / ci-success` check before
merging.

### Checks by Area

- Python services run pytest plus pinned Ruff formatting and lint checks in `CI / Python`.
- The web frontend uses the committed `frontend/bun.lock`, pinned Biome formatting/lint
    checks, and TypeScript type checking.
- Both Flutter applications run `dart format`, `flutter analyze`, and `flutter test`.
- The Rust offline queue runs `cargo fmt`, strict Clippy, and `cargo test` in `CI / Rust`.
- `CI / Services` builds and starts only the backend/frontend path on every branch push. It
    probe the frontend, API proxy, and expense endpoint, collect logs, and always clean up.
- GGUF model-backed checks are not part of every commit because model weights and GPU
    support are not available on standard GitHub-hosted runners.

### Release Artifacts and Permissions

Push a tag such as `v1.2.3` to start a release:

```bash
git tag v1.2.3
git push origin v1.2.3
```

The release workflow builds preview APK and unsigned IPA artifacts for both mobile
applications, publishes immutable version-tagged service images to GitHub Container
Registry, and attaches the mobile files to the GitHub Release. Temporary workflow
artifacts are retained for seven days. Android signing currently uses the repository's
existing preview configuration; production distribution requires signing secrets and
reviewed native platform projects. The `aimodel` image requires the GGUF model to be
mounted separately at `/app/models`.

Manual Release workflow runs are validation-only: they may build preview mobile artifacts
but do not publish Docker images or create GitHub Releases. Only a valid `vMAJOR.MINOR.PATCH`
tag can publish.

Workflow permissions are explicit: CI has read-only repository access, while the release
workflow alone has `contents: write` and `packages: write` for GitHub Releases and GHCR.
Do not expose release secrets to pull requests from forks.

### Inspecting Status

Use the Actions tab to inspect a run, or use the GitHub CLI:

```bash
gh run list --workflow "CI / Success"
gh run view RUN_ID --log-failed
gh run list --workflow "CI / Python"
gh run list --workflow "CI / Frontend"
gh run list --workflow "CI / Flutter"
gh run list --workflow "CI / Rust"
gh run list --workflow "CI / Services"
gh run list --workflow Release
gh run watch RUN_ID
```

To inspect a specific branch rather than the default branch badge:

```bash
gh run list --workflow CI --branch ci/first_commit
gh run list --workflow CI --commit COMMIT_SHA
```

Dependabot groups patch and minor updates by ecosystem. Major upgrades remain separate so
they can be reviewed with any required migration work. Keep `frontend/bun.lock`, Flutter
lockfiles, and `mobile/rust/Cargo.lock` committed when dependencies change.

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
