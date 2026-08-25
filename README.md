# Expense Organizer

A full-stack expense tracking application with Docker support. Features an async FastAPI backend and a Bun-powered React frontend with Excel-style expense views.

## Features

### Backend (FastAPI)
- ✅ Async/await for better performance
- 🔄 CORS enabled for frontend access
- 📊 RESTful API with validation
- 💾 In-memory storage (easily extendable to database)

### Frontend (Bun + React)
- 📅 **Day View**: Expenses grouped by category
- 📆 **Month View**: Excel-style grid with dates as rows, categories as columns
- 📊 **Year View**: Excel-style grid with months as rows, categories as columns
- 💰 Automatic totals calculation
- 🎨 Modern, responsive UI
- ⚡ Built with Bun for fast performance

## Quick Start with Docker

### Prerequisites
- Docker
- Docker Compose

### Run the Application

```bash
cd /home/cachyos/Work/expense-organizer

# Build and start both services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Stop the Application

```bash
docker-compose down
```

## Local Development (without Docker)

### Backend Setup

```bash
# Navigate to project root
cd /home/cachyos/Work/expense-organizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
python main.py
# or
uvicorn main:app --reload
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
bun install

# Run development server
bun run dev
```

## API Endpoints

### Expense Management
- `POST /expenses` - Create a new expense
- `GET /expenses` - Get all expenses
- `DELETE /expenses/{id}` - Delete an expense

### Time-based Views
- `GET /expenses/day/{date}` - Get expenses for a specific day (YYYY-MM-DD)
- `GET /expenses/month/{year}/{month}` - Get expenses for a specific month
- `GET /expenses/year/{year}` - Get expenses for a specific year

### Category Filter
- `GET /expenses/category/{category}` - Get expenses by category

## Usage Examples

### Add an Expense

```bash
curl -X POST "http://localhost:8000/expenses" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Grocery shopping",
    "amount": 125.50,
    "category": "Food",
    "date": "2026-08-23"
  }'
```

### Get Month View

```bash
curl "http://localhost:8000/expenses/month/2026/8"
```

Response:
```json
{
  "total": 450.75,
  "count": 12,
  "expenses": [...]
}
```

## Excel-Style Views

### Month View
- **Headers**: Date (1-31)
- **Columns**: Each expense category
- **Cells**: Total amount for that category on that date
- **Last Column**: Daily totals
- **Last Row**: Category totals

### Year View
- **Headers**: Month (Jan-Dec)
- **Columns**: Each expense category
- **Cells**: Total amount for that category in that month
- **Last Column**: Monthly totals
- **Last Row**: Category totals

## Project Structure

```
expense-organizer/
├── main.py                 # uvicorn entry (re-exports app)
├── app/
│   ├── main.py             # FastAPI app factory + CORS
│   ├── models.py           # Pydantic models
│   ├── storage.py          # In-memory expense store
│   └── routers/
│       └── expenses.py     # Expense routes
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── frontend/
    ├── index.ts            # Bun server + /api proxy
    ├── index.html
    ├── package.json
    ├── Dockerfile
    └── src/
        ├── main.tsx
        ├── App.tsx         # Shell: form, controls, view switch
        ├── api.ts          # Typed fetch client (hits /api)
        ├── types.ts
        ├── dates.ts        # Local-date helpers
        ├── App.css
        ├── index.css
        └── views/
            ├── DayExcelView.tsx
            └── ExcelGridView.tsx   # Shared month/year grid
```

## Technologies

### Backend
- Python 3.11
- FastAPI
- Pydantic
- Uvicorn

### Frontend
- Bun 1.4.0
- React 19
- TypeScript

## Future Enhancements

- [ ] Persistent database (PostgreSQL/MongoDB)
- [ ] User authentication
- [ ] Export to Excel/CSV
- [ ] Charts and visualizations
- [ ] Recurring expenses
- [ ] Budget tracking
- [ ] Multi-currency support
- [ ] Mobile responsive improvements

## Environment Variables

### Backend
- `PORT` - Server port (default: 8000)

### Frontend
- `API_URL` - Backend URL used by the Bun `/api` proxy (default: http://localhost:8000). The browser never talks to the backend directly.

## Docker Configuration

The application uses multi-container Docker setup:
- **backend**: Python FastAPI server on port 8000
- **frontend**: Bun server on port 3000

Both services restart automatically unless stopped manually.

## License

MIT
