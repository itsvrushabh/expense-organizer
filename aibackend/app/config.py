import os
from pathlib import Path

# Resolve base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOCAL_MODEL = BASE_DIR / "models" / "qwen2.5-0.5b-instruct-q4_k_m.gguf"

# Model path with fallback
MODEL_PATH = os.getenv("MODEL_PATH", str(DEFAULT_LOCAL_MODEL))

# Expense Core API URL (FastAPI backend)
EXPENSE_API_URL = os.getenv("EXPENSE_API_URL", "http://localhost:8000").rstrip("/")

# Server config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

# Common expense categories
STANDARD_CATEGORIES = [
    "Food",
    "Groceries",
    "Transport",
    "Shopping",
    "Entertainment",
    "Utilities",
    "Health",
    "Travel",
    "Education",
    "Personal",
    "Other",
]
