import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import HOST, MODEL_PATH, N_GPU_LAYERS, PORT
from app.model import ModelServer, get_model_server
from app.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    HealthResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("aimodel")

model_server: ModelServer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_server
    logger.info(
        "Initializing aimodel server (MODEL_PATH=%s, N_GPU_LAYERS=%s)...", MODEL_PATH, N_GPU_LAYERS
    )
    model_server = get_model_server()
    yield
    logger.info("Shutting down aimodel server.")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Expense AI Model Server (aimodel)",
        description="Dedicated GPU-accelerated GGUF LLM inference server",
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
        server = get_model_server()
        return {
            "name": "Expense AI Model Server (aimodel)",
            "version": "2.0.0",
            "model_path": MODEL_PATH,
            "device": server.device_info,
            "endpoints": {
                "health": "GET /health",
                "chat_completions": "POST /v1/chat/completions",
                "generate": "POST /generate",
            },
        }

    @application.get("/health", response_model=HealthResponse)
    async def health():
        server = get_model_server()
        return server.get_health()

    @application.post("/v1/chat/completions", response_model=ChatCompletionResponse)
    async def chat_completions(req: ChatCompletionRequest):
        server = get_model_server()
        try:
            return server.chat_completion(req)
        except Exception as e:
            logger.error("Chat completion error: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    @application.post("/generate", response_model=CompletionResponse)
    async def generate(req: CompletionRequest):
        server = get_model_server()
        try:
            return server.generate(req)
        except Exception as e:
            logger.error("Text generation error: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
