import logging
import uuid
from typing import Dict, Optional
from datetime import datetime

from app.schemas import (
    ExpenseDraft,
    ChatResponse,
    LLMExtractionResult,
)
from app.llm import LLMEngine
from app.expense_client import insert_expense_to_db

logger = logging.getLogger(__name__)


class UserSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.status = "idle"  # idle | awaiting_confirmation
        self.draft: Optional[ExpenseDraft] = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()


class SessionManager:
    def __init__(self, llm_engine: LLMEngine):
        self.sessions: Dict[str, UserSession] = {}
        self.llm = llm_engine

    def get_or_create_session(self, session_id: Optional[str] = None) -> UserSession:
        sid = session_id or str(uuid.uuid4())
        if sid not in self.sessions:
            self.sessions[sid] = UserSession(session_id=sid)
        session = self.sessions[sid]
        session.last_activity = datetime.now()
        return session

    async def handle_message(self, message: str, session_id: Optional[str] = None) -> ChatResponse:
        session = self.get_or_create_session(session_id)
        text = message.strip()

        # 1. State: AWAITING CONFIRMATION
        if session.status == "awaiting_confirmation" and session.draft is not None:
            # Let LLM or heuristic analyze the intent given the current draft
            extraction = self.llm.parse_user_message(
                text,
                current_draft=session.draft.model_dump(),
            )

            # Case A: Confirm
            if extraction.intent == "confirm":
                return await self.confirm_draft(session.session_id)

            # Case B: Cancel
            if extraction.intent == "cancel":
                return self.cancel_draft(session.session_id)

            # Case C: Update specific field
            if extraction.intent == "update_field" and extraction.field_to_update:
                return self._apply_update(session, extraction.field_to_update, extraction.new_value)

            # Case D: User entered something else - check if it's updating a field implicitly
            # Or asking to revise
            lower = text.lower()
            if any(k in lower for k in ["change", "update", "make", "set", "fix", "instead"]):
                # Try fallback extraction for update
                field_map = {"date": "date", "category": "category", "amount": "amount", "description": "description", "desc": "description", "cost": "amount", "price": "amount"}
                for k, field in field_map.items():
                    if k in lower:
                        return self._apply_update(session, field, text)

            # Case E: If user gives an entirely new expense description, restart draft
            if extraction.amount is not None and extraction.description:
                session.draft = ExpenseDraft(
                    description=extraction.description,
                    amount=extraction.amount,
                    category=extraction.category or "Other",
                    date=extraction.date or datetime.now().strftime("%Y-%m-%d"),
                )
                return self._build_confirmation_prompt(session)

            # Ambiguous input during confirmation
            return ChatResponse(
                session_id=session.session_id,
                message=(
                    f"I currently have this expense ready to save:\n"
                    f"• Description: {session.draft.description}\n"
                    f"• Amount: ${session.draft.amount:.2f}\n"
                    f"• Category: {session.draft.category}\n"
                    f"• Date: {session.draft.date}\n\n"
                    f"Is this correct? Reply 'yes' to save to the database, 'cancel' to discard, "
                    f"or tell me what to change (e.g., 'change category to Groceries' or 'amount 25')."
                ),
                status=session.status,
                draft=session.draft,
                action_required="confirm",
            )

        # 2. State: IDLE
        extraction = self.llm.parse_user_message(text)

        # If user explicitly cancels or confirms while idle
        if extraction.intent == "cancel":
            return ChatResponse(
                session_id=session.session_id,
                message="No pending expense to cancel. Tell me about an expense to add!",
                status="idle",
                draft=None,
                action_required="none",
            )

        if extraction.intent == "confirm":
            return ChatResponse(
                session_id=session.session_id,
                message="No pending expense to confirm. What expense would you like to record?",
                status="idle",
                draft=None,
                action_required="none",
            )

        # Check if user message didn't contain an expense
        if extraction.amount is None:
            if extraction.description and len(extraction.description) > 2:
                # Partial info - got description, missing amount
                session.draft = ExpenseDraft(
                    description=extraction.description,
                    amount=0.01,  # temporary placeholder
                    category=extraction.category or "Other",
                    date=extraction.date or datetime.now().strftime("%Y-%m-%d"),
                )
                session.status = "awaiting_confirmation"
                return ChatResponse(
                    session_id=session.session_id,
                    message=f"I got the expense '{extraction.description}', but how much did it cost?",
                    status="awaiting_confirmation",
                    draft=None,
                    action_required="clarify",
                )
            else:
                return ChatResponse(
                    session_id=session.session_id,
                    message=(
                        "👋 Hello! I can help you record expenses into the database.\n\n"
                        "Try telling me something like:\n"
                        "• 'Spent 45 on groceries yesterday'\n"
                        "• 'Paid $12.50 for coffee at Starbucks'\n"
                        "• 'Uber ride $24 today'"
                    ),
                    status="idle",
                    draft=None,
                    action_required="none",
                )

        # All fields extracted -> Create Draft and move to AWAITING_CONFIRMATION
        session.draft = ExpenseDraft(
            description=extraction.description or "Expense",
            amount=extraction.amount,
            category=extraction.category or "Other",
            date=extraction.date or datetime.now().strftime("%Y-%m-%d"),
        )
        session.status = "awaiting_confirmation"
        return self._build_confirmation_prompt(session)

    def _apply_update(self, session: UserSession, field: str, new_value: any) -> ChatResponse:
        if not session.draft:
            return self.cancel_draft(session.session_id)

        field_lower = field.lower()
        if "amount" in field_lower or "cost" in field_lower or "price" in field_lower:
            try:
                if isinstance(new_value, (int, float)):
                    session.draft.amount = float(new_value)
                else:
                    import re
                    m = re.search(r"(\d+(?:\.\d+)?)", str(new_value))
                    if m:
                        session.draft.amount = float(m.group(1))
            except Exception as e:
                logger.warning("Could not parse new amount: %s", e)
        elif "date" in field_lower:
            session.draft.date = self.llm._resolve_date(str(new_value), datetime.now())
        elif "cat" in field_lower:
            matched = self.llm._match_category(str(new_value))
            session.draft.category = matched or str(new_value).capitalize()
        elif "desc" in field_lower:
            session.draft.description = str(new_value).capitalize()

        return ChatResponse(
            session_id=session.session_id,
            message=(
                f"Updated! Here is your revised expense draft:\n"
                f"• Description: **{session.draft.description}**\n"
                f"• Amount: **${session.draft.amount:.2f}**\n"
                f"• Category: **{session.draft.category}**\n"
                f"• Date: **{session.draft.date}**\n\n"
                f"Is this correct? Reply 'yes' to save to the database, or suggest any other updates."
            ),
            status="awaiting_confirmation",
            draft=session.draft,
            action_required="confirm",
        )

    def _build_confirmation_prompt(self, session: UserSession) -> ChatResponse:
        draft = session.draft
        return ChatResponse(
            session_id=session.session_id,
            message=(
                f"I extracted the following expense:\n"
                f"• Description: **{draft.description}**\n"
                f"• Amount: **${draft.amount:.2f}**\n"
                f"• Category: **{draft.category}**\n"
                f"• Date: **{draft.date}**\n\n"
                f"Is this correct? Reply **'yes'** to insert into the database, "
                f"or tell me what to update (e.g. 'change category to Groceries' or 'change date to yesterday')."
            ),
            status="awaiting_confirmation",
            draft=draft,
            action_required="confirm",
        )

    async def confirm_draft(self, session_id: str) -> ChatResponse:
        session = self.get_or_create_session(session_id)
        if not session.draft:
            return ChatResponse(
                session_id=session.session_id,
                message="There is no pending expense to save. Tell me about an expense first!",
                status="idle",
                draft=None,
                action_required="none",
            )

        saved_draft = session.draft
        try:
            expense_id = await insert_expense_to_db(saved_draft)
            session.draft = None
            session.status = "idle"

            return ChatResponse(
                session_id=session.session_id,
                message=(
                    f"✅ **Expense successfully saved to the database!** (ID #{expense_id})\n"
                    f"• {saved_draft.description} — ${saved_draft.amount:.2f} "
                    f"({saved_draft.category}) on {saved_draft.date}\n\n"
                    f"What other expense would you like to record?"
                ),
                status="saved",
                draft=None,
                action_required="none",
                saved_expense_id=expense_id,
            )
        except Exception as e:
            logger.error("Failed to insert expense into DB: %s", e)
            return ChatResponse(
                session_id=session.session_id,
                message=(
                    f"⚠️ Could not save expense to the core database: {e}\n"
                    f"Your draft is still retained. Reply 'yes' to retry when the core backend is reachable."
                ),
                status="awaiting_confirmation",
                draft=saved_draft,
                action_required="confirm",
            )

    def cancel_draft(self, session_id: str) -> ChatResponse:
        session = self.get_or_create_session(session_id)
        session.draft = None
        session.status = "idle"
        return ChatResponse(
            session_id=session.session_id,
            message="Expense draft has been cancelled. What else would you like to record?",
            status="cancelled",
            draft=None,
            action_required="none",
        )

    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
