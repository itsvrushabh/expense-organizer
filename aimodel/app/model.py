import logging
import os
import time
from typing import Optional, List, Dict, Any

from app.config import MODEL_PATH, N_GPU_LAYERS, N_CTX
from app.schemas import (
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    CompletionRequest,
    CompletionResponse,
    HealthResponse,
)

logger = logging.getLogger("aimodel.model")


class ModelServer:
    """
    Dedicated AI Model Runner.
    Loads GGUF quantized models with GPU CUDA offloading (llama-cpp-python).
    Provides raw inference API without business logic or tools execution.
    """

    def __init__(self, model_path: Optional[str] = None, n_gpu_layers: Optional[int] = None):
        self.model_path = model_path or MODEL_PATH
        self.n_gpu_layers = n_gpu_layers if n_gpu_layers is not None else N_GPU_LAYERS
        self.llm = None
        self.model_loaded = False
        self.device_info = "CPU (AVX2)"
        self._initialize_model()

    def _initialize_model(self):
        if not os.path.exists(self.model_path):
            logger.warning("Model file not found at '%s'. Model server running in mock/standby mode.", self.model_path)
            self.model_loaded = False
            return

        try:
            from llama_cpp import Llama  # type: ignore

            logger.info(
                "Loading GGUF model from %s (n_gpu_layers=%s, n_ctx=%s)...",
                self.model_path,
                self.n_gpu_layers,
                N_CTX,
            )
            self.llm = Llama(
                model_path=self.model_path,
                n_gpu_layers=self.n_gpu_layers,
                n_ctx=N_CTX,
                n_threads=4,
                verbose=False,
            )
            self.model_loaded = True
            if self.n_gpu_layers != 0:
                self.device_info = f"GPU CUDA Offload (n_gpu_layers={self.n_gpu_layers})"
            else:
                self.device_info = "CPU (AVX2)"
            logger.info("Successfully loaded GGUF model (%s)", self.device_info)
        except Exception as e:
            logger.error("Failed to load Llama model from %s: %s", self.model_path, e)
            self.model_loaded = False

    def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Executes chat completion against the loaded GGUF model.
        """
        messages_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
        created_ts = int(time.time())

        if not self.model_loaded or self.llm is None:
            # Standby/Mock response if model file is not present
            logger.warning("Chat completion requested but model is not loaded. Returning fallback message.")
            return ChatCompletionResponse(
                id=f"chatcmpl-{created_ts}",
                created=created_ts,
                model="qwen2.5-0.5b-instruct",
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content='{"tool": "ask_clarification", "arguments": {"missing_field": "model_not_loaded", "question": "AI model is not loaded on server."}}',
                        ),
                        finish_reason="stop",
                    )
                ],
            )

        kwargs: Dict[str, Any] = {
            "messages": messages_dicts,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.response_format:
            kwargs["response_format"] = request.response_format

        output = self.llm.create_chat_completion(**kwargs)
        choice_data = output["choices"][0]
        content = choice_data["message"]["content"]
        finish_reason = choice_data.get("finish_reason", "stop")

        usage = output.get("usage", {})

        return ChatCompletionResponse(
            id=output.get("id", f"chatcmpl-{created_ts}"),
            created=output.get("created", created_ts),
            model=output.get("model", "qwen2.5-0.5b-instruct"),
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=content,
                    ),
                    finish_reason=finish_reason,
                )
            ],
            usage=usage,
        )

    def generate(self, request: CompletionRequest) -> CompletionResponse:
        """
        Raw text completion endpoint.
        """
        if not self.model_loaded or self.llm is None:
            return CompletionResponse(text="[Model not loaded]")

        output = self.llm(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        text = output["choices"][0]["text"]
        return CompletionResponse(text=text)

    def get_health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy" if self.model_loaded else "standby",
            model_file_exists=os.path.exists(self.model_path),
            model_loaded=self.model_loaded,
            model_path=self.model_path,
            device=self.device_info,
        )


# Global singleton
_model_server: Optional[ModelServer] = None


def get_model_server() -> ModelServer:
    global _model_server
    if _model_server is None:
        _model_server = ModelServer()
    return _model_server
