import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Any

from app.config import MODEL_PATH, STANDARD_CATEGORIES
from app.schemas import LLMExtractionResult

logger = logging.getLogger(__name__)

# Category mapping keywords
CATEGORY_KEYWORDS = {
    "Food": ["coffee", "tea", "lunch", "dinner", "breakfast", "burger", "pizza", "restaurant", "cafe", "snack", "beer", "meal", "food"],
    "Groceries": ["grocery", "groceries", "supermarket", "walmart", "dmart", "vegetables", "fruits", "milk", "bread"],
    "Transport": ["uber", "ola", "lyft", "taxi", "bus", "train", "metro", "subway", "fuel", "petrol", "gas", "diesel", "parking"],
    "Shopping": ["amazon", "shoes", "clothes", "shirt", "pants", "dress", "mall", "shopping", "electronics"],
    "Entertainment": ["movie", "cinema", "netflix", "spotify", "concert", "game", "steam"],
    "Utilities": ["electricity", "water", "internet", "wifi", "broadband", "rent", "recharge", "phone bill"],
    "Health": ["doctor", "medicine", "pharmacy", "hospital", "clinic", "dental"],
    "Travel": ["flight", "hotel", "airbnb", "trip", "vacation"],
}


class LLMEngine:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or MODEL_PATH
        self.llm = None
        self.model_loaded = False
        self._initialize_model()

    def _initialize_model(self):
        if not os.path.exists(self.model_path):
            logger.warning(
                "Model file not found at '%s'. Operating in intelligent heuristic fallback mode.",
                self.model_path,
            )
            self.model_loaded = False
            return

        try:
            from llama_cpp import Llama  # type: ignore

            logger.info("Loading GGUF model from %s...", self.model_path)
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )
            self.model_loaded = True
            logger.info("Successfully loaded GGUF model into memory.")
        except Exception as e:
            logger.error("Failed to load Llama model from %s: %s", self.model_path, e)
            self.model_loaded = False

    def parse_user_message(
        self,
        user_message: str,
        current_draft: Optional[dict] = None,
        reference_date: Optional[datetime] = None,
    ) -> LLMExtractionResult:
        """
        Parse user message into structured extraction result using either
        GGUF LLM inference or rule-based fallback.
        """
        ref_date = reference_date or datetime.now()

        # Check for explicit short confirmations / cancellations first
        cleaned = user_message.strip().lower()
        if cleaned in ["yes", "y", "confirm", "correct", "looks good", "save it", "save to db", "ok", "sure", "proceed"]:
            return LLMExtractionResult(intent="confirm")
        if cleaned in ["no", "cancel", "discard", "wrong", "stop", "abort", "nevermind"]:
            return LLMExtractionResult(intent="cancel")

        # If model is loaded, run LLM prompt
        if self.model_loaded and self.llm is not None:
            try:
                return self._parse_with_llm(user_message, current_draft, ref_date)
            except Exception as e:
                logger.warning("LLM generation failed: %s. Falling back to rule-based parser.", e)

        # Fallback to heuristic parser
        return self._heuristic_parse(user_message, current_draft, ref_date)

    def _parse_with_llm(
        self,
        user_message: str,
        current_draft: Optional[dict],
        ref_date: datetime,
    ) -> LLMExtractionResult:
        date_str = ref_date.strftime("%Y-%m-%d")
        categories_str = ", ".join(STANDARD_CATEGORIES)

        system_prompt = (
            f"You are an expense tracking assistant. Today's date is {date_str}.\n"
            f"Available categories: [{categories_str}].\n"
            "Analyze the user message and output a single valid JSON object with:\n"
            "- intent: 'add_expense' | 'update_field' | 'confirm' | 'cancel' | 'chat'\n"
            "- description: short string describing expense\n"
            "- amount: positive float\n"
            "- category: one of the available categories\n"
            "- date: YYYY-MM-DD string\n"
            "- field_to_update: 'description' | 'amount' | 'category' | 'date' (if user asks to update)\n"
            "- new_value: string or float of the new value (if updating)\n"
            "- missing_fields: list of missing fields among ['amount', 'description']\n"
            "Only output the raw JSON object, no explanation."
        )

        user_content = user_message
        if current_draft:
            user_content += f"\n[Active draft pending confirmation: {json.dumps(current_draft)}]"

        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=256,
            response_format={"type": "json_object"},
        )

        content = response["choices"][0]["message"]["content"]
        data = json.loads(content)
        return LLMExtractionResult(**data)

    def _heuristic_parse(
        self,
        text: str,
        current_draft: Optional[dict],
        ref_date: datetime,
    ) -> LLMExtractionResult:
        """
        Robust rule-based parser to guarantee reliable extraction even without weights loaded.
        """
        lower = text.lower().strip()

        # 1. Check for update instructions if draft is present
        if current_draft:
            # Pattern: (change|update|set|make) (date|category|amount|description) (to|=) <val>
            update_match = re.search(
                r"(?:change|update|set|make)\s+(date|category|amount|description)\s+(?:to|=)?\s*(.+)",
                lower,
                re.IGNORECASE,
            )
            if update_match:
                field = update_match.group(1).lower()
                val_raw = update_match.group(2).strip().strip("'\".,")
                val: Any = val_raw

                if field == "amount":
                    num_match = re.search(r"(\d+(?:\.\d+)?)", val_raw)
                    if num_match:
                        val = float(num_match.group(1))
                elif field == "date":
                    val = self._resolve_date(val_raw, ref_date)
                elif field == "category":
                    val = self._match_category(val_raw) or val_raw.capitalize()
                elif field == "description":
                    val = val_raw.capitalize()

                return LLMExtractionResult(
                    intent="update_field",
                    field_to_update=field,
                    new_value=val,
                )

        # 2. Extract Amount
        amount = None
        # Match patterns like: $45.50, 45.50 usd, 45 inr, spent 45, paid 45, 45 dollars
        amount_patterns = [
            r"[$€£₹]\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:usd|inr|eur|gbp|dollars|bucks|rs|rupees)",
            r"(?:spent|paid|for|cost)\s+(\d+(?:\.\d+)?)",
            r"\b(\d+(?:\.\d+)?)\b",
        ]
        for pat in amount_patterns:
            m = re.search(pat, lower)
            if m:
                try:
                    parsed_amount = float(m.group(1))
                    if parsed_amount > 0 and parsed_amount < 100000000:
                        amount = parsed_amount
                        break
                except ValueError:
                    pass

        # 3. Extract Date
        date_str = self._extract_date(lower, ref_date)

        # 4. Extract Category
        category = self._detect_category(lower)

        # 5. Extract Description
        description = self._extract_description(text, amount, lower)

        # Check missing fields
        missing = []
        if amount is None:
            missing.append("amount")
        if not description:
            missing.append("description")

        return LLMExtractionResult(
            intent="add_expense",
            description=description,
            amount=amount,
            category=category,
            date=date_str,
            missing_fields=missing,
        )

    def _resolve_date(self, text: str, ref_date: datetime) -> str:
        text = text.lower().strip()
        if "today" in text:
            return ref_date.strftime("%Y-%m-%d")
        if "yesterday" in text:
            return (ref_date - timedelta(days=1)).strftime("%Y-%m-%d")
        if "tomorrow" in text:
            return (ref_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Check ISO format
        iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if iso_match:
            return iso_match.group(1)
        
        return ref_date.strftime("%Y-%m-%d")

    def _extract_date(self, text: str, ref_date: datetime) -> str:
        if "yesterday" in text:
            return (ref_date - timedelta(days=1)).strftime("%Y-%m-%d")
        if "tomorrow" in text:
            return (ref_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        if iso_match:
            return iso_match.group(1)

        return ref_date.strftime("%Y-%m-%d")

    def _match_category(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for cat in STANDARD_CATEGORIES:
            if cat.lower() in text_lower:
                return cat
        return self._detect_category(text_lower)

    def _detect_category(self, text_lower: str) -> str:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                    return cat
        return "Other"

    def _extract_description(self, original_text: str, amount: Optional[float], text_lower: str) -> str:
        cleaned = original_text
        # Remove spent/paid/bought prefixes
        cleaned = re.sub(r"^(?:i\s+)?(?:spent|paid|bought|got|purchased)\s+", "", cleaned, flags=re.IGNORECASE)
        # Remove amount mentions
        if amount is not None:
            # remove $45 or 45 dollars or for 45
            cleaned = re.sub(rf"[$€£₹]?\s*{re.escape(str(int(amount) if amount.is_integer() else amount))}(?:\.\d+)?\s*(?:dollars|usd|bucks|rs|rupees|inr)?", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(rf"\bfor\s+{re.escape(str(int(amount) if amount.is_integer() else amount))}\b", "", cleaned, flags=re.IGNORECASE)
        # Remove date words
        cleaned = re.sub(r"\b(today|yesterday|tomorrow|\d{4}-\d{2}-\d{2})\b", "", cleaned, flags=re.IGNORECASE)
        # Clean trailing/leading prepositions
        cleaned = re.sub(r"^(?:on|for|at)\s+", "", cleaned.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+(?:on|for|at)$", "", cleaned.strip(), flags=re.IGNORECASE)
        cleaned = " ".join(cleaned.split()).strip()

        if not cleaned:
            return "Expense"
        return cleaned[:100].capitalize()
