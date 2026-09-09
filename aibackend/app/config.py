import os

# AIMODEL Service URL (port 8002 by default in docker / localhost)
AIMODEL_URL = os.getenv("AIMODEL_URL", "http://localhost:8002").rstrip("/")

# Core Expense API URL (port 8000 by default in docker / localhost)
EXPENSE_API_URL = os.getenv("EXPENSE_API_URL", "http://localhost:8000").rstrip("/")

# Server config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

# Standard categories
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
