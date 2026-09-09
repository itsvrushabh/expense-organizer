# Expense Organizer - Setup Complete! 🎉

## What's Been Built

A full-stack, cross-platform expense tracking application with:
- **Backend**: Async FastAPI with Day/Week/Month/Year aggregations, CORS, and Pydantic validation
- **Frontend**: Bun + React 19 + TypeScript with Excel spreadsheet grids, spend heatmaps, and multi-currency
- **Mobile**: Flutter + Rust C-FFI native offline queue engine (`mobile/`)
- **Docker**: Multi-container Docker setup with docker-compose

## Project Structure

```
expense-organizer/
├── .github/
│   └── workflows/build-mobile.yml # CI/CD for Android & iOS
├── backend/
│   ├── main.py                   # App factory + CORS + endpoint catalog
│   ├── models.py                 # Pydantic schemas (Expense, ExpenseSummary)
│   ├── storage.py                # In-memory data store
│   ├── routers/expenses.py       # REST route handlers & aggregations
│   ├── tests/                    # 34 pytest unit & integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.ts                  # Bun server + /api proxy
│   ├── index.html
│   ├── package.json
│   ├── Dockerfile
│   └── src/
│       ├── main.tsx
│       ├── App.tsx               # Shell: controls, currency, view switcher
│       ├── api.ts                # Typed fetch client (hits /api)
│       ├── currency.ts           # Multi-currency live converter
│       ├── colors.ts             # Golden-ratio category colors
│       ├── types.ts
│       ├── dates.ts
│       └── views/
│           ├── DayExcelView.tsx  # Day view with inline entry form
│           ├── ExcelGridView.tsx # Weekly Excel spreadsheet table
│           └── Grid6x6View.tsx   # Month/Year spend heatmap grid
├── mobile/
│   ├── lib/                      # Flutter Material 3 client matching Web UI
│   ├── rust/                     # High-reliability offline queue engine (C-FFI)
│   ├── test/                     # Flutter test suite
│   └── android/ ios/ linux/      # Platform build configs
├── scripts/
│   └── add_recurring_expenses.py # Seeding script for recurring expenses
├── docker-compose.yml
├── start.sh
└── README.md
```

## Quick Start

### Option 1: Using the start script (Recommended)
```bash
./start.sh
```

### Option 2: Manual Docker Compose
```bash
# Build and start services
docker-compose up --build

# Or in detached mode
docker-compose up -d --build
```

### Option 3: Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
bun install
bun run dev
```

**Mobile (Flutter + Rust):**
```bash
cd mobile
flutter run
```

## Access Points

After starting:
- 🌐 **Frontend UI**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs

## Excel-Style Views

### Day View
- Expenses grouped by category
- Shows description and amount for each expense

### Month View (Excel-style)
```
Date | Food    | Transport | Entertainment | Daily Total
-----|---------|-----------|---------------|------------
1    | $50.00  | $20.00    | -            | $70.00
2    | $35.00  | -         | $60.00       | $95.00
...
Total| $450.00 | $200.00   | $150.00      | $800.00
```

### Year View (Excel-style)
```
Month | Food      | Transport | Entertainment | Monthly Total
------|-----------|-----------|---------------|---------------
Jan   | $1,200.00 | $300.00   | $400.00      | $1,900.00
Feb   | $1,100.00 | $280.00   | $350.00      | $1,730.00
...
Total | $13,200.00| $3,200.00 | $4,100.00    | $20,500.00
```

## Features

✅ Add expenses with description, amount, category, and date
✅ View expenses by day, month, or year
✅ Excel-style grid layout with:
   - Sticky headers and first column
   - Automatic totals calculation
   - Color-coded rows for days with expenses
   - Responsive design
✅ Navigate between dates with arrow buttons
✅ Category-based expense grouping
✅ Real-time updates
✅ Fully containerized with Docker

## Next Steps

1. **Start the application**: Run `./start.sh`
2. **Add some expenses**: Use the form at the top
3. **Explore views**: Switch between Day/Month/Year views
4. **Navigate dates**: Use the arrow buttons to move through time

## Stopping the Application

```bash
docker-compose down
```

## Troubleshooting

### Docker issues
```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Rebuild from scratch
docker-compose down
docker-compose up --build
```

### Port conflicts
If ports 3000 or 8000 are in use, modify `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Change host port
```

## Technologies

- **Backend**: Python 3.11, FastAPI, Uvicorn, Pydantic
- **Frontend**: Bun 1.4.0, React 19, TypeScript
- **Containerization**: Docker, Docker Compose

---

Built on 2026-08-23
