import logging
import re
from datetime import datetime, timedelta

from app.schemas import ExpenseDraft, ToolCall, ToolResult
from app.expense_client import (
    fetch_expense_summary,
    insert_expense_to_db,
    normalize_iso_date,
    refresh_exchange_rates_in_backend,
)
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
    {
        "type": "function",
        "function": {
            "name": "refresh_exchange_rates",
            "description": "Refreshes and gets the latest live currency exchange rates from market feeds (USD, INR, EUR, JPY, GBP, CNY). Use when the user asks to update or check exchange rates or currency conversions.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_expense_summary",
            "description": "Queries and summarizes expenses from the database based on filters like time period (month, year, week, or relative like 'this_month', 'last_month', 'today'), category/categories, and target currency (USD, INR, EUR, JPY, GBP, CNY).",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Calendar year to filter by (e.g. 2026)",
                    },
                    "month": {
                        "type": "integer",
                        "description": "Month number to filter by (1-12)",
                    },
                    "week": {
                        "type": "integer",
                        "description": "ISO week number (1-53)",
                    },
                    "relative_period": {
                        "type": "string",
                        "enum": [
                            "today",
                            "yesterday",
                            "this_week",
                            "last_week",
                            "this_month",
                            "last_month",
                            "this_year",
                            "last_year",
                        ],
                        "description": "Relative time period shortcut",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of categories to filter (e.g. ['Online', 'Food'])",
                    },
                    "currency": {
                        "type": "string",
                        "description": "Target currency code for summary total (e.g. 'USD', 'INR', 'EUR', 'JPY', 'GBP', 'CNY')",
                    },
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
    reference_date: datetime | None = None,
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
    current_draft: ExpenseDraft | None,
    reference_date: datetime | None = None,
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
    reference_date: datetime | None = None,
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


def tool_cancel_draft(reason: str | None = None) -> ToolResult:
    """Executes cancel_draft function."""
    msg = "🚫 Discarded the expense draft. What else can I help you with?"
    if reason:
        msg = f"🚫 Cancelled: {reason}."
    return ToolResult(
        status="cancelled",
        message=msg,
        action_required="none",
    )


async def tool_refresh_exchange_rates() -> ToolResult:
    """Refreshes live currency exchange rates via the core backend."""
    currencies = await refresh_exchange_rates_in_backend()
    if currencies:
        lines = []
        for c in currencies:
            code = c.get("code", "")
            sym = c.get("symbol", "")
            rate = float(c.get("exchange_rate", 1.0))
            lines.append(f"• **{code}** ({sym}): {rate:.4f} per USD")
        rates_str = "\n".join(lines)
        return ToolResult(
            status="idle",
            message=f"✅ Successfully refreshed live currency exchange rates:\n\n{rates_str}",
            action_required="none",
        )
    return ToolResult(
        status="idle",
        message="⚠️ Could not connect to core backend to refresh exchange rates. Please ensure backend is running.",
        action_required="none",
    )


async def tool_query_expense_summary(
    year: int | None = None,
    month: int | None = None,
    week: int | None = None,
    relative_period: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    categories: list[str] | None = None,
    currency: str = "USD",
    reference_date: datetime | None = None,
) -> ToolResult:
    """Queries expense summary and details from core database."""
    ref_date = reference_date or datetime.now()

    resolved_year = year
    resolved_month = month
    resolved_week = week
    resolved_start_date = start_date
    resolved_end_date = end_date

    period_desc = ""
    if relative_period:
        rel = relative_period.lower().strip()
        if rel == "today":
            resolved_start_date = ref_date.strftime("%Y-%m-%d")
            resolved_end_date = resolved_start_date
            period_desc = "today"
        elif rel == "yesterday":
            y = ref_date - timedelta(days=1)
            resolved_start_date = y.strftime("%Y-%m-%d")
            resolved_end_date = resolved_start_date
            period_desc = "yesterday"
        elif rel == "this_week":
            start = ref_date - timedelta(days=ref_date.weekday())
            end = start + timedelta(days=6)
            resolved_start_date = start.strftime("%Y-%m-%d")
            resolved_end_date = end.strftime("%Y-%m-%d")
            period_desc = "this week"
        elif rel == "last_week":
            start = ref_date - timedelta(days=ref_date.weekday() + 7)
            end = start + timedelta(days=6)
            resolved_start_date = start.strftime("%Y-%m-%d")
            resolved_end_date = end.strftime("%Y-%m-%d")
            period_desc = "last week"
        elif rel == "this_month":
            resolved_year = ref_date.year
            resolved_month = ref_date.month
            period_desc = ref_date.strftime("%B %Y")
        elif rel == "last_month":
            if ref_date.month == 1:
                resolved_year = ref_date.year - 1
                resolved_month = 12
            else:
                resolved_year = ref_date.year
                resolved_month = ref_date.month - 1
            last_m_dt = datetime(resolved_year, resolved_month, 1)
            period_desc = last_m_dt.strftime("%B %Y")
        elif rel == "this_year":
            resolved_year = ref_date.year
            period_desc = str(resolved_year)
        elif rel == "last_year":
            resolved_year = ref_date.year - 1
            period_desc = str(resolved_year)

    if not period_desc:
        if resolved_month and resolved_year:
            try:
                period_desc = datetime(resolved_year, resolved_month, 1).strftime("%B %Y")
            except Exception:
                period_desc = f"{resolved_year}-{resolved_month:02d}"
        elif resolved_month:
            try:
                period_desc = datetime(2000, resolved_month, 1).strftime("%B")
            except Exception:
                period_desc = f"Month {resolved_month}"
        elif resolved_year:
            period_desc = str(resolved_year)
        elif resolved_week:
            period_desc = f"Week {resolved_week}"
        elif resolved_start_date and resolved_end_date:
            if resolved_start_date == resolved_end_date:
                period_desc = resolved_start_date
            else:
                period_desc = f"{resolved_start_date} to {resolved_end_date}"
        else:
            period_desc = "all time"

    cat_list = [c.strip() for c in categories] if categories else None
    summary = await fetch_expense_summary(
        year=resolved_year,
        month=resolved_month,
        week=resolved_week,
        start_date=resolved_start_date,
        end_date=resolved_end_date,
        categories=cat_list,
        currency=currency or "USD",
    )

    if summary is None:
        return ToolResult(
            status="idle",
            message="⚠️ Could not connect to the backend database to retrieve expense summary.",
            action_required="none",
        )

    total = float(summary.get("total", 0.0))
    count = int(summary.get("count", 0))
    curr_code = summary.get("currency", currency or "USD")
    sym = summary.get("currency_symbol", "$")
    expenses = summary.get("expenses", [])

    cat_desc = f" for category **{', '.join(cat_list)}**" if cat_list else ""
    lines = [
        f"📊 **Expense Summary ({period_desc}){cat_desc}**:",
        f"• **Total Spent**: {sym}{total:,.2f} {curr_code}",
        f"• **Transactions**: {count}",
    ]

    if count > 0:
        lines.append("\n**Expenses:**")
        for exp in expenses[:10]:
            desc = exp.get("description", "Expense")
            amt = float(exp.get("amount", 0.0))
            cat = exp.get("category", "Other")
            d = exp.get("date", "")
            lines.append(f"• `{d}`: **{desc}** ({cat}) — {sym}{amt:,.2f}")
        if count > 10:
            lines.append(f"• *... and {count - 10} more expenses.*")
    else:
        lines.append("\n*No expenses found matching the criteria.*")

    return ToolResult(
        status="idle",
        message="\n".join(lines),
        action_required="none",
    )


async def execute_tool(
    tool_call: ToolCall,
    current_draft: ExpenseDraft | None = None,
    reference_date: datetime | None = None,
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
            description=args.get(
                "description", current_draft.description if current_draft else "Expense"
            ),
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
    elif t_name == "refresh_exchange_rates":
        return await tool_refresh_exchange_rates()
    elif t_name == "query_expense_summary":
        raw_cats = args.get("categories")
        if isinstance(raw_cats, str):
            cats = [raw_cats]
        elif isinstance(raw_cats, list):
            cats = raw_cats
        else:
            cats = None
        return await tool_query_expense_summary(
            year=args.get("year"),
            month=args.get("month"),
            week=args.get("week"),
            relative_period=args.get("relative_period"),
            start_date=args.get("start_date"),
            end_date=args.get("end_date"),
            categories=cats,
            currency=args.get("currency", "USD"),
            reference_date=reference_date,
        )
    else:
        logger.warning("Unknown tool call: %s", t_name)
        return ToolResult(
            status="idle",
            message=f"Unknown tool '{t_name}'.",
            action_required="none",
        )
