# AI Backend Orchestration Service (`aibackend`) 🤖🧠

`aibackend` is a dedicated microservice container running on internal port `8001` (published to host port `18001`) that acts as the **Agentic Orchestrator & Tool Caller**. It handles all application logic, conversation state machines, Python function calling / tool execution, and HTTP communications with both the pure model server (`aimodel:8002`) and the core expense database (`backend:8000`).

---

## 1. System Architecture

```mermaid
flowchart LR
    subgraph Client["Flutter Mobile Client"]
        Mobile["expense-helper/mobile<br/>(Android & iOS)"]
    end

    subgraph AIB["Dedicated aibackend Service (Internal 8001 / Host 18001)"]
        ChatRouter["FastAPI Router<br/>/api/chat/message<br/>/api/chat/confirm<br/>/api/chat/cancel<br/>/health"]
        SessionStore["Session State Machine<br/>(IDLE, AWAITING_CONFIRMATION, SAVED)"]
        ToolEngine["Tool Dispatcher & Logic<br/>• draft_expense<br/>• update_draft_field<br/>• commit_expense<br/>• ask_clarification<br/>• cancel_draft"]
        ModelClient["Model Client<br/>(Calls aimodel:8002 + Fallback)"]
        ExpenseClient["Expense Client<br/>(Calls backend:8000)"]
        
        ChatRouter --> SessionStore
        SessionStore --> ModelClient
        SessionStore --> ToolEngine
        ToolEngine --> ExpenseClient
    end

    subgraph ModelServer["Internal aimodel Service (Port 8002 - No Host Exposure)"]
        AIM["FastAPI Model Server<br/>• GPU CUDA Offload (GTX 1650 Ti)<br/>• Qwen 2.5 0.5B GGUF<br/>• POST /v1/chat/completions"]
    end

    subgraph CoreBackend["Pure Core Backend (Internal Port 8000 - No Host Exposure)"]
        CoreAPI["FastAPI REST API<br/>POST /expenses<br/>SQLite Storage"]
    end

    Mobile -->|"HTTP POST /api/chat/*"| ChatRouter
    ModelClient -->|"Tool-selection prompt"| AIM
    ExpenseClient -->|"Persist confirmed draft"| CoreAPI
```

---

## 2. Key Responsibilities

1. **Python Logic & Function Calling**:
   - Maintains the formal JSON tool schemas (`TOOLS_SCHEMA`).
   - Dispatches tool invocations and normalizes dates (e.g. converting `"today"` or `"yesterday"` to ISO `YYYY-MM-DD`).
2. **Session State Management**:
   - Manages drafts in multi-turn conversation (`awaiting_confirmation`, `saved`, `cancelled`).
   - Supports natural language updates to draft fields (e.g. *"change amount to 50"*, *"change category to Food"*).
3. **HTTP Client (Curl & Httpx)**:
   - Queries `aimodel:8002/v1/chat/completions` for tool-selection decisions with graceful fallback to heuristic selection.
   - Pushes confirmed drafts to `backend:8000/expenses`.
4. **Resilience**:
   - If `aimodel` is temporarily busy or unreachable, `aibackend` automatically falls back to intelligent regex and keyword heuristics so the chat app never freezes.

---

## 3. Registered Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| **`draft_expense`** | `description`, `amount`, `category`, `date` | Creates a validated draft and prompts user for confirmation. |
| **`update_draft_field`** | `field`, `value` | Modifies an existing pending draft field (`amount`, `category`, `date`, `description`). |
| **`commit_expense`** | `description`, `amount`, `category`, `date` | Sends HTTP POST to `http://backend:8000/expenses` to persist in DB. |
| **`ask_clarification`** | `missing_field`, `question` | Prompts user when information is missing or ambiguous. |
| **`cancel_draft`** | `reason` | Discards the active draft and resets session state. |

---

## 4. Endpoints

- `POST /api/chat/message`: Send user message, returns assistant response and active draft card.
- `POST /api/chat/confirm`: Confirm and persist pending draft into core database.
- `POST /api/chat/cancel`: Discard pending draft.
- `POST /api/chat/reset`: Reset conversation session.
- `GET /health`: Health status reporting connectivity to both `aimodel` (port 8002) and `backend` (port 8000).

---

## 5. Local Setup & Testing

```bash
cd aibackend
pip install -r requirements.txt
pytest tests/ -v
uvicorn app.main:app --port 8001 --reload
```
