from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message text content")


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="Chat messages list")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=256, ge=1, le=4096)
    response_format: dict[str, Any] | None = Field(
        default=None, description="e.g. {'type': 'json_object'}"
    )


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str = "chatcmpl-aimodel"
    object: str = "chat.completion"
    created: int = 0
    model: str = "qwen2.5-0.5b-instruct"
    choices: list[ChatCompletionChoice]
    usage: dict[str, int] | None = None


class CompletionRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt to generate completion for")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=256, ge=1, le=4096)


class CompletionResponse(BaseModel):
    text: str = Field(..., description="Generated text completion")


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    status: str
    model_file_exists: bool
    model_loaded: bool
    model_path: str
    device: str
