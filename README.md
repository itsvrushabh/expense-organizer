# Expense Organizer

A modern, full-stack expense tracking system with Docker support, comprising:
- **Backend**: High-performance async FastAPI with validation, CORS, and full Day/Week/Month/Year aggregation endpoints.
- **Web Frontend**: Bun + React 19 + TypeScript with responsive Excel-style spreadsheet grids and calendar spend heatmaps.
- **Mobile App**: Cross-platform Flutter + Rust application (`mobile/`) with identical Web UI views, multi-currency live conversions, and an offline-first persistent queue engine.

---

## Architecture & Features

### 1. Backend (FastAPI)
- ⚡ **Async/Await Engine**: Ultra-fast async endpoints with Pydantic v2 schemas.
- 📅 **Comprehensive Time Aggregations**:
  - `GET /expenses/day/{date}`: Daily transactions
  - `GET /expenses/week/{year}/{week}`: ISO 8601 calendar week aggregations
  - `GET /expenses/week/date/{date}`: Monday–Sunday weekly window containing date
  - `GET /expenses/month/{year}/{month}`: Monthly records sorted by date
  - `GET /expenses/year/{year}`: Annual records
  - `GET /expenses/category/{category}`: Case-insensitive category filtering
- 🔄 **CRUD Operations**: Full `POST /expenses`, `PUT /expenses/{id}`, and `DELETE /expenses/{id}` support.
- 💾 **Storage Engine**: Memory-backed store with thread-safe operations and unit test suite.

### 2. Web Frontend (Bun + React)
- 🎨 **Modern Gradient Header & Controls**: Multi-currency selector (`USD`, `INR`, `CNY`), view switcher, and date stepper.
- 📅 **Day View (`DayExcelView`)**: Inline expense entry form, category grouping with colored chips, and inline edit/delete controls.
- 📊 **Week View (`ExcelGridView`)**: Excel-style spreadsheet grid with sticky category columns, days of the week, and dynamic row/column totals.
- 🗓️ **Month & Year Views (`Grid6x6View`)**: Calendar spend grid with visual heat-map shading and drill-down transaction modal.

### 3. Mobile App (Flutter + Rust)
- 📱 **Identical Web UI Experience**:
  - Purple-pink gradient header (`#6366f1` → `#ec4899`)
  - `Day`, `Week`, `Month`, `Year` pill selector
  - Date navigator with quick **Today** button and date picker
  - Live currency switcher: `USD ($)`, `INR (₹)`, `CNY (¥)`
  - Day view with inline add form and Excel-style edit/delete table
  - Week spreadsheet pivot table with category chips and daily totals
  - Month & Year spend heatmap grid with detail sheets and spreadsheet table toggle
- ⚡ **Rust Native Sync Engine (`expense_sync_engine`)**:
  - Built with Rust and bonded via C-FFI / `dart:ffi` (with automatic pure-Dart fallback).
  - High-reliability offline queue persisted to disk (`expense_queue.json`).
  - Automatic connectivity heartbeat every 4 seconds.
  - **Offline Mode**: Expenses added while offline are queued locally and tagged with `⏳ Queued`.
  - **Auto-Drain**: Once backend connectivity is restored, queued records are pushed automatically.
- 📦 **Platforms**: Android (APK), iOS, and Linux desktop.

---

## Quick Start with Docker

### Prerequisites
- Docker & Docker Compose

```bash
# Build and launch both backend and web frontend services
docker-compose up --build

# Or run in background (detached)
docker-compose up -d --build
```

Access Points:
- 🌐 **Web Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📚 **Interactive Swagger API Docs**: http://localhost:8000/docs

To stop:
```bash
docker-compose down
```

---

## Mobile App Setup & Running (`mobile/`)

### Prerequisites
- Flutter SDK (3.47+)
- Rust & Cargo (1.80+)
- Java 21 & Android SDK (for Android builds)

### 1. Build the Rust Engine (Optional, pre-compiled library included)
```bash
cd mobile/rust
cargo build --release
cargo test
```
Outputs `mobile/rust/target/release/libexpense_sync_engine.so`.

### 2. Run on Linux Desktop
```bash
cd mobile
flutter run
```

### 3. Build & Run for Android
```bash
cd mobile

# Compile debug APK
flutter build apk --debug

# Install directly on a connected device or emulator:
flutter run -d android
# Or manually install the compiled APK:
adb install build/app/outputs/flutter-apk/app-debug.apk
```
*Compiled APK location: `mobile/build/app/outputs/flutter-apk/app-debug.apk`.*

### 4. Build for iOS
> **Note**: Compiling native iOS binaries requires macOS with Xcode.

- **On a Mac**:
  ```bash
  cd mobile
  flutter pub get
  flutter build ipa --no-codesign
  # Or open in Xcode:
  open ios/Runner.xcworkspace
  ```
- **Automated Cloud CI/CD**: A GitHub Actions workflow is provided at `.github/workflows/build-mobile.yml` that builds the iOS app on free macOS runners upon pushing to GitHub.

---

## Local Development (Manual Setup)

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv venv
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

---

## Automated Test Suites

Run all automated tests across all parts of the application:

```bash
# Backend pytest suite (34 tests)
pytest backend/tests

# Rust native sync engine tests (3 tests)
cd mobile/rust && cargo test

# Flutter mobile test suite (7 tests + static analysis)
cd mobile
flutter analyze
flutter test

# Web frontend TypeScript type check
cd frontend
bun x tsc --noEmit
```

---

## API Reference

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/expenses` | Create a new expense |
| `GET` | `/expenses` | Retrieve all expenses |
| `PUT` | `/expenses/{id}` | Update an existing expense |
| `DELETE` | `/expenses/{id}` | Delete an expense by ID |

### Aggregations
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/expenses/day/{date}` | Daily expenses (`YYYY-MM-DD`) |
| `GET` | `/expenses/week/{year}/{week}` | ISO 8601 week expenses (`week: 1-53`, Monday–Sunday) |
| `GET` | `/expenses/week/date/{date}` | 7-day week for given date (`?start_sunday=true` for Sun–Sat; defaults to Mon–Sun) |
| `GET` | `/expenses/month/{year}/{month}` | Monthly expenses (`month: 1-12`) |
| `GET` | `/expenses/year/{year}` | Annual expenses |
| `GET` | `/expenses/category/{category}` | Filter by category name |

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
├── .github/
│   └── workflows/
│       └── build-mobile.yml      # CI/CD: Automated Android & iOS builds
├── backend/
│   ├── main.py                   # App factory, CORS, endpoint catalog
│   ├── models.py                 # Pydantic schemas (Expense, ExpenseSummary)
│   ├── storage.py                # In-memory data store
│   ├── routers/
│   │   └── expenses.py           # REST route handlers & aggregations
│   ├── tests/                    # 34 pytest unit and integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.ts                  # Bun HTTP server & /api reverse proxy
│   ├── src/
│   │   ├── App.tsx               # Main web view controller
│   │   ├── api.ts                # Typed fetch API client
│   │   ├── currency.ts           # Multi-currency rates & formatter
│   │   ├── colors.ts             # Golden-ratio category color palette
│   │   └── views/
│   │       ├── DayExcelView.tsx  # Category grouped table + Edit/Delete
│   │       ├── ExcelGridView.tsx # Weekly Excel spreadsheet table
│   │       └── Grid6x6View.tsx   # Month/Year spend heatmap grid
│   └── Dockerfile
├── mobile/
│   ├── lib/
│   │   ├── main.dart             # App entry & Material 3 gradient theme
│   │   ├── utils/
│   │   │   ├── currency.dart     # Mobile currency converter (USD/INR/CNY)
│   │   │   └── colors.dart       # Web-matching dynamic category colors
│   │   ├── services/
│   │   │   ├── api_service.dart  # FastAPI client
│   │   │   ├── rust_bridge.dart  # C-FFI bindings to Rust sync engine
│   │   │   └── sync_service.dart # Offline queue coordinator & auto-drain
│   │   └── views/
│   │       ├── web_style_app_screen.dart # Master view matching Web UI
│   │       ├── day_excel_view.dart       # Day view with inline form & table
│   │       ├── excel_grid_view.dart      # Week spreadsheet pivot table
│   │       ├── grid_6x6_view.dart        # Month/Year spend heatmap grid
│   │       └── queue_screen.dart         # Offline queue inspector
│   ├── rust/
│   │   ├── Cargo.toml            # Rust cdylib configuration
│   │   ├── src/
│   │   │   ├── queue.rs          # Persistent JSON file queue
│   │   │   ├── sync.rs           # Network health check & HTTP drain
│   │   │   └── ffi.rs            # C-FFI exports for Dart
│   │   └── tests/                # Rust cargo integration tests
│   └── test/                     # Flutter widget and unit tests
├── scripts/
│   └── add_recurring_expenses.py # Seeding script for recurring expenses
├── docker-compose.yml
├── start.sh
└── README.md
```

---

## License

MIT
