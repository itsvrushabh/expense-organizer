import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import HOST, PORT, AIMODEL_URL, EXPENSE_API_URL
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ActionRequest,
    HealthResponse,
)
from app.tools import TOOLS_SCHEMA
from app.model_client import ModelClient
from app.expense_client import check_backend_health
from app.session import SessionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("aibackend")

# Global instances
model_client: ModelClient = None
session_manager: SessionManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_client, session_manager
    logger.info("Initializing aibackend service (AIMODEL_URL=%s, EXPENSE_API_URL=%s)...", AIMODEL_URL, EXPENSE_API_URL)
    model_client = ModelClient(aimodel_url=AIMODEL_URL)
    session_manager = SessionManager(model_client=model_client)
    yield
    logger.info("Shutting down aibackend service.")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Expense AI Backend Service (aibackend)",
        description="Agentic Tool Calling & Function Execution Orchestrator",
        version="2.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/")
    async def root():
        return {
            "name": "Expense AI Backend Service (aibackend)",
            "version": "2.0.0",
            "aimodel_url": AIMODEL_URL,
            "expense_api_url": EXPENSE_API_URL,
            "endpoints": {
                "message": "POST /api/chat/message",
                "confirm": "POST /api/chat/confirm",
                "cancel": "POST /api/chat/cancel",
                "reset": "POST /api/chat/reset",
                "health": "GET /health",
            },
            "registered_tools": [t["function"]["name"] for t in TOOLS_SCHEMA],
        }

    @application.get("/health", response_model=HealthResponse)
    async def health():
        aimodel_h = await model_client.check_aimodel_health() if model_client else {"status": "uninitialized"}
        backend_h = await check_backend_health()

        aimodel_ok = aimodel_h.get("status") == "reachable"
        backend_ok = backend_h.get("status") == "reachable"

        return HealthResponse(
            status="healthy" if (aimodel_ok or backend_ok) else "degraded",
            aimodel_url=AIMODEL_URL,
            aimodel_status="reachable" if aimodel_ok else "unreachable",
            backend_url=EXPENSE_API_URL,
            backend_status="reachable" if backend_ok else "unreachable",
        )

    @application.post("/api/chat/message", response_model=ChatResponse)
    @application.post("/api/ai/chat", response_model=ChatResponse)
    async def chat_message(req: ChatRequest):
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        return await session_manager.handle_message(req.message, req.session_id)

    @application.post("/api/chat/confirm", response_model=ChatResponse)
    @application.post("/api/ai/confirm", response_model=ChatResponse)
    async def chat_confirm(req: ActionRequest):
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        return await session_manager.confirm_draft(req.session_id)

    @application.post("/api/chat/cancel", response_model=ChatResponse)
    @application.post("/api/ai/cancel", response_model=ChatResponse)
    async def chat_cancel(req: ActionRequest):
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        return await session_manager.cancel_draft(req.session_id)

    @application.post("/api/chat/reset")
    async def chat_reset(req: ActionRequest):
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        session_manager.reset_session(req.session_id)
        return {"status": "reset", "session_id": req.session_id}

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
