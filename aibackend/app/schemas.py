from typing import Optional, Any
from pydantic import BaseModel, Field


class ExpenseDraft(BaseModel):
    description: str = Field(..., description="Short summary of the expense")
    amount: float = Field(..., gt=0, description="Amount spent")
    category: str = Field(..., description="Category of the expense")
    date: str = Field(..., description="ISO date format YYYY-MM-DD")


class LLMExtractionResult(BaseModel):
    intent: str = Field(
        default="add_expense",
        description="add_expense, update_field, confirm, cancel, or chat",
    )
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    date: Optional[str] = None
    field_to_update: Optional[str] = None
    new_value: Optional[Any] = None
    missing_fields: list[str] = Field(default_factory=list)
    reply: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(
        default=None, description="Client session identifier"
    )


class ChatResponse(BaseModel):
    session_id: str
    message: str
    status: str = Field(
        ...,
        description="idle, awaiting_confirmation, saved, or cancelled",
    )
    draft: Optional[ExpenseDraft] = None
    action_required: Optional[str] = Field(
        default="none",
        description="confirm, clarify, or none",
    )
    saved_expense_id: Optional[int] = None


class ActionRequest(BaseModel):
    session_id: str = Field(..., description="Client session identifier")


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    status: str
    model_file_exists: bool
    model_loaded: bool
    model_path: str
    device: str
