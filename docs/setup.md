# Setup & Deployment Guide 🚀

This guide covers running the Expense Organizer using Docker or as standalone local services.

---

## Option 1: Docker (Recommended)

The easiest way to start the entire system (FastAPI backend + Bun React frontend) with a single command:

```bash
# Using the start script
./start.sh

# Or directly with Docker Compose
docker-compose up --build
```

To run in background (detached):
```bash
docker-compose up -d --build
```

To stop:
```bash
docker-compose down
```

### Access Points
- 🌐 **Web Frontend**: `http://localhost:3000`
- 🔧 **Backend API**: `http://localhost:8000`
- 📚 **Interactive Swagger API Docs**: `http://localhost:8000/docs`

---

## Option 2: Local Development (Manual Setup)

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

## Environment Variables

### Backend
- `PORT` - Port to bind the Uvicorn server (default: `8000`)

### Frontend
- `PORT` - Port to bind the Bun server (default: `3000`)
- `API_URL` - Backend URL used by the Bun `/api` reverse proxy (default: `http://localhost:8000`)

---

## Troubleshooting

### Port Conflicts
If port `3000` or `8000` is already in use, update `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Change host port
```

### Docker Logs
```bash
# View combined logs
docker-compose logs -f

# View backend only
docker-compose logs -f backend

# View frontend only
docker-compose logs -f frontend
```
