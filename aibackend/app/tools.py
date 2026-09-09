import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.schemas import ExpenseDraft, ToolCall, ToolResult
from app.expense_client import insert_expense_to_db, normalize_iso_date
from app.config import STANDARD_CATEGORIES

logger = logging.getLogger("aibackend.tools")

# Formal JSON Schema for function calling / tool use
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "draft_expense",
            "description": "Extracts expense information (description, amount, category, date) and creates a draft requiring user confirmation before saving to database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Short name or merchant of the expense (e.g. 'Coffee at Starbucks', 'Uber ride', 'Groceries')",
                    },
                    "amount": {
                        "type": "number",
                        "description": "The numerical expense cost (must be greater than 0)",
                    },
                    "category": {
                        "type": "string",
                        "enum": STANDARD_CATEGORIES,
                        "description": "Category classifying the expense",
                    },
                    "date": {
                        "type": "string",
                        "description": "The date of the expense in ISO format YYYY-MM-DD or relative like 'today', 'yesterday'",
                    },
                },
                "required": ["description", "amount", "category", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_draft_field",
            "description": "Updates or modifies a specific field on the currently pending draft expense before confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "enum": ["amount", "category", "date", "description"],
                        "description": "The field name to update",
                    },
                    "value": {
                        "type": "string",
                        "description": "The new value to assign to the field",
                    },
                },
                "required": ["field", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "commit_expense",
            "description": "Explicitly commits and persists the confirmed expense directly into the core database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "amount": {"type": "number"},
                    "category": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["description", "amount", "category", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_clarification",
            "description": "Prompts the user for missing details when an expense statement is ambiguous or incomplete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "missing_field": {
                        "type": "string",
                        "description": "The field that is missing or unclear (e.g. 'amount', 'category')",
                    },
                    "question": {
                        "type": "string",
                        "description": "The helpful question to ask the user",
                    },
                },
                "required": ["missing_field", "question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_draft",
            "description": "Cancels and discards the active pending expense draft.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for cancelling the draft",
                    }
                },
            },
        },
    },
]


def tool_draft_expense(
    description: str,
    amount: float,
    category: str,
    date: str,
    reference_date: Optional[datetime] = None,
) -> ToolResult:
    """Executes draft_expense function."""
    normalized_date = normalize_iso_date(date, reference_date)

    # Validate / match category
    matched_cat = "Other"
    for sc in STANDARD_CATEGORIES:
        if sc.lower() == category.lower():
            matched_cat = sc
            break

    draft = ExpenseDraft(
        description=description.strip() or "Expense",
        amount=float(amount),
        category=matched_cat,
        date=normalized_date,
    )

    return ToolResult(
        status="awaiting_confirmation",
        message=(
            f"I have prepared an expense draft for **{draft.description}**:\n"
            f"• **Amount**: ${draft.amount:.2f}\n"
            f"• **Category**: {draft.category}\n"
            f"• **Date**: {draft.date}\n\n"
            "Would you like me to save this to your database? Or reply to update any field."
        ),
        draft=draft,
        action_required="confirm",
    )


def tool_update_draft_field(
    field: str,
    value: str,
    current_draft: Optional[ExpenseDraft],
    reference_date: Optional[datetime] = None,
) -> ToolResult:
    """Executes update_draft_field function."""
    if not current_draft:
        return ToolResult(
            status="idle",
            message="There is no active draft to update. Please tell me about an expense first.",
            action_required="none",
        )

    field_clean = field.lower().strip()
    val_clean = str(value).strip()

    updated = current_draft.model_copy()

    if field_clean == "amount":
        m = re.search(r"(\d+(?:\.\d+)?)", val_clean)
        if m:
            updated.amount = float(m.group(1))
    elif field_clean == "category":
        matched = "Other"
        for sc in STANDARD_CATEGORIES:
            if sc.lower() == val_clean.lower():
                matched = sc
                break
        updated.category = matched
    elif field_clean == "date":
        updated.date = normalize_iso_date(val_clean, reference_date)
    elif field_clean == "description":
        updated.description = val_clean.strip("'\"")

    return ToolResult(
        status="awaiting_confirmation",
        message=(
            f"Updated **{field_clean}** to `{getattr(updated, field_clean, val_clean)}`.\n"
            f"• **{updated.description}** | ${updated.amount:.2f} | {updated.category} | {updated.date}\n\n"
            "Does this look correct to save to DB?"
        ),
        draft=updated,
        action_required="confirm",
    )


async def tool_commit_expense(
    description: str,
    amount: float,
    category: str,
    date: str,
    reference_date: Optional[datetime] = None,
) -> ToolResult:
    """Executes commit_expense function to persist expense to core DB."""
    normalized_date = normalize_iso_date(date, reference_date)
    draft = ExpenseDraft(
        description=description,
        amount=amount,
        category=category,
        date=normalized_date,
    )
    expense_id = await insert_expense_to_db(draft)
    if expense_id:
        return ToolResult(
            status="saved",
            message=f"✅ Saved expense #{expense_id} (**{draft.description}** for ${draft.amount:.2f}) to your database!",
            draft=draft,
            action_required="none",
            saved_expense_id=expense_id,
        )
    return ToolResult(
        status="awaiting_confirmation",
        message="⚠️ Failed to connect to the core backend database. Please ensure backend is running.",
        draft=draft,
        action_required="confirm",
    )


def tool_ask_clarification(missing_field: str, question: str) -> ToolResult:
    """Executes ask_clarification function."""
    return ToolResult(
        status="idle",
        message=question,
        action_required="clarify",
    )


def tool_cancel_draft(reason: Optional[str] = None) -> ToolResult:
    """Executes cancel_draft function."""
    msg = "🚫 Discarded the expense draft. What else can I help you with?"
    if reason:
        msg = f"🚫 Cancelled: {reason}."
    return ToolResult(
        status="cancelled",
        message=msg,
        action_required="none",
    )


async def execute_tool(
    tool_call: ToolCall,
    current_draft: Optional[ExpenseDraft] = None,
    reference_date: Optional[datetime] = None,
) -> ToolResult:
    """
    Dispatches tool call to corresponding Python function.
    """
    t_name = tool_call.tool
    args = tool_call.arguments

    logger.info("Executing tool '%s' with arguments %s", t_name, args)

    if t_name == "draft_expense":
        return tool_draft_expense(
            description=args.get("description", "Expense"),
            amount=float(args.get("amount", 0.0)),
            category=args.get("category", "Other"),
            date=args.get("date", "today"),
            reference_date=reference_date,
        )
    elif t_name == "update_draft_field":
        return tool_update_draft_field(
            field=args.get("field", "amount"),
            value=str(args.get("value", "")),
            current_draft=current_draft,
            reference_date=reference_date,
        )
    elif t_name == "commit_expense":
        return await tool_commit_expense(
            description=args.get("description", current_draft.description if current_draft else "Expense"),
            amount=float(args.get("amount", current_draft.amount if current_draft else 0.0)),
            category=args.get("category", current_draft.category if current_draft else "Other"),
            date=args.get("date", current_draft.date if current_draft else "today"),
            reference_date=reference_date,
        )
    elif t_name == "ask_clarification":
        return tool_ask_clarification(
            missing_field=args.get("missing_field", "general"),
            question=args.get("question", "Could you provide more details about this expense?"),
        )
    elif t_name == "cancel_draft":
        return tool_cancel_draft(reason=args.get("reason"))
    else:
        logger.warning("Unknown tool call: %s", t_name)
        return ToolResult(
            status="idle",
            message=f"Unknown tool '{t_name}'.",
            action_required="none",
        )
