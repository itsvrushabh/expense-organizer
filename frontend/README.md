# Expense Organizer - Web Frontend 💻✨

The web client for the Expense Organizer system, powered by **Bun**, **React 19**, and **TypeScript**. It provides Excel-style spreadsheet pivot tables, calendar spend heatmaps, inline transaction creation/editing, and live multi-currency conversion.

---

## Features

- **Multi-Currency Live Conversion**: Toggle instantly between `USD ($)`, `INR (₹)`, and `CNY (¥)` with dynamic currency conversion based on central exchange rates.
- **Dynamic Category Palette**: Golden-ratio HSL color generator assigns consistent, aesthetically balanced color chips to every category.
- **Excel-Style Views**:
  - **Day View (`DayExcelView`)**: Inline transaction entry form with category grouping, live total, and inline Edit/Delete actions.
  - **Week View (`ExcelGridView`)**: 7-day (Sunday–Saturday) spreadsheet pivot table with sticky category headers and daily/category totals.
  - **Month & Year Views (`Grid6x6View`)**: Heatmap spend calendar grid with intensity shading and transaction drill-down modal dialogs.
- **Integrated Backend Proxy**: Bun's HTTP server proxies `/api/*` requests to the FastAPI backend, eliminating CORS issues during deployment.

---

## Architecture & File Structure

```
frontend/
├── index.ts                  # Bun HTTP server & /api reverse proxy
├── index.html                # Single-page application root
├── package.json              # Bun dependencies & scripts
├── Dockerfile                # Multi-stage container deployment
└── src/
    ├── main.tsx              # React DOM entry
    ├── App.tsx               # Main application controller & state
    ├── api.ts                # Typed fetch API client
    ├── currency.ts           # Multi-currency rates & formatters
    ├── colors.ts             # Golden-ratio category color palette
    ├── types.ts              # Shared TypeScript definitions
    ├── dates.ts              # Local-date parsing & timezone helpers
    └── views/
        ├── DayExcelView.tsx  # Grouped category table + form + actions
        ├── ExcelGridView.tsx # Weekly Excel spreadsheet table
        └── Grid6x6View.tsx   # Month/Year calendar spend heatmap
```

---

## Getting Started

### Prerequisites
- [Bun](https://bun.sh) (v1.4.0+)

### Install Dependencies
```bash
bun install
```

### Run in Development Mode
```bash
bun run dev
# Or: bun --hot index.ts
```
Starts the server at **http://localhost:3000** with Hot Module Reloading (HMR).

### Production Run
```bash
bun run start
# Or: bun index.ts
```

### Type Checking
```bash
bun x tsc --noEmit
```

---

## Environment Variables

- `PORT` - Port to bind the Bun server (default: `3000`)
- `API_URL` - URL of the FastAPI backend service (default: `http://localhost:8000`)
