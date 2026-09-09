import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import HOST, PORT, MODEL_PATH
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ActionRequest,
    HealthResponse,
)
from app.llm import LLMEngine
from app.session import SessionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("aibackend")

# Global instances
llm_engine: LLMEngine = None
session_manager: SessionManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_engine, session_manager
    logger.info("Initializing AI Backend with model path: %s", MODEL_PATH)
    llm_engine = LLMEngine(model_path=MODEL_PATH)
    session_manager = SessionManager(llm_engine=llm_engine)
    yield
    logger.info("Shutting down AI Backend.")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Expense Helper AI Backend",
        version="1.0.0",
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
            "name": "Expense Helper AI Backend",
            "version": "1.0.0",
            "model_path": MODEL_PATH,
            "endpoints": {
                "message": "POST /api/chat/message",
                "confirm": "POST /api/chat/confirm",
                "cancel": "POST /api/chat/cancel",
                "reset": "POST /api/chat/reset",
                "health": "GET /health",
            },
        }

    @application.get("/health", response_model=HealthResponse)
    async def health():
        target_path = llm_engine.model_path if llm_engine else MODEL_PATH
        file_exists = os.path.exists(target_path)
        loaded = bool(llm_engine and llm_engine.model_loaded)
        return HealthResponse(
            status="healthy" if (file_exists or llm_engine is not None) else "unhealthy",
            model_file_exists=file_exists,
            model_loaded=loaded,
            model_path=target_path,
            device="CPU (AVX2)",
        )

    @application.post("/api/chat/message", response_model=ChatResponse)
    async def chat_message(req: ChatRequest):
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        return await session_manager.handle_message(req.message, req.session_id)

    @application.post("/api/chat/confirm", response_model=ChatResponse)
    async def chat_confirm(req: ActionRequest):
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        return await session_manager.confirm_draft(req.session_id)

    @application.post("/api/chat/cancel", response_model=ChatResponse)
    async def chat_cancel(req: ActionRequest):
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        return session_manager.cancel_draft(req.session_id)

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
