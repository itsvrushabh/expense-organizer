import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import AIMODEL_URL
from app.schemas import ExpenseDraft, ToolCall
from app.tools import TOOLS_SCHEMA

logger = logging.getLogger("aibackend.model_client")

CATEGORY_KEYWORDS = {
    "Food": [
        "coffee",
        "tea",
        "lunch",
        "dinner",
        "breakfast",
        "burger",
        "pizza",
        "restaurant",
        "cafe",
        "snack",
        "beer",
        "meal",
        "food",
    ],
    "Groceries": [
        "grocery",
        "groceries",
        "supermarket",
        "walmart",
        "dmart",
        "vegetables",
        "fruits",
        "milk",
        "bread",
        "costco",
    ],
    "Transport": [
        "uber",
        "ola",
        "lyft",
        "taxi",
        "bus",
        "train",
        "metro",
        "subway",
        "fuel",
        "petrol",
        "gas",
        "diesel",
        "parking",
    ],
    "Shopping": [
        "amazon",
        "shoes",
        "clothes",
        "shirt",
        "pants",
        "dress",
        "mall",
        "shopping",
        "electronics",
    ],
    "Entertainment": ["movie", "cinema", "netflix", "spotify", "concert", "game", "steam"],
    "Utilities": [
        "electricity",
        "water",
        "internet",
        "wifi",
        "broadband",
        "rent",
        "recharge",
        "phone bill",
    ],
    "Health": ["doctor", "medicine", "pharmacy", "hospital", "clinic", "dental"],
    "Travel": ["flight", "hotel", "airbnb", "trip", "vacation"],
}


class ModelClient:
    """
    HTTP Client communicating with the dedicated aimodel container (port 8002).
    Dispatches tool-calling prompts to the LLM model server and parses tool invocations.
    Falls back gracefully to intelligent heuristics if the model server is offline or fails.
    """

    def __init__(self, aimodel_url: str | None = None):
        self.aimodel_url = (aimodel_url or AIMODEL_URL).rstrip("/")

    async def check_aimodel_health(self) -> dict[str, Any]:
        url = f"{self.aimodel_url}/health"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return {"status": "reachable", "details": resp.json()}
                return {"status": "unreachable", "status_code": resp.status_code}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    async def select_tool(
        self,
        user_message: str,
        current_draft: ExpenseDraft | None = None,
        reference_date: datetime | None = None,
    ) -> ToolCall:
        ref_date = reference_date or datetime.now()
        cleaned = user_message.strip().lower()

        # Direct shortcuts for confirmation / cancel when draft exists
        if current_draft is not None:
            if cleaned in [
                "yes",
                "y",
                "confirm",
                "correct",
                "looks good",
                "save",
                "save to db",
                "proceed",
                "sure",
            ]:
                return ToolCall(
                    tool="commit_expense",
                    arguments={
                        "description": current_draft.description,
                        "amount": current_draft.amount,
                        "category": current_draft.category,
                        "date": current_draft.date,
                    },
                )
            if cleaned in ["no", "cancel", "discard", "wrong", "stop", "abort"]:
                return ToolCall(tool="cancel_draft", arguments={})

        # Fast path: deterministic detection for summary queries and exchange rates
        if current_draft is None:
            fast_tool = self._detect_query_or_rate_tool(user_message, ref_date)
            if fast_tool:
                return fast_tool

        # Try calling the dedicated aimodel server
        try:
            tool_call = await self._call_aimodel_server(user_message, current_draft, ref_date)
            if tool_call:
                # If the model server mistakenly asked for clarification when all fields are present,
                # check if heuristic tool selector can construct a valid draft_expense
                if tool_call.tool == "ask_clarification":
                    h_call = self._heuristic_select_tool(user_message, current_draft, ref_date)
                    if h_call.tool == "draft_expense":
                        return h_call
                return tool_call
        except Exception as e:
            logger.warning(
                "aimodel server call failed (%s). Falling back to heuristic tool selection.", e
            )

        # Fallback to intelligent heuristic tool selector
        return self._heuristic_select_tool(user_message, current_draft, ref_date)

    async def _call_aimodel_server(
        self,
        user_message: str,
        current_draft: ExpenseDraft | None,
        ref_date: datetime,
    ) -> ToolCall | None:
        date_str = ref_date.strftime("%Y-%m-%d")
        tools_str = json.dumps(TOOLS_SCHEMA, indent=2)

        system_prompt = (
            f"You are an AI expense tracking assistant. Today's date is {date_str}.\n"
            f"You have access to the following tools for function calling:\n{tools_str}\n\n"
            "Given the user message and current draft, select the appropriate tool and output a single JSON object in the form:\n"
            '{"tool": "<tool_name>", "arguments": {<arguments>}}\n'
            "Only output the JSON object, nothing else."
        )

        user_content = user_message
        if current_draft:
            user_content += (
                f"\n[Active Draft Pending Confirmation: {current_draft.model_dump_json()}]"
            )

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "max_tokens": 256,
            "response_format": {"type": "json_object"},
        }

        url = f"{self.aimodel_url}/v1/chat/completions"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                # Parse tool call JSON from content
                m = re.search(r"\{.*\}", content, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    t_name = parsed.get("tool", "draft_expense")
                    args = parsed.get("arguments", {})
                    return ToolCall(tool=t_name, arguments=args)
        return None

    def _detect_query_or_rate_tool(self, text: str, ref_date: datetime) -> ToolCall | None:
        lower = text.lower().strip()

        # 1. Check live exchange rate inquiries
        if any(
            kw in lower
            for kw in [
                "exchange rate",
                "exchange rates",
                "currency rates",
                "currency rate",
                "refresh rate",
                "refresh rates",
                "live rate",
                "live rates",
                "refresh currencies",
                "refresh exchange",
            ]
        ):
            return ToolCall(tool="refresh_exchange_rates", arguments={})

        # 2. Check expense summary / query inquiries
        summary_triggers = [
            "how much did i spend",
            "how much have i spent",
            "how much spent",
            "what did i spend",
            "what are my expenses",
            "what are my total expenses",
            "show my expenses",
            "show expenses",
            "list expenses",
            "get expenses",
            "summary of expenses",
            "expense summary",
            "total expenses",
            "total spent",
            "spending summary",
            "how much i spent",
            "breakdown of expenses",
        ]
        is_summary_query = any(trigger in lower for trigger in summary_triggers)
        if (
            not is_summary_query
            and (lower.startswith("how much") or lower.startswith("what is my total"))
            and not re.search(r"\b(?:cost|spent|paid)\s+[$€£₹]?\d", lower)
        ):
            is_summary_query = True

        if is_summary_query:
            month_map = {
                "january": 1,
                "jan": 1,
                "february": 2,
                "feb": 2,
                "march": 3,
                "mar": 3,
                "april": 4,
                "apr": 4,
                "may": 5,
                "june": 6,
                "jun": 6,
                "july": 7,
                "jul": 7,
                "august": 8,
                "aug": 8,
                "september": 9,
                "sep": 9,
                "sept": 9,
                "october": 10,
                "oct": 10,
                "november": 11,
                "nov": 11,
                "december": 12,
                "dec": 12,
            }
            detected_month = None
            for m_name, m_num in month_map.items():
                if re.search(rf"\b{m_name}\b", lower):
                    detected_month = m_num
                    break

            detected_year = None
            ym = re.search(r"\b(20\d{2})\b", lower)
            if ym:
                detected_year = int(ym.group(1))
            elif detected_month is not None:
                detected_year = ref_date.year

            detected_rel = None
            if "today" in lower:
                detected_rel = "today"
            elif "yesterday" in lower:
                detected_rel = "yesterday"
            elif "this week" in lower:
                detected_rel = "this_week"
            elif "last week" in lower:
                detected_rel = "last_week"
            elif "this month" in lower:
                detected_rel = "this_month"
            elif "last month" in lower:
                detected_rel = "last_month"
            elif "this year" in lower:
                detected_rel = "this_year"
            elif "last year" in lower:
                detected_rel = "last_year"

            detected_curr = "USD"
            if any(c in lower for c in ["inr", "rupee", "rupees", "₹", "rs"]):
                detected_curr = "INR"
            elif any(c in lower for c in ["eur", "euro", "euros", "€"]):
                detected_curr = "EUR"
            elif any(c in lower for c in ["jpy", "yen", "¥"]):
                detected_curr = "JPY"
            elif any(c in lower for c in ["gbp", "pound", "pounds", "£"]):
                detected_curr = "GBP"
            elif any(c in lower for c in ["cny", "yuan", "rmb"]):
                detected_curr = "CNY"

            detected_cats = []
            known_cats = [
                "Food",
                "Groceries",
                "Transport",
                "Shopping",
                "Entertainment",
                "Utilities",
                "Health",
                "Travel",
                "Online",
                "Other",
            ]
            for c in known_cats:
                if re.search(rf"\b{c.lower()}\b", lower):
                    detected_cats.append(c)

            query_args: dict[str, Any] = {"currency": detected_curr}
            if detected_year:
                query_args["year"] = detected_year
            if detected_month:
                query_args["month"] = detected_month
            if detected_rel:
                query_args["relative_period"] = detected_rel
            if detected_cats:
                query_args["categories"] = detected_cats

            return ToolCall(tool="query_expense_summary", arguments=query_args)

        return None

    def _heuristic_select_tool(
        self,
        text: str,
        current_draft: ExpenseDraft | None,
        ref_date: datetime,
    ) -> ToolCall:
        lower = text.lower().strip()

        # 1. Update draft field if draft is active
        if current_draft:
            update_match = re.search(
                r"(?:change|update|set|make)\s+(date|category|amount|description)\s+(?:to|=)?\s*(.+)",
                lower,
                re.IGNORECASE,
            )
            if update_match:
                field = update_match.group(1).lower()
                val = update_match.group(2).strip().strip("'\".,")
                return ToolCall(
                    tool="update_draft_field",
                    arguments={"field": field, "value": val},
                )

        # 2. Check live exchange rates or expense summary inquiries
        detected_tool = self._detect_query_or_rate_tool(text, ref_date)
        if detected_tool:
            return detected_tool

        # 3. Extract Amount
        amount = None
        patterns = [
            r"[$€£₹]\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:usd|inr|eur|gbp|dollars|bucks|rs|rupees)",
            r"(?:spent|paid|for|cost)\s+(\d+(?:\.\d+)?)",
            r"\b(\d+(?:\.\d+)?)\b",
        ]
        for pat in patterns:
            m = re.search(pat, lower)
            if m:
                try:
                    val = float(m.group(1))
                    if 0 < val < 100000000:
                        amount = val
                        break
                except ValueError:
                    pass

        # 3. Extract Date
        date_str = ref_date.strftime("%Y-%m-%d")
        if "yesterday" in lower:
            date_str = (ref_date - timedelta(days=1)).strftime("%Y-%m-%d")
        elif "tomorrow" in lower:
            date_str = (ref_date + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            iso = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", lower)
            if iso:
                date_str = iso.group(1)

        # 4. Extract Category
        category = "Other"
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", lower):
                    category = cat
                    break
            if category != "Other":
                break

        # 5. Extract Description
        cleaned = text
        cleaned = re.sub(
            r"^(?:i\s+)?(?:spent|paid|bought|got|purchased)\s+", "", cleaned, flags=re.IGNORECASE
        )
        if amount is not None:
            amt_s = str(int(amount) if amount.is_integer() else amount)
            cleaned = re.sub(
                rf"[$€£₹]?\s*{re.escape(amt_s)}(?:\.\d+)?\s*(?:dollars|usd|bucks|rs|rupees|inr)?",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            cleaned = re.sub(rf"\bfor\s+{re.escape(amt_s)}\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(
            r"\b(today|yesterday|tomorrow|\d{4}-\d{2}-\d{2})\b", "", cleaned, flags=re.IGNORECASE
        )
        cleaned = re.sub(r"^(?:on|for|at)\s+", "", cleaned.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+(?:on|for|at)$", "", cleaned.strip(), flags=re.IGNORECASE)
        description = " ".join(cleaned.split()).strip()

        if not description:
            description = "Expense"
        else:
            description = description[:100].capitalize()

        # Missing amount check -> call ask_clarification tool
        if amount is None:
            if description and len(description) > 2 and description != "Expense":
                return ToolCall(
                    tool="ask_clarification",
                    arguments={
                        "missing_field": "amount",
                        "question": f"I found the expense '{description}', but how much did it cost?",
                    },
                )
            return ToolCall(
                tool="ask_clarification",
                arguments={
                    "missing_field": "all",
                    "question": (
                        "👋 Hello! Tell me about an expense, for example:\n"
                        "• 'Spent $45 on groceries today'\n"
                        "• 'Paid 12.50 for coffee at Starbucks'\n"
                        "• 'Uber ride $28 yesterday'"
                    ),
                },
            )

        # Call draft_expense tool
        return ToolCall(
            tool="draft_expense",
            arguments={
                "description": description,
                "amount": amount,
                "category": category,
                "date": date_str,
            },
        )
