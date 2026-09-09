import logging
import uuid
from datetime import datetime
from enum import Enum

from app.model_client import ModelClient
from app.schemas import ChatResponse, ExpenseDraft, ToolResult
from app.tools import execute_tool, tool_cancel_draft, tool_commit_expense

logger = logging.getLogger("aibackend.session")


class SessionState(str, Enum):
    IDLE = "idle"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    SAVED = "saved"
    CANCELLED = "cancelled"


class ChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state: SessionState = SessionState.IDLE
        self.draft: ExpenseDraft | None = None
        self.history: list[dict[str, str]] = []
        self.last_activity: datetime = datetime.now()


class SessionManager:
    """
    State machine orchestrating user interactions and function calling.
    """

    def __init__(self, model_client: ModelClient | None = None):
        self.sessions: dict[str, ChatSession] = {}
        self.model_client = model_client or ModelClient()

    def get_or_create_session(self, session_id: str | None = None) -> ChatSession:
        sid = session_id or str(uuid.uuid4())
        if sid not in self.sessions:
            self.sessions[sid] = ChatSession(session_id=sid)
        session = self.sessions[sid]
        session.last_activity = datetime.now()
        return session

    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    async def handle_message(
        self,
        user_message: str,
        session_id: str | None = None,
        reference_date: datetime | None = None,
    ) -> ChatResponse:
        session = self.get_or_create_session(session_id)
        session.history.append({"role": "user", "content": user_message})

        # 1. Ask model_client (or heuristic fallback) to select tool
        tool_call = await self.model_client.select_tool(
            user_message=user_message,
            current_draft=session.draft,
            reference_date=reference_date,
        )

        logger.info("Session %s: selected tool %s", session.session_id, tool_call.tool)

        # 2. Execute selected tool
        tool_result: ToolResult = await execute_tool(
            tool_call=tool_call,
            current_draft=session.draft,
            reference_date=reference_date,
        )

        # 3. Mutate session state
        if tool_result.status == "awaiting_confirmation":
            session.state = SessionState.AWAITING_CONFIRMATION
            session.draft = tool_result.draft
        elif tool_result.status == "saved":
            session.state = SessionState.SAVED
            session.draft = None
        elif tool_result.status == "cancelled":
            session.state = SessionState.CANCELLED
            session.draft = None
        else:
            # Idle or Clarification
            if tool_result.action_required == "none":
                session.state = SessionState.IDLE

        session.history.append({"role": "assistant", "content": tool_result.message})

        return ChatResponse(
            session_id=session.session_id,
            message=tool_result.message,
            status=tool_result.status,
            draft=tool_result.draft if tool_result.status == "awaiting_confirmation" else None,
            action_required=tool_result.action_required,
            saved_expense_id=tool_result.saved_expense_id,
        )

    async def confirm_draft(
        self,
        session_id: str,
        reference_date: datetime | None = None,
    ) -> ChatResponse:
        session = self.get_or_create_session(session_id)
        if not session.draft:
            return ChatResponse(
                session_id=session.session_id,
                message="There is no active draft to confirm. Please tell me about an expense first.",
                status=SessionState.IDLE.value,
                action_required="none",
            )

        draft = session.draft
        result = await tool_commit_expense(
            description=draft.description,
            amount=draft.amount,
            category=draft.category,
            date=draft.date,
            reference_date=reference_date,
        )

        if result.status == "saved":
            session.state = SessionState.SAVED
            session.draft = None
        session.history.append({"role": "assistant", "content": result.message})

        return ChatResponse(
            session_id=session.session_id,
            message=result.message,
            status=result.status,
            draft=None,
            action_required=result.action_required,
            saved_expense_id=result.saved_expense_id,
        )

    async def cancel_draft(self, session_id: str) -> ChatResponse:
        session = self.get_or_create_session(session_id)
        session.draft = None
        session.state = SessionState.CANCELLED

        result = tool_cancel_draft()
        session.history.append({"role": "assistant", "content": result.message})

        return ChatResponse(
            session_id=session.session_id,
            message=result.message,
            status=result.status,
            draft=None,
            action_required="none",
        )
