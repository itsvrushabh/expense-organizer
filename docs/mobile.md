# Mobile Application & Rust Sync Engine Guide 📱⚡

The Expense Organizer mobile app is a cross-platform client built with **Flutter** (Dart) and a high-reliability **Rust** sync engine (`expense_sync_engine`). It provides complete visual parity with the web frontend and an offline-first persistent queue.

---

## Directory Structure

```
mobile/
├── lib/
│   ├── main.dart                      # App entry point & Material 3 gradient theme
│   ├── models/
│   │   ├── expense.dart               # Expense model & serialization
│   │   ├── expense_summary.dart       # Summary aggregation model
│   │   └── queue_item.dart            # Offline queue item with retry tracking
│   ├── services/
│   │   ├── api_service.dart           # FastAPI HTTP client (Day/Week/Month/Year/CRUD)
│   │   ├── rust_bridge.dart           # C-FFI / dart:ffi bindings
│   │   └── sync_service.dart          # Offline coordinator & background worker
│   ├── utils/
│   │   ├── colors.dart                # Golden-ratio category colors matching web
│   │   └── currency.dart              # Multi-currency rates (USD, INR, CNY)
│   └── views/
│       ├── web_style_app_screen.dart  # Main coordinator matching Web UI layout
│       ├── day_excel_view.dart        # Grouped category table with inline add form
│       ├── excel_grid_view.dart       # Week spreadsheet pivot table
│       ├── grid_6x6_view.dart         # Month/Year spend heatmap & detail sheets
│       ├── queue_screen.dart          # Offline queue inspector & sync trigger
│       └── server_settings_dialog.dart# Backend URL configuration & presets
├── rust/
│   ├── Cargo.toml                     # Rust crate config (cdylib, staticlib, rlib)
│   ├── src/
│   │   ├── lib.rs                     # Crate root & module exports
│   │   ├── queue.rs                   # Persistent JSON file queue (QueueManager)
│   │   ├── sync.rs                    # Network health check & HTTP drain
│   │   └── ffi.rs                     # C-FFI exports for Dart
│   └── tests/
│       └── test_sync.rs               # Rust unit & integration tests
├── test/
│   └── widget_test.dart               # 7 Flutter unit and widget tests
├── android/                           # Android Gradle configuration
├── ios/                               # iOS Xcode project
└── linux/                             # Linux desktop runner
```

---

## Architecture

### Offline-First Data Flow

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

1. **Adding Expenses**:
   - If server is online, the expense is posted directly.
   - If server is offline or unreachable, the record is immediately enqueued locally into `expense_queue.json` and tagged with `⏳ Queued`.
2. **Background Heartbeat & Auto-Drain**:
   - A non-blocking periodic timer pings the backend every 4 seconds.
   - When connection is detected, pending items are drained automatically to `POST /expenses`.
   - Successfully synced records transition to `synced`.
3. **Pure-Dart Fallback**:
   - If the compiled Rust dynamic library is not present on the device, the app transparently falls back to an internal pure-Dart sync engine without crashing.

---

## Server Configuration

Tap the **DNS icon** in the top-right corner of the mobile app to set the server URL:
- **Linux Desktop / iOS Simulator**: `http://localhost:13000/api`
- **Android Emulator**: `http://10.0.2.2:13000/api` (maps to host localhost)
- **Physical Phone on Wi-Fi**: `http://<your-computer-ip>:13000/api`
- Includes a **Test Connection** button for immediate connectivity diagnosis.

---

## Building & Running

### 1. Build the Rust Engine
```bash
cd mobile/rust
cargo build --release
cargo test
```
Generates `mobile/rust/target/release/libexpense_sync_engine.so`.

### 2. Run on Linux Desktop
```bash
cd mobile
flutter run -d linux
```

### 3. Build & Run for Android
```bash
cd mobile
flutter build apk --debug

# Install to emulator or USB-connected phone:
flutter run -d android
# Or install manually:
adb install build/app/outputs/flutter-apk/app-debug.apk
```

### 4. Build for iOS
```bash
cd mobile
flutter pub get
flutter build ipa --no-codesign
# Or open in Xcode:
open ios/Runner.xcworkspace
```

---

## Running Automated Tests

```bash
cd mobile

# Static analysis (0 errors, 0 warnings)
flutter analyze

# Widget & unit tests (7 tests)
flutter test

# Rust engine tests (3 tests)
cd rust && cargo test
```
