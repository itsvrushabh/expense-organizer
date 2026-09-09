# AI Backend Microservice (`aibackend`) 🤖

`aibackend` is a containerized microservice that converts natural language expense messages into structured expense drafts (`description`, `amount`, `category`, `date`), validates them with the user, and inserts confirmed expenses into the core SQLite database via the FastAPI backend.

---

## 1. Features

- **Smallest Effective Local Model**: Powered by `Qwen2.5-0.5B-Instruct-GGUF` (~397 MB) running locally on CPU.
- **Conversational State Machine**: Tracks user sessions through `IDLE`, `AWAITING_CONFIRMATION`, and `SAVED` states.
- **Interactive Field Adjustments**: Users can update fields on the fly (e.g., *"Change category to Groceries"*, *"Change date to yesterday"*, *"Make amount 50"*).
- **Two-Step Confirmation**: Never mutates the core database without explicit user confirmation (`POST /api/chat/confirm` or replying *"yes"*).
- **Resilient Fallback**: Automatically activates a fast heuristic parser if model weights are not loaded or in lightweight CI environments.

---

## 2. Model Setup & Download

The model file must reside in `aibackend/models/`:

- **Model File**: `qwen2.5-0.5b-instruct-q4_k_m.gguf`
- **File Size**: ~397 MB
- **Target Path**: `aibackend/models/qwen2.5-0.5b-instruct-q4_k_m.gguf`

### Download Command
```bash
mkdir -p aibackend/models
curl -L \
  "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf" \
  -o aibackend/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

---

## 3. Running with Docker Compose

`aibackend` is configured as a service in `docker-compose.yml`:

```bash
# Start all services including aibackend
docker-compose up --build -d

# Or view aibackend logs specifically
docker-compose logs -f aibackend
```

Access points:
- 🤖 **Chat Service**: `http://localhost:8001`
- 🩺 **Health Check**: `http://localhost:8001/health`
- 📚 **Swagger Docs**: `http://localhost:8001/docs`

---

## 4. API Endpoints

### `POST /api/chat/message`
Send a user message to analyze or update a draft.
- **Request**:
  ```json
  {
    "message": "Spent 45 on groceries today",
    "session_id": "optional-client-session-uuid"
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "session-uuid",
    "message": "I extracted the following expense: ... Is this correct?",
    "status": "awaiting_confirmation",
    "action_required": "confirm",
    "draft": {
      "description": "Groceries",
      "amount": 45.0,
      "category": "Groceries",
      "date": "2026-09-09"
    }
  }
  ```

### `POST /api/chat/confirm`
Explicit button click to persist the active draft into the database.
- **Request**: `{"session_id": "session-uuid"}`
- **Response**:
  ```json
  {
    "session_id": "session-uuid",
    "message": "✅ Expense successfully saved to the database! (ID #42)",
    "status": "saved",
    "saved_expense_id": 42
  }
  ```

### `POST /api/chat/cancel`
Discards the active draft and resets the conversation session to `idle`.
- **Request**: `{"session_id": "session-uuid"}`

### `GET /health`
Returns runtime status and whether the GGUF model file is present.

---

## 5. Local Development & Testing

```bash
cd aibackend

# Run tests
pytest tests/ -v

# Run locally
uvicorn app.main:app --port 8001 --reload
```
