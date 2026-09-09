# Setup & Deployment Guide 🚀

This guide covers running the Expense Organizer using Docker or as standalone local services with prefixed host port mapping (`13000`, `18001`) and standard internal ports (`8000`, `8001`, `8002`, `3000`).

---

## Option 1: Docker (Recommended)

The easiest way to start the entire system with Docker Compose:

```bash
# Using the start script
./start.sh

# Or directly with Docker Compose
docker-compose up --build -d
```

To stop:
```bash
docker-compose down
```

### Access Points
- 🌐 **Web Frontend**: `http://localhost:13000` (mapped to internal container port `3000`)
- 🔧 **API Proxy (via Frontend)**: `http://localhost:13000/api` (proxied to internal backend `8000`)
- 📚 **Interactive Swagger API Docs**: `http://localhost:13000/api/docs`
- 🧠 **AI Backend Orchestrator (`aibackend`)**: `http://localhost:18001` (mapped to internal container port `8001`)
- 🩺 **AI Health Status**: `http://localhost:18001/health`

> [!NOTE]
> **Zero Unnecessary Port Exposure**:
> - Both `backend` (internal port `8000`) and `aimodel` (internal port `8002`) operate strictly on the internal Docker bridge network (`expense-network`) with **zero host port bindings**.
> - Clients and mobile apps communicate through the frontend reverse proxy (`http://localhost:13000/api`) or interact with the AI assistant at `http://localhost:18001`.

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

### 2. AI Model Service (FastAPI + GPU GGUF Engine)
```bash
cd aimodel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ensure model exists in aimodel/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
uvicorn app.main:app --reload --port 8002
```

### 3. AI Backend Orchestrator (FastAPI + Tool Dispatcher)
```bash
cd aibackend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 18001
```

### 4. Web Frontend (Bun + React)
```bash
cd frontend
bun install
PORT=13000 bun run dev
```

### 5. Expense Organizer Mobile App (Flutter + Rust)
```bash
cd mobile
flutter run
```

### 6. Expense Helper Chat App (Flutter Mobile)
```bash
cd expense-helper/mobile
flutter run
```

---

## Environment Variables

### Backend
- `PORT` - Port to bind the Uvicorn server (default: `8000`)

### Frontend
- `PORT` - Internal port to bind the Bun server (default: `3000`, published as `13000:3000`)
- `API_URL` - Backend URL used by the Bun `/api` reverse proxy (default: `http://backend:8000` or `http://localhost:8000`)

### AI Backend
- `PORT` - Internal port to bind Uvicorn (default: `8001`, published as `18001:8001`)
- `AIMODEL_URL` - AI Model service URL (default: `http://aimodel:8002` or `http://localhost:8002`)
- `EXPENSE_API_URL` - Backend API URL (default: `http://backend:8000` or `http://localhost:8000`)

---

## Docker Logs
```bash
# View combined logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f aibackend
docker-compose logs -f aimodel
```
