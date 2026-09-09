# Expense Organizer Mobile App 📱⚡

A cross-platform mobile application built with **Flutter** and **Rust** (`expense_sync_engine`). It provides identical Excel-style and heatmap views to the web application, multi-currency conversion, and an offline-first persistent queue engine that pushes records to the FastAPI server when online.

---

## Architecture & Features

### 1. Web UI View Replication
The mobile application replicates the exact UI components and layout of the web frontend:
- **Gradient Header**: Styled with the web app's vibrant purple-pink gradient (`#6366f1` → `#8b5cf6` → `#d946ef` → `#ec4899`).
- **View Selector**: `Day`, `Week`, `Month`, and `Year` pill selector with active indicators.
- **Date Navigator**: `[ ◀ ]` Date picker `[ ▶ ]` with a quick **Today** jump button.
- **Multi-Currency Live Conversion**:
  - Switch between `USD ($)`, `INR (₹)`, and `CNY (¥)`.
  - Automatic live rate conversions (`USD: 1.0`, `INR: 84.0`, `CNY: 7.2`) matching the web app.
- **Day View (`DayExcelView`)**:
  - Inline "Add New Expense" form (Description, Amount in selected currency, Category, Date, and Add button).
  - Excel-style table grouped by category with dynamic golden-ratio colored chips.
  - **Edit** (opens modal dialog calling `PUT /expenses/{id}`) and **Delete** actions (confirm dialog calling `DELETE /expenses/{id}`).
- **Week View (`ExcelGridView`)**:
  - Horizontal & vertical scrolling spreadsheet pivot table.
  - Sticky category column with colored chips.
  - 7 day columns (Sunday through Saturday) with formatted dates.
  - Automatic daily and category totals.
- **Month & Year Views (`Grid6x6View`)**:
  - Visual spend heatmap grid with day/month labels, total spend, transaction counts, and intensity-based shading.
  - Tapping any cell opens a modal bottom sheet displaying all transactions with category chips and Grand Total.
  - **Table View Toggle**: A header button allows switching between the Heatmap Spend Grid and the full Spreadsheet Table view for both Month and Year modes.

---

### 2. Offline-First Queue & Rust Sync Engine

```
                          ┌───────────────────────────┐
                          │    Flutter Mobile App     │
                          └─────────────┬─────────────┘
                                        │
                             C-FFI / dart:ffi Bridge
                                        │
                          ┌─────────────▼─────────────┐
                          │   Rust Native Engine      │
                          │ (mobile/rust)             │
                          │                           │
                          │ • QueueManager (Disk I/O) │
                          │ • sync_pending_queue      │
                          │ • check_server_online     │
                          └──────┬─────────────┬──────┘
                                 │             │
                      Server is  │             │ Server is
                      ONLINE     │             │ OFFLINE
                                 ▼             ▼
                     ┌───────────────┐     ┌───────────────────────┐
                     │FastAPI Backend│     │ Local Persistent File │
                     │POST /expenses │     │ (expense_queue.json)  │
                     └───────────────┘     └───────────────────────┘
```

- **Offline Adding**:
  - When the server is **offline**, added expenses are safely serialized to a persistent JSON file (`expense_queue.json`) managed by the Rust sync engine.
  - Records appear immediately in the Day table, Week spreadsheet, and Month/Year heatmap cells with a `⏳ Queued` badge.
- **Automatic Heartbeat & Drain**:
  - A background periodic timer performs a non-blocking async health ping every 4 seconds without freezing the UI thread.
  - When the server comes back online, pending records are automatically pushed to `POST /expenses`.
  - Upon server confirmation, local items transition to `synced`.
- **Queue Screen**:
  - Tap the cloud sync badge icon in the app bar to view all pending, syncing, and failed records formatted in your selected currency (`USD`, `INR`, `CNY`).
  - Inspect retry counts and server error messages.
  - Trigger manual **Sync Now** or clean up confirmed records with **Clear Synced**.
- **Pure-Dart Fallback**:
  - If the compiled Rust dynamic library is absent on a target device, the app automatically falls back to an internal pure-Dart sync engine without crashing.

---

## Directory Structure

```
mobile/
├── lib/
│   ├── main.dart                      # App entry point & Material 3 theme
│   ├── models/
│   │   ├── expense.dart               # Expense data model
│   │   ├── expense_summary.dart       # Aggregation summary model
│   │   └── queue_item.dart            # Offline queue item model
│   ├── services/
│   │   ├── api_service.dart           # FastAPI HTTP client (Day/Week/Month/Year/CRUD)
│   │   ├── rust_bridge.dart           # C-FFI bindings to Rust native engine
│   │   └── sync_service.dart          # Offline coordinator & auto-drain worker
│   ├── utils/
│   │   ├── colors.dart                # Golden-ratio category color generator
│   │   └── currency.dart              # Multi-currency rates & formatting
│   └── views/
│       ├── web_style_app_screen.dart  # Master view matching Web UI
│       ├── day_excel_view.dart        # Day view: inline form & grouped table
│       ├── excel_grid_view.dart       # Week view: spreadsheet pivot table
│       ├── grid_6x6_view.dart         # Month/Year: spend heatmap & modal sheets
│       └── queue_screen.dart          # Offline queue inspector & sync controls
├── rust/
│   ├── Cargo.toml                     # Rust crate config (cdylib, staticlib, rlib)
│   ├── src/
│   │   ├── lib.rs                     # Crate root
│   │   ├── queue.rs                   # Thread-safe persistent file queue
│   │   ├── sync.rs                    # Network health ping & HTTP drain
│   │   └── ffi.rs                     # C-FFI exports for dart:ffi
│   └── tests/
│       └── test_sync.rs               # Rust integration tests
├── android/                           # Android project configuration
├── ios/                               # iOS project configuration
├── linux/                             # Linux desktop runner (bundles Rust .so)
└── test/
    └── widget_test.dart               # Flutter test suite
```

---

## Building & Running

### 1. Build the Rust Sync Engine
The Rust engine compiles into a shared library (`.so` / `.dylib` / `.dll`):
```bash
cd mobile/rust
cargo build --release
cargo test
```
*Artifact: `mobile/rust/target/release/libexpense_sync_engine.so`.*

### 2. Run on Linux Desktop
Linux desktop builds automatically bundle the Rust shared library into the application bundle:
```bash
cd mobile
flutter run -d linux
```

### 3. Build & Run for Android
```bash
cd mobile

# Compile debug APK
flutter build apk --debug

# Install to connected device or emulator
flutter run -d android
# Or manually install via ADB:
adb install build/app/outputs/flutter-apk/app-debug.apk
```
*Compiled APK location: `mobile/build/app/outputs/flutter-apk/app-debug.apk`.*

### 4. Build for iOS
> **Note**: Building native iOS applications requires macOS with Xcode.

#### On a Mac:
```bash
cd mobile
flutter pub get
flutter build ipa --no-codesign

# Or open in Xcode for simulator / physical iPhone debugging:
open ios/Runner.xcworkspace
```

#### Automated Cloud CI/CD (GitHub Actions):
A workflow is configured at `.github/workflows/build-mobile.yml`. When pushed to GitHub, GitHub's free macOS runners will compile the iOS application and make the app bundle available for download in the repository's **Actions** tab.

---

## Server Configuration
In the top-right corner of the mobile app, tap the **DNS Settings** icon to configure the API URL:
- **Linux Desktop**: `http://localhost:8000`
- **Android Emulator**: `http://10.0.2.2:8000` (maps to host localhost)
- **Physical Phone on Wi-Fi**: `http://<your-computer-ip>:8000`

---

## Running Automated Tests

```bash
# Flutter static analysis (0 errors/warnings)
cd mobile
flutter analyze

# Flutter widget & unit test suite (7 tests)
flutter test

# Rust sync engine unit tests (3 tests)
cd mobile/rust
cargo test
```
