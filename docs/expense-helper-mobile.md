# Expense Helper Mobile Client (`expense-helper/mobile`) 📱💬

`expense-helper/mobile` is a multiplatform chat client built with Flutter targeting **Android** and **iOS**. It interacts with `aibackend` (port `18001`) to provide a natural language expense-entry experience.

---

## 1. Key Features

- **Conversational UI**: Clean Material 3 message feed with distinct User and AI avatars and color themes.
- **Interactive Action Cards**: Pending expenses render interactive preview cards with:
  - Description, Amount, Category chip, and Date display.
  - `[Confirm & Save to DB]` button to persist directly to the database.
  - `[Cancel]` button to discard the draft.
  - Quick-update chips (e.g. *"Change date to yesterday"*, *"Change category to Food"*).
- **Flexible Network Configuration**:
  - Android Emulator: `http://10.0.2.2:18001`
  - iOS Simulator & Local: `http://127.0.0.1:18001`
  - In-app connection settings modal to switch IPs for physical devices.
- **Automatic Health Monitoring**: AppBar shows real-time status pill (*AI Connected* / *AI Offline*).

---

## 2. Project Structure

```text
expense-helper/mobile/
├── lib/
│   ├── main.dart                       # App entry point & Material 3 theme
│   ├── models/
│   │   └── chat_models.dart            # ExpenseDraft & ChatMessage models
│   ├── screens/
│   │   └── chat_screen.dart            # Main chat screen & connection dialog
│   ├── services/
│   │   └── ai_chat_service.dart        # HTTP client calling aibackend API (port 18001)
│   └── widgets/
│       ├── chat_bubble.dart            # User & Assistant chat bubbles
│       └── expense_draft_card.dart     # Action cards with confirm/cancel buttons
├── test/
│   └── widget_test.dart                # 3 widget tests verifying UI & interactions
└── pubspec.yaml                        # Dependencies (http, intl, cupertino_icons)
```

---

## 3. Running the App

### Prerequisites
- Flutter SDK 3.x+
- `aibackend` running on port `18001` (or via `docker-compose up -d`)

### Run on Android
```bash
cd expense-helper/mobile
flutter run -d android
```

### Run on iOS
```bash
cd expense-helper/mobile
flutter run -d ios
```

### Run Tests & Analysis
```bash
cd expense-helper/mobile
flutter test
flutter analyze
```
