# Web Frontend Architecture Guide 💻✨

The Expense Organizer web application is built with **Bun**, **React 19**, and **TypeScript**. It delivers desktop-grade Excel-style spreadsheet pivot tables, spend heatmaps, and multi-currency formatting.

---

## Directory Structure

```
frontend/
├── index.ts                  # Bun HTTP server & /api reverse proxy
├── index.html                # Single-page HTML entry point
├── package.json              # Bun configuration & dependencies
├── Dockerfile                # Production Docker container
└── src/
    ├── main.tsx              # React DOM mounting
    ├── App.tsx               # Main controller, state, view coordinator
    ├── api.ts                # Strongly-typed fetch API client
    ├── currency.ts           # Multi-currency rates & formatters
    ├── colors.ts             # Golden-ratio category color palette generator
    ├── types.ts              # Domain interfaces (Expense, ExpenseSummary, etc.)
    ├── dates.ts              # Local-date parser & timezone offset protection
    ├── App.css               # Global application styling
    ├── index.css             # Base reset & typography
    └── views/
        ├── DayExcelView.tsx  # Daily category table with inline add/edit/delete
        ├── ExcelGridView.tsx # Weekly Excel spreadsheet pivot table
        └── Grid6x6View.tsx   # Month/Year spend heatmap grid
```

---

## Core Features

### 1. Multi-Currency Live Conversion (`src/currency.ts`)
- Supported currencies:
  - `USD ($)` (Base rate: 1.0)
  - `INR (₹)` (Rate: 84.0)
  - `CNY (¥)` (Rate: 7.2)
- All amounts sent to the backend are stored in the base currency (USD).
- The UI dynamically converts and formats all display amounts according to the user's active currency selection.

### 2. Category Color Palette (`src/colors.ts`)
- Uses a deterministic Golden Ratio HSL algorithm:
  ```ts
  const GOLDEN_RATIO_CONJUGATE = 0.618033988749895;
  ```
- Hashes each category string into a hue `(h * 360) % 360`.
- Produces balanced, accessible foreground and background chip colors (`bg: hsl(h, 75%, 92%)`, `fg: hsl(h, 85%, 28%)`).

### 3. Excel-Style Views
- **Day View (`DayExcelView`)**:
  - Category-grouped expense rows with colored chips.
  - Inline "Add Expense" form at the top.
  - Inline Edit (modal dialog) and Delete actions.
- **Week View (`ExcelGridView`)**:
  - Spreadsheet pivot table showing 7 day columns (Sunday through Saturday).
  - Sticky category columns with automatic category row totals.
  - Sticky summary footer showing daily column totals and grand total.
  - Directly queries `GET /expenses/week/date/{date}?start_sunday=true`.
- **Month & Year Views (`Grid6x6View`)**:
  - Spend heatmap grid displaying spend per day (for month) or per month (for year).
  - Intensity-based background shading matching expenditure volume.
  - Interactive drill-down modal bottom sheet itemizing transactions.
  - Toggle button to switch between the Heatmap grid and full Spreadsheet table view.

---

## Proxy & Communication (`index.ts`)

Bun runs a built-in HTTP server that serves the compiled React frontend on port `3000` while proxying any `/api/*` request to the FastAPI backend:

```ts
const API_URL = process.env.API_URL || 'http://localhost:8000';
```

This guarantees that browser clients never experience CORS issues in production or containerized environments.

---

## Getting Started

### Install Dependencies
```bash
cd frontend
bun install
```

### Development Mode (with HMR)
```bash
bun run dev
```
Serves the web client at `http://localhost:3000` with instant Hot Module Reloading.

### Type Check
```bash
bun x tsc --noEmit
```
