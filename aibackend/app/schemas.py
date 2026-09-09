from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ExpenseDraft(BaseModel):
    description: str = Field(..., description="Short summary of the expense")
    amount: float = Field(..., gt=0, description="Amount spent")
    category: str = Field(..., description="Category of the expense")
    date: str = Field(..., description="ISO date format YYYY-MM-DD")


class ToolCall(BaseModel):
    tool: str = Field(..., description="Name of the selected tool")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments dictionary for the tool")


class ToolResult(BaseModel):
    status: str = Field(
        ...,
        description="idle, awaiting_confirmation, saved, or cancelled",
    )
    message: str = Field(..., description="Assistant reply message to the user")
    draft: Optional[ExpenseDraft] = None
    action_required: str = Field(default="none", description="confirm, clarify, or none")
    saved_expense_id: Optional[int] = None


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
    status: str
    aimodel_url: str
    aimodel_status: str
    backend_url: str
    backend_status: str
